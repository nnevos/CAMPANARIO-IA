from __future__ import annotations

import asyncio
import pytest

from campanario.composition import build_runtime
from campanario.config import Settings
from campanario.model.protocol import FakeModelProvider
from campanario.runtime.clients import ClientIdentity
from campanario.runtime.devices import DeviceAnnouncement
from campanario.runtime.events import EventType
from campanario.runtime.presence import PresenceState, resolve_wake
from campanario.runtime.voice import VoiceCallCoordinator


def runtime(tmp_path):
    rt = build_runtime(Settings(), database_url=f"sqlite:///{tmp_path/'f5.db'}", create_schema=True)
    fake = FakeModelProvider("ok")
    rt.conversation._model_provider = fake
    rt.conversation._participation._provider = fake
    rt.conversation._default_model = "fake"
    rt.conversation._participation._model = "fake"
    return rt


def device(rt, did):
    rt.devices.connect(DeviceAnnouncement(device_id=did, name=did, type="proof", capabilities=("microphone","speaker")))
    rt.trust.pair(did)


def test_wake_and_direct_address_contract():
    assert resolve_wake("Campanario, me ajuda") == (True, None, "me ajuda")
    assert resolve_wake("Morgana, olha isso") == (True, "morgana", "olha isso")
    assert resolve_wake("Todd explica") == (True, "todd", "explica")
    assert resolve_wake("estou pensando alto") == (False, None, "estou pensando alto")


@pytest.mark.asyncio
async def test_ambient_speech_is_ignored_until_wake_then_window_stays_open(tmp_path):
    rt=runtime(tmp_path); session=rt.sessions.create_session(); device(rt,"pc")
    c=VoiceCallCoordinator(rt); call=c.start(session.id, ClientIdentity(client_id="desktop",device_id="pc"))
    assert rt.presence.get(session.id).state == PresenceState.ATTENTIVE
    rt.presence.quiet(session.id, source_id="test")
    assert [x async for x in c.speech_final(call.call_id,"pensando em voz alta")] == []
    assert not any(e.event_type == EventType.USER_SPEECH_FINAL for e in rt.events.replay())
    first=[x async for x in c.speech_final(call.call_id,"Campanario, quanto e dois mais dois?")]
    assert first
    assert rt.presence.get(session.id).state == PresenceState.ENGAGED
    second=[x async for x in c.speech_final(call.call_id,"e tres mais tres?")]
    assert second
    finals=[e for e in rt.events.replay() if e.event_type == EventType.USER_SPEECH_FINAL]
    assert [e.payload["text"] for e in finals] == ["quanto e dois mais dois?", "e tres mais tres?"]


def test_call_handoff_keeps_same_call_and_session(tmp_path):
    rt=runtime(tmp_path); session=rt.sessions.create_session(); device(rt,"pc"); device(rt,"phone")
    c=VoiceCallCoordinator(rt); call=c.start(session.id,ClientIdentity(client_id="desktop",device_id="pc"))
    moved=rt.calls.handoff(call.call_id,ClientIdentity(client_id="mobile",device_id="phone"))
    assert moved.call_id == call.call_id and moved.session_id == session.id
    assert moved.device_id == "phone" and len(rt.sessions.list_sessions()) == 1


def test_resolve_wake_accepts_accented_campanario_from_ptbr_stt() -> None:
    woke, agent, cleaned = resolve_wake("Campanário, me escuta?")
    assert woke is True
    assert agent is None
    assert cleaned == "me escuta?"
