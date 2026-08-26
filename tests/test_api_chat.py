from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

import campanario.api as api_module
from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.models import ChatSession, Message
from campanario.chat.service import ChatService
from campanario.model.protocol import FakeModelProvider
from campanario.main import app


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




class RuntimeStub:
    def __init__(self, service: ChatService) -> None:
        self.conversation = service
        self.state = SimpleNamespace(runtime_id=uuid4(), status="running")


def install_runtime(monkeypatch, service: ChatService) -> RuntimeStub:
    runtime = RuntimeStub(service)
    monkeypatch.setattr(api_module, "get_runtime", lambda: runtime)
    return runtime

class InMemoryMessages:
    def __init__(self) -> None:
        self.items: list[Message] = []

    def append(self, message: Message) -> Message:
        self.items.append(message)
        return message

    def list_by_session(self, session_id: UUID) -> list[Message]:
        return [message for message in self.items if message.session_id == session_id]


def test_api_session_and_sse_chat(monkeypatch) -> None:
    service = ChatService(
        InMemorySessions(),
        InMemoryMessages(),
        FakeModelProvider("oi"),
        RecentMessagesContextManager(20),
        "fake",
    )
    install_runtime(monkeypatch, service)
    client = TestClient(app)

    created = client.post("/api/sessions", json={}).json()
    session_id = created["id"]

    response = client.post(
        f"/api/sessions/{session_id}/chat/stream",
        json={"message": "olá"},
    )

    assert response.status_code == 200
    assert '"type": "token"' in response.text
    assert '"text": "oi"' in response.text

    history = client.get(f"/api/sessions/{session_id}/messages").json()
    assert [message["content"] for message in history] == ["olá", "oi"]


def test_api_rejects_blank_message(monkeypatch) -> None:
    service = ChatService(
        InMemorySessions(),
        InMemoryMessages(),
        FakeModelProvider("oi"),
        RecentMessagesContextManager(20),
        "fake",
    )
    install_runtime(monkeypatch, service)
    client = TestClient(app)

    created = client.post("/api/sessions", json={}).json()
    session_id = created["id"]

    response = client.post(
        f"/api/sessions/{session_id}/chat/stream",
        json={"message": "   "},
    )

    assert response.status_code == 422
    history = client.get(f"/api/sessions/{session_id}/messages").json()
    assert history == []


def test_api_reports_model_unavailable_without_persisting_assistant(monkeypatch) -> None:
    from campanario.model.protocol import ModelUnavailableError

    class UnavailableProvider:
        async def health(self) -> bool:
            return False

        async def stream(self, request):
            if False:
                yield
            raise ModelUnavailableError("offline")

    messages = InMemoryMessages()
    service = ChatService(
        InMemorySessions(),
        messages,
        UnavailableProvider(),
        RecentMessagesContextManager(20),
        "fake",
    )
    install_runtime(monkeypatch, service)
    client = TestClient(app)

    created = client.post("/api/sessions", json={}).json()
    session_id = created["id"]
    response = client.post(
        f"/api/sessions/{session_id}/chat/stream",
        json={"message": "teste de falha"},
    )

    assert response.status_code == 200
    assert '"error": "model_unavailable"' in response.text

    history = client.get(f"/api/sessions/{session_id}/messages").json()
    assert [message["content"] for message in history] == ["teste de falha"]

def test_api_lists_and_switches_agents(monkeypatch) -> None:
    service = ChatService(
        InMemorySessions(),
        InMemoryMessages(),
        FakeModelProvider("oi"),
        RecentMessagesContextManager(20),
        "fake",
    )
    install_runtime(monkeypatch, service)
    client = TestClient(app)

    agents = client.get("/api/agents")
    assert agents.status_code == 200
    assert [item["id"] for item in agents.json()] == ["morgana", "todd"]

    system = client.get("/api/system")
    assert system.status_code == 200
    assert system.json()["name"] == "Campanario"
    assert system.json()["default_agent_id"] == "morgana"

    created = client.post("/api/sessions", json={"agent_id": "todd"})
    assert created.status_code == 201
    assert created.json()["agent_id"] == "todd"
    session_id = created.json()["id"]

    switched = client.patch(f"/api/sessions/{session_id}/agent", json={"agent_id": "morgana"})
    assert switched.status_code == 200
    assert switched.json()["agent_id"] == "morgana"


def test_api_rejects_unknown_agent(monkeypatch) -> None:
    service = ChatService(
        InMemorySessions(),
        InMemoryMessages(),
        FakeModelProvider("oi"),
        RecentMessagesContextManager(20),
        "fake",
    )
    install_runtime(monkeypatch, service)
    client = TestClient(app)
    response = client.post("/api/sessions", json={"agent_id": "nao-existe"})
    assert response.status_code == 422
    system_as_agent = client.post("/api/sessions", json={"agent_id": "campanario"})
    assert system_as_agent.status_code == 422

def test_api_exposes_primary_speaker_and_persistent_participants(monkeypatch) -> None:
    service = ChatService(
        InMemorySessions(),
        InMemoryMessages(),
        FakeModelProvider("oi"),
        RecentMessagesContextManager(20),
        "fake",
    )
    install_runtime(monkeypatch, service)
    client = TestClient(app)

    system = client.get("/api/system").json()
    assert system["default_primary_agent_id"] == "morgana"
    assert system["participants"] == ["morgana", "todd"]
    assert system["participation_mode"] == "persistent_participants"

    created = client.post("/api/sessions", json={"primary_agent_id": "todd"}).json()
    assert created["primary_agent_id"] == "todd"
    switched = client.patch(
        f"/api/sessions/{created['id']}/primary-speaker",
        json={"agent_id": "morgana"},
    )
    assert switched.status_code == 200
    assert switched.json()["primary_agent_id"] == "morgana"


def test_api_stream_has_explicit_speaker_boundaries_for_group_turn(monkeypatch) -> None:
    class TwoResponseProvider:
        def __init__(self) -> None:
            self.responses = ["Primeira.", "Segunda."]
        async def health(self): return True
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            text = self.responses.pop(0)
            yield ModelChunk(text=text)
            yield ModelChunk(text="", done=True)

    service = ChatService(
        InMemorySessions(),
        InMemoryMessages(),
        TwoResponseProvider(),
        RecentMessagesContextManager(20),
        "fake",
    )
    install_runtime(monkeypatch, service)
    client = TestClient(app)
    session_id = client.post("/api/sessions", json={}).json()["id"]

    response = client.post(
        f"/api/sessions/{session_id}/chat/stream",
        json={"message": "Morgana e Todd, quero ouvir os dois"},
    )
    assert '"type": "speaker_start", "agent_id": "morgana"' in response.text
    assert '"type": "speaker_start", "agent_id": "todd"' in response.text


def test_system_info_exposes_release_identity(monkeypatch) -> None:
    service = ChatService(
        InMemorySessions(),
        InMemoryMessages(),
        FakeModelProvider("oi"),
        RecentMessagesContextManager(20),
        "fake",
    )
    install_runtime(monkeypatch, service)
    client = TestClient(app)
    payload = client.get("/api/system").json()
    assert payload["release_id"] == "realtime-presence-f5c1-voice-stabilization-checkpoint"
    assert payload["ui_version"] == "living-presence-ui-v1.3.1"
    assert payload["architecture_version"] == "realtime-presence-f5c1"
    assert payload["runtime_status"] == "running"
    assert payload["runtime_id"]


def test_web_ui_disables_cache_and_contains_build_marker() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "no-store" in response.headers["cache-control"]
    assert 'id="build"' in response.text
    assert "Morgana e Todd estão aqui" in response.text


