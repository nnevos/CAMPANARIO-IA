from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock

from pydantic import BaseModel, ConfigDict, Field

from campanario.runtime.capabilities import (
    CapabilityDefinition,
    CapabilityProvenance,
    CapabilityProviderKind,
    DeviceCapabilityProvider,
)
from campanario.runtime.events import (
    EventProvenance,
    EventSourceKind,
    EventType,
    LocationUpdatedPayload,
)


class MobileLocationSample(BaseModel):
    """Latest explicit location snapshot supplied by one authenticated mobile device."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    device_id: str = Field(min_length=1, max_length=128)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    accuracy_meters: float | None = Field(default=None, ge=0.0)
    captured_at: datetime

    def capability_output(self) -> dict[str, object]:
        output: dict[str, object] = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "source_device_id": self.device_id,
        }
        if self.accuracy_meters is not None:
            output["accuracy_meters"] = self.accuracy_meters
        return output


class MobileCapabilityState:
    """Process-local mobile snapshots bridged into the normal PF5 Capability Registry.

    PF8 intentionally stores only current test/readiness state here. It is not user memory and is
    invalidated when the device disconnects so stale coordinates cannot masquerade as live data.
    """

    def __init__(self) -> None:
        self._locations: dict[str, MobileLocationSample] = {}
        self._lock = RLock()

    def update_location(
        self,
        device_id: str,
        *,
        latitude: float,
        longitude: float,
        accuracy_meters: float | None = None,
    ) -> MobileLocationSample:
        sample = MobileLocationSample(
            device_id=device_id,
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
            captured_at=datetime.now(UTC),
        )
        with self._lock:
            self._locations[device_id] = sample
        return sample

    def location(self, device_id: str) -> MobileLocationSample | None:
        with self._lock:
            return self._locations.get(device_id)

    def clear_device(self, device_id: str) -> None:
        with self._lock:
            self._locations.pop(device_id, None)


def install_mobile_location_provider(runtime, device_id: str) -> CapabilityDefinition:
    """Expose one authenticated PF8 device snapshot as semantic `location.current`.

    Provider selection remains a runtime concern: callers only see `location.current`. PF8 proves
    one mobile device end-to-end; multi-device provider arbitration is intentionally not invented
    here and can be added later without changing the semantic capability contract.
    """

    async def read_location(capability: str, arguments: dict[str, object]) -> dict[str, object]:  # noqa: ARG001
        sample = runtime.mobile.location(device_id)
        if sample is None:
            from campanario.runtime.capabilities import CapabilityUnavailableError

            raise CapabilityUnavailableError("location.current has no fresh mobile snapshot")
        return sample.capability_output()

    provider = DeviceCapabilityProvider(
        device_id=device_id,
        devices=runtime.devices,
        handler=read_location,
        required_device_capability="gps",
    )
    runtime.tools.register_provider(provider)
    definition = CapabilityDefinition(
        name="location.current",
        description="Current explicit location snapshot supplied by a connected device.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        output_schema={
            "type": "object",
            "required": ["latitude", "longitude", "source_device_id"],
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "accuracy_meters": {"type": "number"},
                "source_device_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
        provider_id=provider.provider_id,
        permissions=("location.read",),
        timeout_seconds=2.0,
        provenance=CapabilityProvenance(
            provider_kind=CapabilityProviderKind.DEVICE,
            provider_id=provider.provider_id,
            device_id=device_id,
        ),
    )
    return runtime.tools.register(definition)


def publish_mobile_location(runtime, sample: MobileLocationSample, *, session_id=None):
    """Publish the PF2 location event after an authenticated mobile snapshot is accepted."""

    return runtime.events.publish(
        EventType.LOCATION_UPDATED,
        LocationUpdatedPayload(
            latitude=sample.latitude,
            longitude=sample.longitude,
            accuracy_meters=sample.accuracy_meters,
            source_device_id=sample.device_id,
        ),
        provenance=EventProvenance(
            source_kind=EventSourceKind.DEVICE,
            source_id=sample.device_id,
            device_id=sample.device_id,
        ),
        session_id=session_id,
    )
