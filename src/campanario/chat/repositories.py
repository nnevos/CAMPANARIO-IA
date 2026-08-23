from typing import Protocol
from uuid import UUID

from campanario.chat.models import ChatSession, Message


class ChatSessionRepository(Protocol):
    def create(self, session: ChatSession) -> ChatSession: ...
    def get(self, session_id: UUID) -> ChatSession | None: ...


class MessageRepository(Protocol):
    def append(self, message: Message) -> Message: ...
    def list_by_session(self, session_id: UUID) -> list[Message]: ...
