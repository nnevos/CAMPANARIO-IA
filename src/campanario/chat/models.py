from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass(frozen=True, slots=True)
class ChatSession:
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: str = "active"
    title: str | None = None


@dataclass(frozen=True, slots=True)
class Message:
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    created_at: datetime
    model: str | None = None
    status: str = "completed"
