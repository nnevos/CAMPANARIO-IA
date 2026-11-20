#!/usr/bin/env python3
"""Fase 4 inc.2: fixed 20-document turn fact-sheet evidence, 100% offline.

This is NOT an Ollama factuality test. It reads only temporary test fixtures.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))
from eval_fase4_inc1 import evaluate as evaluate_inc1  # already validated Windows benchmark
from campanario.utilities.service import UtilityService


class _TemporaryUtilityService(UtilityService):
    """Test-only UtilityService that closes each SQLite handle on every exit.

    `with sqlite3.connect(...)` commits/rolls back but does not close the
    connection. On Windows, TempDirectory cleanup fails while the DB is open.
    This override affects this evaluator only, never production utilities.
    """

    @contextmanager
    def connect(self):
        db = super().connect()
        try:
            with db:  # preserve the original commit/rollback behavior
                yield db
        finally:
            db.close()  # release Windows file locks even if a query fails


async def evaluate():
    from campanario.chat.fact_sheet import build_turn_fact_sheet
    from campanario.chat.local_library import ReadOnlyLocalLibrary

    earlier = await evaluate_inc1()
    fixture_root = ROOT / 'eval' / 'v1'
    cases = [json.loads(line) for line in (fixture_root/'documentos.jsonl').read_text(
        encoding='utf-8').splitlines() if line.strip()]
    with tempfile.TemporaryDirectory(prefix='campanario_fase4_inc2_') as folder:
        util=_TemporaryUtilityService(Path(folder)/'u')
        for name in sorted({case['document'] for case in cases}):
            p=util.roots[0]/name
            p.write_bytes((fixture_root/'fixtures'/name).read_bytes())
            r=util.run('library.import',{'path':str(p),'confirm':True})
            if r['status']!='success':
                raise RuntimeError('fixture import error')
        reader=ReadOnlyLocalLibrary(util.db)
        before=hashlib.sha256(util.db.read_bytes()).hexdigest()
        observations=[]
        # This guard blocks attempted outbound socket connections by the evaluated path.
        with patch.object(socket.socket,'connect',side_effect=AssertionError('network prohibited')):
            for case in cases:
                result=reader.search(case['question'])
                sheet=build_turn_fact_sheet(uuid4(),case['question'],result,
                    fact_lookup_requested=True)
                observations.append({
                    'id':case['id'],
                    'status':sheet.status,
                    'origin':sheet.origin,
                    'source_count':len(sheet.sources),
                    'claims_only_source_assertions':all(c.certainty=='source_assertion'
                        for c in sheet.claims),
                    'exact_source_quote':bool(
                        sheet.sources and case['expected_quote'] in sheet.sources[0].excerpt),
                    'source_filename_matches':bool(
                        sheet.sources and sheet.sources[0].title==case['document']),
                    'extractive_answer_from_local':bool(
                        sheet.extractive_answer and 'Fonte:' in sheet.extractive_answer),
                    'not_persona_specific':all(
                        term not in sheet.render_agent_context() for term in ('Morgana','Todd')),
                })
        after=hashlib.sha256(util.db.read_bytes()).hexdigest()
    sheet_pass=sum(all(v for k,v in row.items() if k not in ('id','status','origin','source_count'))
        and row['status']=='supported' and row['origin']=='library' and row['source_count']>=1
        for row in observations)
    return {
        'increment':'fase4_inc2_neutral_fact_sheet',
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'dataset':'eval/v1', 'cases':len(cases),
        'factual_accuracy_real_model':'not_measured_no_ollama_called',
        'web_retrieval':'not_evaluated',
        'group_semantic_quality':'not_measured',
        'internet':'blocked_by_socket_mock',
        'documents_cited_by_chat':earlier['exact_quotes_and_citations'],
        'documents_in_immutable_source_ledger':sheet_pass,
        'documents_total':len(cases),
        'model_calls_for_document_answers':earlier['model_calls_for_document_answers'],
        'temporary_sqlite_unchanged_by_reader':before==after,
        'user_sqlite_accessed':False,
        'observations':observations,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',default='reports/fase4_inc2/baseline_ficha_neutra.json')
    a=p.parse_args()
    result=asyncio.run(evaluate())
    path=Path(a.report)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"FICHA NEUTRA: {result['documents_in_immutable_source_ledger']}/{result['documents_total']} com "
          f"fonte exata; chat={result['documents_cited_by_chat']}/{result['documents_total']}; "
          f"modelo simulado={result['model_calls_for_document_answers']}; relatorio={path}")
    if (result['documents_in_immutable_source_ledger']!=len(result['observations'])
        or result['documents_cited_by_chat']!=len(result['observations'])
        or result['model_calls_for_document_answers']!=0
        or not result['temporary_sqlite_unchanged_by_reader']):
        raise SystemExit(2)

if __name__=='__main__':
    main()
