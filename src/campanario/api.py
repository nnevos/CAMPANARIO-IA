import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from campanario.agents.profiles import AgentNotFoundError
from campanario.bootstrap import get_chat_service
from campanario.chat.service import ModelNotConfiguredError, SessionNotFoundError
from campanario.release import ARCHITECTURE_VERSION, RELEASE_ID, UI_VERSION
from campanario.model.protocol import (
    ModelProviderError,
    ModelResponseError,
    ModelTimeoutError,
    ModelUnavailableError,
)

router = APIRouter(prefix="/api")


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
        "title": session.title,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "primary_agent_id": session.primary_agent_id,
        # compatibility for old clients; remove after v1.2 adoption.
        "agent_id": session.primary_agent_id,
    }


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(body: CreateSessionRequest) -> dict[str, object]:
    try:
        requested = body.primary_agent_id or body.agent_id
        return _session_payload(get_chat_service().create_session(body.title, requested))
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Unknown agent") from exc


@router.get("/system")
def system_info() -> dict[str, object]:
    service = get_chat_service()
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
    }


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
        for profile in get_chat_service().list_agents()
    ]


@router.patch("/sessions/{session_id}/primary-speaker")
def set_primary_speaker(session_id: UUID, body: SetPrimarySpeakerRequest) -> dict[str, object]:
    try:
        return _session_payload(get_chat_service().set_primary_agent(session_id, body.agent_id))
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Unknown agent") from exc


@router.patch("/sessions/{session_id}/agent")
def set_session_agent_compat(session_id: UUID, body: SetPrimarySpeakerRequest) -> dict[str, object]:
    """Compatibility endpoint from v1.1; sets priority, not exclusive activation."""
    return set_primary_speaker(session_id, body)


@router.get("/sessions")
def list_sessions() -> list[dict[str, object]]:
    return [_session_payload(session) for session in get_chat_service().list_sessions()]


@router.get("/sessions/{session_id}/messages")
def list_messages(session_id: UUID) -> list[dict[str, object]]:
    try:
        messages = get_chat_service().get_messages(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc

    return [
        {
            "id": str(message.id),
            "session_id": str(message.session_id),
            "role": message.role.value,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "model": message.model,
            "status": message.status,
            "agent_id": message.agent_id,
        }
        for message in messages
    ]


@router.post("/sessions/{session_id}/chat/stream")
def stream_chat(session_id: UUID, body: ChatRequest) -> StreamingResponse:
    service = get_chat_service()

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
