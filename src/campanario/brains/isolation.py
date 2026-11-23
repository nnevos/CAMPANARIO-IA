"""R1: bounded child process for the two *known*, read-only local brains.

This is process fault containment, NOT an OS security sandbox. The child runs
with the current user's filesystem privileges and inherits no extra app grants.
No shell, arbitrary code, user-provided path or pickle crosses the protocol.
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
from dataclasses import asdict
from pathlib import Path

from campanario.brains.contracts import BrainRequest, BrainResult, BrainStatus, EvidenceRef
from campanario.chat.data_intent import DataAnalysisResult
from campanario.chat.local_library import LibraryQuote, LocalFactSheet
from campanario.brains.investigation import InvestigationBrain, StrategyBrain

_MAX_STDOUT = 256_000


class WorkerFailure(Exception):
    """Typed process failure, safe to record without exposing file contents."""


def _guard_from_json(kind: str | None, guard: dict | None):
    if guard is None:
        return None
    if kind == 'data':
        return DataAnalysisResult(**guard)
    if kind == 'library':
        return LocalFactSheet(**{
            **guard,
            'quote': LibraryQuote(**guard['quote']),
            'conflicts': tuple(LibraryQuote(**q) for q in guard.get('conflicts', [])),
            'candidates': tuple(guard.get('candidates', [])),
        })
    raise WorkerFailure('invalid_worker_payload')


def encode_result(result: BrainResult) -> bytes:
    kind = ('library' if isinstance(result.guard, LocalFactSheet)
            else 'data' if isinstance(result.guard, DataAnalysisResult) else None)
    data = {
        'brain_id': result.brain_id, 'status': result.status.value,
        'trace_id': str(result.trace_id),
        'evidence_refs': [asdict(ref) for ref in result.evidence_refs],
        'operations': list(result.operations), 'warnings': list(result.warnings),
        'upstream_evidence_ids': list(result.upstream_evidence_ids),
        'error': result.error, 'report': list(result.report), 'guard_kind': kind,
        'guard': asdict(result.guard) if kind else None,
    }
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(raw) > _MAX_STDOUT:
        raise WorkerFailure('worker_output_too_large')
    return raw


def decode_result(raw: bytes) -> BrainResult:
    if not raw or len(raw) > _MAX_STDOUT:
        raise WorkerFailure('invalid_worker_payload')
    try:
        obj = json.loads(raw)
        if not isinstance(obj, dict) or not isinstance(obj.get('operations'), list):
            raise ValueError('invalid envelope')
        from uuid import UUID
        result = BrainResult(
            brain_id=obj['brain_id'], status=BrainStatus(obj['status']),
            trace_id=UUID(obj['trace_id']), elapsed_ms=0,
            evidence_refs=tuple(EvidenceRef(**ref) for ref in obj['evidence_refs']),
            operations=tuple(obj['operations']), warnings=tuple(obj['warnings']),
            upstream_evidence_ids=tuple(obj.get('upstream_evidence_ids', ())),
            error=obj.get('error'), report=tuple(obj.get('report', ())),
            guard=_guard_from_json(obj.get('guard_kind'), obj.get('guard')),
        )
        if (len(result.report) > 20 or any(not isinstance(line, str) or len(line) > 650
                                               for line in result.report)
                or len(result.operations) > 8 or len(result.evidence_refs) > 25
                or len(result.upstream_evidence_ids) > 25
                or any(not isinstance(s, str) or not 1 <= len(s) <= 280
                       for s in result.upstream_evidence_ids)):
            raise ValueError('invalid counts')
        return result
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise WorkerFailure('invalid_worker_payload') from exc


async def _terminate_tree(process):
    """Stop the worker and any children it spawned (best effort per OS)."""
    if process.returncode is not None:
        return
    try:
        import psutil
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except psutil.Error:
                pass
    except (ImportError, OSError):
        pass
    if os.name != 'nt':
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            process.kill()
    else:
        process.kill()
    try:
        await asyncio.wait_for(process.wait(), timeout=2)
    except TimeoutError:
        pass


def _worker_environment(src: Path, inherited: dict[str, str] | None = None) -> dict[str, str]:
    """Return a minimal child environment, never forwarding credential variables."""
    inherited = os.environ if inherited is None else inherited
    allowed = {'PATH', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'TEMP', 'TMP',
               'TMPDIR', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'HOME',
               'LANG', 'LC_ALL', 'VIRTUAL_ENV'}
    env = {key: value for key, value in inherited.items() if key.upper() in allowed}
    env['PYTHONPATH'] = str(src)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONNOUSERSITE'] = '1'
    return env


async def execute_local_worker(brain_id: str, database: Path | None, request: BrainRequest) -> BrainResult:
    """Execute only first-party read-only adapters; never accept executable input."""
    if brain_id not in {'knowledge', 'analysis', 'investigation', 'strategy'} or database is None:
        raise WorkerFailure('worker_not_supported')
    if getattr(sys, 'frozen', False):
        # Executables cannot safely be invoked as `python -m ...` without an
        # explicit sidecar interpreter. Deny rather than silently run in-process.
        raise WorkerFailure('worker_python_unavailable')
    if 'library:read' not in request.permission_scopes:
        raise WorkerFailure('permission_denied')
    try:
        import psutil  # noqa: F401 -- required for process-tree/RSS containment
    except ImportError as exc:
        raise WorkerFailure('process_monitor_unavailable') from exc
    wire = json.dumps({
        'brain_id': brain_id, 'database': str(Path(database).resolve()),
        'request_id': str(request.request_id),
        'conversation_id': str(request.conversation_id) if request.conversation_id else None,
        'trace_id': str(request.trace_id), 'query': request.query[:request.budget.max_input_chars],
        'intent': request.intent, 'document_hint': request.document_hint[:85],
        'timeout_seconds': request.budget.timeout_seconds,
        'max_evidence': request.budget.max_evidence,
        'max_input_chars': request.budget.max_input_chars,
        'max_memory_mb': request.budget.max_memory_mb,
        'upstream_evidence_ids': list(request.upstream_evidence_ids[:25]),
    }, ensure_ascii=False).encode('utf-8')
    if len(wire) > 24_000:
        raise WorkerFailure('worker_input_too_large')
    # On source checkouts `src` must be on the child import path. On installed
    # wheels the package is already resolvable from sys.executable's venv.
    src = Path(__file__).resolve().parents[2]
    env = _worker_environment(src)
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'campanario.brains.worker',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL, env=env,
            start_new_session=(os.name != 'nt'),
        )
    except OSError as exc:
        raise WorkerFailure('worker_start_failed') from exc

    overflow = False
    monitor_error = False
    monitor_stop = asyncio.Event()

    async def memory_watch():
        nonlocal overflow, monitor_error
        try:
            import psutil
            parent = psutil.Process(proc.pid)
            while not monitor_stop.is_set() and proc.returncode is None:
                try:
                    tasks = [parent, *parent.children(recursive=True)]
                    used = sum(p.memory_info().rss for p in tasks if p.is_running())
                    if used > request.budget.max_memory_mb * 1024 * 1024:
                        overflow = True
                        await _terminate_tree(proc)
                        return
                except (psutil.Error, OSError):
                    if proc.returncode is None and not monitor_stop.is_set():
                        monitor_error = True
                        await _terminate_tree(proc)
                    return
                await asyncio.sleep(0.05)
        except ImportError:
            monitor_error = True
            await _terminate_tree(proc)
            return

    monitor = asyncio.create_task(memory_watch())
    try:
        try:
            stdout, _ = await asyncio.wait_for(
                proc.communicate(wire + b'\n'), timeout=request.budget.timeout_seconds)
        except TimeoutError as exc:
            raise WorkerFailure('timeout_terminated') from exc
        if overflow:
            raise WorkerFailure('memory_limit_terminated')
        if monitor_error:
            raise WorkerFailure('process_monitor_failed')
        if proc.returncode != 0:
            raise WorkerFailure('worker_failed')
        return decode_result(stdout)
    finally:
        monitor_stop.set()
        await _terminate_tree(proc)
        await monitor
