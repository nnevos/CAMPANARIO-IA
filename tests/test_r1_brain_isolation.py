"""R1 fault injection; no personal sqlite, models or real system files."""
from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from uuid import uuid4

import pytest

from campanario.brains.contracts import BrainDefinition, BrainRequest, BrainResult, BrainStatus, ResourceBudget
from campanario.brains.executor import BrainExecutor
from campanario.brains.isolation import WorkerFailure, decode_result, execute_local_worker
from campanario.brains.registry import BrainRegistry
from campanario.brains.router import BrainPlan
from campanario.runtime.permissions import AuthorizationContext, PermissionCheck, PermissionDecision


@dataclass
class StubBrain:
    definition = BrainDefinition('stub', 'Isolado', ('test',), installed=True)
    calls = 0

    def health_check(self):
        return True, 'ready'

    def execute(self, request):
        self.calls += 1
        return BrainResult('stub', BrainStatus.COMPLETED, request.trace_id, 0,
                           operations=('library.retrieve',))


class Policy:
    def __init__(self, allow=False):
        self.allow = allow
        self.calls = []

    def check(self, permission, context, *, capability=None, scope=None):
        self.calls.append((permission, context.principal_id, capability))
        return PermissionCheck(decision=PermissionDecision.ALLOW if self.allow else PermissionDecision.DENY,
                               permission=permission, reason='test')


@pytest.mark.asyncio
async def test_runtime_policy_denies_before_adapter_and_requires_context():
    adapter = StubBrain()
    policy = Policy(allow=True)
    executor = BrainExecutor(BrainRegistry({'stub': adapter}), permission_policy=policy)
    trace = uuid4()
    plan = BrainPlan(trace, 'test', ('stub',), ('test',))
    req = BrainRequest(uuid4(), None, 'read', 'test', trace_id=trace)
    result, = await executor.execute(plan, req)
    assert result.error == 'permission_denied' and adapter.calls == 0
    assert policy.calls == []
    auth = AuthorizationContext(principal_kind='local_user', principal_id='test', session_active=True)
    result, = await executor.execute(plan, req, authorization=auth)
    assert result.status == BrainStatus.COMPLETED and adapter.calls == 1
    assert policy.calls == [('library:read', 'test', 'brain.stub')]
    policy.allow = False
    result, = await executor.execute(plan, req, authorization=auth)
    assert result.error == 'permission_denied' and adapter.calls == 1


def test_worker_decoder_fails_closed_on_invalid_or_forged_objects():
    for raw in (b'', b'{}', b'not-json', b'[]', b'{"status":"completed","operations":[]}'):
        with pytest.raises(WorkerFailure):
            decode_result(raw)


@pytest.mark.asyncio
async def test_worker_timeout_actually_terminates_process(tmp_path, monkeypatch):
    import psutil
    import campanario.brains.isolation as isolation
    real_spawn = isolation.asyncio.create_subprocess_exec
    worker_pids = []

    async def fake_spawn(*args, **kwargs):
        child = await real_spawn(sys.executable, '-c', 'import time; time.sleep(30)',
                                 stdin=kwargs['stdin'], stdout=kwargs['stdout'],
                                 stderr=kwargs['stderr'],
                                 start_new_session=kwargs.get('start_new_session', False))
        worker_pids.append(child.pid)
        return child

    monkeypatch.setattr(isolation.asyncio, 'create_subprocess_exec', fake_spawn)
    db = tmp_path / 'test.db'
    db.write_bytes(b'SQLite format 3\x00')
    request = BrainRequest(uuid4(), None, 'question', 'document_lookup',
                           budget=ResourceBudget(timeout_seconds=0.35))
    with pytest.raises(WorkerFailure, match='timeout_terminated'):
        await execute_local_worker('knowledge', db, request)
    assert worker_pids
    assert all(not psutil.pid_exists(pid) or psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
               for pid in worker_pids)


@pytest.mark.asyncio
async def test_worker_memory_budget_interrupts_runaway_child(tmp_path, monkeypatch):
    import campanario.brains.isolation as isolation
    real_spawn = isolation.asyncio.create_subprocess_exec

    async def fake_spawn(*args, **kwargs):
        code = 'import time; blob = bytearray(220_000_000); time.sleep(10)'
        return await real_spawn(sys.executable, '-c', code,
                                stdin=kwargs['stdin'], stdout=kwargs['stdout'],
                                stderr=kwargs['stderr'],
                                start_new_session=kwargs.get('start_new_session', False))

    monkeypatch.setattr(isolation.asyncio, 'create_subprocess_exec', fake_spawn)
    db = tmp_path / 'test.db'
    db.write_bytes(b'SQLite format 3\x00')
    request = BrainRequest(uuid4(), None, 'question', 'data_analysis',
                           budget=ResourceBudget(timeout_seconds=4, max_memory_mb=128))
    with pytest.raises(WorkerFailure, match='memory_limit_terminated'):
        await execute_local_worker('analysis', db, request)


def test_budget_rejects_tiny_and_unbounded_memory():
    with pytest.raises(ValueError):
        ResourceBudget(max_memory_mb=1)
    with pytest.raises(ValueError):
        ResourceBudget(max_memory_mb=100_000)
