import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.models import Message, MessageRole


def _message(
    session_id: UUID,
    role: MessageRole,
    content: str,
    offset: int,
    status: str = "completed",
) -> Message:
    return Message(
        id=uuid4(),
        session_id=session_id,
        role=role,
        content=content,
        created_at=datetime.now(UTC) + timedelta(seconds=offset),
        status=status,
    )


@pytest.mark.asyncio
async def test_short_history_keeps_all_completed_messages_in_order() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "u1", 1),
        _message(session_id, MessageRole.ASSISTANT, "a1", 2),
        _message(session_id, MessageRole.USER, "u2", 3),
    ]

    selected = await RecentMessagesContextManager(10).build(history)

    assert [(item.role, item.content) for item in selected] == [
        (MessageRole.USER, "u1"),
        (MessageRole.ASSISTANT, "a1"),
        (MessageRole.USER, "u2"),
    ]


@pytest.mark.asyncio
async def test_long_history_uses_recent_window_and_avoids_orphan_assistant() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "u1", 1),
        _message(session_id, MessageRole.ASSISTANT, "a1", 2),
        _message(session_id, MessageRole.USER, "u2", 3),
        _message(session_id, MessageRole.ASSISTANT, "a2", 4),
        _message(session_id, MessageRole.USER, "u3", 5),
    ]

    selected = await RecentMessagesContextManager(4).build(history)

    assert [item.content for item in selected] == ["u2", "a2", "u3"]


@pytest.mark.asyncio
async def test_dangling_user_messages_are_preserved() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "u1", 1),
        _message(session_id, MessageRole.ASSISTANT, "a1", 2),
        _message(session_id, MessageRole.USER, "failed-user", 3),
        _message(session_id, MessageRole.USER, "current-user", 4),
    ]

    selected = await RecentMessagesContextManager(2).build(history)

    assert [item.content for item in selected] == ["failed-user", "current-user"]


@pytest.mark.asyncio
async def test_non_completed_messages_do_not_enter_context() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "u1", 1),
        _message(session_id, MessageRole.ASSISTANT, "partial", 2, status="failed"),
        _message(session_id, MessageRole.USER, "u2", 3),
    ]

    selected = await RecentMessagesContextManager(10).build(history)

    assert [item.content for item in selected] == ["u1", "u2"]

from campanario.chat.context import SummarizingContextManager
from campanario.chat.models import ContextSummary
from campanario.model.protocol import ModelChunk, ModelUnavailableError


class InMemorySummaries:
    def __init__(self) -> None:
        self.items: dict[UUID, ContextSummary] = {}

    def get(self, session_id: UUID) -> ContextSummary | None:
        return self.items.get(session_id)

    def upsert(self, summary: ContextSummary) -> ContextSummary:
        self.items[summary.session_id] = summary
        return summary


class SummaryProvider:
    def __init__(self, text: str | None = None) -> None:
        self.text = text or json.dumps(
            {
                "version": 1,
                "first_user_message": "quem e voce?",
                "user_facts": [],
                "user_preferences": [],
                "user_plans": [],
                "user_constraints": [],
                "conversation_topics": ["apresentacao"],
                "assistant_context": [],
            },
            ensure_ascii=False,
        )
        self.requests = []

    async def health(self) -> bool:
        return True

    async def stream(self, request):
        self.requests.append(request)
        yield ModelChunk(text=self.text)


@pytest.mark.asyncio
async def test_summarizing_context_persists_old_messages_and_injects_summary() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "quem e voce?", 1),
        _message(session_id, MessageRole.ASSISTANT, "sou o Campanario", 2),
        _message(session_id, MessageRole.USER, "u2", 3),
        _message(session_id, MessageRole.ASSISTANT, "a2", 4),
        _message(session_id, MessageRole.USER, "qual foi a primeira pergunta?", 5),
    ]
    summaries = InMemorySummaries()
    provider = SummaryProvider()
    manager = SummarizingContextManager(3, summaries, provider, "fake-model")

    selected = await manager.build(history)

    assert len(provider.requests) == 2
    assert summaries.get(session_id) is not None
    assert selected[0].role == MessageRole.SYSTEM
    assert "quem e voce?" in selected[0].content
    assert [item.content for item in selected[1:]] == ["u2", "a2", "qual foi a primeira pergunta?"]


