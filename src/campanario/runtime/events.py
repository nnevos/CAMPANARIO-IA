from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from enum import StrEnum
import logging
from threading import RLock
from typing import Any, Literal, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


EVENT_SCHEMA_VERSION = "1.0"
logger = logging.getLogger(__name__)


class EventType(StrEnum):
    USER_TEXT = "USER_TEXT"
    USER_SPEECH_PARTIAL = "USER_SPEECH_PARTIAL"
    USER_SPEECH_FINAL = "USER_SPEECH_FINAL"
    WAKE_DETECTED = "WAKE_DETECTED"

    SESSION_STARTED = "SESSION_STARTED"
    SESSION_ENDED = "SESSION_ENDED"

    DEVICE_CONNECTED = "DEVICE_CONNECTED"
    DEVICE_DISCONNECTED = "DEVICE_DISCONNECTED"
    DEVICE_STATE_CHANGED = "DEVICE_STATE_CHANGED"

    AGENT_SELECTED = "AGENT_SELECTED"
    AGENT_INTENT_TO_SPEAK = "AGENT_INTENT_TO_SPEAK"
    AGENT_RESPONSE_STARTED = "AGENT_RESPONSE_STARTED"
    AGENT_RESPONSE_CHUNK = "AGENT_RESPONSE_CHUNK"
    AGENT_RESPONSE_FINISHED = "AGENT_RESPONSE_FINISHED"
    AGENT_INTERRUPTED = "AGENT_INTERRUPTED"

    TOOL_REQUESTED = "TOOL_REQUESTED"
    TOOL_STARTED = "TOOL_STARTED"
    TOOL_RESULT = "TOOL_RESULT"
    TOOL_FAILED = "TOOL_FAILED"

    LOCATION_UPDATED = "LOCATION_UPDATED"
    CONTEXT_UPDATED = "CONTEXT_UPDATED"

    MEMORY_CANDIDATE = "MEMORY_CANDIDATE"
    MEMORY_WRITTEN = "MEMORY_WRITTEN"
    MEMORY_CORRECTED = "MEMORY_CORRECTED"

    CALL_STARTED = "CALL_STARTED"
    CALL_ENDED = "CALL_ENDED"


class EventSourceKind(StrEnum):
    RUNTIME = "runtime"
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"
    CLIENT = "client"
    DEVICE = "device"
    TOOL = "tool"


class EventProvenance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_kind: EventSourceKind
    source_id: str = Field(min_length=1, max_length=128)
    agent_id: str | None = Field(default=None, max_length=64)
    client_id: str | None = Field(default=None, max_length=128)
    device_id: str | None = Field(default=None, max_length=128)


class EmptyPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class UserTextPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    text: str = Field(min_length=1)


class SessionStartedPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    title: str | None = None
    primary_agent_id: str = Field(min_length=1, max_length=64)


class SessionEndedPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    reason: str | None = None


class AgentSelectedPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_id: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=1, max_length=128)
    position: Literal["primary", "secondary"]


class AgentResponsePayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_id: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=1, max_length=128)


class AgentResponseChunkPayload(AgentResponsePayload):
    text: str


class SpeechPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    text: str = ""
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class WakeDetectedPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    phrase: str | None = None


class DeviceStatePayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    device_id: str = Field(min_length=1, max_length=128)
    name: str | None = Field(default=None, max_length=128)
    device_type: str | None = Field(default=None, max_length=64)
    connection_state: str = Field(min_length=1, max_length=64)
    capabilities: tuple[str, ...] = ()


class AgentInterruptedPayload(AgentResponsePayload):
    interruption_reason: str = Field(min_length=1, max_length=128)


class ToolEventPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    request_id: UUID
    capability: str = Field(min_length=1, max_length=128)
    status: str = Field(min_length=1, max_length=64)
    data: dict[str, Any] = Field(default_factory=dict)


class LocationUpdatedPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    accuracy_meters: float | None = Field(default=None, ge=0.0)
    source_device_id: str | None = Field(default=None, max_length=128)


class ContextUpdatedPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    keys: tuple[str, ...]
    reason: str | None = Field(default=None, max_length=256)


class MemoryEventPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    memory_id: UUID
    operation: str = Field(min_length=1, max_length=64)


class CallEventPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    call_id: UUID
    state: str = Field(min_length=1, max_length=64)


EventPayload = (
    EmptyPayload
    | UserTextPayload
    | SessionStartedPayload
    | SessionEndedPayload
    | AgentSelectedPayload
    | AgentResponsePayload
    | AgentResponseChunkPayload
    | SpeechPayload
    | WakeDetectedPayload
    | DeviceStatePayload
    | AgentInterruptedPayload
    | ToolEventPayload
    | LocationUpdatedPayload
    | ContextUpdatedPayload
    | MemoryEventPayload
    | CallEventPayload
)


