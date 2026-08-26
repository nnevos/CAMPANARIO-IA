from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from uuid import UUID

import httpx
import pytest
import uvicorn
import websockets
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import campanario.api as api_module
import campanario.gateway.devices as device_gateway_module
import campanario.gateway.realtime as realtime_module
from campanario.composition import build_runtime
from campanario.config import Settings
from campanario.main import app
from campanario.mobile.proof_client import MobileReadinessClient
from campanario.model.protocol import FakeModelProvider
from campanario.runtime.capabilities import CapabilityUnavailableError
from campanario.runtime.events import EventType


def _runtime(tmp_path):
    runtime = build_runtime(
        Settings(),
        database_url=f"sqlite:///{tmp_path / 'mobile.db'}",
        create_schema=True,
    )
    fake = FakeModelProvider("resposta mobile compartilhada")
    runtime.conversation._model_provider = fake
    runtime.conversation._participation._provider = fake
    runtime.conversation._default_model = "fake"
    runtime.conversation._participation._model = "fake"
    return runtime


def _install(monkeypatch, tmp_path):
    runtime = _runtime(tmp_path)
    monkeypatch.setattr(api_module, "get_runtime", lambda: runtime)
    monkeypatch.setattr(device_gateway_module, "get_runtime", lambda: runtime)
    monkeypatch.setattr(realtime_module, "get_runtime", lambda: runtime)
    return runtime


def _hello(device_id="phone-main"):
    return {
        "schema_version": "1.0",
        "frame_type": "device_hello",
        "device_id": device_id,
        "name": "Telefone de prova",
        "device_type": "mobile-proof",
        "capabilities": ["gps", "network", "screen"],
    }


def _receive_ready(ws):
    while True:
        frame = ws.receive_json()
        if frame["frame_type"] == "ready":
            return frame


def test_mobile_device_bootstrap_pair_auth_and_location_capability(monkeypatch, tmp_path):
    runtime = _install(monkeypatch, tmp_path)
    client = TestClient(app)

    with client.websocket_connect("/ws/v1/devices") as ws:
        ws.send_json(_hello())
        ready = ws.receive_json()
        assert ready["pairing_required"] is True
        assert ready["authenticated"] is False

    paired = client.post("/api/v1/devices/phone-main/pair")
    assert paired.status_code == 200
    credential = paired.json()["credential"]

    with client.websocket_connect(
        "/ws/v1/devices",
        headers={"X-Campanario-Device-Credential": credential},
    ) as ws:
        ws.send_json(_hello())
        ready = ws.receive_json()
        assert ready["pairing_required"] is False
        assert ready["authenticated"] is True
        ws.send_json(
            {
                "schema_version": "1.0",
                "frame_type": "location_update",
                "latitude": -23.55052,
                "longitude": -46.633308,
                "accuracy_meters": 8.0,
            }
        )
        updated = ws.receive_json()
        assert updated["frame_type"] == "capability_updated"
        assert updated["capability"] == "location.current"

        status = runtime.tools.get("location.current")
        assert status is not None and status.available is True
        result = asyncio.run(runtime.tools.execute("location.current", {}))
        assert result.output == {
            "latitude": -23.55052,
            "longitude": -46.633308,
            "accuracy_meters": 8.0,
            "source_device_id": "phone-main",
        }
        assert result.provenance.device_id == "phone-main"

        location_events = [
            item for item in runtime.events.replay() if item.event_type == EventType.LOCATION_UPDATED
        ]
        assert len(location_events) == 1
        assert location_events[0].provenance.device_id == "phone-main"
        assert location_events[0].payload["latitude"] == -23.55052

    assert runtime.tools.get("location.current").available is False
    with pytest.raises(CapabilityUnavailableError):
        asyncio.run(runtime.tools.execute("location.current", {}))