@pytest.mark.asyncio
async def test_summarizing_context_reuses_persisted_summary_without_resummarizing_same_prefix() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "u1", 1),
        _message(session_id, MessageRole.ASSISTANT, "a1", 2),
        _message(session_id, MessageRole.USER, "u2", 3),
        _message(session_id, MessageRole.ASSISTANT, "a2", 4),
    ]
    summaries = InMemorySummaries()
    provider = SummaryProvider(
        json.dumps(
            {
                "version": 1,
                "first_user_message": "u1",
                "user_facts": ["fato inicial"],
                "user_preferences": [],
                "user_plans": [],
                "user_constraints": [],
                "conversation_topics": [],
                "assistant_context": [],
            }
        )
    )
    manager = SummarizingContextManager(2, summaries, provider, "fake-model")

    first = await manager.build(history)
    second = await manager.build(history)

    assert len(provider.requests) == 2
    assert first[0].content == second[0].content


class FailingSummaryProvider:
    async def health(self) -> bool:
        return False

    async def stream(self, request):
        if False:
            yield
        raise ModelUnavailableError("offline")


@pytest.mark.asyncio
async def test_summarizing_context_falls_back_to_recent_window_when_summary_fails() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "u1", 1),
        _message(session_id, MessageRole.ASSISTANT, "a1", 2),
        _message(session_id, MessageRole.USER, "u2", 3),
    ]
    manager = SummarizingContextManager(
        2, InMemorySummaries(), FailingSummaryProvider(), "fake-model"
    )

    selected = await manager.build(history)

    assert [item.content for item in selected] == ["u2"]

@pytest.mark.asyncio
async def test_summarizing_context_updates_previous_summary_when_window_advances() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "u1", 1),
        _message(session_id, MessageRole.ASSISTANT, "a1", 2),
        _message(session_id, MessageRole.USER, "u2", 3),
        _message(session_id, MessageRole.ASSISTANT, "a2", 4),
    ]
    summaries = InMemorySummaries()
    summary_1 = json.dumps(
        {
            "version": 1,
            "first_user_message": "u1",
            "user_facts": ["fato-1"],
            "user_preferences": [],
            "user_plans": [],
            "user_constraints": [],
            "conversation_topics": [],
            "assistant_context": [],
        }
    )
    provider = SummaryProvider(summary_1)
    manager = SummarizingContextManager(2, summaries, provider, "fake-model")
    await manager.build(history)

    summary_2 = json.dumps(
        {
            "version": 1,
            "first_user_message": "u1",
            "user_facts": ["fato-1", "fato-2"],
            "user_preferences": [],
            "user_plans": [],
            "user_constraints": [],
            "conversation_topics": [],
            "assistant_context": [],
        }
    )
    provider.text = summary_2
    history.extend(
        [
            _message(session_id, MessageRole.USER, "u3", 5),
            _message(session_id, MessageRole.ASSISTANT, "a3", 6),
        ]
    )
    selected = await manager.build(history)

    assert len(provider.requests) == 4
    assert "fato-1" in provider.requests[2].messages[0].content
    assert json.loads(summaries.get(session_id).content) == json.loads(summary_2)
    assert selected[0].role == MessageRole.SYSTEM


def _structured_summary(**overrides) -> str:
    data = {
        "version": 1,
        "first_user_message": "inicio",
        "user_facts": [],
        "user_preferences": [],
        "user_plans": [],
        "user_constraints": [],
        "conversation_topics": [],
        "assistant_context": [],
    }
    data.update(overrides)
    return json.dumps(data, ensure_ascii=False)


