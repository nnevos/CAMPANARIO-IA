"""V9 integrated tests. Real utility DBs, fake local LLM, no canned lore."""
from __future__ import annotations

from dataclasses import replace
from io import BytesIO
import json
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select

from campanario.agents.profiles import default_agent_registry, MORGANA, TODD
from campanario.agents.router import AgentRouter
from campanario.brains import (
    BrainRegistry, CapabilityRouter, BrainRequest, BrainExecutor, BrainStatus, ResourceBudget,
)
from campanario.brains.builds import AgentBuild, ARCHETYPES, TALENTS, select_talents, render_build_note
from campanario.brains.agents import make_agent_profile
from campanario.brains.package import export_package, import_package
from campanario.brains.models import AgentBuildRow, BrainRunRow
from campanario.brains.store import BuildStore, BuildConflict
from campanario.chat.document_intent import DocumentRequest
from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.canonical_answer import build_canonical, VerificationStatus
from campanario.chat.grounded_expression import validate_expression
from campanario.chat.service import ChatService
from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.storage.database import Base, build_session_factory
from campanario.storage import models  # noqa: F401
from campanario.utilities.service import UtilityService
from test_chat_service import InMemoryMessages, InMemorySessions
from test_v91_expression import ScriptedProvider


@pytest.fixture
def util(tmp_path):
    return UtilityService(tmp_path / 'utility')


@pytest.fixture
def store(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "campanario.db"}')
    Base.metadata.create_all(engine)
    return BuildStore(build_session_factory(engine))


def imported(util, name, content):
    src = util.roots[0] / name
    src.write_text(content, encoding='utf-8')
    outcome = util.run('library.import', {'path': str(src), 'confirm': True})
    assert outcome['status'] == 'success', outcome
    return outcome['result']


def test_speaker_router_independent_from_capability_router():
    speaker = AgentRouter(default_agent_registry())
    capability = CapabilityRouter()
    a = speaker.resolve('Todd, procure no Database: Ocultista 20% NEX?', 'morgana')
    b = capability.plan('Todd, procure no Database: Ocultista 20% NEX?',
                        document_request=DocumentRequest('Ocultista 20% de NEX?'))
    assert a.profile.id == 'todd'
    assert b.brain_ids == ('knowledge',)
    assert speaker.resolve('Olá, tudo bem?', 'todd').profile.id == 'todd'
    assert capability.plan('Olá, Morgana').brain_ids == ()
    assert len(BrainRegistry.local(None).catalog()) == 8
    assert all(x['status'] == 'unavailable' for x in BrainRegistry.local(None).catalog())


@pytest.mark.asyncio
async def test_real_document_nex_retrieval_and_canonical(util):
    doc = imported(util, 'Ordem Paranormal Exemplo.md',
                   '# Ocultista\n\n## Ocultista 20% de NEX\n\nO personagem recebe a Marca de Teste 2.\n')
    executor = BrainExecutor(BrainRegistry.local(util.db))
    plan = CapabilityRouter().plan('O que Ocultista ganha em 20% de NEX?',
                                   document_request=DocumentRequest('O que Ocultista ganha em 20% de NEX?', 'Ordem Paranormal'))
    request = BrainRequest(uuid4(), uuid4(), 'O que Ocultista ganha em 20% de NEX?',
                           plan.intent, document_hint='Ordem Paranormal', trace_id=plan.trace_id)
    output, = await executor.execute(plan, request)
    assert output.status == BrainStatus.COMPLETED
    assert output.operations == ('library.retrieve',)
    assert output.evidence_refs[0].document_id == doc['id']
    assert output.evidence_refs[0].source_id.startswith('library:')
    assert 'Marca de Teste 2' in output.evidence_refs[0].excerpt
    sheet = build_turn_fact_sheet(request.request_id, request.query, output.guard,
                                  fact_lookup_requested=True)
    canonical = build_canonical(sheet, output.guard, brain_ids=('knowledge',))
    assert canonical.status == VerificationStatus.PARTIALLY_VERIFIED
    assert canonical.brain_ids == ('knowledge',)
    assert canonical.sources[0].source_id == output.evidence_refs[0].source_id
    assert not validate_expression(canonical, 'O personagem recebe 900 poderes novos!').accepted
    assert 'Ordem Paranormal' in canonical.canonical_answer
    assert doc['id'] in output.evidence_refs[0].document_id


