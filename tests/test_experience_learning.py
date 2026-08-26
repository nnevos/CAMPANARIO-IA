from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import campanario.api as api_module
import campanario.composition as composition
from campanario.config import Settings
from campanario.main import app
from campanario.model.protocol import ModelChunk
from campanario.runtime.events import EventType


class QueueProvider:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.requests = []

    async def health(self) -> bool:
        return True

    async def stream(self, request):
        self.requests.append(request)
        text = self.responses.pop(0) if self.responses else "Entendido."
        yield ModelChunk(text=text)
        yield ModelChunk(text="", done=True)


@pytest.mark.asyncio
async def test_explicit_user_fact_is_learned_recalled_and_survives_restart(monkeypatch, tmp_path) -> None:
    db = tmp_path / "experience.db"
    provider = QueueProvider(["Certo.", "Você usa Windows 11."])
    monkeypatch.setattr(composition, "build_model_provider", lambda config: provider)
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{db}", create_schema=True)
    session = runtime.sessions.create_session()

    _ = [event async for event in runtime.conversation.stream_turn(session.id, "meu sistema operacional é Windows 11")]
    memories = runtime.experience.list_memories()
    assert len(memories) == 1
    assert memories[0].key == "user.sistema.operacional"
    assert memories[0].value == "Windows 11"
    assert memories[0].source.value == "user_explicit"
    assert memories[0].source_message_id is not None
    assert [e.event_type for e in runtime.events.replay() if e.event_type.value.startswith("MEMORY_")] == [
        EventType.MEMORY_CANDIDATE,
        EventType.MEMORY_WRITTEN,
    ]

    runtime.stop()
    provider2 = QueueProvider(["Windows 11."])
    monkeypatch.setattr(composition, "build_model_provider", lambda config: provider2)
    restarted = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{db}", create_schema=False)
    recalled = restarted.experience.recall("qual sistema operacional eu uso?")
    assert recalled and recalled[0].value == "Windows 11"


@pytest.mark.asyncio
async def test_curiosity_answer_is_captured_but_sensitive_answer_is_not(monkeypatch, tmp_path) -> None:
    provider = QueueProvider([
        "Qual sistema operacional você usa?",
        "Ótimo, isso muda o caminho.",
        "Qual é a sua senha?",
        "Não vou guardar segredo desse tipo.",
    ])
    monkeypatch.setattr(composition, "build_model_provider", lambda config: provider)
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{tmp_path / 'qa.db'}", create_schema=True)
    session = runtime.sessions.create_session()

    _ = [event async for event in runtime.conversation.stream_turn(session.id, "preciso configurar uma integração local")]
    _ = [event async for event in runtime.conversation.stream_turn(session.id, "Windows 11")]
    assert any(memory.value == "Windows 11" and memory.source.value == "user_answer" for memory in runtime.experience.list_memories())

    _ = [event async for event in runtime.conversation.stream_turn(session.id, "agora uma configuração secreta")]
    before = len(runtime.experience.list_memories())
    _ = [event async for event in runtime.conversation.stream_turn(session.id, "minha senha é abc123")]
    assert len(runtime.experience.list_memories()) == before


@pytest.mark.asyncio
async def test_new_explicit_evidence_supersedes_old_value_and_admin_can_forget(monkeypatch, tmp_path) -> None:
    provider = QueueProvider(["ok", "ok"])
    monkeypatch.setattr(composition, "build_model_provider", lambda config: provider)
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{tmp_path / 'correct.db'}", create_schema=True)
    session = runtime.sessions.create_session()

    _ = [event async for event in runtime.conversation.stream_turn(session.id, "meu editor é VS Code")]
    first = runtime.experience.list_memories()[0]
    _ = [event async for event in runtime.conversation.stream_turn(session.id, "meu editor é Zed")]
    active = runtime.experience.list_memories()
    all_items = runtime.experience.list_memories(include_inactive=True)
    assert len(active) == 1 and active[0].value == "Zed"
    assert active[0].supersedes_id == first.id
    assert any(item.id == first.id and item.status.value == "superseded" for item in all_items)

    forgotten = runtime.experience.forget(active[0].id, reason="usuario pediu")
    assert forgotten.status.value == "forgotten"
    assert runtime.experience.list_memories() == []


