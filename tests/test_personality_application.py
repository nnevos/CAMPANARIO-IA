from campanario.agents.personality_application import build_personality_application
from campanario.agents.profiles import default_agent_registry
from campanario.chat.turns import ConversationTurnInterpreter, TurnMode


def _render(agent_id: str, text: str) -> str:
    registry = default_agent_registry()
    turn = ConversationTurnInterpreter().interpret_text(text)
    return build_personality_application(registry.get(agent_id), turn).render().lower()


def test_same_decision_turn_activates_distinct_reasoning_priorities() -> None:
    todd = _render("todd", "o que voce acha: refatoro agora ou entrego primeiro?")
    morgana = _render("morgana", "o que voce acha: refatoro agora ou entrego primeiro?")

    assert "trade-off" in todd or "trade-offs" in todd
    assert "proximo passo" in todd
    assert "criterio" in morgana
    assert "premissa" in morgana or "leitura" in morgana
    assert todd != morgana


def test_technical_turn_preserves_todd_action_vs_morgana_relation_lens() -> None:
    todd = _render("todd", "tenho um bug na api e um teste falhando")
    morgana = _render("morgana", "tenho um bug na api e um teste falhando")

    assert "proximo teste" in todd
    assert "evidencia" in todd
    assert "sintomas" in morgana
    assert "dependencias" in morgana


def test_social_turn_does_not_turn_personas_into_problem_solving_caricatures() -> None:
    todd = _render("todd", "hoje eu to cansado")
    morgana = _render("morgana", "hoje eu to cansado")

    assert "antes de oferecer conserto" in todd
    assert "sem diagnosticar" in morgana
    assert "checklist" in todd
    assert "psicologizar" in morgana


def test_factual_simple_keeps_personality_light_for_both() -> None:
    interpreter = ConversationTurnInterpreter()
    turn = interpreter.interpret_text("quanto e 20 mais 7?")
    assert turn.mode == TurnMode.FACTUAL_SIMPLE

    registry = default_agent_registry()
    for agent_id in ("todd", "morgana"):
        rendered = build_personality_application(registry.get(agent_id), turn).render().lower()
        assert "resposta correta e suficiente" in rendered
        assert "assinatura pessoal deve ser leve" in rendered
