from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from campanario.agents.context import apply_agent_profile
from campanario.agents.participation import ParticipationArbiter, participation_context
from campanario.agents.profiles import AgentProfile, AgentRegistry, default_agent_registry
from campanario.agents.router import AgentRouter
from campanario.chat.context import ContextManager
from campanario.chat.models import ChatSession, Message, MessageRole
from campanario.chat.repositories import ChatSessionRepository, MessageRepository
from campanario.model.protocol import ModelMessage, ModelProvider, ModelRequest


class SessionNotFoundError(LookupError):
    pass


class ModelNotConfiguredError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AgentStreamEvent:
    type: str
    agent_id: str
    text: str = ""
    reason: str | None = None


class ChatService:
    def __init__(
        self,
        sessions: ChatSessionRepository,
        messages: MessageRepository,
        model_provider: ModelProvider,
        context_manager: ContextManager,
        default_model: str,
        agent_registry: AgentRegistry | None = None,
        participation_provider: ModelProvider | None = None,
    ) -> None:
        self._sessions = sessions
        self._messages = messages
        self._model_provider = model_provider
        self._context_manager = context_manager
        self._default_model = default_model
        self._agents = agent_registry or default_agent_registry()
        self._agent_router = AgentRouter(self._agents)
        self._participation = ParticipationArbiter(
            self._agents,
            participation_provider,
            default_model,
        )

    def create_session(self, title: str | None = None, agent_id: str | None = None) -> ChatSession:
        now = datetime.now(UTC)
        profile = self._agents.get(agent_id)
        session = ChatSession(
            id=uuid4(),
            title=title,
            created_at=now,
            updated_at=now,
            primary_agent_id=profile.id,
        )
        return self._sessions.create(session)

    def list_sessions(self) -> list[ChatSession]:
        return self._sessions.list()

    def list_agents(self) -> tuple[AgentProfile, ...]:
        return self._agents.list()

    @property
    def default_agent_id(self) -> str:
        return self._agents.default_id

    @property
    def default_primary_agent_id(self) -> str:
        return self._agents.default_id

    @property
    def model_name(self) -> str:
        return self._default_model

    def set_primary_agent(self, session_id: UUID, agent_id: str) -> ChatSession:
        profile = self._agents.get(agent_id)
        updated = self._set_primary(session_id, profile.id)
        if updated is None:
            raise SessionNotFoundError(str(session_id))
        return updated

    # Compatibility alias for v1.1 API callers; conceptually this sets priority, not exclusivity.
    def set_session_agent(self, session_id: UUID, agent_id: str) -> ChatSession:
        return self.set_primary_agent(session_id, agent_id)


    def _set_primary(self, session_id: UUID, agent_id: str) -> ChatSession | None:
        setter = getattr(self._sessions, "set_primary_agent", None)
        if setter is not None:
            return setter(session_id, agent_id)
        legacy = getattr(self._sessions, "set_agent", None)
        if legacy is not None:
            return legacy(session_id, agent_id)
        raise AttributeError("session repository must implement set_primary_agent")

    def get_messages(self, session_id: UUID) -> list[Message]:
        if self._sessions.get(session_id) is None:
            raise SessionNotFoundError(str(session_id))
        return self._messages.list_by_session(session_id)

    async def _run_agent(
        self,
        *,
        session_id: UUID,
        profile: AgentProfile,
        history: list[Message],
        extra_system_note: str | None,
        reason: str,
    ) -> AsyncIterator[AgentStreamEvent]:
        base_context = await self._context_manager.build(history)
        context = apply_agent_profile(base_context, profile, history)
        if extra_system_note:
            context = self._append_system_note(context, extra_system_note)
        request = ModelRequest(model=self._default_model, messages=context)

        yield AgentStreamEvent("speaker_start", profile.id, reason=reason)
        parts: list[str] = []
        async for chunk in self._model_provider.stream(request):
            if chunk.text:
                parts.append(chunk.text)
                yield AgentStreamEvent("token", profile.id, text=chunk.text, reason=reason)

        assistant_text = "".join(parts)
        assistant_message = Message(
            id=uuid4(),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=assistant_text,
            created_at=datetime.now(UTC),
            model=self._default_model,
            agent_id=profile.id,
        )
        self._messages.append(assistant_message)
        yield AgentStreamEvent("speaker_done", profile.id, reason=reason)

    async def stream_turn(self, session_id: UUID, text: str) -> AsyncIterator[AgentStreamEvent]:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(str(session_id))
        if not self._default_model.strip():
            raise ModelNotConfiguredError(
                "CAMPANARIO_MODEL_NAME is empty. Configure a local model first."
            )

        resolution = self._agent_router.resolve(text, session.primary_agent_id)
        primary = resolution.profile
        if resolution.persist_primary and primary.id != session.primary_agent_id:
            updated = self._set_primary(session_id, primary.id)
            if updated is not None:
                session = updated

        self._messages.append(
            Message(
                id=uuid4(),
                session_id=session_id,
                role=MessageRole.USER,
                content=text,
                created_at=datetime.now(UTC),
            )
        )
        history_before_primary = self._messages.list_by_session(session_id)

        primary_parts: list[str] = []
        async for event in self._run_agent(
            session_id=session_id,
            profile=primary,
            history=history_before_primary,
            extra_system_note=None,
            reason=resolution.source,
        ):
            if event.type == "token":
                primary_parts.append(event.text)
            yield event
        primary_text = "".join(primary_parts)

        decision = await self._participation.decide(
            user_text=text,
            primary=primary,
            primary_text=primary_text,
            history=history_before_primary,
        )
        if not decision.join:
            return

        secondary = self._participation.secondary_for(primary)
        if secondary is None:
            return
        shared_history = self._messages.list_by_session(session_id)
        note = participation_context(primary, secondary, primary_text)
        async for event in self._run_agent(
            session_id=session_id,
            profile=secondary,
            history=shared_history,
            extra_system_note=note,
            reason=decision.reason,
        ):
            yield event

    async def stream_reply(self, session_id: UUID, text: str) -> AsyncIterator[str]:
        """Compatibility text stream.

        New UI/API consumers should use stream_turn so speaker boundaries are preserved. This
        method flattens token events only and remains for E2E/tests that exercise one-speaker turns.
        """
        async for event in self.stream_turn(session_id, text):
            if event.type == "token":
                yield event.text

    @staticmethod
    def _append_system_note(
        context: tuple[ModelMessage, ...],
        note: str,
    ) -> tuple[ModelMessage, ...]:
        messages = list(context)
        if messages and messages[0].role == MessageRole.SYSTEM:
            messages[0] = ModelMessage(
                role=MessageRole.SYSTEM,
                content=f"{messages[0].content.rstrip()}\n\n{note.strip()}\n",
            )
        else:
            messages.insert(0, ModelMessage(role=MessageRole.SYSTEM, content=note.strip()))
        return tuple(messages)

