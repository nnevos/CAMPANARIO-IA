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
    primary_agent_id: str = "morgana"

    @property
    def agent_id(self) -> str:
        """v1.1 compatibility alias; means primary speaker, not exclusive agent."""
        return self.primary_agent_id


@dataclass(frozen=True, slots=True)
class Message:
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    created_at: datetime
    model: str | None = None
    status: str = "completed"
    agent_id: str | None = None


@dataclass(frozen=True, slots=True)
class ContextSummary:
    session_id: UUID
    content: str
    through_message_id: UUID
    updated_at: datetime
