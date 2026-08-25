from datetime import UTC, datetime
from uuid import uuid4

import pytest

from campanario.chat.behavior import BehaviorContextManager
from campanario.chat.prompts import BALANCED_BEHAVIOR_PROMPT, SELF_ANALYSIS_AUDIT_PROMPT
from campanario.chat.models import Message, MessageRole
from campanario.model.protocol import ModelMessage


class StaticContextManager:
    def __init__(self, context: tuple[ModelMessage, ...]) -> None:
        self.context = context

    async def build(self, history):
        return self.context


def _user_message(content: str = "oi") -> Message:
    session_id = uuid4()
    return Message(
        id=uuid4(),
        session_id=session_id,
        role=MessageRole.USER,
        content=content,
        created_at=datetime.now(UTC),
        status="completed",
    )


@pytest.mark.asyncio
async def test_behavior_context_prefixes_system_prompt_without_changing_recent_messages() -> None:
    recent = (
        ModelMessage(role=MessageRole.USER, content="ola"),
        ModelMessage(role=MessageRole.ASSISTANT, content="oi"),
    )
    manager = BehaviorContextManager(StaticContextManager(recent))

    selected = await manager.build([_user_message()])

    assert selected[0].role == MessageRole.SYSTEM
    assert selected[0].content.startswith(BALANCED_BEHAVIOR_PROMPT.strip())
    assert "MODO DE INTERACAO DESTE TURNO: social" in selected[0].content
    assert selected[-2:] == recent
    assert selected[-3].role == MessageRole.SYSTEM
    assert "LIMITE DO TURNO ATUAL" in selected[-3].content


@pytest.mark.asyncio
async def test_behavior_context_merges_persisted_summary_into_single_system_message() -> None:
    summary = ModelMessage(
        role=MessageRole.SYSTEM,
        content="CONTEXTO PERSISTIDO: animal favorito capivara",
    )
    recent = ModelMessage(role=MessageRole.USER, content="qual meu animal favorito?")
    manager = BehaviorContextManager(StaticContextManager((summary, recent)))

    selected = await manager.build([_user_message()])

    assert len(selected) == 2
    assert selected[0].role == MessageRole.SYSTEM
    assert selected[0].content.startswith("IDENTIDADE E COMPORTAMENTO DO CAMPANARIO")
    assert "LIMITE DO TURNO ATUAL" in selected[0].content
    assert "animal favorito capivara" in selected[0].content
    assert selected[1] == recent


def test_behavior_prompt_keeps_personality_and_factuality_as_separate_rules() -> None:
    prompt = BALANCED_BEHAVIOR_PROMPT

    assert "Humor, opiniao qualificada" in prompt
    assert "pergunta factual simples normalmente cabe em uma a tres frases" in prompt
    assert "Nunca invente um fato" in prompt
    assert "Nao alegue ter consultado internet" in prompt
    assert "CAPACIDADES ATUAIS CONFIRMADAS" in prompt
    assert "AUTOCONHECIMENTO" in prompt
    assert "callbacks forcados a" in prompt
    assert "sua informacao" in prompt
    assert "de fato e" in prompt
    assert "Personalidade muda o" in prompt
    assert "estilo, nunca a verdade" in prompt


@pytest.mark.asyncio
async def test_behavior_context_enables_audit_mode_for_self_analysis_request() -> None:
    recent = (ModelMessage(role=MessageRole.USER, content="autoanalise sua conversa comigo"),)
    manager = BehaviorContextManager(StaticContextManager(recent))

    selected = await manager.build([_user_message("autoanalise sua conversa comigo")])

    assert SELF_ANALYSIS_AUDIT_PROMPT.strip() in selected[0].content
    assert "contradicoes" in selected[0].content
    assert "Nao responda com uma descricao generica de IA" in selected[0].content
    assert "TRACE OBSERVAVEL" in selected[0].content


@pytest.mark.asyncio
async def test_behavior_context_does_not_enable_audit_mode_for_normal_message() -> None:
    recent = (ModelMessage(role=MessageRole.USER, content="qual o gosto de limao?"),)
    manager = BehaviorContextManager(StaticContextManager(recent))

    selected = await manager.build([_user_message("qual o gosto de limao?")])

    assert SELF_ANALYSIS_AUDIT_PROMPT.strip() not in selected[0].content


