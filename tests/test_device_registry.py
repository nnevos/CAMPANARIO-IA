from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

import campanario.gateway.devices as device_gateway_module
from campanario.composition import build_runtime
from campanario.config import Settings
from campanario.main import app
from campanario.runtime.devices import DeviceAnnouncement, DeviceConnectionState
from campanario.runtime.events import EventType


def test_device_registry_persists_identity_capabilities_and_reconnect(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'devices.db'}"
    runtime = build_runtime(Settings(), database_url=database_url, create_schema=True)

    first = runtime.devices.connect(
        DeviceAnnouncement(
            device_id="phone-main",
            name="Meu celular",
            type="mobile",
            capabilities=("gps", "microphone", "speaker", "gps"),
        )
    )
    assert first.connection_state == DeviceConnectionState.CONNECTED
    assert first.capabilities == ("gps", "microphone", "speaker")
    assert [item.id for item in runtime.devices.find_capable("GPS")] == ["phone-main"]

    disconnected = runtime.devices.disconnect("phone-main")
    assert disconnected is not None
    assert disconnected.connection_state == DeviceConnectionState.DISCONNECTED
    created_at = disconnected.created_at
    runtime.stop()

    restarted = build_runtime(Settings(), database_url=database_url, create_schema=True)
    persisted = restarted.devices.get("phone-main")
    assert persisted is not None
    assert persisted.created_at == created_at
    assert persisted.connection_state == DeviceConnectionState.DISCONNECTED
    assert persisted.capabilities == ("gps", "microphone", "speaker")

    reconnected = restarted.devices.connect(
        DeviceAnnouncement(
            device_id="phone-main",
            name="Meu celular",
            type="mobile",
            capabilities=("gps", "microphone", "speaker", "battery"),
        )
    )
    assert reconnected.created_at == created_at
    assert reconnected.connection_state == DeviceConnectionState.CONNECTED
    assert len(restarted.devices.list()) == 1
    assert "battery" in reconnected.capabilities


def test_device_registry_emits_ordered_events_with_device_provenance(tmp_path) -> None:
    runtime = build_runtime(
        Settings(), database_url=f"sqlite:///{tmp_path / 'events.db'}", create_schema=True
    )
    runtime.devices.connect(
        DeviceAnnouncement(
            device_id="headset-1",
            name="Headset",
            type="headset",
            capabilities=("microphone", "speaker"),
        )
    )
    runtime.devices.touch("headset-1")
    runtime.devices.disconnect("headset-1")

    events = runtime.events.replay()
    assert [event.event_type for event in events] == [
        EventType.DEVICE_CONNECTED,
        EventType.DEVICE_STATE_CHANGED,
        EventType.DEVICE_DISCONNECTED,
    ]
    assert [event.sequence for event in events] == sorted(event.sequence for event in events)
    assert all(event.provenance.device_id == "headset-1" for event in events)
    assert all(event.provenance.source_id == "headset-1" for event in events)
    assert events[0].payload["capabilities"] == ["microphone", "speaker"]


def test_device_websocket_connect_disconnect_reconnect_preserves_registry_identity(monkeypatch, tmp_path) -> None:
    runtime = build_runtime(
        Settings(), database_url=f"sqlite:///{tmp_path / 'gateway.db'}", create_schema=True
    )
    monkeypatch.setattr(device_gateway_module, "get_runtime", lambda: runtime)
    client = TestClient(app)
    hello = {
        "schema_version": "1.0",
        "frame_type": "device_hello",
        "device_id": "test-remote",
        "name": "Cliente de teste",
        "device_type": "test",
        "capabilities": ["screen", "gps"],
    }

    with client.websocket_connect("/ws/v1/devices") as ws:
        ws.send_json(hello)
        ready = ws.receive_json()
        assert ready["frame_type"] == "device_ready"
        assert ready["runtime_id"] == str(runtime.state.runtime_id)
        assert ready["device"]["id"] == "test-remote"
        assert ready["device"]["connection_state"] == "connected"
        first_created_at = ready["device"]["created_at"]
        ws.send_json({"frame_type": "ping"})
        assert ws.receive_json()["frame_type"] == "pong"

    assert runtime.devices.get("test-remote").connection_state == DeviceConnectionState.DISCONNECTED

    with client.websocket_connect("/ws/v1/devices") as ws:
        ws.send_json(hello)
        ready = ws.receive_json()
        assert ready["device"]["created_at"] == first_created_at
        assert ready["device"]["capabilities"] == ["gps", "screen"]

    assert len([item for item in runtime.devices.list() if item.id == "test-remote"]) == 1


def test_device_api_discovers_by_capability_without_platform_hardcoding(monkeypatch, tmp_path) -> None:
    import campanario.api as api_module

    runtime = build_runtime(
        Settings(), database_url=f"sqlite:///{tmp_path / 'api.db'}", create_schema=True
    )
    runtime.devices.connect(
        DeviceAnnouncement(
            device_id="phone-a",
            name="Phone A",
            type="mobile",
            capabilities=("gps", "battery"),
        )
    )
    runtime.devices.connect(
        DeviceAnnouncement(
            device_id="desktop-a",
            name="Desktop A",
            type="desktop",
            capabilities=("screen", "keyboard"),
        )
    )
    monkeypatch.setattr(api_module, "get_runtime", lambda: runtime)
    client = TestClient(app)

    response = client.get("/api/v1/devices?capability=gps&connected_only=true")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["phone-a"]
    assert response.json()[0]["type"] == "mobile"

    detail = client.get("/api/v1/devices/desktop-a")
    assert detail.status_code == 200
    assert detail.json()["capabilities"] == ["keyboard", "screen"]


def test_device_id_is_registry_identity_not_trust_credential(tmp_path) -> None:
    runtime = build_runtime(
        Settings(), database_url=f"sqlite:///{tmp_path / 'trust.db'}", create_schema=True
    )
    device = runtime.devices.connect(
        DeviceAnnouncement(device_id="untrusted-id", name="Unknown", type="test", capabilities=("gps",))
    )
    dumped = device.model_dump()
    assert "trusted" not in dumped
    assert "permissions" not in dumped
