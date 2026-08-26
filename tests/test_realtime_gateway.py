from uuid import UUID, uuid4

from fastapi.testclient import TestClient

import campanario.api as api_module
import campanario.gateway.realtime as realtime_module
from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.models import ChatSession, Message
from campanario.chat.service import ChatService
from campanario.main import app
from campanario.model.protocol import FakeModelProvider
from campanario.runtime.core import CampanarioRuntime
from campanario.runtime.events import EventType, RuntimeEventBus


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
        updated = current.model_copy(update={"primary_agent_id": agent_id})
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


def build_test_runtime() -> CampanarioRuntime:
    runtime_id = uuid4()
    bus = RuntimeEventBus(runtime_id)
    provider = FakeModelProvider("resposta realtime")
    service = ChatService(
        InMemorySessions(),
        InMemoryMessages(),
        provider,
        RecentMessagesContextManager(20),
        "fake",
        event_bus=bus,
    )
    return CampanarioRuntime(
        service,
        provider,
        runtime_id=runtime_id,
        event_bus=bus,
    ).start()


def install_runtime(monkeypatch) -> CampanarioRuntime:
    runtime = build_test_runtime()
    monkeypatch.setattr(api_module, "get_runtime", lambda: runtime)
    monkeypatch.setattr(realtime_module, "get_runtime", lambda: runtime)
    return runtime


def receive_until_ready(ws):
    events = []
    while True:
        frame = ws.receive_json()
        if frame["frame_type"] == "ready":
            return events, frame
        events.append(frame["event"])


def test_v1_api_and_websocket_observe_same_runtime_turn(monkeypatch) -> None:
    runtime = install_runtime(monkeypatch)
    client = TestClient(app)

    system = client.get("/api/v1/runtime")
    assert system.status_code == 200
    assert system.json()["runtime_id"] == str(runtime.state.runtime_id)

    created = client.post("/api/v1/sessions", json={})
    assert created.status_code == 201
    session_id = created.json()["id"]

    with client.websocket_connect(f"/ws/v1/events?session_id={session_id}&after_sequence=0") as ws:
        replay, ready = receive_until_ready(ws)
        assert [item["event_type"] for item in replay] == [EventType.SESSION_STARTED.value]
        assert ready["runtime_id"] == str(runtime.state.runtime_id)
        assert ready["session_id"] == session_id
        assert ready["runtime_status"] == "running"

        response = client.post(
            f"/api/v1/sessions/{session_id}/turn",
            json={"message": "olá realtime"},
        )
        assert response.status_code == 200
        assert response.json()["speakers"] == ["morgana"]

        observed = [ws.receive_json()["event"] for _ in range(6)]
        assert [item["event_type"] for item in observed] == [
            EventType.USER_TEXT.value,
            EventType.AGENT_SELECTED.value,
            EventType.AGENT_INTENT_TO_SPEAK.value,
            EventType.AGENT_RESPONSE_STARTED.value,
            EventType.AGENT_RESPONSE_CHUNK.value,
            EventType.AGENT_RESPONSE_FINISHED.value,
        ]
        assert observed[4]["payload"]["text"] == "resposta realtime"
        assert observed[4]["provenance"]["agent_id"] == "morgana"


def test_websocket_reconnect_replays_same_session_without_creating_another(monkeypatch) -> None:
    runtime = install_runtime(monkeypatch)
    client = TestClient(app)
    session_id = client.post("/api/v1/sessions", json={}).json()["id"]
    client.post(f"/api/v1/sessions/{session_id}/turn", json={"message": "primeiro"})
    latest = runtime.events.latest_sequence

    with client.websocket_connect(
        f"/ws/v1/events?session_id={session_id}&after_sequence={latest - 2}"
    ) as ws:
        replay, ready = receive_until_ready(ws)

    assert [item["sequence"] for item in replay] == [latest - 1, latest]
    assert all(item["session_id"] == session_id for item in replay)
    assert ready["latest_sequence"] == latest
    assert [str(item.id) for item in runtime.sessions.list_sessions()] == [session_id]


def test_legacy_api_remains_available_during_pf3_migration(monkeypatch) -> None:
    install_runtime(monkeypatch)
    client = TestClient(app)

    assert client.get("/api/system").status_code == 200
    assert client.post("/api/sessions", json={}).status_code == 201


def test_pf3_launcher_remains_localhost_only() -> None:
    root = __import__("pathlib").Path(__file__).resolve().parents[1]
    launcher = (root / "tools" / "windows" / "INICIAR_CAMPANARIO.bat").read_text(encoding="utf-8")
    assert "--host 127.0.0.1" in launcher
    assert "--host 0.0.0.0" not in launcher