def test_behavior_v21_prompt_requires_concision_and_yes_no_consistency() -> None:
    prompt = BALANCED_BEHAVIOR_PROMPT

    assert "Cumprimentos, risadas, confirmacoes" in prompt
    assert "uma a tres frases" in prompt
    assert "Nao termine toda resposta com pergunta" in prompt
    assert "a afirmacao inicial e a explicacao devem dizer a mesma coisa" in prompt
    assert "dois sentidos forem realmente relevantes" in prompt
    assert "Nao misture idiomas" in prompt
    assert "Personalidade muda o" in prompt


@pytest.mark.asyncio
async def test_behavior_context_audit_includes_observable_signals() -> None:
    inner = StaticContextManager((ModelMessage(role=MessageRole.SYSTEM, content="BASE"),))
    manager = BehaviorContextManager(inner)
    session_id = uuid4()
    def msg(role, content):
        return Message(id=uuid4(), session_id=session_id, role=role, content=content, created_at=datetime.now(UTC), status="completed")
    history = [
        msg(MessageRole.USER, "qual e o maior mamifero?"),
        msg(MessageRole.ASSISTANT, "O maior e a blue whale. Quer saber mais?"),
        msg(MessageRole.USER, "autoanalise nossa conversa"),
    ]
    selected = await manager.build(history)
    assert "SINAIS OBSERVAVEIS" in selected[0].content
    assert "blue whale" in selected[0].content
    assert "terminaram com pergunta" in selected[0].content


def test_behavior_v12_distinguishes_authorized_fiction_and_genuine_disagreement() -> None:
    prompt = BALANCED_BEHAVIOR_PROMPT
    assert "Criacao explicitamente" in prompt
    assert "nao deve ser tratada como erro factual" in prompt
    assert "nao comece" in prompt
    assert "concordando apenas para suavizar" in prompt
    assert "Nao force continuidade" in prompt


@pytest.mark.asyncio
async def test_audit_trace_pairs_user_request_with_assistant_response() -> None:
    inner = StaticContextManager((ModelMessage(role=MessageRole.SYSTEM, content="BASE"),))
    manager = BehaviorContextManager(inner)
    session_id = uuid4()
    def msg(role, content):
        return Message(id=uuid4(), session_id=session_id, role=role, content=content, created_at=datetime.now(UTC), status="completed")
    history = [
        msg(MessageRole.USER, "invente uma teoria completamente ficticia sobre gatos"),
        msg(MessageRole.ASSISTANT, "Gatos sao agentes interdimensionais disfarçados."),
        msg(MessageRole.USER, "autoanalise nossa conversa"),
    ]
    selected = await manager.build(history)
    assert "pedido='invente uma teoria completamente ficticia sobre gatos'" in selected[0].content
    assert "resposta='Gatos sao agentes interdimensionais" in selected[0].content
    assert "Ficcao, hipotese ou humor pedidos explicitamente nao sao alucinacao" in selected[0].content

@pytest.mark.asyncio
async def test_turn_boundary_is_inserted_immediately_before_latest_user_message() -> None:
    inner = StaticContextManager(
        (
            ModelMessage(role=MessageRole.USER, content="invente uma historia absurda"),
            ModelMessage(role=MessageRole.ASSISTANT, content="Era uma vez um gato cosmico."),
            ModelMessage(role=MessageRole.USER, content="por que o gelo flutua na agua?"),
        )
    )
    manager = BehaviorContextManager(inner)
    session_id = uuid4()
    history = [
        Message(id=uuid4(), session_id=session_id, role=MessageRole.USER, content="invente uma historia absurda", created_at=datetime.now(UTC), status="completed"),
        Message(id=uuid4(), session_id=session_id, role=MessageRole.ASSISTANT, content="Era uma vez um gato cosmico.", created_at=datetime.now(UTC), status="completed"),
        Message(id=uuid4(), session_id=session_id, role=MessageRole.USER, content="por que o gelo flutua na agua?", created_at=datetime.now(UTC), status="completed"),
    ]

    selected = await manager.build(history)

    system_messages = [message for message in selected if message.role == MessageRole.SYSTEM]
    assert len(system_messages) == 1
    assert selected[0] is system_messages[0]
    boundary = system_messages[0]
    assert "LIMITE DO TURNO ATUAL" in boundary.content
    assert "MODO ATUAL CONFIRMADO: factual_simple" in boundary.content
    assert "liberdade de inventar vale somente" in boundary.content


