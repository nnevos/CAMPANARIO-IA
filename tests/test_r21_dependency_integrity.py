"""R2.1: contracts, real provenance, optional vs mandatory dependencies."""
from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import uuid4

import pytest

from campanario.brains.contracts import (
    BrainDefinition, BrainRequest, BrainResult, BrainStatus, EvidenceRef,
)
from campanario.brains.executor import BrainExecutor
from campanario.brains.registry import BrainRegistry
from campanario.brains.router import BrainPlan, BrainStep, CapabilityRouter
from campanario.brains.result_validation import validate_brain_result, trustworthy_upstream
from campanario.chat.document_intent import DocumentRequest
from campanario.utilities.service import UtilityService


@dataclass
class CounterBrain:
    definition: BrainDefinition
    calls: int = 0
    evidence: tuple[EvidenceRef, ...] = ()

    def health_check(self):
        return True, 'synthetic'

    def execute(self, request):
        self.calls += 1
        return BrainResult(self.definition.brain_id, BrainStatus.COMPLETED,
                           request.trace_id, 0, self.evidence,
                           operations=('synthetic.test',))


def custom(brain_id, evidence=()):
    return CounterBrain(BrainDefinition(brain_id, brain_id, ('test',), installed=True),
                        evidence=evidence)


def mixed(question):
    return CapabilityRouter().plan(question, document_request=DocumentRequest(question, 'protocolo'))


def imported(util, name, content):
    target = util.roots[0] / name
    target.write_text(content, encoding='utf-8')
    outcome = util.run('library.import', {'path': str(target), 'confirm': True})
    assert outcome['status'] == 'success'


def required(plan):
    steps = list(plan.steps)
    steps[1] = replace(steps[1], dependency_policy='required')
    return replace(plan, steps=tuple(steps))


def test_contracts_reject_unknown_dependency_policies_and_input_types():
    with pytest.raises(ValueError, match='dependency policy'):
        BrainStep('knowledge', 'ler', 'explicit', dependency_policy='unsafe')
    with pytest.raises(ValueError, match='input contract'):
        BrainStep('knowledge', 'ler', 'explicit', input_contract='execute_python')
    with pytest.raises(ValueError, match='output contract'):
        BrainStep('knowledge', 'ler', 'explicit', output_contract='shell_command')
    with pytest.raises(ValueError, match='requires dependencies'):
        BrainStep('knowledge', 'ler', 'explicit', input_contract='user_query_plus_prior_evidence_metadata')


@pytest.mark.asyncio
async def test_required_dependency_is_skipped_without_running_downstream():
    a, b = custom('a'), custom('b')
    trace = uuid4()
    plan = BrainPlan(trace, 'test', ('a', 'b'), ('explicit', 'explicit'), (
        BrainStep('a', 'before', 'explicit'),
        BrainStep('b', 'after', 'explicit', depends_on=('a',), dependency_policy='required'),
    ))
    req = BrainRequest(uuid4(), None, 'hello', 'test', trace_id=trace)
    results = await BrainExecutor(BrainRegistry({'a': a, 'b': b})).execute(plan, req)
    assert results[0].status == BrainStatus.COMPLETED
    # A completed synthetic adapter is not proof of actual evidence.
    assert results[1].error == 'dependency_not_met'
    assert b.calls == 0
    assert not results[1].evidence_refs
    assert plan.public()['steps'][1]['dependency_policy'] == 'required'


@pytest.mark.asyncio
async def test_optional_dependency_keeps_independent_task_running():
    a, b = custom('a'), custom('b')
    trace = uuid4()
    plan = BrainPlan(trace, 'test', ('a', 'b'), ('explicit', 'explicit'), (
        BrainStep('a', 'before', 'explicit'),
        BrainStep('b', 'after', 'explicit', depends_on=('a',)),
    ))
    out = await BrainExecutor(BrainRegistry({'a': a, 'b': b})).execute(
        plan, BrainRequest(uuid4(), None, 'hello', 'test', trace_id=trace))
    assert [r.status for r in out] == [BrainStatus.COMPLETED, BrainStatus.COMPLETED]
    assert b.calls == 1
    assert out[1].upstream_evidence_ids == ()