@pytest.mark.asyncio
async def test_missing_source_and_permission_denied_fail_closed(util):
    missing = BrainRequest(uuid4(), None, 'Ocultista NEX 20%?', 'document_lookup',
                           'livro inexistente')
    executor = BrainExecutor(BrainRegistry.local(util.db))
    plan = CapabilityRouter().plan(missing.query, document_request=DocumentRequest(missing.query))
    out, = await executor.execute(plan, missing)
    assert out.status == BrainStatus.PARTIAL and not out.evidence_refs
    denied = replace(missing, permission_scopes=frozenset())
    no, = await executor.execute(plan, denied)
    assert no.status == BrainStatus.FAILED and no.error == 'permission_denied'
    sheet = build_turn_fact_sheet(uuid4(), missing.query, out.guard, fact_lookup_requested=True)
    record = build_canonical(sheet, out.guard)
    assert record.status == VerificationStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_csv_and_xlsx_calculated_without_llm(util):
    imported(util, 'faturamento.csv', 'produto,faturamento\nA,100\nB,200\n')
    executor = BrainExecutor(BrainRegistry.local(util.db))
    q = 'Analise esta planilha e me diga o faturamento total.'
    plan = CapabilityRouter().plan(q)
    request = BrainRequest(uuid4(), None, q, plan.intent)
    res, = await executor.execute(plan, request)
    assert res.status == BrainStatus.COMPLETED and res.evidence_refs
    assert '300' in res.guard.verified_answer
    sheet = build_turn_fact_sheet(request.request_id, q, res.guard)
    canonical = build_canonical(sheet, res.guard, brain_ids=('analysis',))
    assert canonical.status == VerificationStatus.VERIFIED
    assert canonical.sources[0].source_id == res.evidence_refs[0].source_id
    assert not validate_expression(canonical, 'Soma: 900.').accepted
    # Ensure XLSX is read via imported original, not a text snapshot.
    openpyxl = pytest.importorskip('openpyxl')
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(['faturamento']); ws.append([6]); ws.append([7])
    xlsx = util.roots[0] / 'faturamento_extra.xlsx'; wb.save(xlsx)
    assert util.run('library.import', {'path': str(xlsx), 'confirm': True})['status'] == 'success'
    q2 = 'Analise faturamento_extra.xlsx e me diga o faturamento total.'
    req2 = BrainRequest(uuid4(), None, q2, 'data_analysis')
    result2, = await executor.execute(CapabilityRouter().plan(q2), req2)
    assert result2.status == BrainStatus.COMPLETED
    assert '13' in result2.guard.verified_answer
    assert result2.evidence_refs[0].title.endswith('extra.xlsx')


def test_builds_archetypes_talents_do_not_grant_permissions_or_mutate_facts(store):
    assert len(ARCHETYPES) == 8 and len(TALENTS) == 6
    build = AgentBuild(agent_id='morgana', mode='archetype', primary_archetype='investigador',
                       secondary_archetype='oraculo', talents=('olhar_investigativo', 'leitura_profunda', 'sentinela'))
    picked = select_talents(build, intent='document_lookup', text='Consulte o documento e explique.')
    assert len(picked) == 2
    assert 'permiss' not in ' '.join(t.effect for t in picked)
    assert 'seguranca/permissoes > integridade factual' in render_build_note(build, picked)
    recorded = store.save(build, expected_revision=1)
    assert recorded.revision == 2
    assert store.get('morgana').talents == build.talents
    with pytest.raises(BuildConflict):
        store.save(build, expected_revision=1)
    assert store.get('todd').talents == ()
    assert AgentBuild(agent_id='morgana', mode='free').mode == 'free'
    with pytest.raises(ValueError):
        AgentBuild(agent_id='morgana', primary_archetype='guardiao')
    with pytest.raises(ValueError):
        AgentBuild(agent_id='morgana', mode='archetype', primary_archetype='guardiao', secondary_archetype='guardiao')


