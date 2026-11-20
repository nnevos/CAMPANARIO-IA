"""Opt-in non-LLM agent profiles backed by declarative V9 builds.

No cloning of Morgana's or Todd's private persona, history, or memory.
"""
from __future__ import annotations

from campanario.agents.profiles import AgentProfile, PersonalityCore
from campanario.brains.builds import AgentBuild


def make_agent_profile(build: AgentBuild) -> AgentProfile:
    if build.agent_id in {'morgana', 'todd'}:
        raise ValueError('Built-in personalities must not be replaced')
    if not build.display_name:
        raise ValueError('New agents require a display name')
    no = ()
    core = PersonalityCore(
        traits=('Responsivo', 'Cooperativo'), anti_traits=('Inventar fatos',),
        tendencies=('Consultar ferramentas quando necessário',),
        boundaries=('Sem permissão concedida pela ficha',),
        social=no, technical=no, creative=no, discussion=no, urgency=no,
        positive_patterns=no, negative_patterns=no,
    )
    return AgentProfile(
        id=build.agent_id, name=build.display_name,
        summary=build.identity_description or 'Agente customizado local',
        identity=build.identity_description or (
            f'Você é o agente {build.display_name}; uma identidade criada localmente. '
            'Siga as políticas da plataforma e nunca fabrique evidências.'),
        personality=core,
    )