@pytest.mark.asyncio
async def test_mismatched_plan_trace_or_intent_never_runs_workers():
    a, b = custom('a'), custom('b')
    trace = uuid4()
    plan = BrainPlan(trace, 'test', ('a', 'b'), ('explicit', 'explicit'))
    executor = BrainExecutor(BrainRegistry({'a': a, 'b': b}))
    for request in [BrainRequest(uuid4(), None, 'hello', 'test'),
                    BrainRequest(uuid4(), None, 'hello', 'incorrect', trace_id=trace)]:
        outcomes = await executor.execute(plan, request)
        assert [r.error for r in outcomes] == ['plan_request_mismatch', 'plan_request_mismatch']
    assert not a.calls and not b.calls


def test_forged_evidence_and_invalid_worker_claims_rejected():
    trace = uuid4()
    forged = BrainResult('knowledge', BrainStatus.COMPLETED, trace, 1,
                         evidence_refs=(EvidenceRef('fake:123', '123', 'Fake', 'Inventado'),),
                         operations=('library.retrieve',))
    assert not validate_brain_result(forged, brain_id='knowledge', trace_id=trace,
                                     max_evidence=8, required_upstream=(), first_party=True)
    assert trustworthy_upstream(forged) == ()
    duplicate = BrainResult('mock', BrainStatus.COMPLETED, trace, 1,
                            evidence_refs=(EvidenceRef('same', '1', 'Source', 'text'),
                                           EvidenceRef('same', '2', 'Source', 'text')),
                            operations=('mock.read',))
    assert not validate_brain_result(duplicate, brain_id='mock', trace_id=trace,
                                     max_evidence=8, required_upstream=(), first_party=False)
    failed_with_fake_source = BrainResult('mock', BrainStatus.FAILED, trace, 1,
                            evidence_refs=(EvidenceRef('s1', '1', 'T', 'Text'),))
    assert not validate_brain_result(failed_with_fake_source, brain_id='mock',
                                     trace_id=trace, max_evidence=8,
                                     required_upstream=(), first_party=False)


@pytest.mark.asyncio
async def test_required_dependency_real_document_and_csv(tmp_path):
    util = UtilityService(tmp_path / 'data')
    imported(util, 'protocolo.md', '# Protocolo\n\nA entrega depende de aprovação formal.\n')
    imported(util, 'vendas.csv', 'produto,faturamento\nA,100\nB,200\n')
    query = 'Compare o documento de protocolo com a planilha vendas.csv e calcule o faturamento total.'
    plan = required(mixed(query))
    request = BrainRequest(uuid4(), None, query, plan.intent, document_hint='protocolo',
                           trace_id=plan.trace_id)
    outputs = await BrainExecutor(BrainRegistry.local(util.db)).execute(plan, request)
    assert all(r.status == BrainStatus.COMPLETED for r in outputs), [r.public() for r in outputs]
    assert outputs[1].upstream_evidence_ids == tuple(r.source_id for r in outputs[0].evidence_refs)
    assert trustworthy_upstream(outputs[0])
    assert '300' in outputs[1].guard.verified_answer
    assert all(r.trace_id == plan.trace_id for r in outputs)


