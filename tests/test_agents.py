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
