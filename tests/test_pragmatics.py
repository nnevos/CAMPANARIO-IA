import pytest

from campanario.chat.pragmatics import PragmaticAct, PragmaticInterpreter


@pytest.fixture
def interpreter() -> PragmaticInterpreter:
    return PragmaticInterpreter()


@pytest.mark.parametrize("text", ["ok", "uhum", "entendi", "blz"])
def test_acknowledgements_are_understood_as_conversational_acts(interpreter, text) -> None:
    result = interpreter.interpret(text)
    assert PragmaticAct.ACKNOWLEDGE in result.acts


def test_laughter_plus_agreement_can_have_multiple_acts(interpreter) -> None:
    result = interpreter.interpret("kkkk pior que faz sentido")
    assert PragmaticAct.REACT in result.acts
    assert result.informal is True


def test_message_followup_can_be_detected_as_correction(interpreter) -> None:
    result = interpreter.interpret("personagem*")
    assert PragmaticAct.CORRECT_PREVIOUS in result.acts


def test_topic_drop_is_semantic_not_persona_style(interpreter) -> None:
    result = interpreter.interpret("deixa isso pra la por enquanto")
    assert PragmaticAct.CLOSE_TOPIC in result.acts


def test_short_fragment_can_continue_a_thought(interpreter) -> None:
    result = interpreter.interpret("deu ruim")
    assert PragmaticAct.CONTINUE_THOUGHT in result.acts
    assert result.fragment_like is True


def test_informal_vent_is_not_misread_as_information_request(interpreter) -> None:
    result = interpreter.interpret("mano ta foda hoje")
    assert PragmaticAct.VENT_OR_SHARE in result.acts
    assert PragmaticAct.ASK_INFO not in result.acts
    assert result.informal is True


def test_fact_question_is_input_intent_not_response_voice(interpreter) -> None:
    result = interpreter.interpret("qual planeta tem mais luas?")
    assert PragmaticAct.ASK_INFO in result.acts


def test_opinion_request_is_distinguished_from_fact_question(interpreter) -> None:
    result = interpreter.interpret("o que voce acha dessa ideia?")
    assert PragmaticAct.ASK_OPINION in result.acts


def test_action_request_is_detected_without_assuming_tool_exists(interpreter) -> None:
    result = interpreter.interpret("me ajuda a organizar isso")
    assert PragmaticAct.REQUEST_ACTION in result.acts


def test_planning_language_is_detected(interpreter) -> None:
    result = interpreter.interpret("bora marcar sabado de noite")
    assert PragmaticAct.PLAN in result.acts


def test_thinking_aloud_can_coexist_with_uncertainty(interpreter) -> None:
    result = interpreter.interpret("sei la, acho que isso pode funcionar")
    assert PragmaticAct.THINK_ALOUD in result.acts


def test_interpreter_does_not_encode_any_persona_response_style(interpreter) -> None:
    result = interpreter.interpret("slk deu merda aqui dnv")
    assert result.informal is True
    assert not hasattr(result, "response_style")
    assert not hasattr(result, "persona")

@pytest.mark.parametrize("text", ["saquei", "fechou", "boa"])
def test_v15_more_colloquial_acknowledgements_are_semantic_not_literal(interpreter, text) -> None:
    result = interpreter.interpret(text)
    assert PragmaticAct.ACKNOWLEDGE in result.acts


@pytest.mark.parametrize("text", ["muda de assunto", "deixa quieto"])
def test_v15_topic_closure_is_understood_without_needing_persona_rules(interpreter, text) -> None:
    result = interpreter.interpret(text)
    assert PragmaticAct.CLOSE_TOPIC in result.acts


def test_v15_ordinary_long_words_are_not_mistaken_for_laughter(interpreter) -> None:
    result = interpreter.interpret("pressao atmosferica")
    assert PragmaticAct.REACT not in result.acts
    assert result.contains_laughter is False


def test_v15_keyboard_smash_can_be_understood_as_reaction(interpreter) -> None:
    result = interpreter.interpret("KWNXJSNXIANSEIDJJE")
    assert PragmaticAct.REACT in result.acts

@pytest.mark.parametrize("text", ["show", "certinho", "pode crer", "justo", "tranquilo", "é isso"])
def test_v154_acknowledgement_family_generalizes_beyond_previous_scripts(interpreter, text) -> None:
    result = interpreter.interpret(text)
    assert PragmaticAct.ACKNOWLEDGE in result.acts


@pytest.mark.parametrize("text", ["salve parceiro", "fala meu caro", "opa mano", "eae amigo"])
def test_v154_greeting_allows_optional_vocative_without_becoming_literal(interpreter, text) -> None:
    result = interpreter.interpret(text)
    assert PragmaticAct.GREET in result.acts
    assert PragmaticAct.ASK_INFO not in result.acts


@pytest.mark.parametrize(
    "text",
    ["hoje eu tô só no piloto automático", "mano hoje a cabeça demorou pra ligar", "to largado no sofá hoje"],
)
def test_v154_short_personal_state_is_share_not_automatic_request(interpreter, text) -> None:
    result = interpreter.interpret(text)
    assert PragmaticAct.VENT_OR_SHARE in result.acts
    assert PragmaticAct.ASK_INFO not in result.acts
