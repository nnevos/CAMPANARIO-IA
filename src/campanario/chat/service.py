from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from campanario.agents.context import apply_agent_profile
from campanario.agents.participation import (
    ParticipationArbiter,
    independent_group_participation_context,
    participation_context,
)
from campanario.agents.output import (
    extract_arithmetic_correction_anchor, extract_own_labeled_segment, normalize_own_speaker_prefix,
    speaker_label_violations, speaker_repair_note,
)
from campanario.agents.profiles import AgentProfile, AgentRegistry, default_agent_registry
from campanario.agents.personality_application import build_personality_application
from campanario.agents.router import AgentRouter
from campanario.chat.context import ContextManager
from campanario.chat.models import ChatSession, Message, MessageRole
from campanario.chat.dialogue_state import DialogueStateCompiler, build_answer_contract
from campanario.chat.turns import ConversationTurnInterpreter
from campanario.chat.repositories import ChatSessionRepository, MessageRepository
from campanario.model.protocol import ModelMessage, ModelProvider, ModelRequest
from campanario.runtime.clients import ClientIdentity
from campanario.runtime.telemetry import RuntimeTelemetry
from campanario.runtime.experience import ExperienceLayer
from campanario.runtime.events import (
    AgentResponseChunkPayload, AgentResponsePayload, AgentSelectedPayload, EventProvenance,
    EventPublisher, EventSourceKind, EventType, RuntimeEvent, SessionStartedPayload, UserTextPayload,
)


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
        event_bus: EventPublisher | None = None,
        telemetry: RuntimeTelemetry | None = None,
        experience: ExperienceLayer | None = None,
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
        self._dialogue_state = DialogueStateCompiler()
        self._turn_interpreter = ConversationTurnInterpreter()
        self._event_bus = event_bus
        self._telemetry = telemetry
        self._experience = experience

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
        created = self._sessions.create(session)
        self._publish_event(
            EventType.SESSION_STARTED,
            SessionStartedPayload(title=title, primary_agent_id=profile.id),
            session_id=created.id,
            provenance=EventProvenance(
                source_kind=EventSourceKind.RUNTIME,
                source_id="conversation",
            ),
        )
        return created

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

    def _publish_event(
        self,
        event_type: EventType,
        payload,
        *,
        provenance: EventProvenance,
        session_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> RuntimeEvent | None:
        if self._event_bus is None:
            return None
        return self._event_bus.publish(
            event_type,
            payload,
            provenance=provenance,
            session_id=session_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    async def _run_agent(
        self,
        *,
        session_id: UUID,
        profile: AgentProfile,
        history: list[Message],
        extra_system_note: str | None,
        reason: str,
        correlation_id: UUID,
        causation_id: UUID | None,
    ) -> AsyncIterator[AgentStreamEvent]:
        base_context = await self._context_manager.build(history)
        dialogue_state = self._dialogue_state.compile(history)
        if dialogue_state is not None:
            base_context = self._append_system_note(base_context, dialogue_state.render())
        latest_user_for_memory = next((m.content for m in reversed(history) if m.role == MessageRole.USER and m.content.strip()), "")
        if self._experience is not None:
            base_context = self._append_system_note(base_context, self._experience.render_context(latest_user_for_memory))
        context = apply_agent_profile(base_context, profile, history)
        turn_interpretation = self._turn_interpreter.interpret(history)
        personality_application = build_personality_application(profile, turn_interpretation)
        answer_contract = build_answer_contract(dialogue_state) if dialogue_state is not None else None
        if extra_system_note:
            context = self._append_system_note(context, extra_system_note)
        # Activate only the relevant parts of the already-frozen Personality Core near generation
        # time. This is subordinate to factual/context contracts and does not create a second persona.
        context = self._append_system_note(context, personality_application.render())
        # P2.4.1: the resolved discourse obligation is appended last, after persona/social and
        # participation notes, so it cannot be diluted into background context.
        if answer_contract is not None:
            context = self._append_system_note(context, answer_contract.render())

        user_texts = tuple(message.content for message in history if message.role == MessageRole.USER and message.content.strip())
        latest_user = user_texts[-1] if user_texts else ""
        arithmetic_anchor = extract_arithmetic_correction_anchor(latest_user, user_texts[:-1])
        if arithmetic_anchor is not None:
            context = self._append_system_note(context, arithmetic_anchor.prompt_note)
        request = ModelRequest(model=self._default_model, messages=context)
        if self._telemetry is not None:
            self._telemetry.mark("context_ready", correlation_id=correlation_id, session_id=session_id, agent_id=profile.id)

        provenance = EventProvenance(
            source_kind=EventSourceKind.AGENT,
            source_id=profile.id,
            agent_id=profile.id,
        )
        intent_event = self._publish_event(
            EventType.AGENT_INTENT_TO_SPEAK,
            AgentResponsePayload(agent_id=profile.id, reason=reason),
            session_id=session_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            provenance=provenance,
        )
        started_event = self._publish_event(
            EventType.AGENT_RESPONSE_STARTED,
            AgentResponsePayload(agent_id=profile.id, reason=reason),
            session_id=session_id,
            correlation_id=correlation_id,
            causation_id=None if intent_event is None else intent_event.event_id,
            provenance=provenance,
        )
        yield AgentStreamEvent("speaker_start", profile.id, reason=reason)
        if self._telemetry is not None:
            self._telemetry.mark("generation_started", correlation_id=correlation_id, session_id=session_id, agent_id=profile.id)
        first_token_seen = False
        def on_model_token() -> None:
            nonlocal first_token_seen
            if first_token_seen or self._telemetry is None:
                return
            first_token_seen = True
            self._telemetry.mark("first_token", correlation_id=correlation_id, session_id=session_id, agent_id=profile.id)
        assistant_text = await self._collect_agent_response(request, on_first_token=on_model_token)
        if self._telemetry is not None:
            self._telemetry.mark("generation_finished", correlation_id=correlation_id, session_id=session_id, agent_id=profile.id)
        assistant_text = normalize_own_speaker_prefix(assistant_text, profile)

        # Speaker provenance is a runtime invariant, not a personality preference. A redundant
        # *own* header is stripped safely; any transcript-like label that remains gets one clean
        # regeneration. We never silently relabel another participant's generated speech.
        labels = speaker_label_violations(assistant_text)
        if labels:
            repair_request = ModelRequest(
                model=self._default_model,
                messages=self._append_system_note(request.messages, speaker_repair_note(profile, labels)),
            )
            assistant_text = normalize_own_speaker_prefix(
                await self._collect_agent_response(repair_request), profile
            )
            labels = speaker_label_violations(assistant_text)
            if labels:
                recovered = extract_own_labeled_segment(assistant_text, profile)
                if recovered is None:
                    raise RuntimeError(
                        f"speaker output contract violated for {profile.id}: {', '.join(labels)}"
                    )
                assistant_text = recovered

        # P2.4.1 Answer Contract is a runtime binding, not merely prompt advice. Critical
        # follow-ups are validated locally; one repair is allowed before the answer is persisted.
        if answer_contract is not None and not answer_contract.validates(assistant_text):
            repair_request = ModelRequest(
                model=self._default_model,
                messages=self._append_system_note(request.messages, answer_contract.retry_note),
            )
            repaired = normalize_own_speaker_prefix(
                await self._collect_agent_response(repair_request), profile
            )
            if repaired and not speaker_label_violations(repaired) and answer_contract.validates(repaired):
                assistant_text = repaired
            elif answer_contract.acknowledgement_only:
                # A closed decision has a safe deterministic conversational fallback. Do not let a
                # second model miss reopen analysis that the user explicitly closed.
                assistant_text = "Entendido."
            elif answer_contract.require_novel_silence_criterion:
                # Explicit same-question / do-not-repeat turns must not persist the first invalid
                # answer if the single repair also misses the contribution constraint.
                assistant_text = (
                    "Eu fico quieto quando minha entrada não muda a decisão, não reduz um risco concreto "
                    "nem acrescenta um próximo passo útil."
                )

        # Explicit arithmetic corrections are anchored deterministically. If the model mutates an
        # operand (e.g. 18x7 -> 16x7), retry once with the computed anchor; if it still fails, use
        # the narrow deterministic correction rather than persist a false attribution.
        if arithmetic_anchor is not None and not arithmetic_anchor.validates(assistant_text):
            repair_request = ModelRequest(
                model=self._default_model,
                messages=self._append_system_note(request.messages, arithmetic_anchor.retry_note),
            )
            repaired = normalize_own_speaker_prefix(
                await self._collect_agent_response(repair_request), profile
            )
            if speaker_label_violations(repaired):
                repaired = ""
            assistant_text = (
                repaired if repaired and arithmetic_anchor.validates(repaired)
                else arithmetic_anchor.deterministic_fallback
            )

        if assistant_text:
            if self._telemetry is not None:
                self._telemetry.mark("first_usable_output", correlation_id=correlation_id, session_id=session_id, agent_id=profile.id)
            self._publish_event(
                EventType.AGENT_RESPONSE_CHUNK,
                AgentResponseChunkPayload(agent_id=profile.id, reason=reason, text=assistant_text),
                session_id=session_id,
                correlation_id=correlation_id,
                causation_id=None if started_event is None else started_event.event_id,
                provenance=provenance,
            )
            yield AgentStreamEvent("token", profile.id, text=assistant_text, reason=reason)

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
        self._publish_event(
            EventType.AGENT_RESPONSE_FINISHED,
            AgentResponsePayload(agent_id=profile.id, reason=reason),
            session_id=session_id,
            correlation_id=correlation_id,
            causation_id=None if started_event is None else started_event.event_id,
            provenance=provenance,
        )
        yield AgentStreamEvent("speaker_done", profile.id, reason=reason)

    async def stream_turn(
        self,
        session_id: UUID,
        text: str,
        *,
        client: ClientIdentity | None = None,
        correlation_id: UUID | None = None,
        user_causation_id: UUID | None = None,
        turn_system_note: str | None = None,
        independent_group_turn: bool = False,
    ) -> AsyncIterator[AgentStreamEvent]:
        correlation_id = correlation_id or uuid4()
        if self._telemetry is not None:
            self._telemetry.mark("request_received", correlation_id=correlation_id, session_id=session_id, client_id=None if client is None else client.client_id, device_id=None if client is None else client.device_id)
        try:
            async for event in self._stream_turn_impl(
                session_id,
                text,
                client=client,
                correlation_id=correlation_id,
                user_causation_id=user_causation_id,
                turn_system_note=turn_system_note,
                independent_group_turn=independent_group_turn,
            ):
                yield event
        finally:
            if self._telemetry is not None:
                self._telemetry.mark("turn_finished", correlation_id=correlation_id, session_id=session_id, client_id=None if client is None else client.client_id, device_id=None if client is None else client.device_id)

    async def _stream_turn_impl(
        self,
        session_id: UUID,
        text: str,
        *,
        client: ClientIdentity | None = None,
        correlation_id: UUID | None = None,
        user_causation_id: UUID | None = None,
        turn_system_note: str | None = None,
        independent_group_turn: bool = False,
    ) -> AsyncIterator[AgentStreamEvent]:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(str(session_id))
        if not self._default_model.strip():
            raise ModelNotConfiguredError(
                "CAMPANARIO_MODEL_NAME is empty. Configure a local model first."
            )

        correlation_id = correlation_id or uuid4()
        resolution = self._agent_router.resolve(text, session.primary_agent_id)
        if self._telemetry is not None:
            self._telemetry.mark("routing_completed", correlation_id=correlation_id, session_id=session_id, agent_id=resolution.profile.id, route_source=resolution.source)
        primary = resolution.profile
        if resolution.persist_primary and primary.id != session.primary_agent_id:
            updated = self._set_primary(session_id, primary.id)
            if updated is not None:
                session = updated

        history_before_user = self._messages.list_by_session(session_id)
        user_message = Message(
            id=uuid4(),
            session_id=session_id,
            role=MessageRole.USER,
            content=text,
            created_at=datetime.now(UTC),
            client_id=None if client is None else client.client_id,
            device_id=None if client is None else client.device_id,
        )
        self._messages.append(user_message)
        if self._experience is not None:
            self._experience.observe_user_message(
                history_before=history_before_user,
                message=user_message,
                correlation_id=correlation_id,
            )
        user_event = self._publish_event(
            EventType.USER_TEXT,
            UserTextPayload(text=text),
            session_id=session_id,
            correlation_id=correlation_id,
            causation_id=user_causation_id,
            provenance=(
                EventProvenance(source_kind=EventSourceKind.USER, source_id="user")
                if client is None
                else EventProvenance(
                    source_kind=EventSourceKind.CLIENT,
                    source_id=client.client_id,
                    client_id=client.client_id,
                    device_id=client.device_id,
                )
            ),
        )
        selected_event = self._publish_event(
            EventType.AGENT_SELECTED,
            AgentSelectedPayload(agent_id=primary.id, reason=resolution.source, position="primary"),
            session_id=session_id,
            correlation_id=correlation_id,
            causation_id=None if user_event is None else user_event.event_id,
            provenance=EventProvenance(
                source_kind=EventSourceKind.RUNTIME,
                source_id="agent_router",
                agent_id=primary.id,
            ),
        )
        history_before_primary = self._messages.list_by_session(session_id)

        primary_parts: list[str] = []
        async for event in self._run_agent(
            session_id=session_id,
            profile=primary,
            history=history_before_primary,
            extra_system_note=turn_system_note,
            reason=resolution.source,
            correlation_id=correlation_id,
            causation_id=None if selected_event is None else selected_event.event_id,
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
        explicit_group = self._participation.explicitly_invites_group(text)
        if independent_group_turn and explicit_group:
            # Physical voice: both explicitly named participants answer the same original utterance.
            # The first answer is intentionally excluded from the secondary model history so it
            # cannot be misread as a fresh user prompt.
            shared_history = history_before_primary
            note = independent_group_participation_context(primary, secondary, text)
            if turn_system_note:
                note = f"{turn_system_note.strip()}\n\n{note}"
        else:
            shared_history = self._messages.list_by_session(session_id)
            note = participation_context(primary, secondary, primary_text)
        secondary_selected = self._publish_event(
            EventType.AGENT_SELECTED,
            AgentSelectedPayload(agent_id=secondary.id, reason=decision.reason, position="secondary"),
            session_id=session_id,
            correlation_id=correlation_id,
            provenance=EventProvenance(
                source_kind=EventSourceKind.RUNTIME,
                source_id="participation_arbiter",
                agent_id=secondary.id,
            ),
        )
        if self._telemetry is not None:
            self._telemetry.mark("second_agent_started", correlation_id=correlation_id, session_id=session_id, agent_id=secondary.id)
        async for event in self._run_agent(
            session_id=session_id,
            profile=secondary,
            history=shared_history,
            extra_system_note=note,
            reason=decision.reason,
            correlation_id=correlation_id,
            causation_id=None if secondary_selected is None else secondary_selected.event_id,
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

    async def _collect_agent_response(self, request: ModelRequest, on_first_token=None) -> str:
        parts: list[str] = []
        first = True
        async for chunk in self._model_provider.stream(request):
            if chunk.text:
                if first and on_first_token is not None:
                    on_first_token()
                first = False
                parts.append(chunk.text)
            if chunk.done:
                break
        return "".join(parts).strip()

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

