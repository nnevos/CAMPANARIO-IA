from fastapi.testclient import TestClient
import pytest

import campanario.api as api_module
import campanario.composition as composition
from campanario.config import Settings
from campanario.main import app
from campanario.model.protocol import FakeModelProvider
from campanario.runtime.clients import ClientIdentity


@pytest.mark.asyncio
async def test_f3_integrated_runtime_session_clients_events_and_telemetry(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(composition, "build_model_provider", lambda config: FakeModelProvider("Mesmo runtime, mesma conversa."))
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{tmp_path / 'closure.db'}", create_schema=True)
    session = runtime.sessions.create_session("F3 closure")
    web = ClientIdentity(client_id="web-proof")
    second = ClientIdentity(client_id="second-client-proof")

    first_events = [event async for event in runtime.conversation.stream_turn(session.id, "Primeiro cliente.", client=web)]
    second_events = [event async for event in runtime.conversation.stream_turn(session.id, "Segundo cliente, mesma sessão.", client=second)]
    assert first_events and second_events
    messages = runtime.conversation.get_messages(session.id)
    user_messages = [message for message in messages if message.role.value == "user"]
    assert [message.client_id for message in user_messages] == ["web-proof", "second-client-proof"]
    assert {message.session_id for message in messages} == {session.id}
    assert runtime.events.runtime_id == runtime.state.runtime_id == runtime.telemetry.runtime_id
    assert any(point.name == "turn_finished" for point in runtime.telemetry.snapshot())

    monkeypatch.setattr(api_module, "get_runtime", lambda: runtime)
    client = TestClient(app)
    system = client.get("/api/v1/runtime")
    assert system.status_code == 200
    assert system.json()["runtime_id"] == str(runtime.state.runtime_id)
    telemetry = client.get("/api/v1/runtime/telemetry?limit=20")
    assert telemetry.status_code == 200
    assert telemetry.json()


def test_f3_closure_keeps_runtime_headless_and_ui_optional(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(composition, "build_model_provider", lambda config: FakeModelProvider("ok"))
    runtime = composition.build_runtime(Settings(model_name="fake"), database_url=f"sqlite:///{tmp_path / 'headless.db'}", create_schema=True)
    assert runtime.state.status == "running"
    assert runtime.conversation is not None
    assert runtime.events is not None
    assert runtime.devices is not None
    assert runtime.tools is not None
    assert runtime.permissions is not None
    assert runtime.telemetry is not None
