"""Behavior-context assembly.

The large behavior implementation was split during the pre-agent cleanup. This module now
only composes prompt, turn interpretation, audit evidence and provenance into the context
passed to the response/model pipeline.
"""

from collections.abc import Sequence

from campanario.chat.audit import _assistant_trace, _observable_signals
from campanario.chat.context import ContextManager
from campanario.chat.models import Message, MessageRole
from campanario.chat.prompts import BALANCED_BEHAVIOR_PROMPT, SELF_ANALYSIS_AUDIT_PROMPT, TURN_BOUNDARY_PROMPT
from campanario.chat.provenance import (
    _context_provenance,
    _explicit_user_corrections,
    _sanitize_context_by_provenance,
)
from campanario.chat.turns import (
    ContinuationKind,
    ConversationTurnInterpreter,
    TurnInterpretation,
    TurnMode,
)
from campanario.model.protocol import ModelMessage

class BehaviorContextManager:
    """Add behavioral and interaction-mode hints without owning history selection or memory."""

    def __init__(
        self,
        inner: ContextManager,
        prompt: str = BALANCED_BEHAVIOR_PROMPT,
        interpreter: ConversationTurnInterpreter | None = None,
    ) -> None:
        self._inner = inner
        self._prompt = prompt.strip()
        self._interpreter = interpreter or ConversationTurnInterpreter()

    async def build(self, history: Sequence[Message]) -> tuple[ModelMessage, ...]:
        context = await self._inner.build(history)
        interpretation = self._interpreter.interpret(history)
        provenance_note, creative_assistant_texts = _context_provenance(history, self._interpreter)
        context = _sanitize_context_by_provenance(context, interpretation, creative_assistant_texts)
        behavior = (
            f"{self._prompt}\n\nMODO DE INTERACAO DESTE TURNO: {interpretation.mode.value}\n"
            f"{interpretation.guidance}"
        )
        correction_notes = _explicit_user_corrections(history)
        if correction_notes:
            behavior = f"{behavior}\n\n{correction_notes}"
        if provenance_note:
            behavior = f"{behavior}\n\n{provenance_note}"
        if interpretation.mode == TurnMode.AUDIT:
            behavior = (
                f"{behavior}\n\n{SELF_ANALYSIS_AUDIT_PROMPT.strip()}\n\n"
                f"TRACE OBSERVAVEL DAS RESPOSTAS RECENTES:\n"
                f"{_assistant_trace(history, self._interpreter)}\n\n"
                f"SINAIS OBSERVAVEIS:\n{_observable_signals(history)}"
            )

        boundary_text = (
            f"{TURN_BOUNDARY_PROMPT.strip()}\n\n"
            f"MODO ATUAL CONFIRMADO: {interpretation.mode.value}\n"
            f"ATOS PRAGMATICOS DA ENTRADA: "
            f"{', '.join(act.value for act in interpretation.pragmatic_acts) or 'unknown'}\n"
            f"CONFIANCA PRAGMATICA: {interpretation.pragmatic_confidence:.2f}\n"
            f"SEMANTICA DE CONTINUACAO: "
            f"{interpretation.continuation_kind.value if interpretation.continuation_kind else 'nao_aplicavel'}\n"
            "INTERPRETACAO PRAGMATICA DESCREVE A ENTRADA; NAO IMITE O VOCABULARIO DO USUARIO SO POR ISSO.\n"
            f"APLIQUE SOMENTE AO TURNO ATUAL: {interpretation.guidance}"
        )

        # Keep exactly one leading system message. Some local chat templates (including
        # llama-family templates used through Ollama) can behave unpredictably when a
        # second system role is injected between conversation turns, including echoing
        # internal instructions. The current-turn boundary is therefore merged into the
        # leading system instruction instead of being inserted before the latest user.
        if context and context[0].role == MessageRole.SYSTEM:
            system_content = f"{behavior}\n\n{boundary_text}\n\n{context[0].content}"
            prepared = [
                ModelMessage(role=MessageRole.SYSTEM, content=system_content),
                *context[1:],
            ]
        else:
            system_content = f"{behavior}\n\n{boundary_text}"
            prepared = [ModelMessage(role=MessageRole.SYSTEM, content=system_content), *context]

        return tuple(prepared)
