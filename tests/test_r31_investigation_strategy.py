"""R3.1 operational read-only investigation and strategy acceptance cases."""
from __future__ import annotations

from dataclasses import replace
from uuid import uuid4
import pytest

from campanario.brains import BrainExecutor, BrainRegistry, BrainRequest, BrainStatus, CapabilityRouter
from campanario.brains.router import BrainPlan, BrainStep
from campanario.brains.collaboration import consolidate_investigation_strategy
from campanario.brains.result_validation import validate_brain_result
from campanario.brains.investigation import structured_report
from campanario.chat.document_intent import DocumentRequest
from campanario.utilities.service import UtilityService


@pytest.fixture
def imported_database(tmp_path):
    service = UtilityService(tmp_path / 'utility')
    file = service.roots[0] / 'cenario.md'
    file.write_text('Relatório sintético. O prazo contratual acordado é 20 dias. '
                    'As duas equipes precisam revisar o contrato antes da decisão.', encoding='utf-8')
    result = service.run('library.import', {'path': str(file), 'confirm': True})
    assert result['status'] == 'success'
    return service.db


def req(plan, text):
    return BrainRequest(uuid4(), None, text, plan.intent, trace_id=plan.trace_id)


@pytest.mark.parametrize('brain_id', ['investigation', 'strategy'])
@pytest.mark.asyncio
async def test_operational_worker_reads_actual_database(imported_database, brain_id):
    plan = BrainPlan(uuid4(), 'read_only_preview', (brain_id,), ('explicit',),
                     (BrainStep(brain_id, 'revisão', 'explicit'),))
    result, = await BrainExecutor(BrainRegistry.local(imported_database)).execute(
        plan, req(plan, 'Qual é o prazo contratual acordado?'))
    assert result.status == BrainStatus.COMPLETED, result
    assert result.operations == ('library.retrieve', f'{brain_id}.review')
    assert result.evidence_refs and '20 dias' in result.evidence_refs[0].excerpt
    assert result.report
    assert result.report == structured_report(brain_id, result.evidence_refs)
    assert validate_brain_result(result, brain_id=brain_id, trace_id=plan.trace_id,
                                 max_evidence=8, required_upstream=(), first_party=True)
    if brain_id == 'strategy':
        assert any('Critério de parada' in item for item in result.report)
        assert any('Nenhuma ação foi executada' in item for item in result.report)
    else:
        assert any('Lacunas' in item for item in result.report)


@pytest.mark.asyncio
async def test_multibrain_plan_and_factual_consolidation(imported_database):
    text = 'Investigue o prazo contratual acordado e planeje uma estratégia.'
    plan = CapabilityRouter().plan(text)
    assert plan.brain_ids == ('investigation', 'strategy')
    out = await BrainExecutor(BrainRegistry.local(imported_database)).execute(plan, req(plan, text))
    assert all(x.status == BrainStatus.COMPLETED for x in out)
    snapshot = consolidate_investigation_strategy(uuid4(), text, plan, out)
    assert snapshot.completed_steps == ('investigation', 'strategy')
    assert snapshot.canonical.brain_ids == plan.brain_ids
    assert 'INVESTIGAÇÃO' in snapshot.canonical.canonical_answer
    assert 'ESTRATÉGIA' in snapshot.canonical.canonical_answer
    assert snapshot.canonical.sources
    assert snapshot.canonical.status.value == 'partially_verified'


@pytest.mark.parametrize('brain_id', ['investigation', 'strategy'])
@pytest.mark.asyncio
async def test_permission_missing_source_and_tampered_report(imported_database, brain_id, tmp_path):
    plan = BrainPlan(uuid4(), 'read_only_preview', (brain_id,), ('explicit',),
                     (BrainStep(brain_id, 'revisão', 'explicit'),))
    executor = BrainExecutor(BrainRegistry.local(imported_database))
    denied, = await executor.execute(plan, replace(req(plan, 'prazo contratual'),
                                                   permission_scopes=frozenset()))
    assert denied.status == BrainStatus.FAILED and denied.error == 'permission_denied'
    absent, = await BrainExecutor(BrainRegistry.local(tmp_path / 'missing.db')).execute(
        plan, req(plan, 'prazo contratual'))
    assert absent.status in {BrainStatus.UNAVAILABLE, BrainStatus.FAILED} and not absent.report
    good, = await executor.execute(plan, req(plan, 'prazo contratual'))
    assert good.status == BrainStatus.COMPLETED
    altered = replace(good, report=('Eu confirmei uma fraude e executei uma ação.',))
    assert not validate_brain_result(altered, brain_id=brain_id, trace_id=plan.trace_id,
                                     max_evidence=8, required_upstream=(), first_party=True)


def test_router_does_not_activate_for_plain_conversation():
    router = CapabilityRouter()
    assert router.plan('Bom dia, Morgana!').brain_ids == ()
    assert router.plan('O que você acha de histórias de detetive?').brain_ids == ()
    assert router.plan('Quero investigar um documento').brain_ids == ('investigation',)
    assert router.plan('Planeje uma estratégia com base na biblioteca').brain_ids == ('strategy',)
    catalog = BrainRegistry.local(None).catalog()
    assert len(catalog) == 8
    assert sum(x['installed'] for x in catalog) == 4


def test_investigation_numeric_conflict_only_independent_sources():
    from campanario.brains.contracts import EvidenceRef
    left = EvidenceRef(source_id='doc-a:1', document_id='doc-a', title='Contrato A',
                       excerpt='O prazo contratual acordado é 20 dias.')
    right = EvidenceRef(source_id='doc-b:1', document_id='doc-b', title='Contrato B',
                        excerpt='O prazo contratual acordado é 30 dias.')
    result = structured_report('investigation', (left, right))
    assert any('DIVERGÊNCIA NUMÉRICA' in x and '20' in x and '30' in x for x in result)
    assert not any('fraude' in x.lower() or 'culpa' in x.lower() for x in result)
    same_document = replace(right, document_id='doc-a')
    report = structured_report('investigation', (left, same_document))
    assert not any('DIVERGÊNCIA NUMÉRICA' in x for x in report)


def test_mixed_analysis_investigation_strategy_stays_within_three_steps():
    router = CapabilityRouter()
    plan = router.plan('Investigue a planilha CSV de faturamento, analise e planeje uma estratégia.')
    assert plan.brain_ids == ('analysis', 'investigation', 'strategy')
    assert all(s.required_scopes == frozenset({'library:read'}) for s in plan.steps)


def test_date_extraction_is_literal_not_a_claim_about_an_event():
    from campanario.brains.contracts import EvidenceRef
    item = EvidenceRef(source_id='file-a:1', document_id='file-a', title='Ata',
                       excerpt='Ata menciona 05/11/2026. Outra data inválida 99/12/2026.')
    report = structured_report('investigation', (item,))
    assert any('05/11/2026' in line and 'não inferidos' in line for line in report)
    assert not any('Data mencionada' in line and '99/12/2026' in line for line in report)


def test_strategy_blocks_choice_when_independent_numbers_conflict():
    from campanario.brains.contracts import EvidenceRef
    a = EvidenceRef(source_id='a', document_id='doc-a', title='A',
                    excerpt='O orçamento aprovado é 20 reais.')
    b = EvidenceRef(source_id='b', document_id='doc-b', title='B',
                    excerpt='O orçamento aprovado é 30 reais.')
    plan = structured_report('strategy', (a, b))
    assert any('BLOQUEANTE' in line for line in plan)
    assert any('Nenhuma ação' in line for line in plan)
