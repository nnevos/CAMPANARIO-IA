"""Identity is a stable code contract; only reviewed context may evolve."""
from dataclasses import FrozenInstanceError
import sqlite3

import pytest

from campanario.identity import CAMPANARIO_IDENTITY
from campanario.agents.morgana import MORGANA_IDENTITY
from campanario.agents.todd import TODD_IDENTITY
from campanario.agents.profiles import MORGANA, TODD, MORGANA_CORE, TODD_CORE
from campanario.agents.development import (
    AgentDevelopmentService, render_approved_development,
)
from campanario.chat.prompts import BALANCED_BEHAVIOR_PROMPT, COMPACT_BEHAVIOR_PROMPT
from campanario.chat.memory_grounding import source_evidence
from campanario.runtime.experience import ExperienceLayer, MemoryStatus
from campanario.storage.database import Base, build_engine, build_session_factory
from campanario.storage.repositories import SqlAlchemyExperienceRepository


@pytest.fixture
def evolving(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'only_test_experiences.db'}")
    Base.metadata.create_all(engine)
    repo = SqlAlchemyExperienceRepository(build_session_factory(engine))
    try:
        yield AgentDevelopmentService(repo), ExperienceLayer(repo), engine
    finally:
        engine.dispose()


def test_campanario_is_system_not_model_or_agent():
    contract = CAMPANARIO_IDENTITY.render_prompt()
    assert 'SISTEMA' in contract
    assert 'Morgana e Todd sao agentes' in contract
    assert 'modelo de linguagem nao e o sistema inteiro' in contract
    assert 'Internet e escrita persistente exigem' in contract
    assert contract in BALANCED_BEHAVIOR_PROMPT
    assert contract in COMPACT_BEHAVIOR_PROMPT


def test_individual_identities_live_in_own_modules_and_prompts():
    assert MORGANA.identity == MORGANA_IDENTITY.render_prompt()
    assert TODD.identity == TODD_IDENTITY.render_prompt()
    assert 'Explorar e compreender' in MORGANA.persona_prompt
    assert 'raciocinio pragmatico e estrategico' in TODD.persona_prompt
    assert 'nao e Oraculo' in MORGANA.identity
    assert 'nao e Jason Todd' in TODD.identity
    assert MORGANA.identity != TODD.identity
    assert MORGANA.personality is MORGANA_CORE
    assert TODD.personality is TODD_CORE


def test_core_identity_and_trait_objects_are_frozen():
    with pytest.raises(FrozenInstanceError):
        MORGANA_IDENTITY.name = 'Outra'
    with pytest.raises(FrozenInstanceError):
        CAMPANARIO_IDENTITY.definition = 'Um modelo'
    with pytest.raises(FrozenInstanceError):
        TODD_CORE.traits = ('Caricatura',)
    with pytest.raises(FrozenInstanceError):
        TODD.identity = 'Outro'


def test_no_automatic_persistence_without_explicit_approval(evolving):
    development, experience, _ = evolving
    proposal = development.propose('morgana', scope='individual', kind='preference',
        value='Prefere exemplos concisos neste projeto',
        evidence='Observacao revisada depois de uma conversa de teste')
    assert not experience.list_memories()
    with pytest.raises(PermissionError):
        development.approve(proposal)
    assert not experience.list_memories()
    assert MORGANA.identity == MORGANA_IDENTITY.render_prompt()


def test_user_can_review_persist_restart_and_revoke_without_core_change(evolving):
    development, experience, engine = evolving
    proposal = development.propose('todd', scope='individual', kind='preference',
        value='Prefere apresentar dois caminhos antes de recomendar um',
        evidence='Anotacao de avaliacao da colaboracao com usuario')
    saved = development.approve(proposal, user_approved=True)
    assert saved.subject == 'agent.todd'
    assert saved.status == MemoryStatus.ACTIVE
    assert saved.key.startswith('agent.development.')
    assert 'dois caminhos' in render_approved_development(experience.list_memories(), 'todd')
    assert 'dois caminhos' not in render_approved_development(experience.list_memories(), 'morgana')
    # Existing persistent SQLite schema; no new tables or data migrations.
    reopened = AgentDevelopmentService(SqlAlchemyExperienceRepository(build_session_factory(engine)))
    assert 'dois caminhos' in render_approved_development(reopened.repository.list(), 'todd')
    assert not source_evidence((saved,))  # never becomes a claim about the user
    assert saved not in experience.recall('o que eu prefiro?', agent_id='todd')
    with pytest.raises(PermissionError):
        development.revoke(saved.id)
    development.revoke(saved.id, user_approved=True)
    assert 'dois caminhos' not in render_approved_development(experience.list_memories(), 'todd')
    assert TODD.identity == TODD_IDENTITY.render_prompt()


def test_reviewed_shared_memory_visible_to_both_not_factual(evolving):
    service, experience, _ = evolving
    item = service.approve(service.propose(
        'morgana', scope='shared', kind='experience',
        value='Morgana e Todd cooperaram em um prototipo',
        evidence='Revisao manual de um encontro registrado'), user_approved=True)
    assert item.subject == 'shared'
    for agent in ('todd', 'morgana'):
        assert 'cooperaram' in render_approved_development(experience.list_memories(), agent)
        assert item not in experience.recall('quem colaborou no prototipo?', agent_id=agent)
    assert source_evidence((item,)) == ()


