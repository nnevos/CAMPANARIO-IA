"""Etapa 2: deterministic fault injection at core event/model/persistence boundaries.

These tests use synthetic providers. Passing them does NOT validate a real Qwen/Ollama,
Windows, network, or physical voice device.
"""
from __future__ import annotations

import logging
from uuid import uuid4

import httpx
import pytest

from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.models import MessageRole
from campanario.chat.service import ChatService
from campanario.model.adapters.ollama import OllamaProvider
from campanario.model.protocol import (
    FakeModelProvider, ModelMessage, ModelRequest, ModelResponseError,
    ModelTimeoutError, ModelUnavailableError,
)
from campanario.runtime.events import (
    EventProvenance, EventSourceKind, EventType, RuntimeEventBus,
)
from campanario.runtime.telemetry import RuntimeTelemetry


class Sessions:
    def __init__(self):
        self.items = {}

    def create(self, session):
        self.items[session.id] = session
        return session

    def get(self, session_id):
        return self.items.get(session_id)

    def list(self):
        return list(self.items.values())


class Messages:
    def __init__(self, *, fail_assistant=False):
        self.items = []
        self.fail_assistant = fail_assistant

    def append(self, message):
        if self.fail_assistant and message.role == MessageRole.ASSISTANT:
            raise OSError("simulated disk full")
        self.items.append(message)
        return message

    def list_by_session(self, session_id):
        return [msg for msg in self.items if msg.session_id == session_id]


class UnavailableProvider:
    async def health(self):
        return False

    async def stream(self, request):
        if False:
            yield
        raise ModelUnavailableError("private token should not be logged")


class TimeoutProvider:
    async def health(self):
        return False

    async def stream(self, request):
        if False:
            yield
        raise ModelTimeoutError("timeout")


def build_service(provider=None, *, messages=None, event_bus=None, telemetry=None):
    bus = event_bus or RuntimeEventBus(uuid4())
    store = messages or Messages()
    service = ChatService(
        Sessions(), store, provider or FakeModelProvider("resposta validada"),
        RecentMessagesContextManager(20), "fake-model",
        event_bus=bus, telemetry=telemetry,
    )
    return service, bus, store


def event_types(bus):
    return [e.event_type for e in bus.replay()]


def test_one_failing_event_observer_does_not_block_journal_or_other_observers(caplog):
    bus = RuntimeEventBus(uuid4())
    recorded = []

    def failed_observer(event):
        raise ValueError("confidential observer detail")

    bus.subscribe(failed_observer)
    bus.subscribe(recorded.append)
    with caplog.at_level(logging.WARNING):
        event = bus.publish(
            EventType.USER_TEXT, {"text": "conteudo reservado"},
            provenance=EventProvenance(source_kind=EventSourceKind.USER, source_id="user"),
        )
    assert recorded == [event]
    assert bus.replay() == (event,)
    assert "event_subscriber_failed" in caplog.text
    assert "ValueError" in caplog.text
    assert "confidential observer detail" not in caplog.text
    assert "conteudo reservado" not in caplog.text


@pytest.mark.asyncio
async def test_failing_websocket_observer_cannot_abort_successful_turn():
    service, bus, store = build_service()
    bus.subscribe(lambda event: 1 / 0, event_types=[EventType.AGENT_RESPONSE_CHUNK])
    seen = []
    bus.subscribe(seen.append, event_types=[EventType.AGENT_RESPONSE_CHUNK])
    session = service.create_session()
    events = [event async for event in service.stream_turn(session.id, "olá")]
    assert [event.type for event in events] == ["speaker_start", "token", "speaker_done"]
    assert [msg.content for msg in store.items] == ["olá", "resposta validada"]
    assert [event.payload["text"] for event in seen] == ["resposta validada"]
    assert EventType.AGENT_INTERRUPTED not in event_types(bus)


@pytest.mark.asyncio
@pytest.mark.parametrize("provider,error_type", [
    (UnavailableProvider(), ModelUnavailableError),
    (TimeoutProvider(), ModelTimeoutError),
])
async def test_model_outage_does_not_emit_unverified_text(provider, error_type):
    service, bus, store = build_service(provider)
    session = service.create_session()
    emitted = []
    with pytest.raises(error_type):
        async for event in service.stream_turn(session.id, "mensagem importante"):
            emitted.append(event)
    assert [e.type for e in emitted] == ["speaker_start"]
    assert [msg.content for msg in store.items] == ["mensagem importante"]
    assert EventType.AGENT_RESPONSE_CHUNK not in event_types(bus)
    assert EventType.AGENT_RESPONSE_FINISHED not in event_types(bus)
    interrupted = [e for e in bus.replay() if e.event_type == EventType.AGENT_INTERRUPTED]
    assert len(interrupted) == 1
    assert interrupted[0].payload["interruption_reason"] == "generation_failed"
    assert interrupted[0].provenance.agent_id == "morgana"


