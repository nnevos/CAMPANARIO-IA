from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from enum import StrEnum
from threading import RLock
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from campanario.chat.service import AgentStreamEvent
from campanario.agents.addressing import fold_text
from campanario.runtime.clients import ClientIdentity
from campanario.runtime.events import (
    AgentInterruptedPayload,
    CallEventPayload,
    EventProvenance,
    EventSourceKind,
    EventType,
    SpeechPayload,
    WakeDetectedPayload,
)
from campanario.runtime.permissions import AuthorizationContext, PermissionDecision
from campanario.runtime.presence import resolve_wake


VOICE_CONTRACT_VERSION = "1.0"


def voice_turn_directives(text: str) -> tuple[str | None, bool]:
    """Return voice-only prompt guidance and group isolation mode for a final utterance.

    Presence checks are pragmatic call probes, not requests for an explanation of what the user
    wants heard. Explicit Todd+Morgana addressing uses independent group context so each agent
    receives the original user utterance rather than treating the first answer as a new prompt.
    """
    folded = fold_text(text).strip(" .?!,:;-")
    import re
    has_todd = re.search(r"\btodd\b", folded) is not None
    has_morgana = re.search(r"\bmorgana\b", folded) is not None
    independent_group = has_todd and has_morgana

    presence_patterns = (
        r"^(me )?(escuta|ouve)$",
        r"^(voce |voces )?(me )?(escuta|escutam|ouve|ouvem)$",
        r"^(consegue|conseguem) me (escutar|ouvir)$",
        r"^(ta|esta|tá|está) ai$",
        r"^(voce|voces) (ta|estao|esta|estão|tá|está) ai$",
    )
    spoken_style = (
        "CONVERSA POR VOZ — ENTREGA NATURAL\n"
        "Isto sera falado em voz alta, nao exibido como artigo. Responda em portugues brasileiro "
        "conversacional e natural, preservando a personalidade e as prioridades proprias do agente; "
        "nao neutralize Todd e Morgana no mesmo estilo generico. Comece pela resposta, sem introducao "
        "de atendimento. Em pedidos simples, prefira uma ou duas frases; so aprofunde quando o usuario "
        "pedir ou quando o detalhe for necessario. Evite listas faladas, recapitulacoes, definicoes "
        "enciclopedicas, frases de preenchimento e terminar toda resposta oferecendo mais ajuda."
    )

    if any(re.fullmatch(pattern, folded) for pattern in presence_patterns):
        return (
            spoken_style + "\nSEMANTICA DE VOZ — PROBE DE PRESENCA\n"
            "O usuario esta apenas confirmando se esta sendo ouvido/atendido. "
            "Responda diretamente confirmando presenca e audicao, em uma frase curta e natural. "
            "Nao pergunte o que ele gostaria que voce ouvisse e nao transforme isso em uma tarefa aberta.",
            independent_group,
        )

    if folded in {"todd", "morgana", "todd e morgana", "morgana e todd"}:
        return (
            spoken_style + "\nSEMANTICA DE VOZ — CHAMADA DE PRESENCA\n"
            "O usuario apenas chamou o participante ou os participantes pelo nome. "
            "Confirme presenca em uma frase curta e natural; nao invente uma solicitacao ausente.",
            independent_group,
        )

    return spoken_style, independent_group


