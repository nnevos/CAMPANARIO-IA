"""R1.1 defensive tests; no personal files, network or cloud resources."""
from __future__ import annotations

import asyncio
import socket
import sys
import time
from dataclasses import dataclass
from uuid import uuid4

import pytest

from campanario.brains.contracts import (
    BrainDefinition, BrainRequest, BrainResult, BrainStatus, ResourceBudget,
)
from campanario.brains.executor import BrainExecutor
from campanario.brains.isolation import _worker_environment, execute_local_worker
from campanario.brains.network_guard import deny_worker_network
from campanario.brains.registry import BrainRegistry
from campanario.brains.router import BrainPlan


@dataclass
class SyntheticBrain:
    definition: BrainDefinition
    delay: float = 0.0
    failure: str | None = None
    calls: int = 0

    def health_check(self):
        return True, 'synthetic'

    def execute(self, request):
        self.calls += 1
        if self.delay:
            time.sleep(self.delay)
        return BrainResult(self.definition.brain_id,
                           BrainStatus.FAILED if self.failure else BrainStatus.COMPLETED,
                           request.trace_id, 0, error=self.failure,
                           operations=('synthetic.test',))


def make_brain(name, *, delay=0, failure=None):
    return SyntheticBrain(BrainDefinition(name, 'Synthetic', ('test',), installed=True),
                          delay=delay, failure=failure)


@pytest.mark.asyncio
async def test_timeout_budget_applies_to_entire_plan_not_each_brain(monkeypatch):
    import campanario.brains.executor as executor_module
    logical_time = [10.0]
    monkeypatch.setattr(executor_module, 'monotonic', lambda: logical_time[0])
    brains = {f'b{i}': make_brain(f'b{i}') for i in range(3)}
    for brain in brains.values():
        actual = brain.execute
        def run(request, actual=actual):
            logical_time[0] += 0.12
            return actual(request)
        brain.execute = run
    executor = BrainExecutor(BrainRegistry(brains))
    trace = uuid4()
    plan = BrainPlan(trace, 'synthetic', tuple(brains), ('explicit',))
    request = BrainRequest(uuid4(), None, 'synthetic', 'synthetic',
                           trace_id=trace, budget=ResourceBudget(timeout_seconds=0.3))
    begun = time.monotonic()
    results = await executor.execute(plan, request)
    assert [result.status for result in results[:2]] == [BrainStatus.COMPLETED] * 2
    assert results[2].error == 'turn_budget_exhausted'
    assert brains['b2'].calls == 0
    assert time.monotonic() - begun < 0.5


@pytest.mark.asyncio
async def test_circuit_breaker_opens_on_worker_faults_and_recovers(monkeypatch):
    import campanario.brains.executor as module
    now = [1000.0]
    monkeypatch.setattr(module, 'monotonic', lambda: now[0])
    brain = make_brain('broken', failure='worker_failed')
    executor = BrainExecutor(BrainRegistry({'broken': brain}), breaker_threshold=3,
                             breaker_cooldown_seconds=2)
    trace = uuid4()
    plan = BrainPlan(trace, 'test', ('broken',), ('test',))
    request = BrainRequest(uuid4(), None, 'query', 'test', trace_id=trace)
    assert [(await executor.execute(plan, request))[0].error for _ in range(3)] == ['worker_failed'] * 3
    fourth, = await executor.execute(plan, request)
    assert fourth.error == 'circuit_open' and brain.calls == 3
    now[0] += 2.1
    fifth, = await executor.execute(plan, request)
    assert fifth.error == 'worker_failed' and brain.calls == 4


@pytest.mark.asyncio
async def test_denied_or_missing_source_does_not_trigger_breaker():
    brain = make_brain('safe')
    executor = BrainExecutor(BrainRegistry({'safe': brain}), breaker_threshold=1)
    trace = uuid4()
    plan = BrainPlan(trace, 'test', ('safe',), ('test',))
    forbidden = BrainRequest(uuid4(), None, 'query', 'test', trace_id=trace,
                             permission_scopes=frozenset())
    for _ in range(4):
        result, = await executor.execute(plan, forbidden)
        assert result.error == 'permission_denied'
    result, = await executor.execute(plan, BrainRequest(uuid4(), None, 'query', 'test', trace_id=trace))
    assert result.status == BrainStatus.COMPLETED and brain.calls == 1


def test_worker_environment_drops_tokens_proxy_and_external_pythonpath(tmp_path):
    inherited = {'PATH': '/somewhere', 'PYTHONPATH': '/untrusted/module',
                 'CAMPANARIO_SECRET_TOKEN': 'sensitive', 'HTTP_PROXY': 'http://private',
                 'AWS_SECRET_ACCESS_KEY': 'sensitive', 'HOME': '/test'}
    env = _worker_environment(tmp_path, inherited)
    assert env['PYTHONPATH'] == str(tmp_path)
    assert env['HOME'] == '/test'
    assert 'CAMPANARIO_SECRET_TOKEN' not in env
    assert 'HTTP_PROXY' not in env
    assert 'AWS_SECRET_ACCESS_KEY' not in env
    assert env['PYTHONNOUSERSITE'] == '1'


def test_worker_network_guard_denies_python_socket_calls_and_restores():
    original = socket.socket.connect
    with deny_worker_network():
        with socket.socket() as connection:
            with pytest.raises(PermissionError, match='worker_network_disabled'):
                connection.connect(('127.0.0.1', 9))
        with pytest.raises(PermissionError, match='worker_network_disabled'):
            socket.getaddrinfo('localhost', 80)
    assert socket.socket.connect is original


@pytest.mark.asyncio
async def test_external_cancellation_kills_worker_process(tmp_path, monkeypatch):
    import psutil
    import campanario.brains.isolation as isolation
    real_spawn = isolation.asyncio.create_subprocess_exec
    pids = []

    async def sleeping_spawn(*args, **kwargs):
        process = await real_spawn(sys.executable, '-c', 'import time; time.sleep(30)',
                                   stdin=kwargs['stdin'], stdout=kwargs['stdout'],
                                   stderr=kwargs['stderr'], env=kwargs['env'],
                                   start_new_session=kwargs.get('start_new_session', False))
        pids.append(process.pid)
        return process

    monkeypatch.setattr(isolation.asyncio, 'create_subprocess_exec', sleeping_spawn)
    db = tmp_path / 'simulated.db'
    db.write_bytes(b'SQLite format 3\x00')
    req = BrainRequest(uuid4(), None, 'query', 'document_lookup',
                       budget=ResourceBudget(timeout_seconds=10))
    task = asyncio.create_task(execute_local_worker('knowledge', db, req))
    await asyncio.sleep(0.12)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert pids
    for pid in pids:
        assert not psutil.pid_exists(pid) or psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
