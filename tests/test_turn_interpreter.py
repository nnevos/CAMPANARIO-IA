from datetime import UTC, datetime
from uuid import uuid4

import pytest

from campanario.chat.turns import ContinuationKind, ConversationTurnInterpreter, TurnMode
from campanario.chat.models import Message, MessageRole


def _message(role: MessageRole, content: str) -> Message:
    return Message(
        id=uuid4(),
        session_id=uuid4(),
        role=role,
        content=content,
        created_at=datetime.now(UTC),
        status="completed",
    )


@pytest.mark.parametrize("text", ["oi", "beleza?", "kkk", "tudo certo?"])
def test_interpreter_detects_social_turns(text: str) -> None:
    result = ConversationTurnInterpreter().interpret([_message(MessageRole.USER, text)])
    assert result.mode == TurnMode.SOCIAL


@pytest.mark.parametrize(
    "text",
    ["qual o gosto de limão?", "quem é Karl Marx?", "quanto é 17 vezes 6?", "a Lua gira em torno da Terra?"],
)
def test_interpreter_detects_simple_factual_turns(text: str) -> None:
    result = ConversationTurnInterpreter().interpret([_message(MessageRole.USER, text)])
    assert result.mode == TurnMode.FACTUAL_SIMPLE


def test_interpreter_detects_technical_turn() -> None:
    result = ConversationTurnInterpreter().interpret(
        [_message(MessageRole.USER, "me ajude a corrigir um erro nessa API Python")]
    )
    assert result.mode == TurnMode.TECHNICAL


def test_interpreter_detects_discussion_turn() -> None:
    result = ConversationTurnInterpreter().interpret(
        [_message(MessageRole.USER, "na sua opinião, isso faz sentido moralmente?")]
    )
    assert result.mode == TurnMode.DISCUSSION


def test_interpreter_detects_creative_turn() -> None:
    result = ConversationTurnInterpreter().interpret(
        [_message(MessageRole.USER, "crie uma história curta sobre uma cidade na Lua")]
    )
    assert result.mode == TurnMode.CREATIVE


def test_interpreter_detects_audit_turn() -> None:
    result = ConversationTurnInterpreter().interpret(
        [_message(MessageRole.USER, "autoanalise nossa conversa e ache seus erros")]
    )
    assert result.mode == TurnMode.AUDIT


@pytest.mark.parametrize("text", ["sim", "nao", "ok", "certo"])
def test_interpreter_detects_short_continuations(text: str) -> None:
    result = ConversationTurnInterpreter().interpret([_message(MessageRole.USER, text)])
    assert result.mode == TurnMode.CONTINUATION
    assert result.continuation_kind is not None
    assert "resposta anterior" in result.guidance or "fluxo anterior" in result.guidance

@pytest.mark.parametrize("text", ["entendi", "pois é"])
def test_interpreter_detects_natural_short_continuations(text: str) -> None:
    result = ConversationTurnInterpreter().interpret([_message(MessageRole.USER, text)])
    assert result.mode == TurnMode.CONTINUATION
    assert result.continuation_kind is not None
    assert "anterior" in result.guidance.lower()

@pytest.mark.parametrize("text", ["aham", "uhum", "pois então"])
def test_interpreter_detects_more_natural_continuations(text: str) -> None:
    result = ConversationTurnInterpreter().interpret([_message(MessageRole.USER, text)])
    assert result.mode == TurnMode.CONTINUATION


def test_factual_turn_overrides_previous_creative_context() -> None:
    history = [
        _message(MessageRole.USER, "invente uma teoria absurda sobre gatos"),
        _message(MessageRole.ASSISTANT, "Gatos sao agentes interdimensionais."),
        _message(MessageRole.USER, "por que o gelo flutua na agua?"),
    ]
    result = ConversationTurnInterpreter().interpret(history)
    assert result.mode == TurnMode.FACTUAL_SIMPLE


def test_technical_turn_overrides_previous_social_context() -> None:
    history = [
        _message(MessageRole.USER, "kkkk hoje eu to sem assunto"),
        _message(MessageRole.ASSISTANT, "Normal kkk."),
        _message(MessageRole.USER, "minha API Python retorna erro 500"),
    ]
    result = ConversationTurnInterpreter().interpret(history)
    assert result.mode == TurnMode.TECHNICAL

