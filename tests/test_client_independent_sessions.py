from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient

import campanario.api as api_module
import campanario.gateway.realtime as realtime_module
from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.models import ChatSession, Message
from campanario.chat.service import ChatService
from campanario.main import app
from campanario.model.protocol import ModelChunk
from campanario.runtime.core import CampanarioRuntime
from campanario.runtime.events import EventSourceKind, EventType, RuntimeEventBus


class InMemorySessions:
    def __init__(self) -> None:
        self.items: dict[UUID, ChatSession] = {}

    def create(self, session: ChatSession) -> ChatSession:
        self.items[session.id] = session
        return session

    def get(self, session_id: UUID) -> ChatSession | None:
        return self.items.get(session_id)

    def list(self) -> list[ChatSession]:
        return list(self.items.values())

    def set_primary_agent(self, session_id: UUID, agent_id: str) -> ChatSession | None:
        current = self.items.get(session_id)
        if current is None:
            return None
        updated = ChatSession(
            id=current.id,
            title=current.title,
            status=current.status,
            created_at=current.created_at,
            updated_at=current.updated_at,
            primary_agent_id=agent_id,
        )
        self.items[session_id] = updated
        return updated


class InMemoryMessages:
    def __init__(self) -> None:
        self.items: list[Message] = []

    def append(self, message: Message) -> Message:
        self.items.append(message)
        return message

    def list_by_session(self, session_id: UUID) -> list[Message]:
        return [message for message in self.items if message.session_id == session_id]


class ContextAwareProvider:
    def __init__(self) -> None:
        self.requests = []

    async def health(self) -> bool:
        return True

    async def stream(self, request):
        self.requests.append(request)
        user_texts = [item.content for item in request.messages if item.role.value == "user"]
        text = "contexto compartilhado" if "primeiro no pc" in user_texts and "continua no segundo cliente" in user_texts else "resposta"
        yield ModelChunk(text=text)
        yield ModelChunk(text="", done=True)


def _runtime():
    runtime_id = uuid4()
    bus = RuntimeEventBus(runtime_id)
    provider = ContextAwareProvider()
    service = ChatService(
        InMemorySessions(),
        InMemoryMessages(),
        provider,
        RecentMessagesContextManager(50),
        "fake",
        event_bus=bus,
    )
    runtime = CampanarioRuntime(service, provider, runtime_id=runtime_id, event_bus=bus).start()
    return runtime, provider


def _install(monkeypatch):
    runtime, provider = _runtime()
    monkeypatch.setattr(api_module, "get_runtime", lambda: runtime)
    monkeypatch.setattr(realtime_module, "get_runtime", lambda: runtime)
    return runtime, provider


def _ready(ws):
    while True:
        frame = ws.receive_json()
        if frame["frame_type"] == "ready":
            return frame


def test_two_clients_continue_same_session_and_same_model_context(monkeypatch):
    runtime, provider = _install(monkeypatch)
    pc = TestClient(app)
    second = TestClient(app)
    session_id = pc.post("/api/v1/sessions", json={}).json()["id"]

    first = pc.post(
        f"/api/v1/sessions/{session_id}/turn",
        headers={"X-Campanario-Client-Id": "pc-web"},
        json={"message": "primeiro no pc"},
    )
    assert first.status_code == 200
    assert first.json()["client_id"] == "pc-web"

    history_on_second = second.get(f"/api/v1/sessions/{session_id}/messages").json()
    assert [item["content"] for item in history_on_second][:2] == ["primeiro no pc", "resposta"]
    assert history_on_second[0]["client_id"] == "pc-web"

    continuation = second.post(
        f"/api/v1/sessions/{session_id}/turn",
        headers={"X-Campanario-Client-Id": "second-client"},
        json={"message": "continua no segundo cliente"},
    )
    assert continuation.status_code == 200
    assert continuation.json()["client_id"] == "second-client"

    final_history = pc.get(f"/api/v1/sessions/{session_id}/messages").json()
    assert final_history[-2]["client_id"] == "second-client"
    assert final_history[-1]["content"] == "contexto compartilhado"
    assert final_history[-1]["agent_id"] == "morgana"
    assert len(runtime.sessions.list_sessions()) == 1
    assert len(provider.requests) == 2