def test_build_storage_is_separate_from_sessions_memories(store):
    from campanario.storage.models import ChatSessionRow, MessageRow, ExperienceMemoryRow
    from datetime import datetime, UTC
    factory = store._session_factory
    with factory.begin() as db:
        db.add(ChatSessionRow(id=str(uuid4()), created_at=datetime.now(UTC),
                              updated_at=datetime.now(UTC), primary_agent_id='morgana'))
        db.add(ExperienceMemoryRow(id=str(uuid4()), kind='preference', subject='agent', key='example',
            value='personal', confidence=0.75, source='user', status='active', evidence='utterance',
            created_at=datetime.now(UTC), updated_at=datetime.now(UTC), last_confirmed_at=datetime.now(UTC)))
    before = (store._session_factory().query(ChatSessionRow).count(),
              store._session_factory().query(ExperienceMemoryRow).count())
    store.save(AgentBuild(agent_id='morgana', mode='archetype', primary_archetype='arauto'))
    after = (store._session_factory().query(ChatSessionRow).count(),
             store._session_factory().query(ExperienceMemoryRow).count())
    assert before == after == (1, 1)


def test_new_agent_neutral_profile_no_clone():
    build = AgentBuild(agent_id='iris', display_name='Iris', identity_description='Nova assistente de testes')
    agent = make_agent_profile(build)
    assert agent.personality != MORGANA.personality and agent.personality != TODD.personality
    registry = default_agent_registry(); registry.register(agent)
    assert registry.get('iris').name == 'Iris'
    assert AgentRouter(registry).resolve('teste', 'iris').profile.id == 'iris'
    assert registry.get('morgana') is MORGANA


def test_package_hardened_and_no_secrets():
    build = AgentBuild(agent_id='morgana', mode='archetype', primary_archetype='estrategista',
                       talents=('plano_de_acao',))
    raw = export_package(build)
    assert import_package(raw) == build
    for banned in ('memories', 'credentials', 'documents', 'permission_scopes', 'token'):
        assert banned.encode() not in raw
    cases = [
        {'../evil.py': b'import os'},
        {'assets/run.py': b'print(123)'},
        {'assets/safe.png': b'not checked', 'assets/payload.sh': b'x'},
    ]
    for extra in cases:
        with BytesIO() as buffer:
            with ZipFile(buffer, 'w') as archive:
                archive.writestr('manifest.json', json.dumps({'format': 'campagent/1', 'build': build.model_dump(mode='json'), 'assets': {}}))
                for key, value in extra.items(): archive.writestr(key, value)
            with pytest.raises(ValueError): import_package(buffer.getvalue())
    with pytest.raises(ValueError): import_package(b'bad zip')


@pytest.mark.asyncio
async def test_brain_audit_persisted(store, util):
    imported(util, 'dados.csv', 'produto,faturamento\nA,12\nB,13\n')
    executor = BrainExecutor(BrainRegistry.local(util.db), audit=store.record_run)
    text = 'Calcule o faturamento total dessa planilha.'
    plan = CapabilityRouter().plan(text)
    req = BrainRequest(uuid4(), None, text, plan.intent, trace_id=plan.trace_id)
    out, = await executor.execute(plan, req)
    assert store.runs()[0]['trace_id'] == str(out.trace_id)
    assert store.runs()[0]['evidence_count'] == 1
    assert out.elapsed_ms >= 0
    assert store.runs()[0]['status'] == 'completed'


