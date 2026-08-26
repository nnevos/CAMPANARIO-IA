import json
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from campanario.agents.profiles import AgentNotFoundError
from campanario.bootstrap import get_runtime
from campanario.chat.service import ModelNotConfiguredError, SessionNotFoundError
from campanario.runtime.clients import ClientIdentity
from campanario.release import ARCHITECTURE_VERSION, RELEASE_ID, UI_VERSION

from campanario.model.protocol import (
    ModelProviderError,
    ModelResponseError,
    ModelTimeoutError,
    ModelUnavailableError,
)

router = APIRouter(prefix="/api")
v1_router = APIRouter(prefix="/api/v1")


class CreateSessionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    primary_agent_id: str | None = Field(default=None, max_length=64)
    # v1.1 compatibility: interpreted as primary-speaker preference, never exclusivity.
    agent_id: str | None = Field(default=None, max_length=64)


class SetPrimarySpeakerRequest(BaseModel):
    agent_id: str = Field(min_length=1, max_length=64)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=100_000)

    @field_validator("message")
    @classmethod
    def reject_blank_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message must contain non-whitespace characters")
        return cleaned


def _session_payload(session) -> dict[str, object]:
    return {
        "id": str(session.id),
        "episode_id": str(session.id),  # PF7: current technical episode is the durable chat session
        "title": session.title,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "primary_agent_id": session.primary_agent_id,
        # compatibility for old clients; remove after v1.2 adoption.
        "agent_id": session.primary_agent_id,
    }


def _device_payload(device) -> dict[str, object]:
    return {
        "id": device.id,
        "name": device.name,
        "type": device.type,
        "capabilities": list(device.capabilities),
        "connection_state": device.connection_state.value,
        "created_at": device.created_at.isoformat(),
        "updated_at": device.updated_at.isoformat(),
        "last_seen": device.last_seen.isoformat(),
    }


def _capability_payload(status) -> dict[str, object]:
    definition = status.definition
    return {
        "name": definition.name,
        "description": definition.description,
        "input_schema": definition.input_schema,
        "output_schema": definition.output_schema,
        "provider_id": definition.provider_id,
        "permissions": list(definition.permissions),
        "timeout_seconds": definition.timeout_seconds,
        "provenance": definition.provenance.model_dump(mode="json"),
        "available": status.available,
    }


class CorrectMemoryRequest(BaseModel):
    value: str = Field(min_length=1, max_length=10_000)
    reason: str = Field(default="user/admin correction", max_length=1000)


class ForgetMemoryRequest(BaseModel):
    reason: str = Field(default="forgotten by request", max_length=1000)


def _memory_payload(memory) -> dict[str, object]:
    return {
        "id": str(memory.id),
        "kind": memory.kind.value,
        "subject": memory.subject,
        "key": memory.key,
        "value": memory.value,
        "confidence": memory.confidence,
        "source": memory.source.value,
        "status": memory.status.value,
        "evidence": memory.evidence,
        "source_session_id": None if memory.source_session_id is None else str(memory.source_session_id),
        "source_message_id": None if memory.source_message_id is None else str(memory.source_message_id),
        "source_agent_id": memory.source_agent_id,
        "supersedes_id": None if memory.supersedes_id is None else str(memory.supersedes_id),
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
        "last_confirmed_at": memory.last_confirmed_at.isoformat(),
        "last_recalled_at": None if memory.last_recalled_at is None else memory.last_recalled_at.isoformat(),
        "recall_count": memory.recall_count,
    }


