"""Shared brain executor: permissions, turn budget and bounded failure containment.

R1.1 does not turn third-party Python into trusted code. Only the two first-party
read-only adapters have an interruptible subprocess; other adapters retain the
historical extension interface and MUST NOT be used for untrusted input.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from time import monotonic, perf_counter

from campanario.brains.adapters import AnalysisBrain, KnowledgeBrain
from campanario.brains.contracts import BrainRequest, BrainResult, BrainStatus
from campanario.brains.isolation import WorkerFailure, execute_local_worker
from campanario.brains.registry import BrainRegistry
from campanario.brains.router import BrainPlan
from campanario.brains.result_validation import validate_brain_result, trustworthy_upstream

_LOG = logging.getLogger(__name__)
# Only infrastructure failures count; an empty or contradictory document is not
# a worker incident. Keeping the breaker in memory avoids changing Database.
_BREAKER_ERRORS = frozenset({
    'timeout', 'timeout_terminated', 'memory_limit_terminated', 'worker_failed',
    'worker_start_failed', 'invalid_worker_payload', 'invalid_brain_result',
    'worker_output_too_large', 'dependency_result_invalid',
})


class BrainExecutor:
    def __init__(self, registry: BrainRegistry, *, audit=None, permission_policy=None,
                 breaker_threshold: int = 3, breaker_window_seconds: float = 30,
                 breaker_cooldown_seconds: float = 20):
        if not 1 <= breaker_threshold <= 20:
            raise ValueError('invalid breaker threshold')
        if not 1 <= breaker_window_seconds <= 3600 or not 1 <= breaker_cooldown_seconds <= 3600:
            raise ValueError('invalid breaker interval')
        self.registry = registry
        self.audit = audit
        self.permission_policy = permission_policy
        self._threshold = breaker_threshold
        self._window = breaker_window_seconds
        self._cooldown = breaker_cooldown_seconds
        self._incidents: dict[str, list[float]] = {}
        self._open_until: dict[str, float] = {}

    def bind_permissions(self, permission_policy) -> None:
        """Bind the one runtime-owned PermissionPolicy after composition completes."""
        self.permission_policy = permission_policy

    def _authorized(self, brain, authorization) -> bool:
        if authorization is None:
            return False
        from campanario.runtime.permissions import PermissionDecision
        for scope in sorted(brain.definition.permission_scopes):
            try:
                decision = self.permission_policy.check(
                    scope, authorization, capability='brain.' + brain.definition.brain_id)
            except Exception as exc:
                _LOG.warning('brain_permission_check_failed error=%s', type(exc).__name__)
                return False
            if decision.decision != PermissionDecision.ALLOW:
                return False
        return True

    def _circuit_open(self, brain_id: str, now: float) -> bool:
        until = self._open_until.get(brain_id, 0.0)
        if until > now:
            return True
        if until:
            self._open_until.pop(brain_id, None)
            self._incidents.pop(brain_id, None)
        return False

    def _record_health(self, result: BrainResult, now: float) -> None:
        if result.error not in _BREAKER_ERRORS or result.status != BrainStatus.FAILED:
            if result.status in {BrainStatus.COMPLETED, BrainStatus.PARTIAL}:
                self._incidents.pop(result.brain_id, None)
            return
        recent = [t for t in self._incidents.get(result.brain_id, []) if now - t <= self._window]
        recent.append(now)
        self._incidents[result.brain_id] = recent
        if len(recent) >= self._threshold:
            self._open_until[result.brain_id] = now + self._cooldown
            self._incidents.pop(result.brain_id, None)

    def _audit(self, result: BrainResult, request: BrainRequest) -> None:
        if self.audit is not None:
            try:
                self.audit(record=result, request=request)
            except Exception as exc:
                _LOG.warning('brain_run_audit_failed brain=%s error_type=%s',
                             result.brain_id, type(exc).__name__)

    async def execute(self, plan: BrainPlan, request: BrainRequest, *, authorization=None) -> tuple[BrainResult, ...]:
        """One timeout budget for the *whole* plan, not once per selected brain.

        External task cancellation propagates, while the subprocess's finally
        block kills the child. No automatic retry can repeat a tool side effect.
        """
        # Multi-brain runs require a single, matching trace and intent; never
        # execute a partly forged plan under the identity of another request.
        if len(plan.steps) > 1 and (request.trace_id != plan.trace_id or request.intent != plan.intent):
            rejected = tuple(BrainResult(step.brain_id, BrainStatus.FAILED,
                                         request.trace_id, 0,
                                         error='plan_request_mismatch') for step in plan.steps)
            for result in rejected:
                self._audit(result, request)
            return rejected
        deadline = monotonic() + request.budget.timeout_seconds
        results = []
        for step in plan.steps:
            brain_id = step.brain_id
            start = perf_counter()
            # Only evidence IDs from executions actually completed in this plan.
            prior = {previous.brain_id: previous for previous in results}
            verified_upstream = tuple(dict.fromkeys(
                source_id
                for name in step.depends_on
                for source_id in trustworthy_upstream(prior[name])
            ))[:request.budget.max_evidence]
            dependency_unmet = bool(step.depends_on) and step.dependency_policy == 'required' and any(
                not trustworthy_upstream(prior[name]) for name in step.depends_on)
            bounded_request = replace(request, upstream_evidence_ids=verified_upstream,
                                      query=step.query_override or request.query)
            brain = self.registry.get(brain_id)
            if dependency_unmet:
                # Required dependencies fail closed. Optional dependencies remain
                # independent (e.g., a calculation when the document was absent).
                result = BrainResult(brain_id, BrainStatus.UNAVAILABLE, request.trace_id, 0,
                                     error='dependency_not_met')
            elif brain is None:
                result = BrainResult(brain_id, BrainStatus.UNAVAILABLE, request.trace_id, 0,
                                     error='not_installed')
            elif (not step.required_scopes.issubset(request.permission_scopes)
                  or not brain.definition.permission_scopes.issubset(request.permission_scopes)
                  or not brain.definition.permission_scopes.issubset(step.required_scopes)):
                result = BrainResult(brain_id, BrainStatus.FAILED, request.trace_id, 0,
                                     error='permission_denied')
            elif self.permission_policy is not None and not self._authorized(brain, authorization):
                result = BrainResult(brain_id, BrainStatus.FAILED, request.trace_id, 0,
                                     error='permission_denied')
            elif self._circuit_open(brain_id, monotonic()):
                result = BrainResult(brain_id, BrainStatus.UNAVAILABLE, request.trace_id, 0,
                                     error='circuit_open')
            else:
                remaining = deadline - monotonic()
                if remaining < 0.1:
                    result = BrainResult(brain_id, BrainStatus.FAILED, request.trace_id, 0,
                                         error='turn_budget_exhausted')
                else:
                    try:
                        bounded = replace(bounded_request, budget=replace(
                            request.budget, timeout_seconds=min(remaining, request.budget.timeout_seconds)))
                        if isinstance(brain, (KnowledgeBrain, AnalysisBrain)):
                            result = await execute_local_worker(brain_id, brain.database, bounded)
                        else:
                            # Compatibility with trusted, in-process test adapters.
                            # A timed-out thread is NOT a security boundary.
                            result = await asyncio.wait_for(
                                asyncio.to_thread(brain.execute, bounded), timeout=bounded.budget.timeout_seconds)
                        if not validate_brain_result(
                                result, brain_id=brain_id, trace_id=request.trace_id,
                                max_evidence=request.budget.max_evidence,
                                required_upstream=verified_upstream,
                                first_party=isinstance(brain, (KnowledgeBrain, AnalysisBrain))):
                            result = BrainResult(brain_id, BrainStatus.FAILED, request.trace_id, 0,
                                                 error='invalid_brain_result')
                    except WorkerFailure as exc:
                        result = BrainResult(brain_id, BrainStatus.FAILED, request.trace_id, 0,
                                             error=str(exc))
                    except TimeoutError:
                        result = BrainResult(brain_id, BrainStatus.FAILED, request.trace_id, 0,
                                             error='timeout')
                    except Exception as exc:
                        result = BrainResult(brain_id, BrainStatus.FAILED, request.trace_id, 0,
                                             error=type(exc).__name__)
            # Older trusted in-process adapters do not know the new R2 metadata.
            # Only immutable observed IDs are attached; this does not promote data.
            if (brain is not None and not isinstance(brain, (KnowledgeBrain, AnalysisBrain))
                    and result.status in {BrainStatus.COMPLETED, BrainStatus.PARTIAL}):
                result = replace(result, upstream_evidence_ids=verified_upstream)
            result = replace(result, elapsed_ms=round((perf_counter() - start) * 1000, 2))
            results.append(result)
            self._record_health(result, monotonic())
            self._audit(result, request)
        return tuple(results)
