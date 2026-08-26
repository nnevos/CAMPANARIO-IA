from uuid import uuid4

import pytest

import campanario.composition as composition
from campanario.config import Settings
from campanario.model.protocol import FakeModelProvider
from campanario.runtime.capabilities import CallbackCapabilityProvider, CapabilityDefinition, CapabilityProvenance, CapabilityProviderKind
from campanario.runtime.telemetry import RuntimeTelemetry


@pytest.mark.asyncio
async def test_conversation_records_required_latency_milestones(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(composition, "build_model_provider", lambda config: FakeModelProvider("Resposta curta."))
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{tmp_path / 'telemetry.db'}", create_schema=True)
    session = runtime.sessions.create_session("telemetry")
    correlation_id = uuid4()

    events = [event async for event in runtime.conversation.stream_turn(session.id, "Responda objetivamente.", correlation_id=correlation_id)]
    assert events

    points = runtime.telemetry.snapshot(correlation_id=correlation_id)
    names = [point.name for point in points]
    for required in (
        "request_received", "routing_completed", "context_ready", "generation_started",
        "first_token", "first_usable_output", "generation_finished", "turn_finished",
    ):
        assert required in names
    positions = {name: names.index(name) for name in set(names)}
    assert positions["request_received"] < positions["routing_completed"] < positions["context_ready"]
    assert positions["generation_started"] < positions["first_token"] <= positions["generation_finished"]
    assert positions["first_token"] <= positions["first_usable_output"] < positions["turn_finished"]
    assert all(point.runtime_id == runtime.state.runtime_id for point in points)
    assert all(point.session_id == session.id for point in points)


@pytest.mark.asyncio
async def test_tool_events_feed_same_runtime_telemetry(tmp_path) -> None:
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{tmp_path / 'tool-telemetry.db'}", create_schema=True)
    provider = CallbackCapabilityProvider("mock-weather", lambda capability, arguments: {"value": "ok"})
    runtime.tools.register_provider(provider)
    runtime.tools.register(CapabilityDefinition(
        name="weather.current", description="Weather", input_schema={"type": "object", "additionalProperties": False},
        output_schema={"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"], "additionalProperties": False},
        provider_id="mock-weather", permissions=(), timeout_seconds=1.0,
        provenance=CapabilityProvenance(provider_kind=CapabilityProviderKind.MOCK, provider_id="mock-weather"),
    ))
    await runtime.tools.execute("weather.current", {})
    names = [point.name for point in runtime.telemetry.snapshot()]
    assert "tool_started" in names
    assert "tool_finished" in names


def test_telemetry_journal_is_bounded_and_duration_is_monotonic() -> None:
    runtime_id = uuid4()
    telemetry = RuntimeTelemetry(runtime_id, journal_limit=2)
    first = telemetry.mark("a")
    second = telemetry.mark("b")
    third = telemetry.mark("c")
    assert [point.name for point in telemetry.snapshot()] == ["b", "c"]
    assert telemetry.duration_ms(first, third) >= 0

@pytest.mark.asyncio
async def test_explicit_group_turn_marks_second_agent_start(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(composition, "build_model_provider", lambda config: FakeModelProvider("Contribuição distinta."))
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{tmp_path / 'multi-telemetry.db'}", create_schema=True)
    session = runtime.sessions.create_session("multi")
    correlation_id = uuid4()
    events = [event async for event in runtime.conversation.stream_turn(session.id, "Quero ouvir vocês dois sobre isso.", correlation_id=correlation_id)]
    assert len([event for event in events if event.type == "speaker_start"]) == 2
    second = [point for point in runtime.telemetry.snapshot(correlation_id=correlation_id) if point.name == "second_agent_started"]
    assert len(second) == 1
    assert second[0].agent_id in {"todd", "morgana"}