@pytest.mark.asyncio
async def test_flag_off_keeps_existing_chat_and_flag_on_records_trace(util, store):
    imported(util, 'Ordem Paranormal.md', '# Ocultista\n\n## Ocultista 20% NEX\n\nRecebe Marca Exemplo.\n')
    provider = ScriptedProvider(['O personagem recebe Marca Exemplo.'])
    def make():
        return ChatService(InMemorySessions(), InMemoryMessages(), provider,
                           RecentMessagesContextManager(10), 'local',
                           local_library=ReadOnlyLocalLibrary(util.db), grounded_synthesis=False)
    legacy = make()
    assert legacy._brain_executor is None
    s = legacy.create_session()
    async for _ in legacy.stream_turn(s.id, 'Olá, Morgana'): pass
    assert legacy.get_messages(s.id)
    modern = make()
    modern.configure_brains(BrainExecutor(BrainRegistry.local(util.db), audit=store.record_run),
                            CapabilityRouter(), store)
    s2 = modern.create_session()
    questions = ['O que Ocultista ganha em 20% de NEX?',
                 'No Database existe um documento de Ordem Paranormal com essas informações.',
                 'Então o que Ocultista ganha em 20% de NEX?']
    for question in questions:
        async for _ in modern.stream_turn(s2.id, question): pass
    trace = modern.get_factual_debug(s2.id)
    assert trace and trace['brain_plan']['selected'] == ['knowledge']
    assert trace['brain_runs'][0]['status'] == 'completed'
    assert trace['sources'] and trace['sources'][0]['title'].endswith('.md')
    assert 'Marca Exemplo' in trace['canonical_answer']
    assert store.runs()[0]['brain_id'] == 'knowledge'
    assert all('desconhecido' not in m.content.lower() for m in modern.get_messages(s2.id))


def test_v9_migration_upgrade_backfill_downgrade_keeps_legacy_rows(tmp_path):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect
    from types import SimpleNamespace
    from campanario.storage.models import ChatSessionRow
    from datetime import datetime, UTC
    location = tmp_path / 'old.db'
    settings = SimpleNamespace(database_path=location)
    cfg = Config()
    cfg.set_main_option('script_location', str(Path(__file__).resolve().parents[1] / 'src/campanario/migrations'))
    cfg.attributes['campanario_settings'] = settings
    cfg.attributes['configure_logging'] = False
    command.upgrade(cfg, '0009')
    engine = create_engine(f'sqlite:///{location}')
    with engine.begin() as db:
        db.execute(ChatSessionRow.__table__.insert().values(
            id=str(uuid4()), primary_agent_id='todd', title='Sessão preservada',
            status='active', created_at=datetime.now(UTC), updated_at=datetime.now(UTC)))
    command.upgrade(cfg, 'head')
    tables = set(inspect(engine).get_table_names())
    assert {'agent_builds', 'brain_runs', 'brain_registry', 'talent_definitions'} <= tables
    with engine.connect() as conn:
        from sqlalchemy import text
        builds = conn.execute(text('SELECT agent_id, config FROM agent_builds')).fetchall()
        assert {b.agent_id for b in builds} == {'morgana', 'todd'}
        assert all(json.loads(b.config)['mode'] == 'free' for b in builds)
        assert conn.execute(text('SELECT COUNT(*) FROM chat_sessions')).scalar() == 1
    command.downgrade(cfg, '0009')
    assert 'agent_builds' not in inspect(engine).get_table_names()
    with engine.connect() as conn:
        assert conn.execute(text('SELECT COUNT(*) FROM chat_sessions')).scalar() == 1


def test_v9_composition_loads_custom_profile_on_restart(tmp_path):
    from campanario.config import Settings
    from campanario.composition import build_chat_stack
    settings = Settings(_env_file=None, model_name='local',
        data_dir=tmp_path, brains_v9_enabled=True, semantic_memory_enabled=False,
        library_semantic_enabled=False)
    db = f'sqlite:///{tmp_path / "stack.db"}'
    service, _ = build_chat_stack(settings, database_url=db, create_schema=True)
    assert service._brain_executor is not None
    created = AgentBuild(agent_id='iris', display_name='Iris',
                         identity_description='Agente neutro de laboratório')
    service._build_store.save(created)
    service2, _ = build_chat_stack(settings, database_url=db, create_schema=True)
    assert service2._agents.get('iris').name == 'Iris'
    assert service2.default_agent_id == 'morgana'
    assert service2._agents.get('todd').personality == TODD.personality
    service3, _ = build_chat_stack(settings.model_copy(update={'brains_v9_enabled': False}),
                                   database_url=db, create_schema=True)
    assert service3._brain_executor is None
    assert {p.id for p in service3.list_agents()} == {'morgana', 'todd'}