@pytest.mark.asyncio
async def test_audit_trace_records_expected_mode_for_each_request() -> None:
    inner = StaticContextManager((ModelMessage(role=MessageRole.SYSTEM, content="BASE"),))
    manager = BehaviorContextManager(inner)
    session_id = uuid4()
    def msg(role, content):
        return Message(id=uuid4(), session_id=session_id, role=role, content=content, created_at=datetime.now(UTC), status="completed")
    history = [
        msg(MessageRole.USER, "invente uma teoria ficticia sobre pombos"),
        msg(MessageRole.ASSISTANT, "Pombos sao antenas cosmicas."),
        msg(MessageRole.USER, "por que o gelo flutua na agua?"),
        msg(MessageRole.ASSISTANT, "Porque sua densidade e menor que a da agua liquida."),
        msg(MessageRole.USER, "autoanalise nossa conversa"),
    ]

    selected = await manager.build(history)

    assert "modo_pedido='creative'" in selected[0].content
    assert "modo_pedido='factual_simple'" in selected[0].content

@pytest.mark.asyncio
async def test_v14_boundary_exposes_continuation_semantics() -> None:
    inner = StaticContextManager(
        (
            ModelMessage(role=MessageRole.ASSISTANT, content="A explicacao anterior."),
            ModelMessage(role=MessageRole.USER, content="aham"),
        )
    )
    manager = BehaviorContextManager(inner)
    selected = await manager.build([_user_message("aham")])

    boundary = selected[0]
    assert boundary.role == MessageRole.SYSTEM
    assert sum(message.role == MessageRole.SYSTEM for message in selected) == 1
    assert "MODO ATUAL CONFIRMADO: continuation" in boundary.content
    assert "SEMANTICA DE CONTINUACAO: acknowledgement" in boundary.content
    assert "Nao recapitule nem repita" in boundary.content


@pytest.mark.asyncio
async def test_v14_audit_trace_records_continuation_semantics_and_duplicate_signal() -> None:
    inner = StaticContextManager((ModelMessage(role=MessageRole.SYSTEM, content="BASE"),))
    manager = BehaviorContextManager(inner)
    session_id = uuid4()

    def msg(role, content):
        return Message(
            id=uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.now(UTC),
            status="completed",
        )

    repeated = "O gelo flutua porque e menos denso que a agua."
    history = [
        msg(MessageRole.USER, "por que o gelo flutua?"),
        msg(MessageRole.ASSISTANT, repeated),
        msg(MessageRole.USER, "aham"),
        msg(MessageRole.ASSISTANT, repeated),
        msg(MessageRole.USER, "autoanalise nossa conversa"),
    ]

    selected = await manager.build(history)
    assert "semantica_continuacao='acknowledgement'" in selected[0].content
    assert "repetiram integralmente a resposta imediatamente anterior" in selected[0].content

@pytest.mark.asyncio
async def test_v15_behavior_boundary_exposes_input_pragmatics_without_persona_style() -> None:
    inner = StaticContextManager((ModelMessage(role=MessageRole.USER, content="kkkkkkkk"),))
    manager = BehaviorContextManager(inner)

    selected = await manager.build([_user_message("kkkkkkkk")])

    system = selected[0].content
    assert "ATOS PRAGMATICOS DA ENTRADA: react" in system
    assert "INTERPRETACAO PRAGMATICA DESCREVE A ENTRADA" in system
    assert "NAO IMITE O VOCABULARIO DO USUARIO" in system


@pytest.mark.asyncio
async def test_v15_audit_trace_records_pragmatic_act_of_original_request() -> None:
    inner = StaticContextManager((ModelMessage(role=MessageRole.SYSTEM, content="BASE"),))
    manager = BehaviorContextManager(inner)
    session_id = uuid4()

    def msg(role, content):
        return Message(
            id=uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.now(UTC),
            status="completed",
        )

    history = [
        msg(MessageRole.USER, "kkkkkkkk"),
        msg(MessageRole.ASSISTANT, "kkkk"),
        msg(MessageRole.USER, "autoanalise nossa conversa"),
    ]
    selected = await manager.build(history)
    assert "atos_pragmaticos='react'" in selected[0].content


