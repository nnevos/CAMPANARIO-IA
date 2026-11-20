#!/usr/bin/env python3
"""Fase 4 inc.1: real chat path on 20 synthetic library cases; no Ollama/web.

The production code under evaluation is ChatService + ReadOnlyLocalLibrary.
Only temporary SQLite data is created; the user's data_dir is never accessed.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import sys
import tempfile
from time import perf_counter
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / 'eval' / 'v1'
sys.path.insert(0, str(ROOT / 'src'))
from campanario.utilities.service import UtilityService


class _TemporaryUtilityService(UtilityService):
    """Test-only DB context: commit/rollback and CLOSE the SQLite handle.

    UtilityService uses `with sqlite3.Connection`, which finalizes the
    transaction but does not close it. An open handle blocks deletion of
    temporary SQLite files on Windows. Production UtilityService is unchanged.
    """

    @contextmanager
    def connect(self):
        db = super().connect()
        try:
            with db:
                yield db
        finally:
            db.close()


async def evaluate() -> dict:
    from campanario.chat.context import RecentMessagesContextManager
    from campanario.chat.local_library import ReadOnlyLocalLibrary
    from campanario.chat.models import ChatSession
    from campanario.chat.service import ChatService
    from campanario.model.protocol import ModelChunk
    from dataclasses import replace
    from uuid import uuid4

    class Sessions:
        def __init__(self): self.rows = {}
        def create(self, row): self.rows[row.id] = row; return row
        def get(self, key): return self.rows.get(key)
        def set_primary_agent(self, key, agent_id):
            self.rows[key] = replace(self.rows[key], primary_agent_id=agent_id)
            return self.rows[key]
        def list(self): return list(self.rows.values())

    class Messages:
        def __init__(self): self.rows = []
        def append(self, row): self.rows.append(row); return row
        def list_by_session(self, key): return [x for x in self.rows if x.session_id == key]

    class GuardProvider:
        def __init__(self): self.calls = 0
        async def health(self): return True
        async def stream(self, request):
            self.calls += 1
            yield ModelChunk(text='FASE4_PROVEDOR_SIMULADO_NAO_E_FATO')
            yield ModelChunk(text='', done=True)

    required = [DATASET / 'documentos.jsonl', *[DATASET/'fixtures'/n for n in
         ('manual_faro.md','guia_rumo.md','protocolo_ponte.md','diario_aurora.md','guia_horizonte.md')]]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError('Instale antes o corpus da Fase 3: ' + ', '.join(missing))
    cases = [json.loads(line) for line in required[0].read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(cases) != 20: raise ValueError('Esperadas 20 perguntas documentais da Fase 3')
    with tempfile.TemporaryDirectory(prefix='campanario_fase4_inc1_') as folder:
        service = _TemporaryUtilityService(Path(folder) / 'utilidades')
        for name in sorted({row['document'] for row in cases}):
            imported = service.roots[0] / name
            imported.write_bytes((DATASET / 'fixtures' / name).read_bytes())
            result = service.run('library.import', {'path': str(imported), 'confirm': True})
            if result['status'] != 'success':
                raise RuntimeError(f'Não foi possível importar fixture {name}')
        reader = ReadOnlyLocalLibrary(service.db)
        provider = GuardProvider()
        chat = ChatService(Sessions(), Messages(), provider,
                           RecentMessagesContextManager(10), 'stub',
                           local_library=reader, low_latency_mode=True, grounded_synthesis=False,
                           web_auto_search=False)
        outcomes = []
        # Fail if chat or retrieval attempts an external network socket.
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('network prohibited')):
            for case in cases:
                session = chat.create_session()
                start = perf_counter()
                parts = [event.text async for event in chat.stream_turn(session.id, case['question'])
                         if event.type == 'token']
                ms = round((perf_counter() - start) * 1000, 3)
                answer = ''.join(parts)
                outcomes.append({
                    'id': case['id'], 'document': case['document'],
                    'exact_quote_in_answer': case['expected_quote'] in answer,
                    'document_named_in_answer': case['document'] in answer,
                    'contains_source_attribution': 'Fonte:' in answer,
                    'fake_model_text_excluded': 'FASE4_PROVEDOR_SIMULADO' not in answer,
                    'elapsed_ms_stub_only': ms,
                })
        return {
            'stage': 'fase4_incremento1',
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'test_scope': 'chat_integrado_20_documentos_sinteticos',
            'model_factual_accuracy': 'NOT_MEASURED_no_real_llm',
            'internet': 'blocked_by_socket_mock',
            'user_database_accessed': False,
            'dataset_version': 'fase3_v1',
            'documents_cases': len(outcomes),
            'exact_quotes_and_citations': sum(all(row[k] for k in (
                'exact_quote_in_answer', 'document_named_in_answer',
                'contains_source_attribution', 'fake_model_text_excluded')) for row in outcomes),
            'model_calls_for_document_answers': provider.calls,
            'observations': outcomes,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', default='reports/fase4_inc1/baseline_local_docs.json')
    options = parser.parse_args()
    # Existing project editable installation or explicit PYTHONPATH=src.
    sys.path.insert(0, str(ROOT / 'src'))
    summary = asyncio.run(evaluate())
    path = Path(options.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"DOCUMENTOS: {summary['exact_quotes_and_citations']}/{summary['documents_cases']} com trecho exato e fonte; "
          f"chamadas ao modelo simulado={summary['model_calls_for_document_answers']}; "
          f"relatorio={path}")
    if summary['exact_quotes_and_citations'] != 20 or summary['model_calls_for_document_answers']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