@pytest.mark.parametrize("text", ["ok", "aham", "entendi", "certo"])
def test_v14_acknowledgements_have_specific_semantics(text: str) -> None:
    result = ConversationTurnInterpreter().interpret([_message(MessageRole.USER, text)])
    assert result.mode == TurnMode.CONTINUATION
    assert result.continuation_kind.value == "acknowledgement"
    assert "Nao recapitule nem repita" in result.guidance


@pytest.mark.parametrize("text", ["pois é", "é complicado", "pois então"])
def test_v14_reflections_have_specific_semantics(text: str) -> None:
    result = ConversationTurnInterpreter().interpret([_message(MessageRole.USER, text)])
    assert result.mode == TurnMode.CONTINUATION
    assert result.continuation_kind.value == "reflection"
    assert "Reflexao curta" in result.guidance


@pytest.mark.parametrize("text", ["mas posso estar errado", "não tenho certeza"])
def test_v14_revisions_have_specific_semantics(text: str) -> None:
    result = ConversationTurnInterpreter().interpret([_message(MessageRole.USER, text)])
    assert result.mode == TurnMode.CONTINUATION
    assert result.continuation_kind.value == "revision"
    assert "Revisao, hesitacao ou suspeita" in result.guidance


@pytest.mark.parametrize("text", ["deixa isso pra lá por enquanto", "esquece isso", "vamos mudar de assunto"])
def test_v14_topic_drop_has_specific_semantics(text: str) -> None:
    result = ConversationTurnInterpreter().interpret([_message(MessageRole.USER, text)])
    assert result.mode == TurnMode.CONTINUATION
    assert result.continuation_kind.value == "topic_drop"
    assert "pare esse tema" in result.guidance

@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("acho que posso ter entendido errado", ContinuationKind.REVISION),
        ("talvez eu esteja confundindo as duas coisas", ContinuationKind.REVISION),
        ("muda de assunto", ContinuationKind.TOPIC_DROP),
        ("blz", ContinuationKind.ACKNOWLEDGEMENT),
    ],
)
def test_v142_continuation_semantics_cover_manual_gate_phrases(text, kind) -> None:
    interpretation = ConversationTurnInterpreter().interpret_text(text)

    assert interpretation.mode == TurnMode.CONTINUATION
    assert interpretation.continuation_kind == kind


def test_v142_acknowledgement_guidance_is_short_and_forbids_mirroring() -> None:
    interpretation = ConversationTurnInterpreter().interpret_text("blz")

    assert "no maximo 4 palavras" in interpretation.guidance
    assert "blz tambem" in interpretation.guidance
    assert "nao faca pergunta" in interpretation.guidance


def test_v142_topic_drop_guidance_forbids_new_topic_question() -> None:
    interpretation = ConversationTurnInterpreter().interpret_text("muda de assunto")

    assert interpretation.continuation_kind == ContinuationKind.TOPIC_DROP
    assert "no maximo 4 palavras" in interpretation.guidance
    assert "nao proponha tema novo" in interpretation.guidance
    assert "nao pergunte" in interpretation.guidance

@pytest.mark.parametrize("text", ["saquei", "fechou", "boa"])
def test_v15_pragmatics_drives_colloquial_acknowledgements(text: str) -> None:
    result = ConversationTurnInterpreter().interpret_text(text)
    assert result.mode == TurnMode.CONTINUATION
    assert result.continuation_kind == ContinuationKind.ACKNOWLEDGEMENT
    assert "acknowledge" in {act.value for act in result.pragmatic_acts}


def test_v15_pragmatics_drives_topic_drop_without_literal_followup() -> None:
    result = ConversationTurnInterpreter().interpret_text("deixa quieto")
    assert result.mode == TurnMode.CONTINUATION
    assert result.continuation_kind == ContinuationKind.TOPIC_DROP
    assert "close_topic" in {act.value for act in result.pragmatic_acts}


def test_v15_laughter_is_interpreted_as_social_reaction_not_information_request() -> None:
    result = ConversationTurnInterpreter().interpret_text("kkkkkkkk")
    assert result.mode == TurnMode.SOCIAL
    assert "react" in {act.value for act in result.pragmatic_acts}
    assert "nao explique que o usuario riu" in result.guidance


def test_v15_vent_or_share_does_not_default_to_problem_solving() -> None:
    result = ConversationTurnInterpreter().interpret_text("mano ta foda hoje")
    assert result.mode == TurnMode.SOCIAL
    assert "vent_or_share" in {act.value for act in result.pragmatic_acts}
    assert "nao um pedido automatico de solucao" in result.guidance
