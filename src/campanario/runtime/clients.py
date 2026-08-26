from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ClientIdentity(BaseModel):
    """Identity of one software client surface.

    client_id identifies an application/browser instance. device_id, when present, identifies the
    physical PF4 device hosting that client. Neither field is a social participant or agent id.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    client_id: str = Field(min_length=1, max_length=128)
    device_id: str | None = Field(default=None, max_length=128)


class ClientAttachment(BaseModel):
    """Ephemeral attachment of one client to a durable Campanario session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    attachment_id: UUID
    session_id: UUID
    client_id: str = Field(min_length=1, max_length=128)
    device_id: str | None = Field(default=None, max_length=128)
    connected_at: datetime
    last_seen: datetime


class ClientSessionRegistry:
    """Process-local client attachments.

    Sessions remain durable/shared in the conversation repository. Attachments intentionally do not
    survive process restart because they represent live transport connections, not conversation
    ownership or memory.
    """

    def __init__(self) -> None:
        self._items: dict[UUID, ClientAttachment] = {}
        self._lock = RLock()

    def attach(self, session_id: UUID, identity: ClientIdentity) -> ClientAttachment:
        now = datetime.now(UTC)
        attachment = ClientAttachment(
            attachment_id=uuid4(),
            session_id=session_id,
            client_id=identity.client_id,
            device_id=identity.device_id,
            connected_at=now,
            last_seen=now,
        )
        with self._lock:
            self._items[attachment.attachment_id] = attachment
        return attachment

    def detach(self, attachment_id: UUID) -> None:
        with self._lock:
            self._items.pop(attachment_id, None)

    def touch(self, attachment_id: UUID) -> ClientAttachment | None:
        with self._lock:
            current = self._items.get(attachment_id)
            if current is None:
                return None
            updated = current.model_copy(update={"last_seen": datetime.now(UTC)})
            self._items[attachment_id] = updated
            return updated

    def list(self, *, session_id: UUID | None = None) -> tuple[ClientAttachment, ...]:
        with self._lock:
            values = tuple(self._items.values())
        if session_id is not None:
            values = tuple(item for item in values if item.session_id == session_id)
        return tuple(sorted(values, key=lambda item: (item.connected_at, str(item.attachment_id))))
