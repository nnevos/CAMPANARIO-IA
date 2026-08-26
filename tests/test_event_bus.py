from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.models import ChatSession, Message
from campanario.chat.service import ChatService
from campanario.model.protocol import FakeModelProvider
from campanario.runtime.events import (
    EVENT_SCHEMA_VERSION,
    EventProvenance,
    EventSourceKind,
    EventType,
    RuntimeEventBus,
    UserTextPayload,
)


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
            created_at=current.created_at,
            updated_at=current.updated_at,
            status=current.status,
            title=current.title,
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
        return [item for item in self.items if item.session_id == session_id]


def test_event_bus_assigns_versioned_ordered_envelopes_and_replays() -> None:
    runtime_id = uuid4()
    session_id = uuid4()
    correlation_id = uuid4()
    bus = RuntimeEventBus(runtime_id)
    provenance = EventProvenance(source_kind=EventSourceKind.USER, source_id="client-test")

    first = bus.publish(
        EventType.USER_TEXT,
        UserTextPayload(text="primeiro"),
        session_id=session_id,
        correlation_id=correlation_id,
        provenance=provenance,
    )
    second = bus.publish(
        EventType.USER_TEXT,
        UserTextPayload(text="segundo"),
        session_id=session_id,
        correlation_id=correlation_id,
        causation_id=first.event_id,
        provenance=provenance,
    )

    assert first.schema_version == EVENT_SCHEMA_VERSION
    assert first.runtime_id == runtime_id
    assert [first.sequence, second.sequence] == [1, 2]
    assert second.causation_id == first.event_id
    assert second.correlation_id == correlation_id
    assert second.provenance.source_id == "client-test"
    assert [event.event_id for event in bus.replay(session_id=session_id)] == [
        first.event_id,
        second.event_id,
    ]
    assert bus.replay(after_sequence=1) == (second,)


def test_event_bus_filters_subscriptions_and_unsubscribe() -> None:
    bus = RuntimeEventBus(uuid4())
    seen = []
    subscription = bus.subscribe(seen.append, event_types=[EventType.USER_TEXT])
    provenance = EventProvenance(source_kind=EventSourceKind.USER, source_id="user")

    bus.publish(EventType.USER_TEXT, {"text": "oi"}, provenance=provenance)
    bus.publish(
        EventType.SESSION_STARTED,
        {"title": None, "primary_agent_id": "morgana"},
        provenance=EventProvenance(source_kind=EventSourceKind.RUNTIME, source_id="conversation"),
    )
    bus.unsubscribe(subscription)
    bus.publish(EventType.USER_TEXT, {"text": "depois"}, provenance=provenance)

    assert [event.event_type for event in seen] == [EventType.USER_TEXT]
    assert seen[0].payload == {"text": "oi"}


def test_event_bus_rejects_payload_outside_event_contract() -> None:
    bus = RuntimeEventBus(uuid4())
    provenance = EventProvenance(source_kind=EventSourceKind.USER, source_id="user")

    with pytest.raises(ValidationError):
        bus.publish(EventType.USER_TEXT, {"text": "oi", "provider_specific": True}, provenance=provenance)


@pytest.mark.asyncio
async def test_conversation_emits_ordered_provenance_for_one_agent_turn() -> None:
    bus = RuntimeEventBus(uuid4())
    service = ChatService(
        InMemorySessions(),
        InMemoryMessages(),
        FakeModelProvider("resposta"),
        RecentMessagesContextManager(20),
        "fake-model",
        event_bus=bus,
    )
    session = service.create_session("evento")
    session_started = bus.replay(session_id=session.id)
    assert len(session_started) == 1
    assert session_started[0].event_type == EventType.SESSION_STARTED

    streamed = [event async for event in service.stream_turn(session.id, "olá")]
    turn_events = bus.replay(after_sequence=session_started[0].sequence, session_id=session.id)

    assert [item.type for item in streamed] == ["speaker_start", "token", "speaker_done"]
    assert [event.event_type for event in turn_events] == [
        EventType.USER_TEXT,
        EventType.AGENT_SELECTED,
        EventType.AGENT_INTENT_TO_SPEAK,
        EventType.AGENT_RESPONSE_STARTED,
        EventType.AGENT_RESPONSE_CHUNK,
        EventType.AGENT_RESPONSE_FINISHED,
    ]
    assert [event.sequence for event in turn_events] == sorted(event.sequence for event in turn_events)
    assert len({event.correlation_id for event in turn_events}) == 1
    assert all(event.runtime_id == bus.runtime_id for event in turn_events)
    agent_events = [event for event in turn_events if event.provenance.source_kind == EventSourceKind.AGENT]
    assert agent_events
    assert all(event.provenance.agent_id == "morgana" for event in agent_events)
    assert turn_events[1].causation_id == turn_events[0].event_id
    assert turn_events[2].causation_id == turn_events[1].event_id
    assert turn_events[3].causation_id == turn_events[2].event_id
