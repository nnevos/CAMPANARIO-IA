from datetime import UTC, datetime
from uuid import uuid4

import pytest

from campanario.agents.context import apply_agent_profile
from campanario.agents.profiles import AgentNotFoundError, default_agent_registry
from campanario.agents.router import AgentRouter
from campanario.chat.models import Message, MessageRole
from campanario.model.protocol import ModelMessage


def _message(role: MessageRole, content: str, *, agent_id: str | None = None) -> Message:
    return Message(
        id=uuid4(),
        session_id=uuid4(),
        role=role,
        content=content,
        created_at=datetime.now(UTC),
        agent_id=agent_id,
    )


def test_default_registry_contains_only_bridge_agents_and_defaults_to_morgana() -> None:
    registry = default_agent_registry()
    assert [profile.id for profile in registry.list()] == ["morgana", "todd"]
    assert registry.get(None).id == "morgana"
    assert registry.get("TODD").name == "Todd"
    assert registry.get("morgana").name == "Morgana"
    with pytest.raises(AgentNotFoundError):
        registry.get("campanario")


def test_unknown_agent_is_rejected() -> None:
    registry = default_agent_registry()
    with pytest.raises(AgentNotFoundError):
        registry.get("desconhecido")


def test_agent_profiles_share_truth_memory_and_capability_rules() -> None:
    registry = default_agent_registry()
    for agent_id in ("todd", "morgana"):
        prompt = registry.get(agent_id).persona_prompt.lower()
        assert "nao um ser humano" in prompt
        assert "campanario e o sistema, nao uma persona e nao um agente" in prompt
        assert "nunca muda fatos, memoria, capacidades" in prompt
        assert "nao alegue possuir uma memoria" in prompt
        assert "nao transforme toda resposta em demonstracao da persona" in prompt


def test_morgana_is_always_a_persona_layer_not_a_system_noop() -> None:
    registry = default_agent_registry()
    context = (
        ModelMessage(role=MessageRole.SYSTEM, content="BASE"),
        ModelMessage(role=MessageRole.USER, content="oi"),
    )
    result = apply_agent_profile(context, registry.get(None), [])
    assert result[0].content.startswith("BASE")
    assert "AGENTE COM PRIORIDADE DE FALA: MORGANA" in result[0].content


def test_todd_profile_is_merged_into_single_system_message() -> None:
    registry = default_agent_registry()
    context = (
        ModelMessage(role=MessageRole.SYSTEM, content="BASE"),
        ModelMessage(role=MessageRole.USER, content="decisao dificil"),
    )
    result = apply_agent_profile(context, registry.get("todd"), [])
    assert len([m for m in result if m.role == MessageRole.SYSTEM]) == 1
    assert result[0].content.startswith("BASE")
    assert "AGENTE COM PRIORIDADE DE FALA: TODD" in result[0].content
    assert "pragmatico" in result[0].content.lower()


def test_morgana_profile_keeps_other_agent_history_as_context_not_voice() -> None:
    registry = default_agent_registry()
    history = [
        _message(MessageRole.USER, "me ajuda"),
        _message(MessageRole.ASSISTANT, "Vamos por partes.", agent_id="todd"),
    ]
    context = (ModelMessage(role=MessageRole.SYSTEM, content="BASE"),)
    result = apply_agent_profile(context, registry.get("morgana"), history)
    assert "AGENTE COM PRIORIDADE DE FALA: MORGANA" in result[0].content
    assert "outros agentes: todd" in result[0].content.lower()
    assert "nao imite o estilo anterior" in result[0].content.lower()


def test_system_wake_routes_to_current_agent_and_new_default_is_morgana() -> None:
    router = AgentRouter(default_agent_registry())
    assert router.resolve("Campanário", None).profile.id == "morgana"
    assert router.resolve("Campanário", "todd").profile.id == "todd"


def test_direct_agent_wake_routes_and_persists_selection() -> None:
    router = AgentRouter(default_agent_registry())
    todd = router.resolve("Todd, olha isso", "morgana")
    assert todd.profile.id == "todd"
    assert todd.persist_selection is True
    morgana = router.resolve("Morgana", "todd")
    assert morgana.profile.id == "morgana"
    assert morgana.persist_selection is True


def test_system_wake_can_name_specific_agent_without_becoming_an_agent() -> None:
    router = AgentRouter(default_agent_registry())
    result = router.resolve("Campanário, chama o Todd", "morgana")
    assert result.profile.id == "todd"
    assert result.source == "system_wake_explicit_agent"
    assert result.persist_selection is True

from campanario.agents.participation import ParticipationArbiter


def test_agents_are_persistent_participants_not_mutually_exclusive() -> None:
    registry = default_agent_registry()
    for agent_id in ("morgana", "todd"):
        prompt = registry.get(agent_id).persona_prompt.lower()
        assert "coexistem no mesmo espaco conversacional" in prompt
        assert "nao torna o outro indisponivel nem silencioso" in prompt


