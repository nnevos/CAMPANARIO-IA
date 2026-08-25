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
    assert provider.request.messages[-1].content == "context-selected"
    assert "AGENTE COM PRIORIDADE DE FALA: MORGANA" in provider.request.messages[0].content

@pytest.mark.asyncio
async def test_chat_service_switches_agent_per_session_and_persists_response_provenance() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = RecordingProvider()
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
    )
    session = service.create_session(agent_id="todd")

    _ = [chunk async for chunk in service.stream_reply(session.id, "oi")]
    assert service.get_messages(session.id)[-1].agent_id == "todd"
    assert provider.request is not None
    assert "AGENTE COM PRIORIDADE DE FALA: TODD" in provider.request.messages[0].content

    updated = service.set_session_agent(session.id, "morgana")
    assert updated.primary_agent_id == "morgana"
    _ = [chunk async for chunk in service.stream_reply(session.id, "continua")]
    assert service.get_messages(session.id)[-1].agent_id == "morgana"
    assert provider.request is not None
    assert "AGENTE COM PRIORIDADE DE FALA: MORGANA" in provider.request.messages[0].content
    assert "outros agentes: todd" in provider.request.messages[0].content.lower()

@pytest.mark.asyncio
async def test_direct_wake_switches_bridge_agent_and_provenance() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = RecordingProvider()
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
    )
    session = service.create_session()
    assert session.primary_agent_id == "morgana"

    _ = [chunk async for chunk in service.stream_reply(session.id, "Todd, olha isso")]
    assert sessions.get(session.id).primary_agent_id == "todd"
    assert service.get_messages(session.id)[-1].agent_id == "todd"
    assert provider.request is not None
    assert "AGENTE COM PRIORIDADE DE FALA: TODD" in provider.request.messages[0].content

    _ = [chunk async for chunk in service.stream_reply(session.id, "Campanário")]
    assert sessions.get(session.id).primary_agent_id == "todd"
    assert service.get_messages(session.id)[-1].agent_id == "todd"

    _ = [chunk async for chunk in service.stream_reply(session.id, "Morgana")]
    assert sessions.get(session.id).primary_agent_id == "morgana"
    assert service.get_messages(session.id)[-1].agent_id == "morgana"

class QueueProvider:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.requests = []

    async def health(self) -> bool:
        return True

    async def stream(self, request):
        from campanario.model.protocol import ModelChunk
        self.requests.append(request)
        response = self.responses.pop(0)
        yield ModelChunk(text=response)
        yield ModelChunk(text="", done=True)


class JoinDecisionProvider:
    async def health(self) -> bool:
        return True

    async def stream(self, request):
        from campanario.model.protocol import ModelChunk
        yield ModelChunk(text="JOIN")
        yield ModelChunk(text="", done=True)


@pytest.mark.asyncio
async def test_explicit_group_turn_can_produce_two_agent_messages_in_same_session() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider(["Morgana primeiro.", "Todd complementa."])
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
    )
    session = service.create_session()

    events = [event async for event in service.stream_turn(session.id, "Morgana e Todd, o que vocês acham disso?")]

    starts = [event.agent_id for event in events if event.type == "speaker_start"]
    assert starts == ["morgana", "todd"]
    assistant_messages = [m for m in service.get_messages(session.id) if m.role.value == "assistant"]
    assert [(m.agent_id, m.content) for m in assistant_messages] == [
        ("morgana", "Morgana primeiro."),
        ("todd", "Todd complementa."),
    ]
    assert sessions.get(session.id).primary_agent_id == "morgana"


@pytest.mark.asyncio
async def test_secondary_can_spontaneously_join_open_discussion_when_arbiter_finds_distinct_value() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider(["Eu iria pelo caminho A.", "Eu discordo do A por causa do risco B."])
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
        participation_provider=JoinDecisionProvider(),
    )
    session = service.create_session()

    events = [event async for event in service.stream_turn(session.id, "o que você acha dessa decisão?")]

    assert [event.agent_id for event in events if event.type == "speaker_start"] == ["morgana", "todd"]
    history = service.get_messages(session.id)
    assert [m.agent_id for m in history if m.role.value == "assistant"] == ["morgana", "todd"]
    assert sessions.get(session.id).primary_agent_id == "morgana"


@pytest.mark.asyncio
async def test_closed_factual_turn_does_not_spawn_panel_even_if_decider_would_join() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider(["Wellington."])
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
        participation_provider=JoinDecisionProvider(),
    )
    session = service.create_session()

    events = [event async for event in service.stream_turn(session.id, "qual é a capital da Nova Zelândia?")]
    assert [event.agent_id for event in events if event.type == "speaker_start"] == ["morgana"]

@pytest.mark.asyncio
async def test_short_social_share_may_invite_secondary_but_greeting_does_not() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider(["Entendi.", "Eu acrescentaria uma coisa."])
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
        participation_provider=JoinDecisionProvider(),
    )
    session = service.create_session()
    share_events = [event async for event in service.stream_turn(session.id, "hoje tô meio perdido")]
    assert [e.agent_id for e in share_events if e.type == "speaker_start"] == ["morgana", "todd"]

    sessions2 = InMemorySessions()
    messages2 = InMemoryMessages()
    provider2 = QueueProvider(["Opa."])
    service2 = ChatService(
        sessions2,
        messages2,
        provider2,
        RecentMessagesContextManager(20),
        "fake-model",
        participation_provider=JoinDecisionProvider(),
    )
    session2 = service2.create_session()
    greet_events = [event async for event in service2.stream_turn(session2.id, "eae")]
    assert [e.agent_id for e in greet_events if e.type == "speaker_start"] == ["morgana"]
