from __future__ import annotations

from collections.abc import Sequence

from campanario.agents.profiles import AgentProfile, render_compact_persona
from campanario.agents.social import SOCIAL_PROTOCOL_PROMPT
from campanario.chat.models import Message, MessageRole
from campanario.model.protocol import ModelMessage


def apply_agent_profile(
    context: tuple[ModelMessage, ...],
    profile: AgentProfile,
    history: Sequence[Message],
    *,
    compact: bool = False,
) -> tuple[ModelMessage, ...]:
    """Attach the selected persona to the existing Campanario system context.

    Persona is deliberately downstream from shared context/pragmatics and does not own memory.
    """
    recent_agents: list[str] = []
    for message in history[-12:]:
        if message.role == MessageRole.ASSISTANT and message.agent_id and message.agent_id not in recent_agents:
            recent_agents.append(message.agent_id)

    history_note = ""
    other_agents = [agent for agent in recent_agents if agent != profile.id]
    if other_agents:
        history_note = (
            "\n\nHISTORICO DE PERSONAS\n"
            "Ha respostas recentes produzidas por outros agentes: " + ", ".join(other_agents) + ". "
            "Preserve o contexto util, mas responda segundo sua propria persona e nao imite o estilo anterior. O outro agente continua sendo um participante presente, nao uma persona desativada."
        )

    output_contract = (
        "\n\nCONTRATO DE SAIDA DO SPEAKER\n"
        f"Voce e {profile.name} neste turno. Gere somente a proxima fala de {profile.name}. "
        f"Nao comece com '{profile.name}:' e nao escreva falas, labels ou cabecalhos de Todd, Morgana ou Campanario. "
        "Se precisar se referir ao que outro participante disse, faca isso em prosa normal, sem recriar a fala dele como transcript."
    )
    persona = (
        render_compact_persona(profile) if compact else
        profile.persona_prompt.strip() + "\n\n" + SOCIAL_PROTOCOL_PROMPT.strip()
    ) + history_note + output_contract
    if context and context[0].role == MessageRole.SYSTEM:
        merged = ModelMessage(
            role=MessageRole.SYSTEM,
            content=f"{context[0].content}\n\n{persona}",
        )
        return (merged, *context[1:])
    return (ModelMessage(role=MessageRole.SYSTEM, content=persona), *context)