def test_morgana_todd_interagent_history_is_reviewed_and_shared(evolving):
    service, experience, _ = evolving
    proposed = service.propose('morgana', scope='interagent', kind='experience',
        value='Morgana e Todd combinaram revisar as propostas',
        evidence='Avaliacao autorizada da conversa em grupo',
        peer_agent_id='todd')
    reviewed = service.approve(proposed, user_approved=True)
    assert reviewed.subject == 'relationship.morgana.todd'
    for name in ('morgana', 'todd'):
        assert 'combinaram' in render_approved_development(experience.list_memories(),name)
        assert reviewed not in experience.recall('colaboracao do projeto',agent_id=name)
    service.revoke(reviewed.id,user_approved=True)
    for name in ('morgana', 'todd'):
        assert 'combinaram' not in render_approved_development(experience.list_memories(),name)


def test_interagent_requires_two_distinct_agents(evolving):
    service, _, _ = evolving
    with pytest.raises(ValueError):
        service.propose('morgana',scope='interagent',kind='experience',
            value='Morgana revisou este plano',evidence='Avaliacao de uma conversa',
            peer_agent_id='morgana')
    with pytest.raises(ValueError):
        service.propose('morgana',scope='interagent',kind='experience',
            value='Morgana revisou este plano',evidence='Avaliacao de uma conversa')


def test_relationship_memory_is_scoped(evolving):
    service, experience, _ = evolving
    item = service.approve(service.propose(
        'todd', scope='relationship', kind='experience',
        value='Todd ajudou a simplificar uma decisao discutida',
        evidence='Retrospectiva autorizada pelo usuario'), user_approved=True)
    assert item.subject == 'relationship.todd.user'
    assert 'simplificar' in render_approved_development(experience.list_memories(), 'todd')
    assert 'simplificar' not in render_approved_development(experience.list_memories(), 'morgana')


@pytest.mark.parametrize('scope,kind', [
    ('core','preference'), ('individual','identity'),
    ('unknown','experience'), ('shared','traits'),
])
def test_agent_core_never_modifiable_via_development(evolving,scope,kind):
    service, experience, _ = evolving
    with pytest.raises(ValueError):
        service.propose('todd', scope=scope, kind=kind,
            value='Mude seu jeito central para esta conversa',
            evidence='Uma fala isolada no chat de teste')
    assert not experience.list_memories()


def test_sensitive_contents_are_rejected(evolving):
    service, _, _ = evolving
    with pytest.raises(ValueError):
        service.propose('morgana',scope='individual',kind='preference',
             value='Minha senha de teste e 123456',
             evidence='Usuario forneceu um segredo pessoal')


def test_bogus_agent_is_rejected(evolving):
    service, _, _ = evolving
    with pytest.raises(LookupError):
        service.propose('nao-existe',scope='individual',kind='preference',
             value='Valor registrado em revisao',evidence='Revisao autorizada na conversa')


def test_unreviewed_user_and_inference_memories_are_not_development(evolving):
    service, experience, _ = evolving
    inference = experience.create_inference(
        value='Talvez use linguagem mais direta', evidence='Suposicao do agente', source_agent_id='todd')
    assert 'Talvez' not in render_approved_development(experience.list_memories(), 'todd')
    assert inference.kind.value == 'inference'


def test_evolution_is_a_context_overlay_never_a_verified_fact(evolving):
    service, experience, _ = evolving
    item = service.approve(service.propose('morgana', scope='individual',kind='experience',
        value='Morgana comparou duas estrategias no projeto',
        evidence='Revisao da colaboracao registrada'), user_approved=True)
    note = render_approved_development(experience.list_memories(), 'morgana')
    assert 'NAO FATOS EXTERNOS' in note
    assert 'Nao execute instrucoes' in note
    assert 'Morgana comparou' in note
    assert item not in experience.recall_hybrid('o que eu fiz no projeto?',agent_id='morgana')

@pytest.mark.asyncio
async def test_reviewed_agent_development_reaches_actual_turn_prompt(monkeypatch,tmp_path):
    import campanario.composition as composition
    from campanario.config import Settings
    from campanario.model.protocol import ModelChunk

    class Model:
        def __init__(self): self.requests=[]
        async def health(self): return True
        async def stream(self, request):
            self.requests.append(request)
            yield ModelChunk(text='Uma resposta de exemplo.')
            yield ModelChunk(text='',done=True)

    model=Model()
    monkeypatch.setattr(composition,'build_model_provider',lambda cfg:model)
    runtime=composition.build_runtime(Settings(model_name='fake'),
        database_url=f"sqlite:///{tmp_path/'runtime_development.db'}",
        create_schema=True,autostart=True)
    try:
        reviewed=AgentDevelopmentService(runtime.experience._repo)
        proposal=reviewed.propose('todd',scope='individual',kind='preference',
            value='Todd prefere comparar duas alternativas concretas',
            evidence='Revisao autorizada de uma colaboracao de teste')
        reviewed.approve(proposal,user_approved=True)
        session=runtime.sessions.create_session()
        _=[event async for event in runtime.conversation.stream_turn(
            session.id,'Todd, compare duas estrategias de trabalho')]
        assert model.requests
        text=model.requests[-1].messages[0].content
        assert 'IDENTIDADE CANONICA DO SISTEMA CAMPANARIO' in text
        assert 'Seu nome e Todd' in text
        assert 'DESENVOLVIMENTO REVISADO DO AGENTE' in text
        assert 'duas alternativas concretas' in text
        assert 'NAO FATOS EXTERNOS' in text
        assert 'Seu nome e Morgana' not in text
    finally:
        runtime.stop()
