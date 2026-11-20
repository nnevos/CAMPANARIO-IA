"""R2.1: observable provenance checks on typed, read-only brain results.

These checks do not prove the truth of a source, or make arbitrary third-party
brain adapters trusted. They reject inconsistent envelopes *before* a result
can be used as input to another brain or accepted by the factual compiler.
"""
from __future__ import annotations

from campanario.brains.contracts import BrainResult, BrainStatus
from campanario.chat.data_intent import DataAnalysisResult
from campanario.chat.local_library import LocalFactSheet


def validate_brain_result(result: BrainResult, *, brain_id: str, trace_id,
                          max_evidence: int, required_upstream: tuple[str, ...],
                          first_party: bool) -> bool:
    if not isinstance(result, BrainResult) or result.brain_id != brain_id or result.trace_id != trace_id:
        return False
    if (len(result.evidence_refs) > max_evidence or len(result.operations) > 8
            or len(result.upstream_evidence_ids) > max_evidence
            or len(set(result.upstream_evidence_ids)) != len(result.upstream_evidence_ids)):
        return False
    if (any(not isinstance(op, str) or not op or len(op) > 100 for op in result.operations)
            or len({ref.source_id for ref in result.evidence_refs}) != len(result.evidence_refs)):
        return False
    if result.status in {BrainStatus.FAILED, BrainStatus.UNAVAILABLE} and result.evidence_refs:
        return False
    if result.status == BrainStatus.COMPLETED and not result.operations:
        return False
    if first_party:
        if result.upstream_evidence_ids != required_upstream:
            return False
        if result.status == BrainStatus.COMPLETED:
            if not result.evidence_refs or result.guard is None:
                return False
            if brain_id == 'knowledge':
                if not isinstance(result.guard, LocalFactSheet) or result.guard.read_count < 1:
                    return False
                quotes = (result.guard.quote, *result.guard.conflicts)
                expected = {
                    (q.evidence_id or f'{q.document_id}:{q.page or 0}',
                     q.document_id, q.name, q.page, q.section, q.excerpt[:1800])
                    for q in quotes[:max_evidence]
                }
                return (result.operations == ('library.retrieve',)
                        and {(ref.source_id, ref.document_id, ref.title, ref.page,
                              ref.section, ref.excerpt) for ref in result.evidence_refs} == expected)
            if brain_id == 'analysis':
                if not isinstance(result.guard, DataAnalysisResult):
                    return False
                g = result.guard
                if g.status != 'grounded' or g.read_count < 1 or not g.source_id or not g.digest:
                    return False
                return (len(result.evidence_refs) == 1
                        and result.operations == ('data.inspect', 'data.' + g.operation)
                        and result.evidence_refs[0].source_id == f'analysis:{g.source_id}:{g.digest[:16]}'
                        and result.evidence_refs[0].document_id == g.source_id
                        and result.evidence_refs[0].title == g.source_name
                        and result.evidence_refs[0].excerpt == g.evidence_excerpt[:1800])
            return False
    return True


def trustworthy_upstream(result: BrainResult) -> tuple[str, ...]:
    """Only first-party read-only evidence is transferable to another worker.

    Successful status/operation strings alone are not proof of a real read.
    """
    if result.brain_id not in {'knowledge', 'analysis'}:
        return ()
    if result.status != BrainStatus.COMPLETED or not result.evidence_refs or not result.guard:
        return ()
    if not validate_brain_result(result, brain_id=result.brain_id,
                                  trace_id=result.trace_id, max_evidence=25,
                                  required_upstream=result.upstream_evidence_ids,
                                  first_party=True):
        return ()
    return tuple(ref.source_id for ref in result.evidence_refs)
