from uuid import UUID

import pytest

from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.models import ChatSession, Message
from campanario.chat.service import ChatService
from campanario.model.protocol import FakeModelProvider


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
    service = ChatService(
        sessions,
        messages,
        FakeModelProvider("resposta"),
        RecentMessagesContextManager(20),
        "fake-model",
    )
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
        from campanario.model.protocol import ModelUnavailableError

        if False:
            yield
        raise ModelUnavailableError("model unavailable")


@pytest.mark.asyncio
async def test_chat_service_keeps_user_message_and_does_not_persist_assistant_on_model_failure() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    service = ChatService(
        sessions,
        messages,
        FailingModelProvider(),
        RecentMessagesContextManager(20),
        "fake-model",
    )
    session = service.create_session()

    from campanario.model.protocol import ModelUnavailableError

    with pytest.raises(ModelUnavailableError):
        _ = [chunk async for chunk in service.stream_reply(session.id, "mensagem importante")]

    history = service.get_messages(session.id)
    assert [message.content for message in history] == ["mensagem importante"]
    assert history[0].role.value == "user"


class RecordingContextManager:
    def __init__(self) -> None:
        self.history: list[Message] | None = None

    async def build(self, history):
        from campanario.model.protocol import ModelMessage

        self.history = list(history)
        return (ModelMessage(role=self.history[-1].role, content="context-selected"),)


class RecordingProvider:
    def __init__(self) -> None:
        self.request = None

    async def health(self) -> bool:
        return True

    async def stream(self, request):
        from campanario.model.protocol import ModelChunk

        self.request = request
        yield ModelChunk(text="ok")


@pytest.mark.asyncio
async def test_chat_service_delegates_context_selection() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    context_manager = RecordingContextManager()
    provider = RecordingProvider()
    service = ChatService(sessions, messages, provider, context_manager, "fake-model")
    session = service.create_session()

    _ = [chunk async for chunk in service.stream_reply(session.id, "mensagem atual")]

    assert context_manager.history is not None
    assert [message.content for message in context_manager.history] == ["mensagem atual"]
    assert provider.request is not None
    assert [message.content for message in provider.request.messages] == ["context-selected"]
