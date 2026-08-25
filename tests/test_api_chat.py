from uuid import UUID

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
    monkeypatch.setattr(api_module, "get_chat_service", lambda: service)
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
    monkeypatch.setattr(api_module, "get_chat_service", lambda: service)
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
    monkeypatch.setattr(api_module, "get_chat_service", lambda: service)
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
