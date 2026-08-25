from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

from campanario.chat.context import ContextManager
from campanario.chat.models import ChatSession, Message, MessageRole
from campanario.chat.repositories import ChatSessionRepository, MessageRepository
from campanario.model.protocol import ModelProvider, ModelRequest


class SessionNotFoundError(LookupError):
    pass


class ModelNotConfiguredError(RuntimeError):
    pass


class ChatService:
    def __init__(
        self,
        sessions: ChatSessionRepository,
        messages: MessageRepository,
        model_provider: ModelProvider,
        context_manager: ContextManager,
        default_model: str,
    ) -> None:
        self._sessions = sessions
        self._messages = messages
        self._model_provider = model_provider
        self._context_manager = context_manager
        self._default_model = default_model

    def create_session(self, title: str | None = None) -> ChatSession:
        now = datetime.now(UTC)
        session = ChatSession(
            id=uuid4(),
            title=title,
            created_at=now,
            updated_at=now,
        )
        return self._sessions.create(session)

    def list_sessions(self) -> list[ChatSession]:
        return self._sessions.list()

    def get_messages(self, session_id: UUID) -> list[Message]:
        if self._sessions.get(session_id) is None:
            raise SessionNotFoundError(str(session_id))
        return self._messages.list_by_session(session_id)

    async def stream_reply(self, session_id: UUID, text: str) -> AsyncIterator[str]:
        if self._sessions.get(session_id) is None:
            raise SessionNotFoundError(str(session_id))
        if not self._default_model.strip():
            raise ModelNotConfiguredError(
                "CAMPANARIO_MODEL_NAME is empty. Configure a local model first."
            )

        user_message = Message(
            id=uuid4(),
            session_id=session_id,
            role=MessageRole.USER,
            content=text,
            created_at=datetime.now(UTC),
        )
        self._messages.append(user_message)

        history = self._messages.list_by_session(session_id)
        request = ModelRequest(
            model=self._default_model,
            messages=await self._context_manager.build(history),
        )

        parts: list[str] = []
        async for chunk in self._model_provider.stream(request):
            if chunk.text:
                parts.append(chunk.text)
                yield chunk.text

        assistant_text = "".join(parts)
        assistant_message = Message(
            id=uuid4(),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=assistant_text,
            created_at=datetime.now(UTC),
            model=self._default_model,
        )
        self._messages.append(assistant_message)
