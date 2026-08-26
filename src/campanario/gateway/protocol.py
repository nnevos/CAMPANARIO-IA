from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from campanario.runtime.devices import Device
from campanario.runtime.events import RuntimeEvent


GATEWAY_SCHEMA_VERSION = "1.0"


class GatewayReadyFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = GATEWAY_SCHEMA_VERSION
    frame_type: Literal["ready"] = "ready"
    runtime_id: UUID
    session_id: UUID | None = None
    latest_sequence: int = Field(ge=0)
    replayed_through_sequence: int = Field(ge=0)
    runtime_status: str = Field(min_length=1, max_length=32)
    client_id: str | None = Field(default=None, max_length=128)
    device_id: str | None = Field(default=None, max_length=128)
    attachment_id: UUID | None = None


class GatewayEventFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = GATEWAY_SCHEMA_VERSION
    frame_type: Literal["event"] = "event"
    event: RuntimeEvent


class TurnCompletedResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = GATEWAY_SCHEMA_VERSION
    status: Literal["completed"] = "completed"
    session_id: UUID
    speakers: tuple[str, ...]
    event_sequence: int = Field(ge=0)
    client_id: str | None = Field(default=None, max_length=128)
    device_id: str | None = Field(default=None, max_length=128)


class DeviceHelloFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = GATEWAY_SCHEMA_VERSION
    frame_type: Literal["device_hello"] = "device_hello"
    device_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    device_type: str = Field(min_length=1, max_length=64)
    capabilities: tuple[str, ...] = ()


class DeviceLocationUpdateFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = GATEWAY_SCHEMA_VERSION
    frame_type: Literal["location_update"] = "location_update"
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    accuracy_meters: float | None = Field(default=None, ge=0.0)
    session_id: UUID | None = None


class DeviceCapabilityUpdatedFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = GATEWAY_SCHEMA_VERSION
    frame_type: Literal["capability_updated"] = "capability_updated"
    device_id: str = Field(min_length=1, max_length=128)
    capability: Literal["location.current"] = "location.current"
    event_sequence: int = Field(ge=1)


class DeviceReadyFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = GATEWAY_SCHEMA_VERSION
    frame_type: Literal["device_ready"] = "device_ready"
    runtime_id: UUID
    device: Device
    authenticated: bool = False
    pairing_required: bool = True


class GatewayPongFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = GATEWAY_SCHEMA_VERSION
    frame_type: Literal["pong"] = "pong"
    device_id: str = Field(min_length=1, max_length=128)
    last_seen: datetime | None = None
