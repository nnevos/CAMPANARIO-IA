"""V9 declarative agent builds. Builds never grant permissions or knowledge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ARCHETYPES: dict[str, str] = {
    'investigador': 'Confrontar hipóteses com evidências',
    'executor': 'Organizar ações autorizadas e verificáveis',
    'oraculo': 'Contextualizar conceitos sem fabricar fatos',
    'artifice': 'Priorizar revisão e depuração',
    'estrategista': 'Explicitar alternativas e riscos',
    'guardiao': 'Priorizar limites e segurança',
    'explorador': 'Investigar possíveis fontes',
    'arauto': 'Comunicar com clareza',
}


class TalentDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    id: str
    title: str
    trigger: Literal['document_lookup', 'data_analysis', 'technical', 'sensitive', 'complex', 'task']
    preconditions: tuple[str, ...] = ()
    effect: Literal['review_conflicts', 'show_context', 'outline_steps', 'request_tests',
                    'require_confirmation', 'plain_language']
    priority: int = Field(default=5, ge=0, le=10)
    conflicts: tuple[str, ...] = ()
    version: str = '1.0'


TALENTS: dict[str, TalentDefinition] = {t.id: t for t in (
    TalentDefinition(id='olhar_investigativo', title='Olhar Investigativo', trigger='document_lookup',
                     effect='review_conflicts', priority=8),
    TalentDefinition(id='leitura_profunda', title='Leitura Profunda', trigger='document_lookup',
                     effect='show_context', priority=7),
    TalentDefinition(id='plano_de_acao', title='Plano de Ação', trigger='task',
                     effect='outline_steps', priority=5),
    TalentDefinition(id='revisao_tecnica', title='Revisão Técnica', trigger='technical',
                     effect='request_tests', priority=6),
    TalentDefinition(id='sentinela', title='Sentinela', trigger='sensitive',
                     effect='require_confirmation', priority=10),
    TalentDefinition(id='traducao_clara', title='Tradução Clara', trigger='complex',
                     effect='plain_language', priority=4),
)}


class AgentBuild(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    agent_id: str = Field(min_length=1, max_length=64, pattern=r'^[a-z0-9_-]+$')
    package_version: str = '1.0'
    display_name: str = Field(default='', max_length=64)
    identity_description: str = Field(default='', max_length=400)
    persona_core_ref: str = Field(default='', max_length=128)
    voice_ref: str = Field(default='', max_length=128)
    appearance_ref: str = Field(default='', max_length=128)
    revision: int = Field(default=1, ge=1)
    mode: Literal['free', 'archetype'] = 'free'
    primary_archetype: str | None = None
    secondary_archetype: str | None = None
    talents: tuple[str, ...] = Field(default=(), max_length=6)
    affinities: dict[str, int] = Field(default_factory=dict)
    requested_capabilities: tuple[str, ...] = ()

    @model_validator(mode='after')
    def valid_build(self):
        if self.agent_id not in {'morgana', 'todd'} and not self.display_name.strip():
            raise ValueError('new agent requires a display_name')
        if self.mode == 'archetype' and not self.primary_archetype:
            raise ValueError('primary archetype required unless free mode')
        if self.mode == 'free' and (self.primary_archetype or self.secondary_archetype):
            raise ValueError('free mode has no archetypes')
        if self.primary_archetype and self.primary_archetype not in ARCHETYPES:
            raise ValueError('unknown primary archetype')
        if self.secondary_archetype and (self.secondary_archetype not in ARCHETYPES or self.secondary_archetype == self.primary_archetype):
            raise ValueError('invalid secondary archetype')
        if len(set(self.talents)) != len(self.talents) or any(t not in TALENTS for t in self.talents):
            raise ValueError('unknown or duplicated talent')
        if any(k not in ARCHETYPES or not 0 <= n <= 5 for k, n in self.affinities.items()):
            raise ValueError('affinities are preferences on 0..5, not accuracies')
        # requested capabilities are wishes, never permissions.
        if len(self.requested_capabilities) > 8 or any(len(v) > 64 for v in self.requested_capabilities):
            raise ValueError('capability request limit exceeded')
        return self


@dataclass(frozen=True)
class ActiveTalent:
    id: str
    trigger: str
    effect: str


def select_talents(build: AgentBuild, *, intent: str, text: str) -> tuple[ActiveTalent, ...]:
    """MVP selects <=2 advisory effects. Nothing here executes tools or changes facts."""
    folded = text.casefold()
    active_triggers = {intent}
    if any(word in folded for word in ('código', 'codigo', 'python', 'bug', 'teste', 'depurar')):
        active_triggers.add('technical')
    if any(word in folded for word in ('apagar', 'excluir', 'segredo', 'permissão', 'permissao', 'externo')):
        active_triggers.add('sensitive')
    if any(word in folded for word in ('plano', 'etapas', 'passos', 'como fazer')):
        active_triggers.add('task')
    if any(word in folded for word in ('explique', 'simplifique', 'complexo', 'resuma')):
        active_triggers.add('complex')
    matches = [TALENTS[t] for t in build.talents if TALENTS[t].trigger in active_triggers]
    matches.sort(key=lambda x: (-x.priority, x.id))
    chosen: list[ActiveTalent] = []
    for talent in matches:
        if len(chosen) == 2:
            break
        if any(t.id in talent.conflicts or talent.id in TALENTS[t.id].conflicts for t in chosen):
            continue
        chosen.append(ActiveTalent(talent.id, talent.trigger, talent.effect))
    return tuple(chosen)


def render_build_note(build: AgentBuild, talents: tuple[ActiveTalent, ...]) -> str:
    """Non-authoritative style hints after the immutable source/permission contract."""
    if build.mode == 'free' and not talents:
        return ''
    lines = [
        'PREFERENCIAS DE ATUACAO V9 (sem novos direitos ou fatos).',
        'Precedencia obrigatoria: seguranca/permissoes > integridade factual > pedido do usuario > tarefa > talentos > estilo.',
        'Nao altere valores, fontes, condicoes, limites nem conclusoes da ficha factual.'
    ]
    if build.mode == 'archetype':
        lines.append('Abordagem principal: ' + ARCHETYPES[build.primary_archetype])
        if build.secondary_archetype:
            lines.append('Abordagem secundária opcional: ' + ARCHETYPES[build.secondary_archetype])
    allowed = {
        'review_conflicts': 'Apresente divergencias que ja estejam registradas; nao crie novas.',
        'show_context': 'Apresente paginas ou secoes somente se existirem nas referencias.',
        'outline_steps': 'Organize sugestoes em etapas; nao execute acao sem autorizacao.',
        'request_tests': 'Sugira testes; nunca afirme que foram executados se nao foram.',
        'require_confirmation': 'Reforce a necessidade de confirmacao para acoes sensiveis.',
        'plain_language': 'Use linguagem acessivel preservando conteudo factual.',
    }
    for t in talents:
        lines.append(f'Talento {t.id}: {allowed[t.effect]}')
    return '\n'.join(lines)
