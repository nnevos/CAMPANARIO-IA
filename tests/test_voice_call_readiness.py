from __future__ import annotations

import asyncio
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import campanario.api as api_module
import campanario.gateway.call as call_gateway_module
import campanario.gateway.devices as device_gateway_module
from campanario.composition import build_runtime
from campanario.config import Settings
from campanario.main import app
from campanario.model.protocol import FakeModelProvider
from campanario.runtime.clients import ClientIdentity
from campanario.runtime.devices import DeviceAnnouncement
from campanario.runtime.events import EventType
from campanario.runtime.voice import VoiceCallCoordinator


def _runtime(tmp_path):
    runtime = build_runtime(
        Settings(),
        database_url=f"sqlite:///{tmp_path / 'voice.db'}",
        create_schema=True,
    )
    fake = FakeModelProvider("resposta por voz")
    runtime.conversation._model_provider = fake
    runtime.conversation._participation._provider = fake
    runtime.conversation._default_model = "fake"
    runtime.conversation._participation._model = "fake"
    return runtime


def _install(monkeypatch, tmp_path):
    runtime = _runtime(tmp_path)
    monkeypatch.setattr(api_module, "get_runtime", lambda: runtime)
    monkeypatch.setattr(device_gateway_module, "get_runtime", lambda: runtime)
    monkeypatch.setattr(call_gateway_module, "get_runtime", lambda: runtime)
    return runtime


def _device(runtime, *, device_id="voice-phone", capabilities=("microphone", "speaker")):
    runtime.devices.connect(DeviceAnnouncement(
        device_id=device_id,
        name="Voice proof device",
        type="mobile-proof",
        capabilities=capabilities,
    ))
    return runtime.trust.pair(device_id)


@pytest.mark.asyncio
async def test_voice_final_reuses_same_conversation_and_preserves_causation(tmp_path):
    runtime = _runtime(tmp_path)
    session = runtime.sessions.create_session()
    _device(runtime)
    coordinator = VoiceCallCoordinator(runtime)
    call = coordinator.start(session.id, ClientIdentity(client_id="voice-client", device_id="voice-phone"))

    coordinator.speech_partial(call.call_id, "oi campa")
    assert runtime.conversation.get_messages(session.id) == []

    async for _ in coordinator.speech_final(call.call_id, "oi campanario"):
        pass

    history = runtime.conversation.get_messages(session.id)
    assert [item.content for item in history] == ["oi campanario", "resposta por voz"]
    assert history[0].client_id == "voice-client"
    assert history[0].device_id == "voice-phone"

    events = runtime.events.replay(session_id=session.id)
    final = next(item for item in events if item.event_type == EventType.USER_SPEECH_FINAL)
    user_text = next(item for item in events if item.event_type == EventType.USER_TEXT)
    assert final.correlation_id == user_text.correlation_id
    assert user_text.causation_id == final.event_id
    assert user_text.provenance.client_id == "voice-client"
    assert user_text.provenance.device_id == "voice-phone"


@pytest.mark.asyncio
async def test_voice_interruption_is_explicit_signal_without_claiming_model_cancellation(tmp_path):
    runtime = _runtime(tmp_path)
    session = runtime.sessions.create_session()
    _device(runtime)
    coordinator = VoiceCallCoordinator(runtime)
    call = coordinator.start(session.id, ClientIdentity(client_id="voice-client", device_id="voice-phone"))

    coordinator.interrupt(call.call_id, agent_id="morgana", reason="barge_in")
    interrupted = [event for event in runtime.events.replay(session_id=session.id) if event.event_type == EventType.AGENT_INTERRUPTED]
    assert len(interrupted) == 1
    assert interrupted[0].payload["agent_id"] == "morgana"
    assert interrupted[0].payload["interruption_reason"] == "barge_in"
    assert runtime.conversation.get_messages(session.id) == []


@pytest.mark.asyncio
async def test_voice_call_requires_trusted_microphone_device(tmp_path):
    runtime = _runtime(tmp_path)
    session = runtime.sessions.create_session()
    runtime.devices.connect(DeviceAnnouncement(device_id="no-mic", name="No mic", type="test", capabilities=("speaker",)))
    runtime.trust.pair("no-mic")
    coordinator = VoiceCallCoordinator(runtime)
    with pytest.raises(ValueError, match="microphone"):
        coordinator.start(session.id, ClientIdentity(client_id="voice-client", device_id="no-mic"))