@pytest.mark.asyncio
async def test_memory_context_is_shared_and_keeps_inference_separate_from_fact(monkeypatch, tmp_path) -> None:
    provider = QueueProvider(["Certo.", "Resposta baseada no contexto."])
    monkeypatch.setattr(composition, "build_model_provider", lambda config: provider)
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{tmp_path / 'context.db'}", create_schema=True)
    session = runtime.sessions.create_session()

    _ = [event async for event in runtime.conversation.stream_turn(session.id, "eu prefiro respostas curtas")]
    inference = runtime.experience.create_inference(
        value="talvez goste de exemplos de terminal",
        evidence="hipotese de um agente",
        source_agent_id="todd",
        session_id=session.id,
    )
    assert inference.kind.value == "inference"
    assert inference.confidence < 0.8

    _ = [event async for event in runtime.conversation.stream_turn(session.id, "responda curto com um exemplo de terminal")]
    system_prompt = provider.requests[-1].messages[0].content
    assert "Nao invente fatos sobre o usuario" in system_prompt
    assert "respostas curtas" in system_prompt
    assert "INFERENCIA" in system_prompt
    memory_section = system_prompt.split("CONTEXTO APRENDIDO RELEVANTE", 1)[1].split("AGENTE COM PRIORIDADE", 1)[0]
    assert "source_agent" not in memory_section.lower()  # shared store, not an agent-owned fact bank


def test_memory_admin_api_lists_corrects_and_forgets(monkeypatch, tmp_path) -> None:
    provider = QueueProvider([])
    monkeypatch.setattr(composition, "build_model_provider", lambda config: provider)
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{tmp_path / 'api.db'}", create_schema=True)
    monkeypatch.setattr(api_module, "get_runtime", lambda: runtime)
    # Create through the experience API to avoid a model turn in this sync test.
    memory = runtime.experience.create_inference(
        value="talvez prefira modo compacto",
        evidence="teste",
        source_agent_id="morgana",
        confidence=0.5,
    )
    client = TestClient(app)

    listed = client.get("/api/v1/memory")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == str(memory.id)
    assert listed.json()[0]["kind"] == "inference"

    corrected = client.patch(f"/api/v1/memory/{memory.id}", json={"value": "prefere modo compacto", "reason": "confirmado"})
    assert corrected.status_code == 200
    assert corrected.json()["kind"] == "fact"
    corrected_id = UUID(corrected.json()["id"])

    forgotten = client.post(f"/api/v1/memory/{corrected_id}/forget", json={"reason": "usuario pediu"})
    assert forgotten.status_code == 200
    assert forgotten.json()["status"] == "forgotten"
    assert client.get("/api/v1/memory").json() == []

@pytest.mark.asyncio
async def test_shared_outcome_memory_and_natural_forget(monkeypatch, tmp_path) -> None:
    provider = QueueProvider(["Tente reiniciar apenas o worker afetado.", "Boa.", "Certo."])
    monkeypatch.setattr(composition, "build_model_provider", lambda config: provider)
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{tmp_path / 'outcome.db'}", create_schema=True)
    session = runtime.sessions.create_session()

    _ = [event async for event in runtime.conversation.stream_turn(session.id, "o worker travou")]
    _ = [event async for event in runtime.conversation.stream_turn(session.id, "isso funcionou")]
    experiences = [m for m in runtime.experience.list_memories() if m.kind.value == "shared_experience"]
    assert len(experiences) == 1
    assert "funcionou" in experiences[0].value
    assert experiences[0].subject.startswith("relationship.")

    _ = [event async for event in runtime.conversation.stream_turn(session.id, "esquece sobre reiniciar o worker")]
    assert not [m for m in runtime.experience.list_memories() if m.kind.value == "shared_experience"]