def test_two_realtime_clients_attach_to_same_session_without_ownership(monkeypatch):
    runtime, _ = _install(monkeypatch)
    client = TestClient(app)
    session_id = client.post("/api/v1/sessions", json={}).json()["id"]

    with client.websocket_connect(f"/ws/v1/events?session_id={session_id}&client_id=pc-web") as pc_ws:
        pc_ready = _ready(pc_ws)
        with client.websocket_connect(f"/ws/v1/events?session_id={session_id}&client_id=phone-shell") as phone_ws:
            phone_ready = _ready(phone_ws)
            attached = client.get(f"/api/v1/sessions/{session_id}/clients").json()
            assert {item["client_id"] for item in attached} == {"pc-web", "phone-shell"}
            assert pc_ready["session_id"] == phone_ready["session_id"] == session_id
            assert pc_ready["attachment_id"] != phone_ready["attachment_id"]

            response = client.post(
                f"/api/v1/sessions/{session_id}/turn",
                headers={"X-Campanario-Client-Id": "pc-web"},
                json={"message": "evento compartilhado"},
            )
            assert response.status_code == 200
            first_live = phone_ws.receive_json()["event"]
            assert first_live["event_type"] == EventType.USER_TEXT.value
            assert first_live["provenance"]["source_kind"] == EventSourceKind.CLIENT.value
            assert first_live["provenance"]["client_id"] == "pc-web"

        remaining = client.get(f"/api/v1/sessions/{session_id}/clients").json()
        assert [item["client_id"] for item in remaining] == ["pc-web"]

    assert runtime.clients.list(session_id=UUID(session_id)) == ()


def test_reconnect_same_client_keeps_session_but_gets_new_attachment(monkeypatch):
    runtime, _ = _install(monkeypatch)
    client = TestClient(app)
    session_id = client.post("/api/v1/sessions", json={}).json()["id"]

    with client.websocket_connect(f"/ws/v1/events?session_id={session_id}&client_id=pc-web") as ws:
        first_attachment = _ready(ws)["attachment_id"]
    with client.websocket_connect(f"/ws/v1/events?session_id={session_id}&client_id=pc-web") as ws:
        second_attachment = _ready(ws)["attachment_id"]

    assert first_attachment != second_attachment
    assert len(runtime.sessions.list_sessions()) == 1


def test_user_and_agent_provenance_remain_separate(monkeypatch):
    runtime, _ = _install(monkeypatch)
    client = TestClient(app)
    session_id = client.post("/api/v1/sessions", json={}).json()["id"]
    client.post(
        f"/api/v1/sessions/{session_id}/turn",
        headers={"X-Campanario-Client-Id": "desktop-a"},
        json={"message": "teste provenance"},
    )
    events = runtime.events.replay(session_id=UUID(session_id))
    user = next(item for item in events if item.event_type == EventType.USER_TEXT)
    agent = next(item for item in events if item.event_type == EventType.AGENT_RESPONSE_FINISHED)
    assert user.provenance.client_id == "desktop-a"
    assert user.provenance.agent_id is None
    assert agent.provenance.agent_id == "morgana"
    assert agent.provenance.client_id is None


def test_message_client_provenance_survives_sqlite_roundtrip(tmp_path):
    from datetime import UTC, datetime
    from campanario.chat.models import MessageRole
    from campanario.storage.database import Base, build_engine, build_session_factory
    from campanario.storage.repositories import SqlAlchemyChatSessionRepository, SqlAlchemyMessageRepository

    engine = build_engine(f"sqlite:///{tmp_path / 'pf7.db'}")
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)
    sessions = SqlAlchemyChatSessionRepository(factory)
    messages = SqlAlchemyMessageRepository(factory)
    session = ChatSession(id=uuid4(), created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
    sessions.create(session)
    messages.append(
        Message(
            id=uuid4(),
            session_id=session.id,
            role=MessageRole.USER,
            content="origem persistente",
            created_at=datetime.now(UTC),
            client_id="desktop-main",
            device_id="pc-main",
        )
    )
    restored = messages.list_by_session(session.id)[0]
    assert restored.client_id == "desktop-main"
    assert restored.device_id == "pc-main"
    assert restored.agent_id is None


def test_presence_ui_reuses_stable_client_id_for_http_and_realtime():
    from pathlib import Path
    html = Path("src/campanario/web/index.html").read_text(encoding="utf-8")
    assert "campanario.client_id" in html
    assert "client_id=${encodeURIComponent(clientId)}" in html
    assert "'X-Campanario-Client-Id':clientId" in html