def test_call_websocket_contract_emits_tts_directive_and_call_events(monkeypatch, tmp_path):
    runtime = _install(monkeypatch, tmp_path)
    client = TestClient(app)
    session_id = client.post("/api/v1/sessions", json={}).json()["id"]
    credential = _device(runtime)

    url = f"/ws/v1/call?session_id={session_id}&client_id=voice-ui&device_id=voice-phone"
    with client.websocket_connect(url, headers={"X-Campanario-Device-Credential": credential}) as ws:
        ready = ws.receive_json()
        assert ready["frame_type"] == "call_ready"
        call_id = ready["call_id"]

        ws.send_json({"schema_version": "1.0", "frame_type": "wake_detected", "phrase": "campanario"})
        wake = ws.receive_json()
        assert wake["frame_type"] == "call_event"
        assert wake["event_type"] == EventType.WAKE_DETECTED.value

        ws.send_json({"schema_version": "1.0", "frame_type": "speech_partial", "text": "teste par"})
        partial = ws.receive_json()
        assert partial["event_type"] == EventType.USER_SPEECH_PARTIAL.value

        ws.send_json({"schema_version": "1.0", "frame_type": "speech_final", "text": "teste final"})
        saw_tts = False
        saw_finished = False
        for _ in range(20):
            frame = ws.receive_json()
            if frame["frame_type"] == "tts_text":
                saw_tts = True
                assert frame["agent_id"] == "morgana"
                assert frame["text"] == "resposta por voz"
            if frame["frame_type"] == "call_event" and frame["event_type"] == EventType.AGENT_RESPONSE_FINISHED.value:
                saw_finished = True
                break
        assert saw_tts and saw_finished

        ws.send_json({"schema_version": "1.0", "frame_type": "interrupt", "agent_id": "morgana"})
        got_ack = False
        for _ in range(5):
            frame = ws.receive_json()
            if frame["frame_type"] == "interrupt_ack":
                got_ack = True
                assert frame["cancellation_mode"] == "cooperative_task"
                break
        assert got_ack

        ws.send_json({"schema_version": "1.0", "frame_type": "call_end", "reason": "test_done"})

    call = runtime.calls.get(UUID(call_id))
    assert call is not None and call.state.value == "ended"
    assert call.end_reason == "test_done"
    types = [event.event_type for event in runtime.events.replay(session_id=UUID(session_id))]
    assert EventType.CALL_STARTED in types
    assert EventType.CALL_ENDED in types


def test_call_websocket_rejects_device_without_microphone(monkeypatch, tmp_path):
    runtime = _install(monkeypatch, tmp_path)
    client = TestClient(app)
    session_id = client.post("/api/v1/sessions", json={}).json()["id"]
    credential = _device(runtime, device_id="speaker-only", capabilities=("speaker",))
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            f"/ws/v1/call?session_id={session_id}&client_id=voice-ui&device_id=speaker-only",
            headers={"X-Campanario-Device-Credential": credential},
        ) as ws:
            ws.receive_json()
    assert exc.value.code == 1008


def test_voice_presence_probe_gets_short_presence_directive() -> None:
    from campanario.runtime.voice import voice_turn_directives

    note, group = voice_turn_directives("me escuta?")
    assert group is False
    assert note is not None
    assert "PROBE DE PRESENCA" in note
    assert "Nao pergunte o que ele gostaria" in note

    note, group = voice_turn_directives("Todd e Morgana")
    assert group is True
    assert note is not None
    assert "CHAMADA DE PRESENCA" in note


def test_voice_group_directive_marks_both_agents_without_false_group_for_single_name() -> None:
    from campanario.runtime.voice import voice_turn_directives

    _, both = voice_turn_directives("Todd e Morgana, me escutam?")
    _, todd_only = voice_turn_directives("Todd, me escuta?")
    assert both is True
    assert todd_only is False


@pytest.mark.asyncio
async def test_voice_explicit_group_secondary_uses_original_turn_not_primary_answer(tmp_path):
    from campanario.model.protocol import ModelChunk

    class RecordingProvider:
        def __init__(self):
            self.requests = []
            self.responses = iter(("Todd presente.", "Morgana presente."))

        async def health(self):
            return True

        async def stream(self, request):
            self.requests.append(request)
            yield ModelChunk(text=next(self.responses))
            yield ModelChunk(text="", done=True)

    runtime = build_runtime(
        Settings(),
        database_url=f"sqlite:///{tmp_path / 'voice-group.db'}",
        create_schema=True,
    )
    provider = RecordingProvider()
    runtime.conversation._model_provider = provider
    runtime.conversation._participation._provider = provider
    runtime.conversation._default_model = "fake"
    runtime.conversation._participation._model = "fake"
    session = runtime.sessions.create_session()

    events = []
    async for event in runtime.conversation.stream_turn(
        session.id,
        "Todd e Morgana",
        turn_system_note="Confirme presenca em uma frase curta.",
        independent_group_turn=True,
    ):
        events.append(event)

    tokens = [(event.agent_id, event.text) for event in events if event.type == "token"]
    assert tokens == [("todd", "Todd presente."), ("morgana", "Morgana presente.")]
    assert len(provider.requests) == 2
    secondary_text = "\n".join(message.content for message in provider.requests[1].messages)
    assert "Todd presente." not in secondary_text
    assert "FALA ORIGINAL DO USUARIO:\nTodd e Morgana" in secondary_text