@pytest.mark.asyncio
async def test_required_dependency_with_absent_document_preserves_csv_safety(tmp_path):
    util = UtilityService(tmp_path / 'data')
    imported(util, 'vendas.csv', 'produto,faturamento\nA,100\nB,200\n')
    query = 'Compare o documento de protocolo com a planilha vendas.csv e calcule o faturamento total.'
    plan = required(mixed(query))
    request = BrainRequest(uuid4(), None, query, plan.intent,
                           document_hint='protocolo', trace_id=plan.trace_id)
    outputs = await BrainExecutor(BrainRegistry.local(util.db)).execute(plan, request)
    assert outputs[0].status == BrainStatus.PARTIAL
    assert outputs[1].status == BrainStatus.UNAVAILABLE
    assert outputs[1].error == 'dependency_not_met'
    assert all(not o.evidence_refs for o in outputs)


@pytest.mark.asyncio
async def test_optional_dependency_with_absent_document_still_computes(tmp_path):
    util = UtilityService(tmp_path / 'data')
    imported(util, 'vendas.csv', 'produto,faturamento\nA,100\nB,200\n')
    query = 'Compare o documento de protocolo com a planilha vendas.csv e calcule o faturamento total.'
    plan = mixed(query)
    request = BrainRequest(uuid4(), None, query, plan.intent,
                           document_hint='protocolo', trace_id=plan.trace_id)
    outputs = await BrainExecutor(BrainRegistry.local(util.db)).execute(plan, request)
    assert outputs[0].status == BrainStatus.PARTIAL
    assert outputs[1].status == BrainStatus.COMPLETED
    assert outputs[1].upstream_evidence_ids == ()
    assert '300' in outputs[1].guard.verified_answer

@pytest.mark.asyncio
async def test_opt_in_runtime_utility_registry_denies_missing_identity_and_write_without_approval(tmp_path):
    from campanario.runtime.capabilities import CapabilityRegistry
    from campanario.runtime.events import RuntimeEventBus
    from campanario.runtime.permissions import (
        AuthorizationContext, PermissionCheck, PermissionDecision,
        PermissionDeniedError, PermissionConfirmationRequired,
    )
    from campanario.utilities.integration import register_utilities
    from campanario.utilities.service import UtilityService

    class Policy:
        def check(self, permission, context, **kwargs):
            decision = PermissionDecision.CONFIRM if permission == 'utilities.write' else PermissionDecision.ALLOW
            return PermissionCheck(decision=decision, permission=permission,
                                   reason='mock policy', confirmation_id=uuid4() if decision == PermissionDecision.CONFIRM else None)

    util = UtilityService(tmp_path / 'utilities')
    registry = CapabilityRegistry(RuntimeEventBus(uuid4()), Policy(),
                                  require_explicit_authorization=True)
    register_utilities(registry, util)
    with pytest.raises(PermissionDeniedError, match='explicit authorization'):
        await registry.execute('notes.save', {'title': 'nao salvar', 'confirm': True})
    with pytest.raises(PermissionDeniedError, match='explicit authorization'):
        await registry.execute('notes.list')
    assert util.run('notes.list', {})['result']['count'] == 0
    user = AuthorizationContext(principal_kind='local_user', principal_id='user', session_active=True)
    readable = await registry.execute('notes.list', {}, authorization=user)
    assert readable.output['status'] == 'success'
    with pytest.raises(PermissionConfirmationRequired):
        await registry.execute('notes.save', {'title': 'nao salvar', 'confirm': True}, authorization=user)
    assert util.run('notes.list', {})['result']['count'] == 0

@pytest.mark.asyncio
async def test_real_runtime_v9_flag_enables_strict_utility_authorization(tmp_path):
    from campanario.composition import build_runtime
    from campanario.config import Settings
    from campanario.runtime.permissions import PermissionDeniedError

    runtime = build_runtime(
        Settings(brains_v9_enabled=True, semantic_memory_enabled=False,
                 model_name='fake', data_dir=tmp_path),
        database_url=f'sqlite:///{tmp_path / "runtime.sqlite"}', create_schema=True)
    assert runtime.tools._require_explicit_authorization is True
    with pytest.raises(PermissionDeniedError, match='authorization context required'):
        await runtime.tools.execute('notes.list', {})