def test_group_address_invites_secondary_without_changing_primary_priority() -> None:
    arbiter = ParticipationArbiter(default_agent_registry(), None, "fake")
    assert arbiter.explicitly_invites_group("Todd e Morgana, o que vocês acham?") is True
    assert arbiter.explicitly_invites_group("quero ouvir os dois sobre isso") is True
    assert arbiter.explicitly_invites_group("Todd, responde isso") is False
    assert arbiter.explicitly_invites_group("Morgana, pega o ponto do Todd e comenta") is False
    assert arbiter.explicitly_invites_group("Todd, responde à ressalva da Morgana") is False


def test_personality_core_is_structured_for_both_agents() -> None:
    registry = default_agent_registry()
    for agent_id in ("todd", "morgana"):
        core = registry.get(agent_id).personality
        assert core.traits
        assert core.anti_traits
        assert core.tendencies
        assert core.boundaries
        assert core.social
        assert core.technical
        assert core.creative
        assert core.discussion
        assert core.urgency
        assert core.positive_patterns
        assert core.negative_patterns


def test_personality_prompt_is_rendered_from_structured_contract() -> None:
    registry = default_agent_registry()
    todd = registry.get("todd")
    morgana = registry.get("morgana")

    for profile in (todd, morgana):
        prompt = profile.persona_prompt
        assert "TRAITS CORE" in prompt
        assert "ANTI-TRAITS" in prompt
        assert "BOUNDARIES" in prompt
        assert "COMPORTAMENTO SOCIAL" in prompt
        assert "COMPORTAMENTO TECNICO" in prompt
        assert "COMPORTAMENTO CRIATIVO" in prompt
        assert "DISCUSSAO E DISCORDANCIA" in prompt
        assert "URGENCIA" in prompt
        assert "PADROES POSITIVOS" in prompt
        assert "PADROES A EVITAR" in prompt
        assert "nao frases prontas" in prompt.lower()

    assert "oposicao performatica" in todd.persona_prompt.lower()
    assert "overengineering" in todd.persona_prompt.lower()
    assert "psicologizar" in morgana.persona_prompt.lower()
    assert "rigor epistemico" in morgana.persona_prompt.lower()


def test_personality_cores_preserve_distinct_priorities_without_distinct_truth() -> None:
    registry = default_agent_registry()
    todd = registry.get("todd")
    morgana = registry.get("morgana")

    assert any("risco" in value for value in todd.personality.tendencies)
    assert any("contexto" in value for value in morgana.personality.tendencies)
    assert "nunca muda fatos, memoria, capacidades" in todd.persona_prompt.lower()
    assert "nunca muda fatos, memoria, capacidades" in morgana.persona_prompt.lower()


def test_social_protocol_is_shared_and_forbids_speaker_simulation() -> None:
    from campanario.agents.context import apply_agent_profile
    from campanario.chat.models import MessageRole
    from campanario.model.protocol import ModelMessage

    registry = default_agent_registry()
    for agent_id in ("todd", "morgana"):
        context = apply_agent_profile(
            (ModelMessage(role=MessageRole.SYSTEM, content="base"),),
            registry.get(agent_id),
            (),
        )
        prompt = context[0].content.lower()
        assert "protocolo social multiagente v1" in prompt
        assert "nao repita ou parafraseie" in prompt
        assert "sua saida contem somente a sua propria fala" in prompt
        assert "nao tem autoridade social para silenciar" in prompt
        assert "campanario:" in prompt


def test_direct_address_blocks_secondary_even_when_semantic_arbiter_would_join() -> None:
    import asyncio
    from campanario.agents.participation import ParticipationArbiter
    from campanario.model.protocol import ModelChunk

    class JoinProvider:
        async def stream(self, request):
            yield ModelChunk(text="JOIN", done=True)

    registry = default_agent_registry()
    arbiter = ParticipationArbiter(registry, JoinProvider(), "fake")
    decision = asyncio.run(arbiter.decide(
        user_text="Morgana, o Todd disse que prototiparia antes. O que voce acha?",
        primary=registry.get("morgana"),
        primary_text="Eu manteria o prototipo pequeno.",
        history=(),
    ))
    assert decision.join is False
    assert decision.reason == "direct_address_exclusive"


def test_social_protocol_requires_literal_fidelity_when_correcting() -> None:
    from campanario.agents.social import SOCIAL_PROTOCOL_PROMPT
    folded = SOCIAL_PROTOCOL_PROMPT.lower()
    assert "preserve literalmente" in folded
    assert "numeros" in folded
    assert "nao troque o enunciado" in folded


def test_agent_context_has_single_speaker_output_contract() -> None:
    from campanario.agents.context import apply_agent_profile
    from campanario.model.protocol import ModelMessage
    from campanario.chat.models import MessageRole
    profile = default_agent_registry().get("morgana")
    result = apply_agent_profile((ModelMessage(role=MessageRole.SYSTEM, content="base"),), profile, ())
    prompt = result[0].content.lower()
    assert "contrato de saida do speaker" in prompt
    assert "gere somente a proxima fala de morgana" in prompt
    assert "nao comece com 'morgana:'" in prompt