@pytest.mark.asyncio
async def test_failed_assistant_commit_never_exposes_unpersisted_completion():
    store = Messages(fail_assistant=True)
    service, bus, _ = build_service(messages=store)
    session = service.create_session()
    emitted = []
    with pytest.raises(OSError, match="disk full"):
        async for event in service.stream_turn(session.id, "o que acha?"):
            emitted.append(event)
    assert [e.type for e in emitted] == ["speaker_start"]
    assert [msg.content for msg in store.items] == ["o que acha?"]
    assert EventType.AGENT_RESPONSE_CHUNK not in event_types(bus)
    assert EventType.AGENT_RESPONSE_FINISHED not in event_types(bus)
    assert EventType.AGENT_INTERRUPTED in event_types(bus)


@pytest.mark.asyncio
async def test_explicit_stream_close_reports_interruption_and_cleans_nested_generator():
    telemetry = RuntimeTelemetry(uuid4())
    service, bus, store = build_service(telemetry=telemetry)
    session = service.create_session()
    streamed = service.stream_turn(session.id, "oi")
    assert (await anext(streamed)).type == "speaker_start"
    await streamed.aclose()  # client disconnects before any model response is exposed
    interrupted = [e for e in bus.replay() if e.event_type == EventType.AGENT_INTERRUPTED]
    assert len(interrupted) == 1
    assert interrupted[0].payload["interruption_reason"] == "consumer_closed"
    assert [m.content for m in store.items] == ["oi"]
    assert any(point.name == "agent_generation_interrupted" for point in telemetry.snapshot())


@pytest.mark.asyncio
async def test_normal_completion_has_no_interruption_signal():
    service, bus, store = build_service()
    session = service.create_session()
    streamed = [event async for event in service.stream_turn(session.id, "oi")]
    assert [event.type for event in streamed] == ["speaker_start", "token", "speaker_done"]
    assert event_types(bus).count(EventType.AGENT_RESPONSE_FINISHED) == 1
    assert EventType.AGENT_INTERRUPTED not in event_types(bus)


def request():
    return ModelRequest(model="qwen-mock", messages=(ModelMessage(MessageRole.USER, "olá"),))


def install_mock_http(monkeypatch, handler):
    original = httpx.AsyncClient
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=transport, **kwargs))


@pytest.mark.asyncio
@pytest.mark.parametrize("response_data", [
    '{"message":{"content":"parcial"},"done":false}\n',
    '{"message":{"content":"ola"},"done":false}\n{bad_json}\n',
    '["not-an-object"]\n',
    '{"message":0,"done":true}\n',
    '{"message":{"content":0},"done":true}\n',
    '{"message":{"content":[]},"done":true}\n',
    '{"message":{"content":"oi"},"done":"true"}\n',
    '{"error":"fault"}\n',
])
async def test_ollama_rejects_truncated_or_malformed_payloads(monkeypatch, response_data):
    install_mock_http(monkeypatch, lambda req: httpx.Response(200, text=response_data))
    provider = OllamaProvider("http://ollama.test")
    with pytest.raises(ModelResponseError):
        _ = [c async for c in provider.stream(request())]


@pytest.mark.asyncio
async def test_ollama_valid_chunk_and_done_marker(monkeypatch):
    install_mock_http(
        monkeypatch,
        lambda req: httpx.Response(200, text=(
            '{"message":{"content":"bom "},"done":false}\n'
            '{"message":{"content":"dia"},"done":false}\n'
            '{"done":true,"eval_count":2}\n'
        )),
    )
    chunks = [c async for c in OllamaProvider("http://ollama.test").stream(request())]
    assert "".join(chunk.text for chunk in chunks) == "bom dia"
    assert chunks[-1].done is True


@pytest.mark.asyncio
@pytest.mark.parametrize("kind,expected", [
    ("connect", ModelUnavailableError),
    ("read_timeout", ModelTimeoutError),
    ("http_500", ModelResponseError),
])
async def test_ollama_transport_faults_are_typed(monkeypatch, kind, expected):
    def handler(req):
        if kind == "connect":
            raise httpx.ConnectError("connection refused", request=req)
        if kind == "read_timeout":
            raise httpx.ReadTimeout("read timed out", request=req)
        return httpx.Response(500, text="error")

    install_mock_http(monkeypatch, handler)
    with pytest.raises(expected):
        _ = [c async for c in OllamaProvider("http://ollama.test").stream(request())]


def test_browser_clears_speaker_state_when_runtime_interrupts_response():
    from pathlib import Path

    script = (Path(__file__).resolve().parents[1] / "src/campanario/web/static/chat.js").read_text(encoding="utf-8")
    assert "event.event_type==='AGENT_INTERRUPTED'" in script
    assert "bubble=null;speaker=null;setState('attentive'" in script
    assert "event.event_type==='AGENT_RESPONSE_FINISHED'" in script
