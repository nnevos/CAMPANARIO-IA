from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from campanario.chat.models import ChatSession, Message
from campanario.chat.service import AgentStreamEvent
from campanario.runtime.capabilities import CapabilityExecutionResult, CapabilityStatus
from campanario.runtime.clients import ClientAttachment, ClientIdentity
from campanario.runtime.devices import Device
from campanario.runtime.events import EventProvenance, EventType, RuntimeEvent


class ConversationService(Protocol):
    """Client-independent conversation boundary owned by the Campanario runtime."""

    def create_session(self, title: str | None = None, agent_id: str | None = None) -> ChatSession: ...
    def list_sessions(self) -> list[ChatSession]: ...
    def get_messages(self, session_id: UUID) -> list[Message]: ...
    def stream_turn(self, session_id: UUID, user_text: str, *, client: ClientIdentity | None = None) -> AsyncIterator[AgentStreamEvent]: ...


class SessionManager(Protocol):
    """Session lifecycle boundary. Sessions belong to Campanario, not to a UI client."""

    def create_session(self, title: str | None = None, primary_agent_id: str | None = None) -> ChatSession: ...
    def list_sessions(self) -> list[ChatSession]: ...


class AgentRuntime(Protocol):
    """Future agent execution boundary; must share the runtime's state and evidence."""

    @property
    def participant_ids(self) -> tuple[str, ...]: ...


class ToolRuntime(Protocol):
    """Provider-independent capability execution boundary owned by Campanario."""

    @property
    def available(self) -> bool: ...
    def get(self, name: str) -> CapabilityStatus | None: ...
    def list(self, *, available_only: bool = False) -> list[CapabilityStatus]: ...
    async def execute(self, name: str, arguments=None, *, session_id=None, requested_by=None) -> CapabilityExecutionResult: ...


class DeviceRuntime(Protocol):
    """Connected-device boundary, independent from social participants and authorization."""

    @property
    def available(self) -> bool: ...
    def get(self, device_id: str) -> Device | None: ...
    def list(self) -> list[Device]: ...
    def find_capable(self, capability: str, *, connected_only: bool = True) -> list[Device]: ...


class EventBus(Protocol):
    """Versioned ordered event stream owned by the runtime, not by any client transport."""

    def publish(
        self,
        event_type: EventType,
        payload=None,
        *,
        provenance: EventProvenance,
        session_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> RuntimeEvent: ...

    def replay(
        self,
        *,
        after_sequence: int = 0,
        session_id: UUID | None = None,
        event_types=None,
    ) -> tuple[RuntimeEvent, ...]: ...


class ClientRuntime(Protocol):
    """Live client attachment boundary. Client identity is not session ownership or speaker identity."""

    def attach(self, session_id: UUID, identity: ClientIdentity) -> ClientAttachment: ...
    def detach(self, attachment_id: UUID) -> None: ...
    def list(self, *, session_id: UUID | None = None) -> tuple[ClientAttachment, ...]: ...