@v1_router.get("/memory")
def list_experience_memory_v1(
    include_inactive: bool = Query(default=False),
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[dict[str, object]]:
    return [_memory_payload(item) for item in get_runtime().experience.list_memories(include_inactive=include_inactive, limit=limit)]


@v1_router.patch("/memory/{memory_id}")
def correct_experience_memory_v1(memory_id: UUID, body: CorrectMemoryRequest) -> dict[str, object]:
    try:
        return _memory_payload(get_runtime().experience.correct(memory_id, body.value, reason=body.reason))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Memory not found") from exc


@v1_router.post("/memory/{memory_id}/forget")
def forget_experience_memory_v1(memory_id: UUID, body: ForgetMemoryRequest | None = None) -> dict[str, object]:
    try:
        reason = "forgotten by request" if body is None else body.reason
        return _memory_payload(get_runtime().experience.forget(memory_id, reason=reason))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Memory not found") from exc


@v1_router.get("/capabilities")
def list_capabilities_v1(available_only: bool = Query(default=False)) -> list[dict[str, object]]:
    return [_capability_payload(item) for item in get_runtime().tools.list(available_only=available_only)]


@v1_router.get("/capabilities/{capability_name}")
def get_capability_v1(capability_name: str) -> dict[str, object]:
    status_item = get_runtime().tools.get(capability_name)
    if status_item is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    return _capability_payload(status_item)


@v1_router.get("/devices")
def list_devices_v1(
    capability: str | None = Query(default=None, max_length=64),
    connected_only: bool = Query(default=False),
) -> list[dict[str, object]]:
    registry = get_runtime().devices
    if capability:
        devices = registry.find_capable(capability, connected_only=connected_only)
    else:
        devices = registry.list()
        if connected_only:
            devices = [item for item in devices if item.connection_state.value == "connected"]
    return [_device_payload(device) for device in devices]


@v1_router.get("/devices/{device_id}")
def get_device_v1(device_id: str) -> dict[str, object]:
    device = get_runtime().devices.get(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    payload = _device_payload(device)
    trust = get_runtime().trust.status(device_id)
    payload["trusted"] = bool(trust and trust["trusted"])
    payload["revoked_at"] = trust["revoked_at"].isoformat() if trust and trust["revoked_at"] else None
    return payload


@v1_router.post("/devices/{device_id}/pair")
def pair_device_v1(device_id: str) -> dict[str, object]:
    try:
        token = get_runtime().trust.pair(device_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Device not found") from exc
    return {"device_id": device_id, "credential": token, "warning": "credential is shown once; store it securely"}


@v1_router.post("/devices/{device_id}/revoke")
def revoke_device_v1(device_id: str) -> dict[str, object]:
    try:
        get_runtime().trust.revoke(device_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Device not found") from exc
    return {"device_id": device_id, "revoked": True}


@v1_router.get("/security/audit")
def security_audit_v1(limit: int = Query(default=100, ge=1, le=1000)) -> list[dict[str, object]]:
    rows = get_runtime().trust.audit(limit=limit)
    return [{**row, "created_at": row["created_at"].isoformat()} for row in rows]


def _resolve_client_identity(
    *,
    client_id: str | None,
    device_id: str | None,
    device_credential: str | None,
) -> ClientIdentity | None:
    client_id = client_id.strip() if client_id else None
    device_id = device_id.strip() if device_id else None
    if device_id is not None:
        if client_id is None or not device_credential:
            raise HTTPException(status_code=401, detail="device authentication required")
        if not get_runtime().trust.authenticate(device_id, device_credential):
            raise HTTPException(status_code=401, detail="invalid device credential")
    if client_id is None:
        return None
    return ClientIdentity(client_id=client_id, device_id=device_id)


@v1_router.post("/sessions", status_code=status.HTTP_201_CREATED)
@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(body: CreateSessionRequest) -> dict[str, object]:
    try:
        requested = body.primary_agent_id or body.agent_id
        return _session_payload(get_runtime().conversation.create_session(body.title, requested))
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Unknown agent") from exc


@v1_router.get("/runtime")
@v1_router.get("/system")
@router.get("/system")
def system_info() -> dict[str, object]:
    runtime = get_runtime()
    service = runtime.conversation
    participants = [profile.id for profile in service.list_agents()]
    return {
        "name": "Campanario",
        "kind": "personal_ai_system",
        "default_primary_agent_id": service.default_primary_agent_id,
        "default_agent_id": service.default_primary_agent_id,  # compatibility
        "model": service.model_name,
        "participants": participants,
        "agents": participants,
        "participation_mode": "persistent_participants",
        "release_id": RELEASE_ID,
        "ui_version": UI_VERSION,
        "architecture_version": ARCHITECTURE_VERSION,
        "runtime_id": str(runtime.state.runtime_id),
        "runtime_status": runtime.state.status,
    }


@v1_router.get("/runtime/telemetry")
def runtime_telemetry_v1(limit: int = Query(default=200, ge=1, le=2000)) -> list[dict[str, object]]:
    points = get_runtime().telemetry.snapshot()[-limit:]
    return [
        {
            "name": point.name,
            "occurred_at": point.occurred_at.isoformat(),
            "runtime_id": str(point.runtime_id),
            "correlation_id": None if point.correlation_id is None else str(point.correlation_id),
            "session_id": None if point.session_id is None else str(point.session_id),
            "agent_id": point.agent_id,
            "client_id": point.client_id,
            "device_id": point.device_id,
            "attributes": dict(point.attributes),
        }
        for point in points
    ]


@v1_router.get("/agents")
@router.get("/agents")
def list_agents() -> list[dict[str, object]]:
    return [
        {
            "id": profile.id,
            "name": profile.name,
            "summary": profile.summary,
            "is_default": profile.is_default,
            "presence": "listening",
        }
        for profile in get_runtime().conversation.list_agents()
    ]


@v1_router.patch("/sessions/{session_id}/primary-speaker")
@router.patch("/sessions/{session_id}/primary-speaker")
def set_primary_speaker(session_id: UUID, body: SetPrimarySpeakerRequest) -> dict[str, object]:
    try:
        return _session_payload(get_runtime().conversation.set_primary_agent(session_id, body.agent_id))
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Unknown agent") from exc


@router.patch("/sessions/{session_id}/agent")
def set_session_agent_compat(session_id: UUID, body: SetPrimarySpeakerRequest) -> dict[str, object]:
    """Compatibility endpoint from v1.1; sets priority, not exclusive activation."""
    return set_primary_speaker(session_id, body)


@v1_router.get("/sessions")
@router.get("/sessions")
def list_sessions() -> list[dict[str, object]]:
    return [_session_payload(session) for session in get_runtime().conversation.list_sessions()]


@v1_router.get("/sessions/{session_id}/clients")
def list_session_clients_v1(session_id: UUID) -> list[dict[str, object]]:
    if not any(item.id == session_id for item in get_runtime().sessions.list_sessions()):
        raise HTTPException(status_code=404, detail="Session not found")
    return [item.model_dump(mode="json") for item in get_runtime().clients.list(session_id=session_id)]


@v1_router.get("/sessions/{session_id}/calls")
def list_session_calls_v1(session_id: UUID) -> list[dict[str, object]]:
    runtime = get_runtime()
    if not any(item.id == session_id for item in runtime.sessions.list_sessions()):
        raise HTTPException(status_code=404, detail="Session not found")
    return [item.model_dump(mode="json") for item in runtime.calls.list(session_id=session_id)]


@v1_router.get("/sessions/{session_id}/messages")
@router.get("/sessions/{session_id}/messages")
def list_messages(session_id: UUID) -> list[dict[str, object]]:
    try:
        messages = get_runtime().conversation.get_messages(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc

    return [
        {
            "id": str(message.id),
            "session_id": str(message.session_id),
            "episode_id": str(message.session_id),
            "role": message.role.value,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "model": message.model,
            "status": message.status,
            "agent_id": message.agent_id,
            "client_id": message.client_id,
            "device_id": message.device_id,
        }
        for message in messages
    ]


@router.post("/sessions/{session_id}/chat/stream")
def stream_chat(session_id: UUID, body: ChatRequest) -> StreamingResponse:
    service = get_runtime().conversation

    async def events():
        try:
            async for event in service.stream_turn(session_id, body.message):
                payload = {
                    "type": event.type,
                    "agent_id": event.agent_id,
                }
                if event.text:
                    payload["text"] = event.text
                if event.reason:
                    payload["reason"] = event.reason
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            yield 'data: {"type":"done"}\n\n'
        except SessionNotFoundError:
            payload = json.dumps({"type": "error", "error": "session_not_found"})
            yield f"data: {payload}\n\n"
        except ModelNotConfiguredError as exc:
            payload = json.dumps({"type": "error", "error": str(exc)}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        except ModelTimeoutError:
            payload = json.dumps({'type': 'error', 'error': 'model_timeout'})
            yield f"data: {payload}\n\n"
        except ModelUnavailableError:
            payload = json.dumps({'type': 'error', 'error': 'model_unavailable'})
            yield f"data: {payload}\n\n"
        except ModelResponseError:
            payload = json.dumps({'type': 'error', 'error': 'model_response_error'})
            yield f"data: {payload}\n\n"
        except ModelProviderError:
            payload = json.dumps({'type': 'error', 'error': 'model_provider_error'})
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@v1_router.post("/sessions/{session_id}/turn")
async def submit_turn_v1(
    session_id: UUID,
    body: ChatRequest,
    x_campanario_client_id: str | None = Header(default=None, alias="X-Campanario-Client-Id"),
    x_campanario_device_id: str | None = Header(default=None, alias="X-Campanario-Device-Id"),
    x_campanario_device_credential: str | None = Header(default=None, alias="X-Campanario-Device-Credential"),
):
    """Run one conversation turn while realtime clients observe PF2 events over /ws/v1/events."""
    from campanario.gateway.protocol import TurnCompletedResponse

    runtime = get_runtime()
    client = _resolve_client_identity(
        client_id=x_campanario_client_id,
        device_id=x_campanario_device_id,
        device_credential=x_campanario_device_credential,
    )
    speakers: list[str] = []
    try:
        async for event in runtime.conversation.stream_turn(session_id, body.message, client=client):
            if event.type == "speaker_start" and event.agent_id and event.agent_id not in speakers:
                speakers.append(event.agent_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    except ModelNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ModelTimeoutError as exc:
        raise HTTPException(status_code=504, detail="model_timeout") from exc
    except ModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail="model_unavailable") from exc
    except ModelResponseError as exc:
        raise HTTPException(status_code=502, detail="model_response_error") from exc
    except ModelProviderError as exc:
        raise HTTPException(status_code=502, detail="model_provider_error") from exc

    return TurnCompletedResponse(
        session_id=session_id,
        speakers=tuple(speakers),
        event_sequence=runtime.events.latest_sequence,
        client_id=None if client is None else client.client_id,
        device_id=None if client is None else client.device_id,
    ).model_dump(mode="json")