def test_arithmetic_correction_anchor_is_generic_not_benchmark_specific() -> None:
    from campanario.agents.output import extract_arithmetic_correction_anchor

    anchor = extract_arithmetic_correction_anchor(
        "Morgana, o Todd disse que 9 vezes 6 é 53. Corrija isso em uma frase."
    )
    assert anchor is not None
    assert anchor.left_text == "9"
    assert anchor.right_text == "6"
    assert anchor.claimed_text == "53"
    assert anchor.expected_text == "54"
    assert anchor.validates("9 vezes 6 e 54, nao 53.")
    assert not anchor.validates("8 vezes 6 e 48.")


def test_speaker_output_normalization_never_erases_foreign_label() -> None:
    from campanario.agents.output import normalize_own_speaker_prefix, speaker_label_violations

    profile = default_agent_registry().get("morgana")
    assert normalize_own_speaker_prefix("**Morgana:** ponto", profile) == "ponto"
    foreign = normalize_own_speaker_prefix("Todd: ponto dele", profile)
    assert foreign == "Todd: ponto dele"
    assert speaker_label_violations(foreign) == ("Todd",)


def test_speaker_output_can_recover_only_explicit_own_segment_from_malformed_transcript() -> None:
    from campanario.agents.output import extract_own_labeled_segment
    from campanario.agents.profiles import default_agent_registry

    profile = default_agent_registry().get("morgana")
    text = "Todd: Eu faria A.  Morgana: Eu manteria B e observaria o contexto."
    assert extract_own_labeled_segment(text, profile) == "Eu manteria B e observaria o contexto."
    assert extract_own_labeled_segment("Todd: Eu faria A.", profile) is None


def test_call_vocative_is_recognized_at_end_without_confusing_mid_sentence_reference() -> None:
    router = AgentRouter(default_agent_registry())
    assert router.resolve("24 vezes 6 dá quanto, Morgana?", "todd").profile.id == "morgana"
    assert router.resolve("resume a decisão em uma frase, Morgana.", "todd").profile.id == "morgana"
    assert router.resolve("o Todd disse isso ontem, o que você acha?", "morgana").profile.id == "morgana"


def test_trailing_direct_address_is_exclusive_for_participation() -> None:
    import asyncio
    from campanario.agents.participation import ParticipationArbiter
    from campanario.model.protocol import ModelChunk

    class JoinProvider:
        async def stream(self, request):
            yield ModelChunk(text="JOIN", done=True)

    registry = default_agent_registry()
    arbiter = ParticipationArbiter(registry, JoinProvider(), "fake")
    decision = asyncio.run(arbiter.decide(
        user_text="resume a decisão em uma frase, Morgana.",
        primary=registry.get("morgana"),
        primary_text="Eu manteria a parte estável até a entrega.",
        history=(),
    ))
    assert decision.join is False
    assert decision.reason == "direct_address_exclusive"


def test_speaker_output_strips_narrow_redundant_self_identification_in_call() -> None:
    from campanario.agents.output import normalize_own_speaker_prefix

    todd = default_agent_registry().get("todd")
    morgana = default_agent_registry().get("morgana")
    assert normalize_own_speaker_prefix("Todd aqui. Eu cortaria os controles visíveis.", todd) == "Eu cortaria os controles visíveis."
    assert normalize_own_speaker_prefix("Morgana aqui: eu preservaria a presença.", morgana) == "eu preservaria a presença."
    # Foreign self-identification must never be silently laundered into the current speaker.
    assert normalize_own_speaker_prefix("Todd aqui. Eu faria A.", morgana).startswith("Todd aqui")


def test_arithmetic_correction_anchor_can_resolve_previous_question() -> None:
    from campanario.agents.output import extract_arithmetic_correction_anchor

    anchor = extract_arithmetic_correction_anchor(
        "Todd, suponha que eu diga agora que ela respondeu 142. Corrige só esse ponto.",
        ("mudando totalmente: 24 vezes 6 dá quanto, Morgana?",),
    )
    assert anchor is not None
    assert anchor.left_text == "24"
    assert anchor.right_text == "6"
    assert anchor.claimed_text == "142"
    assert anchor.expected_text == "144"


def test_social_protocol_supports_ambient_call_without_magic_invocation() -> None:
    from campanario.agents.social import SOCIAL_PROTOCOL_PROMPT
    folded = SOCIAL_PROTOCOL_PROMPT.lower()
    assert "nao precisa chamar todd, morgana ou campanario pelo nome a cada turno" in folded
    assert "apenas pensando em voz alta" in folded
    assert "nao exija palavra magica" in folded
    assert "dizer 'campanario' no fim da frase" in folded
