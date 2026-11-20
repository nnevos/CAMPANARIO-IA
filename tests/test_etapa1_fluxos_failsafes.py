"""Etapa 1: invariants at the conversation/persistence/web/memory boundaries."""
from uuid import uuid4

import pytest

from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.service import ChatService, ModelNotConfiguredError, SessionNotFoundError
from campanario.model.protocol import FakeModelProvider
from campanario.runtime.telemetry import RuntimeTelemetry
from campanario.release import UI_VERSION


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
    def __init__(self):
        self.items = []

    def append(self, message):
        self.items.append(message)
        return message

    def list_by_session(self, session_id):
        return [m for m in self.items if m.session_id == session_id]


class UnavailableMemory:
    def observe_user_message(self, **kwargs):
        raise OSError("memory-write-down")

    def recall(self, *args, **kwargs):
        raise OSError("memory-read-down")

    def recall_hybrid(self, *args, **kwargs):
        raise OSError("memory-vector-down")


def make_service(*, model="fake", experience=None, telemetry=None):
    service = ChatService(
        Sessions(), Messages(), FakeModelProvider("resposta real"),
        RecentMessagesContextManager(10), model,
        experience=experience, telemetry=telemetry,
    )
    return service


@pytest.mark.asyncio
async def test_invalid_session_never_starts_web_research(monkeypatch):
    from campanario.utilities import web_chat

    called = []
    monkeypatch.setattr(web_chat, "research_topic", lambda *args, **kw: called.append("topic"))
    monkeypatch.setattr(web_chat, "research_entity", lambda *args, **kw: called.append("entity"))
    service = make_service()

    with pytest.raises(SessionNotFoundError):
        _ = [event async for event in service.stream_turn(uuid4(), "/pesquisar quem é Ada Lovelace?")]

    assert called == []
    assert service._messages.items == []


@pytest.mark.asyncio
async def test_missing_model_never_starts_web_research(monkeypatch):
    from campanario.utilities import web_chat

    called = []
    monkeypatch.setattr(web_chat, "research_topic", lambda *args, **kw: called.append("topic"))
    monkeypatch.setattr(web_chat, "research_entity", lambda *args, **kw: called.append("entity"))
    service = make_service(model="  ")
    session = service.create_session()

    with pytest.raises(ModelNotConfiguredError):
        _ = [event async for event in service.stream_turn(session.id, "/pesquisar Ada Lovelace")]

    assert called == []
    assert service.get_messages(session.id) == []


@pytest.mark.asyncio
async def test_assistant_answer_is_committed_before_first_visible_token():
    service = make_service()
    session = service.create_session()
    stream = service.stream_turn(session.id, "olá")
    try:
        first_token = None
        async for event in stream:
            if event.type == "token":
                first_token = event.text
                break  # simulate an interrupted client immediately after seeing output
        assert first_token == "resposta real"
        assert [m.content for m in service.get_messages(session.id)] == ["olá", "resposta real"]
    finally:
        await stream.aclose()


@pytest.mark.asyncio
async def test_memory_unavailable_does_not_hallucinate_personal_history():
    telemetry = RuntimeTelemetry(uuid4())
    service = make_service(experience=UnavailableMemory(), telemetry=telemetry)
    session = service.create_session()

    events = [e async for e in service.stream_turn(session.id, "Qual era meu editor favorito?")]
    output = "".join(e.text for e in events if e.type == "token")
    assert "não consegui consultar minhas memórias" in output.casefold()
    assert "resposta real" not in output
    assert [m.content for m in service.get_messages(session.id)] == ["Qual era meu editor favorito?", output]
    assert "memory_observation_failed" in [point.name for point in telemetry.snapshot()]
    assert "memory_retrieval_failed" in [point.name for point in telemetry.snapshot()]


@pytest.mark.asyncio
async def test_memory_unavailable_does_not_abort_ordinary_turn():
    service = make_service(experience=UnavailableMemory())
    session = service.create_session()

    events = [e async for e in service.stream_turn(session.id, "olá")]
    assert "".join(e.text for e in events if e.type == "token") == "resposta real"
    assert [m.content for m in service.get_messages(session.id)] == ["olá", "resposta real"]


def test_web_assets_match_current_release_version():
    from pathlib import Path

    index = Path(__file__).resolve().parents[1] / "src/campanario/web/index.html"
    html = index.read_text(encoding="utf-8")
    for asset in ("chat.js", "voice25.js", "gps-map.js", "workspaces.js", "memory.js", "desktop-settings.js"):
        assert f'/static/{asset}?v={UI_VERSION}' in html


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [
    '{"message":{"content":"resposta parcial"},"done":false}\n',
    '{"error":"failure"}\n',
    '["invalid"]\n',
    '{"message": "invalid", "done": true}\n',
    '{"message":{"content":12},"done":true}\n',
    '{"message":{"content":"a"},"done":"false"}\n',
])
async def test_ollama_rejects_truncated_or_malformed_stream(body, monkeypatch):
    import httpx
    from campanario.chat.models import MessageRole
    from campanario.model.adapters.ollama import OllamaProvider
    from campanario.model.protocol import ModelMessage, ModelRequest, ModelResponseError

    real_client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=body))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(transport=transport, **kwargs))
    provider = OllamaProvider("http://127.0.0.1:11434")
    request = ModelRequest(model="fake", messages=(ModelMessage(role=MessageRole.USER, content="olá"),))

    with pytest.raises(ModelResponseError):
        _ = [chunk async for chunk in provider.stream(request)]


@pytest.mark.asyncio
async def test_ollama_accepts_explicit_successful_stream(monkeypatch):
    import httpx
    from campanario.chat.models import MessageRole
    from campanario.model.adapters.ollama import OllamaProvider
    from campanario.model.protocol import ModelMessage, ModelRequest

    real_client = httpx.AsyncClient
    body = '{"message":{"content":"Tudo certo."},"done":false}\n{"done":true}\n'
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=body))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(transport=transport, **kwargs))
    provider = OllamaProvider("http://127.0.0.1:11434")
    request = ModelRequest(model="fake", messages=(ModelMessage(role=MessageRole.USER, content="olá"),))

    chunks = [chunk async for chunk in provider.stream(request)]
    assert "".join(chunk.text for chunk in chunks) == "Tudo certo."
    assert chunks[-1].done is True


def test_memory_strength_gate_rejects_favorite_and_exclusivity_without_user_evidence():
    from campanario.chat.memory_grounding import unlicensed_personal_strength

    evidence = ("- gosto de comida tailandesa",)
    assert unlicensed_personal_strength("Sua favorita é comida tailandesa.", evidence)
    assert unlicensed_personal_strength("Você come apenas comida tailandesa.", evidence)
    assert not unlicensed_personal_strength("Você comentou que gosta de comida tailandesa.", evidence)
