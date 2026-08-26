from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from campanario.bootstrap import get_runtime
from campanario.gateway.protocol import (
    DeviceCapabilityUpdatedFrame,
    DeviceHelloFrame,
    DeviceLocationUpdateFrame,
    DeviceReadyFrame,
    GatewayPongFrame,
)
from campanario.runtime.devices import DeviceAnnouncement
from campanario.runtime.mobile import install_mobile_location_provider, publish_mobile_location


router = APIRouter(prefix="/ws/v1")


def _authenticate_if_paired(runtime, websocket: WebSocket, device_id: str) -> tuple[bool, bool]:
    """Return (authenticated, pairing_required) without treating device_id as a credential."""

    trust = runtime.trust.status(device_id)
    trusted = bool(trust and trust["trusted"] and not trust["revoked_at"])
    if not trusted:
        return False, True
    credential = websocket.headers.get("x-campanario-device-credential")
    if not credential or not runtime.trust.authenticate(device_id, credential):
        raise PermissionError("device_authentication_failed")
    return True, False


@router.websocket("/devices")
async def device_channel(websocket: WebSocket) -> None:
    """Register one device and, once paired, accept PF8 device capability snapshots.

    First contact may register identity/capabilities so PF6 can pair it. If a trust record already
    exists, reconnect requires the credential. Unpaired channels may ping but cannot provide
    location or any other privileged capability data.
    """

    runtime = get_runtime()
    await websocket.accept()
    device_id: str | None = None
    authenticated = False
    try:
        raw = await websocket.receive_json()
        hello = DeviceHelloFrame.model_validate(raw)
        device = runtime.devices.connect(
            DeviceAnnouncement(
                device_id=hello.device_id,
                name=hello.name,
                type=hello.device_type,
                capabilities=hello.capabilities,
            )
        )
        device_id = device.id
        try:
            authenticated, pairing_required = _authenticate_if_paired(runtime, websocket, device_id)
        except PermissionError:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="device_authentication_failed",
            )
            return

        await websocket.send_json(
            DeviceReadyFrame(
                runtime_id=runtime.state.runtime_id,
                device=device,
                authenticated=authenticated,
                pairing_required=pairing_required,
            ).model_dump(mode="json")
        )

        while True:
            frame = await websocket.receive_json()
            if frame.get("frame_type") == "ping":
                touched = runtime.devices.touch(device_id)
                await websocket.send_json(
                    GatewayPongFrame(device_id=device_id, last_seen=touched.last_seen if touched else None)
                    .model_dump(mode="json")
                )
                continue
            if frame.get("frame_type") == "location_update":
                if not authenticated:
                    await websocket.close(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="device_pairing_required",
                    )
                    return
                update = DeviceLocationUpdateFrame.model_validate(frame)
                device = runtime.devices.get(device_id)
                if device is None or "gps" not in device.capabilities:
                    await websocket.close(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="gps_capability_required",
                    )
                    return
                sample = runtime.mobile.update_location(
                    device_id,
                    latitude=update.latitude,
                    longitude=update.longitude,
                    accuracy_meters=update.accuracy_meters,
                )
                install_mobile_location_provider(runtime, device_id)
                event = publish_mobile_location(runtime, sample, session_id=update.session_id)
                runtime.devices.touch(device_id)
                await websocket.send_json(
                    DeviceCapabilityUpdatedFrame(
                        device_id=device_id,
                        event_sequence=event.sequence,
                    ).model_dump(mode="json")
                )
                continue
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="unsupported_device_frame",
            )
            return
    except ValidationError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid_device_frame")
    except WebSocketDisconnect:
        pass
    finally:
        if device_id is not None:
            runtime.mobile.clear_device(device_id)
            runtime.devices.disconnect(device_id)
