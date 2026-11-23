"""R2: conservative, deterministic consolidation of independent read-only runs.

This is NOT a semantic comparison engine. It presents separate tool answers
with honest provenance. It does not elevate one source to proof of another.
No LLM, network, database writes or model instructions are involved.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from campanario.brains.contracts import BrainResult, BrainStatus
from campanario.brains.router import BrainPlan
from campanario.chat.canonical_answer import (
    AnswerMode, CanonicalAnswer, CanonicalFact, SourceRecord,
    ToolExecution, VerificationStatus, build_canonical,
)
from campanario.chat.fact_sheet import (
    TurnFactSheet, FactClaim, FactSource, build_turn_fact_sheet,
)


@dataclass(frozen=True, slots=True)
class CollaborationSnapshot:
    fact_sheet: TurnFactSheet
    canonical: CanonicalAnswer
    # Useful for UI/telemetry; never a claim of semantic entailment.
    completed_steps: tuple[str, ...]
    incomplete_steps: tuple[str, ...]


def consolidate_read_only(request_id: UUID, question: str, plan: BrainPlan,
                          outcomes: tuple[BrainResult, ...]) -> CollaborationSnapshot:
    """Combine only already-observed, recognized retrieval/calc results.

    Each source must match an evidence ID emitted by the same completed worker.
    Partial/error/unavailable runs cannot create sources or factual claims.
    """
    if len(outcomes) != len(plan.steps) or len(outcomes) < 2:
        raise ValueError('collaboration needs all planned steps')
    if any(out.brain_id != step.brain_id or out.trace_id != plan.trace_id
           for step, out in zip(plan.steps, outcomes)):
        raise ValueError('collaboration results do not match the plan')
    facts: list[CanonicalFact] = []
    sources: list[SourceRecord] = []
    source_ledger: list[FactSource] = []
    claims: list[FactClaim] = []
    tool_executions: list[ToolExecution] = []
    answers: list[str] = []
    limitations: list[str] = []
    missing: list[str] = []
    contradictions: list[str] = []
    completed: list[str] = []
    incomplete: list[str] = []
    used_ids: set[str] = set()
    for step, result in zip(plan.steps, outcomes):
        label = 'Documento' if step.brain_id == 'knowledge' else 'Planilha'
        trustworthy = (result.status == BrainStatus.COMPLETED and bool(result.operations)
                       and bool(result.evidence_refs) and result.guard is not None)
        if trustworthy:
            ledger = build_turn_fact_sheet(request_id, question, result.guard,
                                            fact_lookup_requested=True)
            per_source = build_canonical(ledger, result.guard, brain_ids=(step.brain_id,))
            declared = {ref.source_id for ref in result.evidence_refs}
            trustworthy = (per_source.status in {
                VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_VERIFIED,
                VerificationStatus.CONFLICTING,
            } and bool(per_source.sources) and
                {s.source_id for s in per_source.sources}.issubset(declared) and
                not {s.source_id for s in per_source.sources} & used_ids and
                any(ex.status == 'success' and ex.read_count > 0
                    for ex in per_source.tool_executions))
        if not trustworthy:
            incomplete.append(step.brain_id)
            limitations.append(f'{label}: consulta sem evidência suficiente ou não concluída '
                               f'({result.error or ", ".join(result.warnings) or result.status.value}).')
            missing.append(step.brain_id)
            tool_executions.append(ToolExecution(
                operation=step.brain_id + '.run',
                status='error' if result.status == BrainStatus.FAILED else 'not_found',
                read_count=0))
            continue
        completed.append(step.brain_id)
        used_ids.update(s.source_id for s in per_source.sources)
        sources.extend(per_source.sources)
        source_ledger.extend(ledger.sources)
        claims.extend(ledger.claims)
        for fact in per_source.facts:
            facts.append(fact.model_copy(update={'fact_id': f'fact_{len(facts)+1:03d}'}))
        tool_executions.extend(per_source.tool_executions)
        limitations.extend(ledger.limitations)
        contradictions.extend(per_source.contradictions)
        # The answer comes from the deterministic, existing single-source builder.
        # Do not generate a new comparison, causal claim, or numerical result.
        answers.append(f'{label} ({step.brain_id}):\n{per_source.canonical_answer}')

    limitations.append('Os resultados foram colocados lado a lado; uma comparação '
                       'semântica entre documento e planilha ainda não foi executada.')
    if answers:
        combined_answer = ('Resultados das consultas independentes:\n\n' +
                           '\n\n'.join(answers) +
                           '\n\nLimite: não foi realizada comparação semântica entre as fontes.')
        if incomplete:
            combined_answer += '\nConsultas incompletas: ' + ', '.join(incomplete) + '.'
    else:
        combined_answer = ('Não foi possível recuperar evidências suficientes das '
                           'fontes solicitadas. Não vou inventar uma comparação.')
    if contradictions:
        status = VerificationStatus.CONFLICTING
    elif sources:
        # A document's assertion remains a claim, even beside a verified sum.
        status = VerificationStatus.PARTIALLY_VERIFIED
    elif any(r.status == BrainStatus.FAILED for r in outcomes):
        status = VerificationStatus.TOOL_ERROR
    else:
        status = VerificationStatus.NOT_FOUND
    ledger_status = ('conflict' if contradictions else 'supported' if sources else 'insufficient')
    sheet = TurnFactSheet(
        turn_id=request_id, question=question[:1000], subject=question[:200],
        status=ledger_status, origin='library' if sources else 'none',
        sources=tuple(source_ledger), claims=tuple(claims),
        limitations=tuple(dict.fromkeys(limitations)),
        extractive_answer=combined_answer if sources else None,
    )
    canonical = CanonicalAnswer(
        request_id=request_id, query=question[:1000], intent=plan.intent,
        mode=AnswerMode.GROUNDED, status=status, facts=tuple(facts),
        sources=tuple(sources), tool_executions=tuple(tool_executions),
        limitations=tuple(dict.fromkeys(limitations)),
        contradictions=tuple(contradictions), missing=tuple(missing),
        canonical_answer=combined_answer, brain_ids=tuple(completed),
    )
    return CollaborationSnapshot(sheet, canonical, tuple(completed), tuple(incomplete))


def consolidate_investigation_strategy(request_id: UUID, question: str, plan: BrainPlan,
                                       outcomes: tuple[BrainResult, ...]) -> CollaborationSnapshot:
    """Join reviews of an already-read source without double-counting shared citations.

    Each first-party result was validated by BrainExecutor; recheck the guard's
    canonical evidence before exposing review lines. This is not a model planner.
    """
    if len(outcomes) != len(plan.steps) or not outcomes or len(outcomes) > 3:
        raise ValueError('invalid review plan')
    if any(o.brain_id != step.brain_id or o.trace_id != plan.trace_id
           for o, step in zip(outcomes, plan.steps)):
        raise ValueError('review trace mismatch')
    candidate = None
    completed: list[str] = []
    incomplete: list[str] = []
    reviews: list[str] = []
    for o in outcomes:
        if o.status != BrainStatus.COMPLETED or o.guard is None or not o.evidence_refs:
            incomplete.append(o.brain_id)
            continue
        ledger = build_turn_fact_sheet(request_id, question, o.guard, fact_lookup_requested=True)
        record = build_canonical(ledger, o.guard, brain_ids=(o.brain_id,))
        if (record.status not in {VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_VERIFIED,
                                  VerificationStatus.CONFLICTING}
                or not record.sources or not {s.source_id for s in record.sources}.issubset(
                    {r.source_id for r in o.evidence_refs})):
            incomplete.append(o.brain_id)
            continue
        if candidate is None:
            candidate = (ledger, record)
        completed.append(o.brain_id)
        if o.report:
            reviews.extend(o.report)
    if candidate is None:
        ledger = build_turn_fact_sheet(request_id, question, None, fact_lookup_requested=True)
        canonical = build_canonical(ledger, None, brain_ids=tuple())
    else:
        ledger, canonical = candidate
        # Canonical facts remain from the independently verified primary source.
        # Review lines are deterministic navigation/conditional steps, not new facts.
        canonical = canonical.model_copy(update={
            'brain_ids': tuple(completed),
            'canonical_answer': canonical.canonical_answer +
                ('\n\n' + '\n'.join(reviews[:45]) if reviews else '') +
                ('\n\nConsultas incompletas: ' + ', '.join(incomplete) if incomplete else ''),
        })
    return CollaborationSnapshot(ledger, canonical, tuple(completed), tuple(incomplete))