@pytest.mark.asyncio
async def test_structured_summary_prompt_separates_user_evidence_from_assistant_speculation() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "Meu primeiro livro sera astronomia.", 1),
        _message(
            session_id,
            MessageRole.ASSISTANT,
            "Talvez voce leve ficcao cientifica ou autoajuda.",
            2,
        ),
        _message(session_id, MessageRole.USER, "Meu segundo livro sera historia.", 3),
        _message(session_id, MessageRole.ASSISTANT, "Legal.", 4),
        _message(session_id, MessageRole.USER, "recente", 5),
    ]
    provider = SummaryProvider(
        _structured_summary(
            first_user_message="Meu primeiro livro sera astronomia.",
            user_plans=["Livros: astronomia; historia"],
            assistant_context=["O assistant sugeriu outros generos sem confirmacao do usuario."],
        )
    )
    manager = SummarizingContextManager(1, InMemorySummaries(), provider, "fake-model")

    selected = await manager.build(history)

    user_prompt = provider.requests[0].messages[0].content
    assistant_prompt = provider.requests[1].messages[0].content
    assert '"Meu primeiro livro sera astronomia."' in user_prompt
    assert "Talvez voce leve ficcao cientifica ou autoajuda." not in user_prompt
    assert '"Talvez voce leve ficcao cientifica ou autoajuda."' in assistant_prompt
    assert "Meu primeiro livro sera astronomia." not in assistant_prompt
    assert "NAO recebera mensagens ASSISTANT" in user_prompt
    assert "NAO pode produzir autoridade" in assistant_prompt
    assert "astronomia; historia" in selected[0].content
    assert "prioridade sobre assistant_context" in selected[0].content


@pytest.mark.asyncio
async def test_legacy_freeform_summary_is_rebuilt_from_old_messages() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "codigo CODIGO-TESTE-4821", 1),
        _message(session_id, MessageRole.ASSISTANT, "anotado", 2),
        _message(session_id, MessageRole.USER, "animal capivara", 3),
        _message(session_id, MessageRole.ASSISTANT, "ok", 4),
        _message(session_id, MessageRole.USER, "recente", 5),
    ]
    summaries = InMemorySummaries()
    summaries.upsert(
        ContextSummary(
            session_id=session_id,
            content="Resumo antigo livre e potencialmente contaminado.",
            through_message_id=history[1].id,
            updated_at=datetime.now(UTC),
        )
    )
    provider = SummaryProvider(
        _structured_summary(
            first_user_message="codigo CODIGO-TESTE-4821",
            user_facts=["codigo=CODIGO-TESTE-4821", "animal=capivara"],
        )
    )
    manager = SummarizingContextManager(1, summaries, provider, "fake-model")

    selected = await manager.build(history)

    assert len(provider.requests) == 2
    prompt = provider.requests[0].messages[0].content
    assert "Resumo antigo livre e potencialmente contaminado" not in prompt
    assert "codigo CODIGO-TESTE-4821" in prompt
    assert "animal capivara" in prompt
    saved = json.loads(summaries.get(session_id).content)
    assert saved["version"] == 1
    assert saved["user_facts"] == ["codigo=CODIGO-TESTE-4821", "animal=capivara"]
    assert "CODIGO-TESTE-4821" in selected[0].content


@pytest.mark.asyncio
async def test_persisted_context_tells_model_restart_does_not_imply_memory_loss() -> None:
    session_id = uuid4()
    history = [
        _message(session_id, MessageRole.USER, "codigo CODIGO-TESTE-4821", 1),
        _message(session_id, MessageRole.ASSISTANT, "anotado", 2),
        _message(session_id, MessageRole.USER, "u2", 3),
        _message(session_id, MessageRole.ASSISTANT, "a2", 4),
    ]
    summaries = InMemorySummaries()
    provider = SummaryProvider(
        _structured_summary(
            first_user_message="codigo CODIGO-TESTE-4821",
            user_facts=["codigo=CODIGO-TESTE-4821"],
        )
    )
    manager = SummarizingContextManager(2, summaries, provider, "fake-model")

    selected = await manager.build(history)

    assert "pode sobreviver a reinicios" in selected[0].content
    assert "nao alegue perda de contexto" in selected[0].content
