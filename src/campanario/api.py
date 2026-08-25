import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from campanario.bootstrap import get_chat_service
from campanario.chat.service import ModelNotConfiguredError, SessionNotFoundError
from campanario.model.protocol import (
    ModelProviderError,
    ModelResponseError,
    ModelTimeoutError,
    ModelUnavailableError,
)

router = APIRouter(prefix="/api")


class CreateSessionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)


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
    }


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(body: CreateSessionRequest) -> dict[str, object]:
    return _session_payload(get_chat_service().create_session(body.title))


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
        }
        for message in messages
    ]


@router.post("/sessions/{session_id}/chat/stream")
def stream_chat(session_id: UUID, body: ChatRequest) -> StreamingResponse:
    service = get_chat_service()

    async def events():
        try:
            async for text in service.stream_reply(session_id, body.message):
                payload = json.dumps({"type": "token", "text": text}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            yield 'data: {"type":"done"}\n\n'
        except SessionNotFoundError:
            payload = json.dumps({"type": "error", "error": "session_not_found"})
            yield f"data: {payload}\n\n"
        except ModelNotConfiguredError as exc:
            payload = json.dumps({"type": "error", "error": str(exc)}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        except ModelTimeoutError:
            payload = json.dumps({"type": "error", "error": "model_timeout"})
            yield f"data: {payload}\n\n"
        except ModelUnavailableError:
            payload = json.dumps({"type": "error", "error": "model_unavailable"})
            yield f"data: {payload}\n\n"
        except ModelResponseError:
            payload = json.dumps({"type": "error", "error": "model_response_error"})
            yield f"data: {payload}\n\n"
        except ModelProviderError:
            payload = json.dumps({"type": "error", "error": "model_provider_error"})
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
