from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from campanario.bootstrap import get_runtime
from campanario.gateway.protocol import GatewayEventFrame, GatewayReadyFrame
from campanario.runtime.clients import ClientIdentity


router = APIRouter(prefix="/ws/v1")


def _session_exists(runtime, session_id: UUID) -> bool:
    return any(item.id == session_id for item in runtime.sessions.list_sessions())


def _resolve_ws_client(runtime, websocket: WebSocket, client_id: str | None, device_id: str | None) -> ClientIdentity:
    resolved_client_id = (client_id or f"ws-{uuid4()}").strip()
    if not resolved_client_id or len(resolved_client_id) > 128:
        raise ValueError("invalid_client_id")
    resolved_device_id = device_id.strip() if device_id else None
    if resolved_device_id is not None:
        credential = websocket.headers.get("x-campanario-device-credential")
        if not credential or not runtime.trust.authenticate(resolved_device_id, credential):
            raise PermissionError("device_authentication_failed")
    return ClientIdentity(client_id=resolved_client_id, device_id=resolved_device_id)


@router.websocket("/events")
async def runtime_events(
    websocket: WebSocket,
    session_id: UUID | None = Query(default=None),
    after_sequence: int = Query(default=0, ge=0),
    client_id: str | None = Query(default=None),
    device_id: str | None = Query(default=None),
) -> None:
    """Observe the shared RuntimeEventBus from one client attachment.

    PF7 makes client identity explicit without making sessions client-owned. A session-specific
    observer is attached process-locally while its WebSocket is alive; reconnecting can use the
    same client_id and session_id but receives a new attachment id. A device_id is optional and,
    when supplied, must authenticate through the PF6 trust boundary.
    """
    runtime = get_runtime()
    if session_id is not None and not _session_exists(runtime, session_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="session_not_found")
        return
    try:
        identity = _resolve_ws_client(runtime, websocket, client_id, device_id)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid_client_id")
        return
    except PermissionError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="device_authentication_failed")
        return

    await websocket.accept()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    attachment = runtime.clients.attach(session_id, identity) if session_id is not None else None

    def on_event(event) -> None:
        if session_id is not None and event.session_id != session_id:
            return
        loop.call_soon_threadsafe(queue.put_nowait, event)

    # Subscribe before replay to avoid a gap between reading journal and observing live events.
    subscription_id = runtime.events.subscribe(on_event)
    try:
        replay = runtime.events.replay(after_sequence=after_sequence, session_id=session_id)
        replayed_through = after_sequence
        for event in replay:
            await websocket.send_json(GatewayEventFrame(event=event).model_dump(mode="json"))
            replayed_through = max(replayed_through, event.sequence)

        await websocket.send_json(
            GatewayReadyFrame(
                runtime_id=runtime.state.runtime_id,
                session_id=session_id,
                latest_sequence=runtime.events.latest_sequence,
                replayed_through_sequence=replayed_through,
                runtime_status=runtime.state.status,
                client_id=identity.client_id,
                device_id=identity.device_id,
                attachment_id=None if attachment is None else attachment.attachment_id,
            ).model_dump(mode="json")
        )

        while True:
            event = await queue.get()
            if event.sequence <= replayed_through:
                continue
            if attachment is not None:
                runtime.clients.touch(attachment.attachment_id)
            await websocket.send_json(GatewayEventFrame(event=event).model_dump(mode="json"))
            replayed_through = event.sequence
    except WebSocketDisconnect:
        pass
    finally:
        runtime.events.unsubscribe(subscription_id)
        if attachment is not None:
            runtime.clients.detach(attachment.attachment_id)
