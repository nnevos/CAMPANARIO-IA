"""Minimal, allowlisted V9 brain worker. Run only as a subprocess of R1 executor."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from uuid import UUID

from campanario.brains.adapters import AnalysisBrain, KnowledgeBrain
from campanario.brains.contracts import BrainRequest, ResourceBudget
from campanario.brains.isolation import encode_result
from campanario.brains.network_guard import deny_worker_network


def main() -> int:
    try:
        raw = sys.stdin.buffer.readline(24_001)
        if not raw.endswith(b'\n') or len(raw) > 24_000:
            return 2
        item = json.loads(raw)
        if item.get('brain_id') not in ('knowledge', 'analysis'):
            return 3
        db = Path(item['database']).resolve(strict=True)
        if not db.is_file() or db.suffix.lower() not in {'.sqlite', '.sqlite3', '.db'}:
            return 4
        request = BrainRequest(
            request_id=UUID(item['request_id']),
            conversation_id=UUID(item['conversation_id']) if item['conversation_id'] else None,
            query=item['query'], intent=item['intent'], document_hint=item['document_hint'],
            budget=ResourceBudget(timeout_seconds=float(item['timeout_seconds']),
                                  max_evidence=int(item['max_evidence']),
                                  max_input_chars=int(item['max_input_chars']),
                                  max_memory_mb=int(item['max_memory_mb'])),
            permission_scopes=frozenset({'library:read'}), trace_id=UUID(item['trace_id']),
        )
        # Soft CPU cap on POSIX; Windows uses parent wall-time and RSS monitoring.
        if sys.platform != 'win32':
            try:
                import resource
                ceiling = max(2, math.ceil(request.budget.timeout_seconds) + 1)
                resource.setrlimit(resource.RLIMIT_CPU, (ceiling, ceiling + 1))
            except (ImportError, ValueError, OSError):
                pass
        adapter = KnowledgeBrain(db) if item['brain_id'] == 'knowledge' else AnalysisBrain(db)
        with deny_worker_network():
            outcome = adapter.execute(request)
        sys.stdout.buffer.write(encode_result(outcome))
        sys.stdout.buffer.flush()
        return 0
    except (Exception, KeyboardInterrupt):
        # Never leak raw prompts, SQL, filesystem paths or private documents via stdout.
        return 5


if __name__ == '__main__':
    raise SystemExit(main())
