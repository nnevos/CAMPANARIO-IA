"""R2 read-only sequenced plans with provenance and honest partial failures."""
from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from campanario.agents.router import AgentRouter
from campanario.agents.profiles import default_agent_registry
from campanario.brains.router import BrainPlan, BrainStep, CapabilityRouter
from campanario.brains.contracts import BrainRequest, BrainResult, BrainStatus
from campanario.brains.executor import BrainExecutor
from campanario.brains.registry import BrainRegistry
from campanario.brains.collaboration import consolidate_read_only
from campanario.chat.canonical_answer import VerificationStatus
from campanario.chat.document_intent import DocumentRequest
from campanario.utilities.service import UtilityService


def _import(util, name, content):
    path = util.roots[0] / name
    path.write_text(content, encoding='utf-8')
    outcome = util.run('library.import', {'path': str(path), 'confirm': True})
    assert outcome['status'] == 'success', outcome
    return outcome['result']


def _plan(question):
    return CapabilityRouter().plan(question,
        document_request=DocumentRequest(question, 'protocolo'))


def test_r2_plan_structure_cannot_reorder_cycle_or_overgrant():
    trace = uuid4()
    steps = (BrainStep('knowledge', 'Ler fonte', 'explicit'),
             BrainStep('analysis', 'Calcular', 'explicit', ('knowledge',)))
    plan = BrainPlan(trace, 'document_and_data', ('knowledge', 'analysis'),
                     ('explicit', 'explicit'), steps)
    assert plan.steps[1].depends_on == ('knowledge',)
    assert plan.public()['steps'][1]['required_scopes'] == ['library:read']
    with pytest.raises(ValueError):
        BrainPlan(trace, 'test', ('knowledge', 'analysis'), (), tuple(reversed(steps)))
    with pytest.raises(ValueError):
        BrainPlan(trace, 'test', ('knowledge',), (),
                  (BrainStep('knowledge', 'Ler', 'explicit', ('analysis',)),))
    with pytest.raises(ValueError):
        BrainStep('knowledge', 'Ler', 'explicit', ('knowledge',))
    with pytest.raises(ValueError):
        BrainPlan(trace, 'test', ('knowledge', 'analysis', 'other', 'more'), ())


def test_r2_deterministic_selection_and_speaker_isolation():
    q = 'Compare o documento de protocolo com a planilha de vendas e calcule o faturamento total.'
    plan = _plan(q)
    assert plan.brain_ids == ('knowledge', 'analysis')
    assert plan.intent == 'document_and_data'
    assert CapabilityRouter().plan('Oi, Morgana').brain_ids == ()
    assert CapabilityRouter().plan('O que diz o documento?', document_request=DocumentRequest('texto')).brain_ids == ('knowledge',)
    assert CapabilityRouter().plan('Calcule o faturamento total da planilha').brain_ids == ('analysis',)
    assert AgentRouter(default_agent_registry()).resolve('Todd, ' + q, 'morgana').profile.id == 'todd'


@pytest.mark.asyncio
async def test_r2_real_sequential_workers_and_consolidation(tmp_path):
    util = UtilityService(tmp_path / 'util')
    doc = _import(util, 'protocolo.md', '# Protocolo\n\nA entrega depende de aprovação formal.\n')
    table = _import(util, 'vendas.csv', 'produto,faturamento\nA,100\nB,200\n')
    q = 'Compare o documento de protocolo com a planilha vendas.csv e calcule o faturamento total.'
    plan = _plan(q)
    req = BrainRequest(uuid4(), None, q, plan.intent,
                       document_hint='protocolo', trace_id=plan.trace_id)
    outputs = await BrainExecutor(BrainRegistry.local(util.db)).execute(plan, req)
    assert len(outputs) == 2
    assert outputs[0].status == outputs[1].status == BrainStatus.COMPLETED, [o.public() for o in outputs]
    assert outputs[1].upstream_evidence_ids == tuple(e.source_id for e in outputs[0].evidence_refs)
    assert outputs[0].evidence_refs[0].document_id == doc['id']
    assert outputs[1].evidence_refs[0].document_id == table['id']
    snapshot = consolidate_read_only(req.request_id, q, plan, outputs)
    assert snapshot.canonical.status == VerificationStatus.PARTIALLY_VERIFIED
    assert {s.document_id for s in snapshot.canonical.sources} == {doc['id'], table['id']}
    assert len(snapshot.canonical.tool_executions) == 2
    assert snapshot.completed_steps == ('knowledge', 'analysis')
    assert '300' in snapshot.canonical.canonical_answer
    assert 'aprovação formal' in snapshot.canonical.canonical_answer
    assert 'não foi realizada comparação semântica' in snapshot.canonical.canonical_answer
    assert snapshot.fact_sheet.extractive_answer == snapshot.canonical.canonical_answer