def test_v9_local_api_catalog_forge_preview_disabled_and_remote(monkeypatch, store, util):
    from types import SimpleNamespace
    import campanario.brains.api as brain_api
    from campanario.main import app
    imported(util, 'Ordem Paranormal.md', '# Ocultista\n\n20% de NEX concede Marca Teste.\n')
    service = ChatService(InMemorySessions(), InMemoryMessages(), ScriptedProvider(['a']),
                          RecentMessagesContextManager(10), 'local',
                          local_library=ReadOnlyLocalLibrary(util.db))
    service.configure_brains(BrainExecutor(BrainRegistry.local(util.db), audit=store.record_run),
                             CapabilityRouter(), store)
    monkeypatch.setattr(brain_api, 'get_settings', lambda: SimpleNamespace(brains_v9_enabled=True))
    monkeypatch.setattr(brain_api, '_service', lambda: service)
    client = TestClient(app)
    catalog = client.get('/api/v1/brains/catalog')
    assert catalog.status_code == 200
    assert len(catalog.json()['brains']) == 8
    assert client.get('/api/v1/brains/builds/morgana').status_code == 200
    build = AgentBuild(agent_id='morgana', mode='archetype', primary_archetype='oraculo')
    saved = client.put('/api/v1/brains/builds/morgana',
                       json={'build': build.model_dump(mode='json'), 'expected_revision': 1})
    assert saved.status_code == 200 and saved.json()['revision'] == 2
    bad = client.put('/api/v1/brains/builds/morgana',
                     json={'build': build.model_dump(mode='json'), 'expected_revision': 1})
    assert bad.status_code == 409
    add = client.post('/api/v1/brains/agents', json=AgentBuild(
        agent_id='iris', display_name='Iris').model_dump(mode='json'))
    assert add.status_code == 201
    assert any(a['id'] == 'iris' for a in client.get('/api/v1/brains/catalog').json()['agents'])
    test = client.post('/api/v1/brains/preview', json={
        'query': 'O que ganha Ocultista em 20% NEX?', 'brain_id': 'knowledge',
        'document_hint': 'Ordem Paranormal', 'agent_id': 'morgana'})
    assert test.status_code == 200, test.text
    assert test.json()['evidence'] and '20%' in test.json()['evidence'][0]['excerpt']
    assert test.json()['runs'][0]['status'] == 'completed'
    assert client.get('/api/v1/brains/runs').json()['items']
    exported = client.get('/api/v1/brains/builds/morgana/export')
    assert exported.status_code == 200 and import_package(exported.content).primary_archetype == 'oraculo'
    inspected = client.post('/api/v1/brains/package/inspect', data=exported.content,
                            headers={'Content-Type': 'application/octet-stream'})
    assert inspected.status_code == 200 and not inspected.json()['imported']
    assert client.post('/api/v1/brains/package/inspect', data=b'BADZIP',
                       headers={'Content-Type': 'application/octet-stream'}).status_code == 422
    assert client.post('/api/v1/brains/preview', json={'query': 'Apagar tudo', 'brain_id': 'programming'}).status_code == 422
    # The global security boundary denies remote clients even for GET.
    from campanario.app.security import local_request
    assert not local_request({'client': ('192.0.2.4', 12), 'headers': [(b'host', b'localhost')]})


def test_v9_dark_matter_ui_has_functional_endpoints_and_mobile_css():
    root = Path(__file__).resolve().parents[1] / 'src/campanario/web'
    js = (root / 'ferramentas.js').read_text(encoding='utf-8')
    css = (root / 'ferramentas.css').read_text(encoding='utf-8')
    assert "views.cerebros=async" in js and "views.forja=async" in js
    assert "fetch('/api/v1/brains/package/inspect'" in js
    assert "api('/api/v1/brains/preview'" in js
    assert '@media(max-width:690px)' in css
    assert '.v9-talent-list' in css