_PAYLOAD_TYPES: dict[EventType, type[BaseModel]] = {
    EventType.USER_TEXT: UserTextPayload,
    EventType.USER_SPEECH_PARTIAL: SpeechPayload,
    EventType.USER_SPEECH_FINAL: SpeechPayload,
    EventType.WAKE_DETECTED: WakeDetectedPayload,
    EventType.SESSION_STARTED: SessionStartedPayload,
    EventType.SESSION_ENDED: SessionEndedPayload,
    EventType.DEVICE_CONNECTED: DeviceStatePayload,
    EventType.DEVICE_DISCONNECTED: DeviceStatePayload,
    EventType.DEVICE_STATE_CHANGED: DeviceStatePayload,
    EventType.AGENT_SELECTED: AgentSelectedPayload,
    EventType.AGENT_INTENT_TO_SPEAK: AgentResponsePayload,
    EventType.AGENT_RESPONSE_STARTED: AgentResponsePayload,
    EventType.AGENT_RESPONSE_CHUNK: AgentResponseChunkPayload,
    EventType.AGENT_RESPONSE_FINISHED: AgentResponsePayload,
    EventType.AGENT_INTERRUPTED: AgentInterruptedPayload,
    EventType.TOOL_REQUESTED: ToolEventPayload,
    EventType.TOOL_STARTED: ToolEventPayload,
    EventType.TOOL_RESULT: ToolEventPayload,
    EventType.TOOL_FAILED: ToolEventPayload,
    EventType.LOCATION_UPDATED: LocationUpdatedPayload,
    EventType.CONTEXT_UPDATED: ContextUpdatedPayload,
    EventType.MEMORY_CANDIDATE: MemoryEventPayload,
    EventType.MEMORY_WRITTEN: MemoryEventPayload,
    EventType.MEMORY_CORRECTED: MemoryEventPayload,
    EventType.CALL_STARTED: CallEventPayload,
    EventType.CALL_ENDED: CallEventPayload,
}


class RuntimeEvent(BaseModel):
    """Versioned internal event envelope.

    PF2 keeps replay process-local and in-memory. Durable replay/network delivery are intentionally
    deferred; the contract itself is stable enough for PF3 adapters to consume without inventing
    transport-specific dictionaries.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = EVENT_SCHEMA_VERSION
    event_id: UUID
    sequence: int = Field(ge=1)
    event_type: EventType
    occurred_at: datetime
    runtime_id: UUID
    session_id: UUID | None = None
    correlation_id: UUID
    causation_id: UUID | None = None
    provenance: EventProvenance
    payload: dict[str, Any]


EventSubscriber = Callable[[RuntimeEvent], None]


class EventPublisher(Protocol):
    def publish(
        self,
        event_type: EventType,
        payload: BaseModel | dict[str, Any] | None = None,
        *,
        provenance: EventProvenance,
        session_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> RuntimeEvent: ...


class RuntimeEventBus:
    """Ordered process-local event bus with versioned envelopes and basic replay journal."""

    def __init__(self, runtime_id: UUID, *, journal_limit: int = 10_000) -> None:
        if journal_limit < 1:
            raise ValueError("journal_limit must be >= 1")
        self._runtime_id = runtime_id
        self._journal_limit = journal_limit
        self._sequence = 0
        self._journal: list[RuntimeEvent] = []
        self._subscribers: dict[UUID, tuple[EventSubscriber, frozenset[EventType] | None]] = {}
        self._lock = RLock()

    @property
    def runtime_id(self) -> UUID:
        return self._runtime_id

    @property
    def latest_sequence(self) -> int:
        with self._lock:
            return self._sequence

    def publish(
        self,
        event_type: EventType,
        payload: BaseModel | dict[str, Any] | None = None,
        *,
        provenance: EventProvenance,
        session_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> RuntimeEvent:
        payload_type = _PAYLOAD_TYPES.get(event_type, EmptyPayload)
        if payload is None:
            validated = payload_type()
        elif isinstance(payload, BaseModel):
            validated = payload_type.model_validate(payload.model_dump())
        else:
            validated = payload_type.model_validate(payload)

        with self._lock:
            self._sequence += 1
            event = RuntimeEvent(
                event_id=uuid4(),
                sequence=self._sequence,
                event_type=event_type,
                occurred_at=datetime.now(UTC),
                runtime_id=self._runtime_id,
                session_id=session_id,
                correlation_id=correlation_id or uuid4(),
                causation_id=causation_id,
                provenance=provenance,
                payload=validated.model_dump(mode="json"),
            )
            self._journal.append(event)
            if len(self._journal) > self._journal_limit:
                del self._journal[: len(self._journal) - self._journal_limit]
            subscribers = tuple(self._subscribers.values())

        for callback, event_types in subscribers:
            if event_types is None or event.event_type in event_types:
                try:
                    callback(event)
                except Exception as exc:
                    # A browser, TTS observer or metrics subscriber is not part
                    # of the event transaction. The committed journal and other
                    # subscribers must remain available when one fails.
                    logger.warning(
                        "event_subscriber_failed type=%s sequence=%d error_type=%s",
                        event.event_type.value, event.sequence, type(exc).__name__,
                    )
        return event

    def subscribe(
        self,
        callback: EventSubscriber,
        *,
        event_types: Iterable[EventType] | None = None,
    ) -> UUID:
        subscription_id = uuid4()
        selected = None if event_types is None else frozenset(event_types)
        with self._lock:
            self._subscribers[subscription_id] = (callback, selected)
        return subscription_id

    def unsubscribe(self, subscription_id: UUID) -> None:
        with self._lock:
            self._subscribers.pop(subscription_id, None)

    def replay(
        self,
        *,
        after_sequence: int = 0,
        session_id: UUID | None = None,
        event_types: Iterable[EventType] | None = None,
    ) -> tuple[RuntimeEvent, ...]:
        selected = None if event_types is None else frozenset(event_types)
        with self._lock:
            return tuple(
                event
                for event in self._journal
                if event.sequence > after_sequence
                and (session_id is None or event.session_id == session_id)
                and (selected is None or event.event_type in selected)
            )
