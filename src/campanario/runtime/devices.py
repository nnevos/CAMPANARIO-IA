from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from campanario.runtime.events import (
    DeviceStatePayload,
    EventProvenance,
    EventSourceKind,
    EventType,
    RuntimeEventBus,
)


class DeviceConnectionState(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class Device(BaseModel):
    """Persistent device identity described by capabilities, not by a hardcoded platform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=64)
    capabilities: tuple[str, ...] = ()
    connection_state: DeviceConnectionState
    created_at: datetime
    updated_at: datetime
    last_seen: datetime

    @field_validator("capabilities", mode="before")
    @classmethod
    def normalize_capabilities(cls, value) -> tuple[str, ...]:
        items = value or ()
        normalized = []
        for item in items:
            capability = str(item).strip().lower()
            if not capability:
                continue
            if len(capability) > 64:
                raise ValueError("device capability must be <= 64 characters")
            if capability not in normalized:
                normalized.append(capability)
        return tuple(sorted(normalized))


class DeviceAnnouncement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    device_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=64)
    capabilities: tuple[str, ...] = ()

    @field_validator("capabilities", mode="before")
    @classmethod
    def normalize_capabilities(cls, value) -> tuple[str, ...]:
        return Device.normalize_capabilities(value)


class DeviceRepository(Protocol):
    def get(self, device_id: str) -> Device | None: ...
    def list(self) -> list[Device]: ...
    def upsert(self, device: Device) -> Device: ...
    def find_by_capability(self, capability: str) -> list[Device]: ...


class DeviceRegistry:
    """Runtime-owned registry of persistent device identities and their advertised capabilities.

    PF4 deliberately does not assign trust or permissions. A registered device can be discovered by
    capability, but PF6 must still decide whether a later action is authorized.
    """

    def __init__(self, repository: DeviceRepository, events: RuntimeEventBus) -> None:
        self._repository = repository
        self._events = events

    @property
    def available(self) -> bool:
        return True

    def get(self, device_id: str) -> Device | None:
        return self._repository.get(device_id)

    def list(self) -> list[Device]:
        return self._repository.list()

    def find_capable(self, capability: str, *, connected_only: bool = True) -> list[Device]:
        normalized = capability.strip().lower()
        if not normalized:
            return []
        devices = self._repository.find_by_capability(normalized)
        if connected_only:
            devices = [item for item in devices if item.connection_state == DeviceConnectionState.CONNECTED]
        return devices

    def connect(self, announcement: DeviceAnnouncement) -> Device:
        now = datetime.now(UTC)
        previous = self._repository.get(announcement.device_id)
        device = Device(
            id=announcement.device_id,
            name=announcement.name,
            type=announcement.type,
            capabilities=announcement.capabilities,
            connection_state=DeviceConnectionState.CONNECTED,
            created_at=previous.created_at if previous else now,
            updated_at=now,
            last_seen=now,
        )
        saved = self._repository.upsert(device)
        event_type = (
            EventType.DEVICE_CONNECTED
            if previous is None or previous.connection_state == DeviceConnectionState.DISCONNECTED
            else EventType.DEVICE_STATE_CHANGED
        )
        self._publish(event_type, saved)
        return saved

    def disconnect(self, device_id: str) -> Device | None:
        previous = self._repository.get(device_id)
        if previous is None:
            return None
        if previous.connection_state == DeviceConnectionState.DISCONNECTED:
            return previous
        now = datetime.now(UTC)
        saved = self._repository.upsert(
            previous.model_copy(
                update={
                    "connection_state": DeviceConnectionState.DISCONNECTED,
                    "updated_at": now,
                    "last_seen": now,
                }
            )
        )
        self._publish(EventType.DEVICE_DISCONNECTED, saved)
        return saved

    def touch(self, device_id: str) -> Device | None:
        previous = self._repository.get(device_id)
        if previous is None:
            return None
        now = datetime.now(UTC)
        saved = self._repository.upsert(previous.model_copy(update={"updated_at": now, "last_seen": now}))
        self._publish(EventType.DEVICE_STATE_CHANGED, saved)
        return saved

    def _publish(self, event_type: EventType, device: Device) -> None:
        self._events.publish(
            event_type,
            DeviceStatePayload(
                device_id=device.id,
                name=device.name,
                device_type=device.type,
                connection_state=device.connection_state.value,
                capabilities=device.capabilities,
            ),
            provenance=EventProvenance(
                source_kind=EventSourceKind.DEVICE,
                source_id=device.id,
                device_id=device.id,
            ),
        )
