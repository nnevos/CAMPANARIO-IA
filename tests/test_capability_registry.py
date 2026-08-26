from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

import campanario.api as api_module
from campanario.config import Settings
from campanario.main import app
from campanario.composition import build_runtime
from campanario.runtime.capabilities import (
    CallbackCapabilityProvider,
    CapabilityDefinition,
    CapabilityProvenance,
    CapabilityProviderKind,
    CapabilityUnavailableError,
    CapabilityValidationError,
    DeviceCapabilityProvider,
)
from campanario.runtime.devices import DeviceAnnouncement
from campanario.runtime.events import EventType


def definition(*, name: str, provider_id: str, provenance: CapabilityProvenance) -> CapabilityDefinition:
    return CapabilityDefinition(
        name=name,
        description=f"Capability {name}",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
            "additionalProperties": False,
        },
        provider_id=provider_id,
        permissions=("example.read",),
        timeout_seconds=2.0,
        provenance=provenance,
    )


@pytest.mark.asyncio
async def test_registry_executes_by_capability_name_without_caller_knowing_provider(tmp_path) -> None:
    runtime = build_runtime(Settings(), database_url=f"sqlite:///{tmp_path / 'cap.db'}", create_schema=True)
    seen: list[tuple[str, dict]] = []

    async def handler(capability: str, arguments: dict) -> dict:
        seen.append((capability, arguments))
        return {"value": f"result:{arguments['query']}"}

    provider = CallbackCapabilityProvider("provider-a", handler)
    runtime.tools.register_provider(provider)
    runtime.tools.register(
        definition(
            name="web.search",
            provider_id="provider-a",
            provenance=CapabilityProvenance(
                provider_kind=CapabilityProviderKind.MOCK,
                provider_id="provider-a",
            ),
        )
    )

    result = await runtime.tools.execute("web.search", {"query": "campanario"})

    assert result.output == {"value": "result:campanario"}
    assert result.provider_id == "provider-a"
    assert seen == [("web.search", {"query": "campanario"})]
    assert [event.event_type for event in runtime.events.replay()] == [
        EventType.TOOL_REQUESTED,
        EventType.TOOL_STARTED,
        EventType.TOOL_RESULT,
    ]
    assert runtime.events.replay()[-1].provenance.source_id == "provider-a"


@pytest.mark.asyncio
async def test_device_can_provide_capability_and_disconnect_makes_it_unavailable(tmp_path) -> None:
    runtime = build_runtime(Settings(), database_url=f"sqlite:///{tmp_path / 'device-cap.db'}", create_schema=True)
    runtime.devices.connect(
        DeviceAnnouncement(
            device_id="phone-main",
            name="Phone",
            type="mobile",
            capabilities=("gps", "battery"),
        )
    )

    async def remote_handler(capability: str, arguments: dict) -> dict:  # noqa: ARG001
        return {"value": "-23.55,-46.63"}

    provider = DeviceCapabilityProvider(
        device_id="phone-main",
        devices=runtime.devices,
        handler=remote_handler,
        required_device_capability="gps",
    )
    runtime.tools.register_provider(provider)
    runtime.tools.register(
        definition(
            name="location.current",
            provider_id=provider.provider_id,
            provenance=CapabilityProvenance(
                provider_kind=CapabilityProviderKind.DEVICE,
                provider_id=provider.provider_id,
                device_id="phone-main",
            ),
        )
    )

    result = await runtime.tools.execute("location.current", {"query": "current"})
    assert result.output["value"] == "-23.55,-46.63"
    assert result.provenance.device_id == "phone-main"
    tool_events = [event for event in runtime.events.replay() if event.event_type.value.startswith("TOOL_")]
    assert tool_events[-1].provenance.device_id == "phone-main"

    runtime.devices.disconnect("phone-main")
    assert runtime.tools.get("location.current").available is False
    with pytest.raises(CapabilityUnavailableError):
        await runtime.tools.execute("location.current", {"query": "current"})


@pytest.mark.asyncio
async def test_registry_validates_input_schema_before_provider_execution(tmp_path) -> None:
    runtime = build_runtime(Settings(), database_url=f"sqlite:///{tmp_path / 'schema.db'}", create_schema=True)
    called = False

    async def handler(capability: str, arguments: dict) -> dict:  # noqa: ARG001
        nonlocal called
        called = True
        return {"value": "never"}

    runtime.tools.register_provider(CallbackCapabilityProvider("provider-schema", handler))
    runtime.tools.register(
        definition(
            name="files.search",
            provider_id="provider-schema",
            provenance=CapabilityProvenance(
                provider_kind=CapabilityProviderKind.MOCK,
                provider_id="provider-schema",
            ),
        )
    )

    with pytest.raises(CapabilityValidationError):
        await runtime.tools.execute("files.search", {})
    assert called is False


@pytest.mark.asyncio
async def test_capability_timeout_emits_failed_event(tmp_path) -> None:
    from campanario.runtime.capabilities import CapabilityTimeoutError

    runtime = build_runtime(Settings(), database_url=f"sqlite:///{tmp_path / 'timeout.db'}", create_schema=True)

    async def slow_handler(capability: str, arguments: dict) -> dict:  # noqa: ARG001
        await asyncio.sleep(0.05)
        return {"value": "late"}

    provider = CallbackCapabilityProvider("provider-slow", slow_handler)
    runtime.tools.register_provider(provider)
    base = definition(
        name="weather.current",
        provider_id="provider-slow",
        provenance=CapabilityProvenance(
            provider_kind=CapabilityProviderKind.MOCK,
            provider_id="provider-slow",
        ),
    )
    runtime.tools.register(base.model_copy(update={"timeout_seconds": 0.01}))

    with pytest.raises(CapabilityTimeoutError):
        await runtime.tools.execute("weather.current", {"query": "now"})

    assert [event.event_type for event in runtime.events.replay()] == [
        EventType.TOOL_REQUESTED,
        EventType.TOOL_STARTED,
        EventType.TOOL_FAILED,
    ]
    assert runtime.events.replay()[-1].payload["status"] == "timeout"


def test_capability_api_lists_contracts_but_does_not_expose_execute_endpoint(monkeypatch, tmp_path) -> None:
    runtime = build_runtime(Settings(), database_url=f"sqlite:///{tmp_path / 'api-cap.db'}", create_schema=True)
    provider = CallbackCapabilityProvider("provider-api", lambda capability, arguments: {"value": "ok"})
    runtime.tools.register_provider(provider)
    runtime.tools.register(
        definition(
            name="device.status",
            provider_id="provider-api",
            provenance=CapabilityProvenance(
                provider_kind=CapabilityProviderKind.SYSTEM,
                provider_id="provider-api",
            ),
        )
    )
    monkeypatch.setattr(api_module, "get_runtime", lambda: runtime)
    client = TestClient(app)

    response = client.get("/api/v1/capabilities")
    assert response.status_code == 200
    item = response.json()[0]
    assert item["name"] == "device.status"
    assert item["provider_id"] == "provider-api"
    assert item["permissions"] == ["example.read"]
    assert item["available"] is True
    assert client.post("/api/v1/capabilities/device.status/execute", json={}).status_code == 404