@pytest.mark.asyncio
async def test_r2_partial_missing_document_never_claims_comparison(tmp_path):
    util = UtilityService(tmp_path / 'util')
    _import(util, 'vendas.csv', 'produto,faturamento\nA,100\nB,200\n')
    q = 'Compare o documento de protocolo com a planilha vendas.csv e calcule o faturamento total.'
    plan = _plan(q)
    req = BrainRequest(uuid4(), None, q, plan.intent,
                       document_hint='protocolo', trace_id=plan.trace_id)
    outputs = await BrainExecutor(BrainRegistry.local(util.db)).execute(plan, req)
    assert outputs[0].status == BrainStatus.PARTIAL
    assert outputs[1].upstream_evidence_ids == ()
    result = consolidate_read_only(req.request_id, q, plan, outputs)
    assert result.incomplete_steps == ('knowledge',)
    assert result.completed_steps == ('analysis',)
    assert result.canonical.status == VerificationStatus.PARTIALLY_VERIFIED
    assert all(src.kind != 'imported_document' for src in result.canonical.sources)
    assert 'Consultas incompletas: knowledge' in result.canonical.canonical_answer
    assert '300' in result.canonical.canonical_answer


@pytest.mark.asyncio
async def test_r2_permission_denied_no_evidence_propagation(tmp_path):
    util = UtilityService(tmp_path / 'util')
    _import(util, 'protocolo.md', '# Protocolo\n\nTexto.\n')
    _import(util, 'vendas.csv', 'produto,faturamento\nA,10\n')
    q = 'Compare o documento de protocolo com a planilha vendas.csv e calcule o faturamento total.'
    plan = _plan(q)
    req = BrainRequest(uuid4(), None, q, plan.intent,
                       document_hint='protocolo', trace_id=plan.trace_id,
                       permission_scopes=frozenset())
    outputs = await BrainExecutor(BrainRegistry.local(util.db)).execute(plan, req)
    assert all(o.error == 'permission_denied' for o in outputs)
    assert not any(o.evidence_refs or o.upstream_evidence_ids for o in outputs)
    snapshot = consolidate_read_only(req.request_id, q, plan, outputs)
    assert snapshot.canonical.status == VerificationStatus.TOOL_ERROR
    assert not snapshot.canonical.facts and not snapshot.canonical.sources


def test_r2_reject_forged_source_status_and_trace():
    q = 'Compare documentos e planilhas'
    plan = _plan(q)
    assert plan.brain_ids == ('knowledge', 'analysis')
    bogus = BrainResult('knowledge', BrainStatus.COMPLETED, uuid4(), 1,
                        operations=('library.retrieve',))
    other = BrainResult('analysis', BrainStatus.PARTIAL, plan.trace_id, 1)
    with pytest.raises(ValueError, match='do not match'):
        consolidate_read_only(uuid4(), q, plan, (bogus, other))

@pytest.mark.asyncio
async def test_r2_chat_uses_combined_canonical_not_first_brain_only(tmp_path):
    from campanario.chat.service import ChatService
    from campanario.chat.context import RecentMessagesContextManager
    from campanario.chat.local_library import ReadOnlyLocalLibrary
    from test_chat_service import InMemorySessions, InMemoryMessages
    from test_v91_expression import ScriptedProvider

    util = UtilityService(tmp_path / 'util')
    _import(util, 'protocolo.md', '# Protocolo\n\nA entrega depende de aprovação formal.\n')
    _import(util, 'vendas.csv', 'produto,faturamento\nA,100\nB,200\n')
    provider = ScriptedProvider(['O total foi 999 e não precisa de aprovação.'])
    chat = ChatService(InMemorySessions(), InMemoryMessages(), provider,
                       RecentMessagesContextManager(10), 'local',
                       local_library=ReadOnlyLocalLibrary(util.db),
                       grounded_synthesis=False)
    chat.configure_brains(BrainExecutor(BrainRegistry.local(util.db)), CapabilityRouter(), None)
    session = chat.create_session()
    q = 'Compare o documento de protocolo com a planilha vendas.csv e calcule o faturamento total.'
    async for _ in chat.stream_turn(session.id, q):
        pass
    report = chat.get_factual_debug(session.id)
    assert report is not None
    assert report['brain_plan']['selected'] == ['knowledge', 'analysis']
    assert report['collaboration']['semantic_comparison_performed'] is False
    assert len(report['sources']) == 2
    assert '300' in report['canonical_answer']
    assert '999' not in report['canonical_answer']
    assert all(run['trace_id'] == report['brain_plan']['trace_id'] for run in report['brain_runs'])
    messages = chat.get_messages(session.id)
    assert any('300' in m.content and 'aprovação' in m.content for m in messages)
    assert not any('999' in m.content for m in messages)
