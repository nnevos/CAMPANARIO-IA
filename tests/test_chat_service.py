from uuid import UUID

import pytest

from campanario.chat.models import ChatSession, Message
from campanario.chat.service import ChatService
from campanario.llm.provider import FakeModelProvider


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


@pytest.mark.asyncio
async def test_chat_service_persists_user_and_assistant_messages() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    service = ChatService(sessions, messages, FakeModelProvider("resposta"), "fake-model")
    session = service.create_session()

    streamed = "".join([chunk async for chunk in service.stream_reply(session.id, "olá")])

    assert streamed == "resposta"
    history = service.get_messages(session.id)
    assert [message.content for message in history] == ["olá", "resposta"]
    assert history[1].model == "fake-model"


class FailingModelProvider:
    async def health(self) -> bool:
        return False

    async def stream(self, request):
        from campanario.llm.provider import ModelUnavailableError

        if False:
            yield
        raise ModelUnavailableError("model unavailable")


@pytest.mark.asyncio
async def test_chat_service_keeps_user_message_and_does_not_persist_assistant_on_model_failure() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    service = ChatService(sessions, messages, FailingModelProvider(), "fake-model")
    session = service.create_session()

    from campanario.llm.provider import ModelUnavailableError

    with pytest.raises(ModelUnavailableError):
        _ = [chunk async for chunk in service.stream_reply(session.id, "mensagem importante")]

    history = service.get_messages(session.id)
    assert [message.content for message in history] == ["mensagem importante"]
    assert history[0].role.value == "user"