def test_unpaired_mobile_cannot_publish_location(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    client = TestClient(app)
    with client.websocket_connect("/ws/v1/devices") as ws:
        ws.send_json(_hello("unpaired-phone"))
        assert ws.receive_json()["authenticated"] is False
        ws.send_json(
            {
                "schema_version": "1.0",
                "frame_type": "location_update",
                "latitude": 1.0,
                "longitude": 2.0,
            }
        )
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
        assert exc.value.code == 1008


def test_mobile_authenticated_client_uses_same_session_and_reconnects(monkeypatch, tmp_path):
    runtime = _install(monkeypatch, tmp_path)
    pc = TestClient(app)
    mobile = TestClient(app)
    session_id = pc.post("/api/v1/sessions", json={}).json()["id"]

    pc.post(
        f"/api/v1/sessions/{session_id}/turn",
        headers={"X-Campanario-Client-Id": "pc-web"},
        json={"message": "contexto iniciado no pc"},
    )

    with mobile.websocket_connect("/ws/v1/devices") as ws:
        ws.send_json(_hello())
        ws.receive_json()
    credential = mobile.post("/api/v1/devices/phone-main/pair").json()["credential"]
    auth = {
        "X-Campanario-Client-Id": "phone-shell",
        "X-Campanario-Device-Id": "phone-main",
        "X-Campanario-Device-Credential": credential,
    }

    with mobile.websocket_connect(
        f"/ws/v1/events?session_id={session_id}&client_id=phone-shell&device_id=phone-main",
        headers={"X-Campanario-Device-Credential": credential},
    ) as events:
        first_ready = _receive_ready(events)
        response = mobile.post(
            f"/api/v1/sessions/{session_id}/turn",
            headers=auth,
            json={"message": "continuando pelo celular"},
        )
        assert response.status_code == 200
        assert response.json()["client_id"] == "phone-shell"
        assert response.json()["device_id"] == "phone-main"

    latest = runtime.events.latest_sequence
    with mobile.websocket_connect(
        f"/ws/v1/events?session_id={session_id}&client_id=phone-shell&device_id=phone-main&after_sequence={latest}",
        headers={"X-Campanario-Device-Credential": credential},
    ) as events:
        second_ready = _receive_ready(events)

    assert first_ready["session_id"] == second_ready["session_id"] == session_id
    assert first_ready["attachment_id"] != second_ready["attachment_id"]
    assert len(runtime.sessions.list_sessions()) == 1
    history = pc.get(f"/api/v1/sessions/{session_id}/messages").json()
    mobile_user = next(item for item in history if item["content"] == "continuando pelo celular")
    assert mobile_user["client_id"] == "phone-shell"
    assert mobile_user["device_id"] == "phone-main"
    assert any(item["content"] == "contexto iniciado no pc" for item in history)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.mark.asyncio
async def test_mobile_proof_client_over_real_local_http_and_websocket(monkeypatch, tmp_path):
    """PF8 E2E uses real loopback sockets, not only TestClient/mocked transports."""

    runtime = _install(monkeypatch, tmp_path)
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="off")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 5.0
    while not server.started and time.time() < deadline:
        await asyncio.sleep(0.02)
    assert server.started

    proof = MobileReadinessClient(
        base_url=f"http://127.0.0.1:{port}",
        client_id="mobile-proof-e2e",
        device_id="mobile-proof-device",
    )
    try:
        await proof.bootstrap_pair()
        session = await proof.create_session("PF8 real socket")
        session_id = session["id"]

        device_ws, device_ready = await proof.open_device()
        assert device_ready["authenticated"] is True
        try:
            location_ack = await proof.send_location(
                device_ws,
                latitude=-22.9,
                longitude=-43.2,
                accuracy_meters=5.0,
                session_id=session_id,
            )
            assert location_ack["capability"] == "location.current"
            assert runtime.tools.get("location.current").available is True
            assert (await runtime.tools.execute("location.current", {}, session_id=UUID(session_id))).output[
                "source_device_id"
            ] == "mobile-proof-device"

            event_ws = await proof.open_events(session_id)
            try:
                ready = json.loads(await event_ws.recv())
                while ready["frame_type"] != "ready":
                    ready = json.loads(await event_ws.recv())
                assert ready["session_id"] == session_id
                turn = await proof.send_text(session_id, "mensagem enviada pelo cliente mobile real")
                assert turn["device_id"] == "mobile-proof-device"
                observed_types = []
                last_sequence = ready["latest_sequence"]
                while EventType.AGENT_RESPONSE_FINISHED.value not in observed_types:
                    frame = json.loads(await event_ws.recv())
                    if frame["frame_type"] != "event":
                        continue
                    observed_types.append(frame["event"]["event_type"])
                    last_sequence = frame["event"]["sequence"]
                assert EventType.USER_TEXT.value in observed_types
            finally:
                await event_ws.close()

            reconnect = await proof.open_events(session_id, after_sequence=last_sequence)
            try:
                reconnect_ready = json.loads(await reconnect.recv())
                assert reconnect_ready["frame_type"] == "ready"
                assert reconnect_ready["session_id"] == session_id
            finally:
                await reconnect.close()
        finally:
            await device_ws.close()

        history = await proof.messages(session_id)
        user = next(item for item in history if item["content"] == "mensagem enviada pelo cliente mobile real")
        assert user["client_id"] == "mobile-proof-e2e"
        assert user["device_id"] == "mobile-proof-device"
        assert len(runtime.sessions.list_sessions()) == 1
    finally:
        server.should_exit = True
        thread.join(timeout=5.0)
