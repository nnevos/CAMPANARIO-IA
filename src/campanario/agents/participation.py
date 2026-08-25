from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from collections.abc import Sequence

from campanario.agents.profiles import AgentProfile, AgentRegistry
from campanario.chat.models import Message, MessageRole
from campanario.chat.pragmatics import PragmaticAct
from campanario.chat.turns import ConversationTurnInterpreter, TurnMode
from campanario.model.protocol import ModelMessage, ModelProvider, ModelRequest


@dataclass(frozen=True, slots=True)
class ParticipationDecision:
    join: bool
    reason: str


class ParticipationArbiter:
    """Conservative semantic arbiter for non-primary agent participation.

    Agents are never forbidden from participating by identity. The arbiter exists only to
    avoid both agents replying to every trivial turn. Explicit group address always allows
    the second participant. Otherwise an eligible open-ended turn may ask the shared model
    for a tiny JOIN/SKIP decision after seeing the primary response.
    """

    _GROUP_MARKERS = (
        "voces", "vocês", "os dois", "as duas", "ambos", "todd e morgana",
        "morgana e todd", "quero ouvir os dois", "o que voces acham", "o que vocês acham",
    )

    def __init__(
        self,
        registry: AgentRegistry,
        provider: ModelProvider | None,
        model: str,
        interpreter: ConversationTurnInterpreter | None = None,
    ) -> None:
        self._registry = registry
        self._provider = provider
        self._model = model
        self._interpreter = interpreter or ConversationTurnInterpreter()

    def secondary_for(self, primary: AgentProfile) -> AgentProfile | None:
        others = [profile for profile in self._registry.list() if profile.id != primary.id]
        return others[0] if others else None

    def explicitly_invites_group(self, text: str) -> bool:
        folded = _fold(text)
        both_named = "todd" in folded and "morgana" in folded
        return both_named or any(marker in folded for marker in self._GROUP_MARKERS)

    async def decide(
        self,
        *,
        user_text: str,
        primary: AgentProfile,
        primary_text: str,
        history: Sequence[Message],
    ) -> ParticipationDecision:
        secondary = self.secondary_for(primary)
        if secondary is None:
            return ParticipationDecision(False, "no_secondary")

        if self.explicitly_invites_group(user_text):
            return ParticipationDecision(True, "explicit_group_invitation")

        if self._primary_invites_secondary(primary_text, secondary):
            return ParticipationDecision(True, "primary_invited_secondary")

        interpretation = self._interpreter.interpret_text(user_text)
        if interpretation.mode not in {TurnMode.DISCUSSION, TurnMode.GENERAL, TurnMode.SOCIAL, TurnMode.CREATIVE}:
            return ParticipationDecision(False, "closed_or_task_turn")
        if interpretation.mode == TurnMode.SOCIAL and any(
            act in interpretation.pragmatic_acts
            for act in (PragmaticAct.GREET, PragmaticAct.ACKNOWLEDGE, PragmaticAct.REACT)
        ):
            return ParticipationDecision(False, "closed_social_turn")
        if self._secondary_spoke_recently(history, secondary.id):
            return ParticipationDecision(False, "participation_cooldown")
        if self._provider is None:
            return ParticipationDecision(False, "semantic_arbiter_disabled")

        prompt = ModelRequest(
            model=self._model,
            messages=(
                ModelMessage(
                    role=MessageRole.SYSTEM,
                    content=(
                        "Voce e apenas um arbitro de turno do sistema Campanario, nao uma persona. "
                        "Responda exatamente JOIN ou SKIP. O segundo agente deve entrar somente se tiver "
                        "uma contribuicao distinta e natural: discordancia relevante, complemento importante, "
                        "observacao social realmente oportuna ou perspectiva diferente. Nao entre para repetir, "
                        "cumprimentar, confirmar, competir por atencao ou transformar toda conversa em painel."
                    ),
                ),
                ModelMessage(
                    role=MessageRole.USER,
                    content=(
                        f"Mensagem do usuario:\n{user_text}\n\n"
                        f"Agente que respondeu primeiro: {primary.name}\n"
                        f"Resposta dele:\n{primary_text}\n\n"
                        f"Segundo participante: {secondary.name}\n"
                        "Esse segundo participante tem um motivo concreto para falar agora?"
                    ),
                ),
            ),
        )
        answer = await self._collect(prompt)
        token = answer.strip().upper().split()[0] if answer.strip() else "SKIP"
        return ParticipationDecision(token == "JOIN", "semantic_arbiter")

    async def _collect(self, request: ModelRequest) -> str:
        chunks: list[str] = []
        async for chunk in self._provider.stream(request):
            if chunk.text:
                chunks.append(chunk.text)
            if chunk.done:
                break
        return "".join(chunks)

    @staticmethod
    def _primary_invites_secondary(text: str, secondary: AgentProfile) -> bool:
        folded = _fold(text)
        if secondary.id not in folded:
            return False
        return bool(re.search(rf"\b{re.escape(secondary.id)}\b.*(?:\?|o que acha|quer acrescentar|discorda|completa)", folded))

    @staticmethod
    def _secondary_spoke_recently(history: Sequence[Message], secondary_id: str) -> bool:
        assistants = [m for m in history if m.role == MessageRole.ASSISTANT]
        return any(m.agent_id == secondary_id for m in assistants[-2:])


def participation_context(primary: AgentProfile, secondary: AgentProfile, primary_text: str) -> str:
    return (
        "PARTICIPACAO MULTIAGENTE\n"
        f"{primary.name} ja respondeu primeiro neste turno. Voce, {secondary.name}, decidiu participar agora. "
        "Acrescente apenas uma contribuicao distinta e proporcional. Nao repita a resposta anterior. "
        "Voce pode concordar, discordar, complementar ou falar diretamente com o outro agente quando isso "
        "for natural. Nao explique o mecanismo de roteamento ou a decisao de participar.\n\n"
        f"RESPOSTA DE {primary.name.upper()}:\n{primary_text}"
    )


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).strip()
