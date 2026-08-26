from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from enum import StrEnum
from time import perf_counter
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from campanario.runtime.devices import DeviceConnectionState, DeviceRegistry
from campanario.runtime.permissions import AuthorizationContext, PermissionConfirmationRequired, PermissionDecision, PermissionDeniedError, PermissionPolicy
from campanario.runtime.events import EventProvenance, EventSourceKind, EventType, RuntimeEventBus, ToolEventPayload


class CapabilityError(RuntimeError):
    pass


class CapabilityNotFoundError(CapabilityError):
    pass


class CapabilityUnavailableError(CapabilityError):
    pass


class CapabilityValidationError(CapabilityError):
    pass


class CapabilityExecutionError(CapabilityError):
    pass


class CapabilityTimeoutError(CapabilityError):
    pass


class CapabilityProviderKind(StrEnum):
    SYSTEM = "system"
    DEVICE = "device"
    EXTERNAL = "external"
    MOCK = "mock"


class CapabilityProvenance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_kind: CapabilityProviderKind
    provider_id: str = Field(min_length=1, max_length=160)
    device_id: str | None = Field(default=None, max_length=128)


class CapabilityDefinition(BaseModel):
    """Provider-independent capability contract exposed by the Campanario runtime."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=512)
    input_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object", "properties": {}})
    output_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    provider_id: str = Field(min_length=1, max_length=160)
    permissions: tuple[str, ...] = ()
    timeout_seconds: float = Field(default=10.0, gt=0.0, le=300.0)
    provenance: CapabilityProvenance

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized or any(ch.isspace() for ch in normalized):
            raise ValueError("capability name must be a non-blank dotted identifier")
        return normalized

    @field_validator("permissions", mode="before")
    @classmethod
    def normalize_permissions(cls, value) -> tuple[str, ...]:
        items = []
        for item in value or ():
            normalized = str(item).strip().lower()
            if normalized and normalized not in items:
                items.append(normalized)
        return tuple(sorted(items))


class CapabilityStatus(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    definition: CapabilityDefinition
    available: bool


class CapabilityExecutionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: UUID
    capability: str
    provider_id: str
    output: dict[str, Any]
    provenance: CapabilityProvenance
    duration_ms: float = Field(ge=0.0)


class CapabilityProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    @property
    def available(self) -> bool: ...

    async def invoke(self, capability: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


CapabilityHandler = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]] | dict[str, Any]]


class CallbackCapabilityProvider:
    """Small transport-neutral provider adapter useful for local, mock and future provider bridges."""

    def __init__(self, provider_id: str, handler: CapabilityHandler, *, available: Callable[[], bool] | None = None) -> None:
        self._provider_id = provider_id
        self._handler = handler
        self._available = available or (lambda: True)

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def available(self) -> bool:
        return bool(self._available())

    async def invoke(self, capability: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = self._handler(capability, arguments)
        if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
            result = await result
        if not isinstance(result, dict):
            raise CapabilityExecutionError("capability provider must return an object")
        return result


class DeviceCapabilityProvider(CallbackCapabilityProvider):
    """Provider bridge whose availability follows one PF4 device identity.

    PF5 does not authenticate the device. PF6 must decide whether an available capability is
    authorized before this bridge is exposed beyond trusted/local test flows.
    """

    def __init__(
        self,
        *,
        device_id: str,
        devices: DeviceRegistry,
        handler: CapabilityHandler,
        required_device_capability: str | None = None,
    ) -> None:
        self.device_id = device_id
        self.required_device_capability = required_device_capability.strip().lower() if required_device_capability else None

        def is_available() -> bool:
            device = devices.get(device_id)
            if device is None or device.connection_state != DeviceConnectionState.CONNECTED:
                return False
            return self.required_device_capability is None or self.required_device_capability in device.capabilities

        super().__init__(f"device:{device_id}", handler, available=is_available)


class CapabilityRegistry:
    """Runtime-owned provider-independent capability/tool registry.

    Agents and clients reason about capability names. Provider selection, timeout, validation and
    provenance remain runtime concerns. Permission strings are metadata only until PF6.
    """

    def __init__(self, events: RuntimeEventBus, permissions: PermissionPolicy | None = None) -> None:
        self._events = events
        self._permissions = permissions
        self._definitions: dict[str, CapabilityDefinition] = {}
        self._providers: dict[str, CapabilityProvider] = {}

    @property
    def available(self) -> bool:
        return True

    def register_provider(self, provider: CapabilityProvider) -> None:
        provider_id = provider.provider_id.strip()
        if not provider_id:
            raise ValueError("provider_id cannot be blank")
        self._providers[provider_id] = provider

    def register(self, definition: CapabilityDefinition) -> CapabilityDefinition:
        if definition.provider_id not in self._providers:
            raise CapabilityUnavailableError(f"provider not registered: {definition.provider_id}")
        self._definitions[definition.name] = definition
        return definition

    def unregister(self, name: str) -> None:
        self._definitions.pop(name.strip().lower(), None)

    def get(self, name: str) -> CapabilityStatus | None:
        definition = self._definitions.get(name.strip().lower())
        if definition is None:
            return None
        provider = self._providers.get(definition.provider_id)
        return CapabilityStatus(definition=definition, available=bool(provider and provider.available))

    def list(self, *, available_only: bool = False) -> list[CapabilityStatus]:
        statuses = [self.get(name) for name in sorted(self._definitions)]
        result = [status for status in statuses if status is not None]
        if available_only:
            result = [status for status in result if status.available]
        return result

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        *,
        session_id: UUID | None = None,
        requested_by: EventProvenance | None = None,
        authorization: AuthorizationContext | None = None,
        permission_scope: str | None = None,
    ) -> CapabilityExecutionResult:
        normalized = name.strip().lower()
        status = self.get(normalized)
        if status is None:
            raise CapabilityNotFoundError(normalized)
        if not status.available:
            raise CapabilityUnavailableError(normalized)

        definition = status.definition
        provider = self._providers[definition.provider_id]
        arguments = dict(arguments or {})
        _validate_schema(arguments, definition.input_schema, where="input")

        if self._permissions and definition.permissions:
            auth = authorization or AuthorizationContext.internal_system()
            for permission in definition.permissions:
                check = self._permissions.check(permission, auth, capability=definition.name, scope=permission_scope)
                if check.decision == PermissionDecision.DENY:
                    raise PermissionDeniedError(permission, check.reason)
                if check.decision == PermissionDecision.CONFIRM:
                    raise PermissionConfirmationRequired(permission, check.confirmation_id)

        request_id = uuid4()
        correlation_id = uuid4()
        request_provenance = requested_by or EventProvenance(source_kind=EventSourceKind.SYSTEM, source_id="capability-registry")
        requested = self._events.publish(
            EventType.TOOL_REQUESTED,
            ToolEventPayload(
                request_id=request_id,
                capability=definition.name,
                status="requested",
                data={"provider_id": definition.provider_id, "arguments": arguments},
            ),
            provenance=request_provenance,
            session_id=session_id,
            correlation_id=correlation_id,
        )
        provider_event_provenance = _event_provenance(definition.provenance)
        started = self._events.publish(
            EventType.TOOL_STARTED,
            ToolEventPayload(
                request_id=request_id,
                capability=definition.name,
                status="started",
                data={"provider_id": definition.provider_id},
            ),
            provenance=provider_event_provenance,
            session_id=session_id,
            correlation_id=correlation_id,
            causation_id=requested.event_id,
        )
        began = perf_counter()
        try:
            output = await asyncio.wait_for(
                provider.invoke(definition.name, arguments), timeout=definition.timeout_seconds
            )
            _validate_schema(output, definition.output_schema, where="output")
        except asyncio.TimeoutError as exc:
            self._events.publish(
                EventType.TOOL_FAILED,
                ToolEventPayload(
                    request_id=request_id,
                    capability=definition.name,
                    status="timeout",
                    data={"provider_id": definition.provider_id},
                ),
                provenance=provider_event_provenance,
                session_id=session_id,
                correlation_id=correlation_id,
                causation_id=started.event_id,
            )
            raise CapabilityTimeoutError(definition.name) from exc
        except CapabilityError as exc:
            self._events.publish(
                EventType.TOOL_FAILED,
                ToolEventPayload(
                    request_id=request_id,
                    capability=definition.name,
                    status="failed",
                    data={"provider_id": definition.provider_id, "error_type": type(exc).__name__},
                ),
                provenance=provider_event_provenance,
                session_id=session_id,
                correlation_id=correlation_id,
                causation_id=started.event_id,
            )
            raise
        except Exception as exc:
            self._events.publish(
                EventType.TOOL_FAILED,
                ToolEventPayload(
                    request_id=request_id,
                    capability=definition.name,
                    status="failed",
                    data={"provider_id": definition.provider_id, "error_type": type(exc).__name__},
                ),
                provenance=provider_event_provenance,
                session_id=session_id,
                correlation_id=correlation_id,
                causation_id=started.event_id,
            )
            raise CapabilityExecutionError(definition.name) from exc

        duration_ms = (perf_counter() - began) * 1000.0
        self._events.publish(
            EventType.TOOL_RESULT,
            ToolEventPayload(
                request_id=request_id,
                capability=definition.name,
                status="completed",
                data={"provider_id": definition.provider_id, "output": output, "duration_ms": duration_ms},
            ),
            provenance=provider_event_provenance,
            session_id=session_id,
            correlation_id=correlation_id,
            causation_id=started.event_id,
        )
        return CapabilityExecutionResult(
            request_id=request_id,
            capability=definition.name,
            provider_id=definition.provider_id,
            output=output,
            provenance=definition.provenance,
            duration_ms=duration_ms,
        )


def _event_provenance(provenance: CapabilityProvenance) -> EventProvenance:
    source_kind = EventSourceKind.DEVICE if provenance.provider_kind == CapabilityProviderKind.DEVICE else EventSourceKind.TOOL
    return EventProvenance(
        source_kind=source_kind,
        source_id=provenance.provider_id,
        device_id=provenance.device_id,
    )


def _validate_schema(value: Any, schema: dict[str, Any], *, where: str) -> None:
    """Validate the small JSON-Schema subset used by PF5 contracts without adding a provider lib."""
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            raise CapabilityValidationError(f"{where} must be an object")
        required = set(schema.get("required", ()))
        missing = sorted(required - value.keys())
        if missing:
            raise CapabilityValidationError(f"{where} missing required fields: {', '.join(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(value.keys() - properties.keys())
            if extras:
                raise CapabilityValidationError(f"{where} contains unsupported fields: {', '.join(extras)}")
        for key, child_schema in properties.items():
            if key in value:
                _validate_schema(value[key], child_schema, where=f"{where}.{key}")
        return
    if expected == "array":
        if not isinstance(value, list):
            raise CapabilityValidationError(f"{where} must be an array")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _validate_schema(item, item_schema, where=f"{where}[{index}]")
        return
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
    }
    expected_type = type_map.get(expected)
    if expected_type is not None and (not isinstance(value, expected_type) or (expected == "integer" and isinstance(value, bool))):
        raise CapabilityValidationError(f"{where} must be {expected}")