class CallState(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"


class VoiceCall(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    call_id: UUID
    session_id: UUID
    client_id: str = Field(min_length=1, max_length=128)
    device_id: str = Field(min_length=1, max_length=128)
    state: CallState
    started_at: datetime
    ended_at: datetime | None = None
    end_reason: str | None = Field(default=None, max_length=128)


class VoiceCallRegistry:
    """Process-local live Call state.

    Calls are transport/lifecycle state, not memory containers. The durable conversation remains
    the existing session_id. A future native/mobile call shell can reconnect to the same session
    without creating another Todd, Morgana or ChatService.
    """

    def __init__(self) -> None:
        self._calls: dict[UUID, VoiceCall] = {}
        self._lock = RLock()

    def start(self, session_id: UUID, identity: ClientIdentity) -> VoiceCall:
        if not identity.device_id:
            raise ValueError("voice call requires device_id")
        call = VoiceCall(
            call_id=uuid4(),
            session_id=session_id,
            client_id=identity.client_id,
            device_id=identity.device_id,
            state=CallState.ACTIVE,
            started_at=datetime.now(UTC),
        )
        with self._lock:
            self._calls[call.call_id] = call
        return call

    def handoff(self, call_id: UUID, identity: ClientIdentity) -> VoiceCall:
        """Move the live transport endpoint while preserving call_id/session_id."""
        if not identity.device_id:
            raise ValueError("voice call requires device_id")
        with self._lock:
            current = self._calls.get(call_id)
            if current is None or current.state != CallState.ACTIVE:
                raise KeyError(call_id)
            moved = current.model_copy(update={"client_id": identity.client_id, "device_id": identity.device_id})
            self._calls[call_id] = moved
            return moved

    def get(self, call_id: UUID) -> VoiceCall | None:
        with self._lock:
            return self._calls.get(call_id)

    def list(self, *, session_id: UUID | None = None, active_only: bool = False) -> tuple[VoiceCall, ...]:
        with self._lock:
            values = tuple(self._calls.values())
        if session_id is not None:
            values = tuple(item for item in values if item.session_id == session_id)
        if active_only:
            values = tuple(item for item in values if item.state == CallState.ACTIVE)
        return values

    def end(self, call_id: UUID, reason: str = "ended") -> VoiceCall:
        with self._lock:
            current = self._calls.get(call_id)
            if current is None:
                raise KeyError(call_id)
            if current.state == CallState.ENDED:
                return current
            ended = current.model_copy(
                update={
                    "state": CallState.ENDED,
                    "ended_at": datetime.now(UTC),
                    "end_reason": reason,
                }
            )
            self._calls[call_id] = ended
            return ended


class VadResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    speech_detected: bool
    probability: float | None = Field(default=None, ge=0.0, le=1.0)


class WakeResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    detected: bool
    phrase: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class SttSegment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    text: str
    final: bool
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class TtsChunk(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_id: str = Field(min_length=1, max_length=64)
    audio: bytes
    final: bool = False
    audio_format: str = Field(default="pcm_s16le", min_length=1, max_length=32)


class VoiceActivityDetector(Protocol):
    async def detect(self, audio: bytes) -> VadResult: ...


class WakeWordDetector(Protocol):
    async def detect(self, audio: bytes) -> WakeResult: ...


class SpeechToTextAdapter(Protocol):
    async def transcribe(self, audio: bytes, *, final: bool) -> SttSegment: ...


class TextToSpeechAdapter(Protocol):
    def synthesize(self, text: str, *, agent_id: str) -> AsyncIterator[TtsChunk]: ...


class VoiceCallCoordinator:
    """PF9 semantic Call adapter over the existing Conversation Runtime.

    This class deliberately accepts already-decoded speech text. Real VAD/wake/STT/TTS engines are
    adapter protocols above and remain outside PF9. Only a final speech segment enters ChatService;
    partials/wake/interruption remain realtime operational events.
    """

    def __init__(self, runtime) -> None:
        self._runtime = runtime

    def start(self, session_id: UUID, identity: ClientIdentity) -> VoiceCall:
        if not any(item.id == session_id for item in self._runtime.sessions.list_sessions()):
            raise KeyError(session_id)
        if not identity.device_id:
            raise ValueError("device_id required")
        device = self._runtime.devices.get(identity.device_id)
        if device is None or "microphone" not in device.capabilities:
            raise ValueError("device microphone capability required")
        context = AuthorizationContext(
            principal_kind="device",
            principal_id=identity.device_id,
            device_id=identity.device_id,
            session_id=session_id,
            session_active=True,
            call_active=True,
        )
        check = self._runtime.permissions.check("microphone.listen", context, capability="voice.call")
        if check.decision != PermissionDecision.ALLOW:
            raise PermissionError(check.reason)
        call = self._runtime.calls.start(session_id, identity)
        self._runtime.presence.wake(session_id, source_id=identity.device_id)
        self._runtime.events.publish(
            EventType.CALL_STARTED,
            CallEventPayload(call_id=call.call_id, state=call.state.value),
            provenance=self._device_provenance(call),
            session_id=session_id,
        )
        return call

    def handoff(self, call_id: UUID, identity: ClientIdentity) -> VoiceCall:
        current = self._require_active(call_id)
        if not identity.device_id:
            raise ValueError("device_id required")
        device = self._runtime.devices.get(identity.device_id)
        if device is None or "microphone" not in device.capabilities:
            raise ValueError("device microphone capability required")
        context = AuthorizationContext(principal_kind="device", principal_id=identity.device_id, device_id=identity.device_id, session_id=current.session_id, session_active=True, call_active=True)
        check = self._runtime.permissions.check("microphone.listen", context, capability="voice.call")
        if check.decision != PermissionDecision.ALLOW:
            raise PermissionError(check.reason)
        return self._runtime.calls.handoff(call_id, identity)

    def wake(self, call_id: UUID, *, phrase: str | None = None) -> None:
        call = self._require_active(call_id)
        _, direct_agent, _ = resolve_wake(phrase or "Campanario")
        self._runtime.presence.wake(call.session_id, source_id=call.device_id, direct_agent_id=direct_agent)
        self._runtime.events.publish(
            EventType.WAKE_DETECTED,
            WakeDetectedPayload(phrase=phrase),
            provenance=self._device_provenance(call),
            session_id=call.session_id,
        )

    def speech_partial(self, call_id: UUID, text: str, *, confidence: float | None = None) -> None:
        call = self._require_active(call_id)
        self._runtime.events.publish(
            EventType.USER_SPEECH_PARTIAL,
            SpeechPayload(text=text, confidence=confidence),
            provenance=self._device_provenance(call),
            session_id=call.session_id,
        )

    async def speech_final(
        self,
        call_id: UUID,
        text: str,
        *,
        confidence: float | None = None,
        correlation_id: UUID | None = None,
    ) -> AsyncIterator[AgentStreamEvent]:
        call = self._require_active(call_id)
        woke, direct_agent, cleaned = resolve_wake(text)
        presence = self._runtime.presence.get(call.session_id)
        if woke:
            self._runtime.presence.wake(call.session_id, source_id=call.device_id, direct_agent_id=direct_agent)
            if direct_agent is None:
                text = cleaned
        elif not presence.attention_open:
            # Ambient speech outside an attention window is observable but must not become conversation.
            self.speech_partial(call_id, text, confidence=confidence)
            return
        if not text.strip():
            return
        turn_system_note, independent_group_turn = voice_turn_directives(text)
        self._runtime.presence.engage(call.session_id, source_id=call.device_id, agent_id=direct_agent)
        correlation_id = correlation_id or uuid4()
        final_event = self._runtime.events.publish(
            EventType.USER_SPEECH_FINAL,
            SpeechPayload(text=text, confidence=confidence),
            provenance=self._device_provenance(call),
            session_id=call.session_id,
            correlation_id=correlation_id,
        )
        identity = ClientIdentity(client_id=call.client_id, device_id=call.device_id)
        async for event in self._runtime.conversation.stream_turn(
            call.session_id,
            text,
            client=identity,
            correlation_id=correlation_id,
            user_causation_id=final_event.event_id,
            turn_system_note=turn_system_note,
            independent_group_turn=independent_group_turn,
        ):
            yield event

    def interrupt(self, call_id: UUID, *, agent_id: str, reason: str = "barge_in") -> None:
        call = self._require_active(call_id)
        self._runtime.events.publish(
            EventType.AGENT_INTERRUPTED,
            AgentInterruptedPayload(
                agent_id=agent_id,
                reason="voice_interrupt",
                interruption_reason=reason,
            ),
            provenance=self._device_provenance(call),
            session_id=call.session_id,
        )

    def end(self, call_id: UUID, *, reason: str = "ended") -> VoiceCall:
        call = self._runtime.calls.end(call_id, reason)
        self._runtime.presence.quiet(call.session_id, source_id=call.device_id)
        self._runtime.events.publish(
            EventType.CALL_ENDED,
            CallEventPayload(call_id=call.call_id, state=call.state.value),
            provenance=self._device_provenance(call),
            session_id=call.session_id,
        )
        return call

    def _require_active(self, call_id: UUID) -> VoiceCall:
        call = self._runtime.calls.get(call_id)
        if call is None or call.state != CallState.ACTIVE:
            raise KeyError(call_id)
        return call

    @staticmethod
    def _device_provenance(call: VoiceCall) -> EventProvenance:
        return EventProvenance(
            source_kind=EventSourceKind.DEVICE,
            source_id=call.device_id,
            client_id=call.client_id,
            device_id=call.device_id,
        )