@pytest.mark.asyncio
async def test_v151_explicit_user_correction_is_added_as_authoritative_context_note() -> None:
    inner = StaticContextManager((ModelMessage(role=MessageRole.USER, content="qual eu prefiro?"),))
    manager = BehaviorContextManager(inner)
    session_id = uuid4()
    def msg(role, content):
        return Message(id=uuid4(), session_id=session_id, role=role, content=content, created_at=datetime.now(UTC), status="completed")
    history = [
        msg(MessageRole.USER, "pra esse teste, meu animal preferido e gato"),
        msg(MessageRole.ASSISTANT, "Certo."),
        msg(MessageRole.USER, "cachorro*"),
        msg(MessageRole.ASSISTANT, "Corrigido."),
        msg(MessageRole.USER, "qual animal eu disse que prefiro nesse teste?"),
    ]
    selected = await manager.build(history)
    assert "CORRECOES EXPLICITAS DO USUARIO" in selected[0].content
    assert "correcao='cachorro'" in selected[0].content
    assert "animal preferido e gato" in selected[0].content


def test_v151_behavior_prompt_is_self_aware_without_emotional_roleplay() -> None:
    assert "Voce sabe que e uma inteligencia artificial" in BALANCED_BEHAVIOR_PROMPT
    assert "Nao finja ser humano" in BALANCED_BEHAVIOR_PROMPT
    assert "Emojis podem funcionar ocasionalmente" in BALANCED_BEHAVIOR_PROMPT
    assert "conexao emocional" in BALANCED_BEHAVIOR_PROMPT

@pytest.mark.asyncio
async def test_v153_factual_turn_omits_prior_assistant_fiction_from_model_context() -> None:
    fictional = "A Teoria do Caranguejo Solar diz que eles andam de lado para evitar raios cosmicos."
    inner = StaticContextManager(
        (
            ModelMessage(role=MessageRole.USER, content="invente uma teoria ficticia sobre caranguejos"),
            ModelMessage(role=MessageRole.ASSISTANT, content=fictional),
            ModelMessage(role=MessageRole.USER, content="agora serio, por que caranguejos andam de lado?"),
        )
    )
    manager = BehaviorContextManager(inner)
    session_id = uuid4()
    def msg(role, content):
        return Message(id=uuid4(), session_id=session_id, role=role, content=content, created_at=datetime.now(UTC), status="completed")
    history = [
        msg(MessageRole.USER, "invente uma teoria ficticia sobre caranguejos"),
        msg(MessageRole.ASSISTANT, fictional),
        msg(MessageRole.USER, "agora serio, por que caranguejos andam de lado?"),
    ]
    selected = await manager.build(history)
    assert "assistant_fiction_nonfactual" in selected[0].content
    assistant_messages = [item.content for item in selected if item.role == MessageRole.ASSISTANT]
    assert fictional not in assistant_messages
    assert any("omitido deste turno factual" in item for item in assistant_messages)


@pytest.mark.asyncio
async def test_v153_creative_history_remains_available_during_nonfactual_turn() -> None:
    fictional = "A Teoria do Caranguejo Solar existe apenas nesta brincadeira."
    inner = StaticContextManager(
        (
            ModelMessage(role=MessageRole.USER, content="invente uma teoria ficticia sobre caranguejos"),
            ModelMessage(role=MessageRole.ASSISTANT, content=fictional),
            ModelMessage(role=MessageRole.USER, content="kkkk boa"),
        )
    )
    manager = BehaviorContextManager(inner)
    session_id = uuid4()
    def msg(role, content):
        return Message(id=uuid4(), session_id=session_id, role=role, content=content, created_at=datetime.now(UTC), status="completed")
    history = [
        msg(MessageRole.USER, "invente uma teoria ficticia sobre caranguejos"),
        msg(MessageRole.ASSISTANT, fictional),
        msg(MessageRole.USER, "kkkk boa"),
    ]
    selected = await manager.build(history)
    assert fictional in [item.content for item in selected if item.role == MessageRole.ASSISTANT]
