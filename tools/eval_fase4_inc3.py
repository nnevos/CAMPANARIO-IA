#!/usr/bin/env python3
"""Fase 4 Inc.3A: offline FTS5 RAM vs legacy lexical; synthetic data only.

No user DB, web, Ollama, embeddings or Kiwix. Exact source attribution is
measured; semantic factual correctness is NOT. The source of a quote is not
proof that a quote answers the precise question.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import statistics
import sys
import tempfile
from time import perf_counter
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))

from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.local_library import ReadOnlyLocalLibrary
from eval_fase4_inc1 import _TemporaryUtilityService, evaluate as chat_eval

DATASET = ROOT / 'eval' / 'v1'
VARIATIONS = [
    ('M001', 'Quais arquivos de Horizonte?', 'guia_horizonte.md', 'arquivo norte.csv'),
    ('M002', 'Quais etiquetas de Ponte?', 'protocolo_ponte.md', 'cor marfim'),
    ('M003', 'Quais símbolos de Horizonte?', 'guia_horizonte.md', 'círculo verde'),
    ('M004', 'Quais inventários de Aurora?', 'diario_aurora.md', '14 amostras'),
    ('M005', 'Quais checklists de Ponte?', 'protocolo_ponte.md', 'versão 7'),
    ('M006', 'E as revisões de Rumo?', 'guia_rumo.md', '18 minutos'),
]
NEGATIVES = [
    'Quem foi Ada Lovelace?',
    'Quem foi Célia Vornacz?',
    'Os assinantes de Rumo?',
    'Quem criou o Projeto Rumo no século XII?',
    'Onde fica a marca secreta de Ponte?',
]
KNOWN_OLD_FALSE_RELEVANCE = 'O Projeto Faro teve autorização de Zeus?'


def _query(reader: ReadOnlyLocalLibrary, question: str):
    start = perf_counter()
    hit = reader.search(question)
    elapsed_ms = round((perf_counter() - start) * 1000, 3)
    return hit, elapsed_ms


def _evaluate_reader(reader, cases):
    docs = []
    first_ms = None
    for case in cases:
        hit, ms = _query(reader, case['question'])
        if first_ms is None:
            first_ms = ms
        sheet = build_turn_fact_sheet(uuid4(), case['question'], hit,
                                      fact_lookup_requested=True)
        correct = bool(sheet.sources and sheet.sources[0].title == case['document']
                       and case['expected_quote'] in sheet.sources[0].excerpt
                       and sheet.status == 'supported')
        docs.append({'id': case['id'], 'source_and_exact_quote': correct,
                     'source': sheet.sources[0].title if sheet.sources else None,
                     'ms': ms})
    variations = []
    for code, question, expected_doc, expected_fragment in VARIATIONS:
        hit, ms = _query(reader, question)
        correct = bool(hit and hit.status == 'grounded' and
                       hit.quote.name == expected_doc and
                       expected_fragment in hit.quote.excerpt)
        variations.append({'id': code, 'source_and_quote': correct, 'ms': ms})
    negatives = []
    for question in NEGATIVES:
        hit, ms = _query(reader, question)
        negatives.append({'question': question, 'no_unsupported_quote': hit is None,
                          'ms': ms})
    unsupported, _ = _query(reader, KNOWN_OLD_FALSE_RELEVANCE)
    return {
        'docs_exact_and_cited': sum(row['source_and_exact_quote'] for row in docs),
        'docs_total': len(docs),
        'plural_variants_grounded': sum(row['source_and_quote'] for row in variations),
        'plural_variants_total': len(variations),
        'negative_tests_abstained': sum(row['no_unsupported_quote'] for row in negatives),
        'negative_tests_total': len(negatives),
        'known_partial_overlap_false_relevance_still_present': unsupported is not None,
        'first_query_ms_including_index_build': first_ms,
        'warm_queries_median_ms_stub_only': round(statistics.median(
            row['ms'] for row in docs[1:]), 3),
        'index_builds': reader.index_build_count,
        'last_backend_used': reader.last_backend_used,
        'documents': docs, 'variants': variations, 'negatives': negatives,
    }


async def evaluate():
    cases = [json.loads(line) for line in (DATASET / 'documentos.jsonl').read_text(
        encoding='utf-8').splitlines() if line.strip()]
    if len(cases) != 20:
        raise ValueError('Fase 3 corpus incompleto: esperados 20 documentos')
    with tempfile.TemporaryDirectory(prefix='campanario_fase4_inc3_') as folder:
        utility = _TemporaryUtilityService(Path(folder) / 'utility')
        for filename in sorted({case['document'] for case in cases}):
            source = DATASET / 'fixtures' / filename
            path = utility.roots[0] / filename
            path.write_bytes(source.read_bytes())
            result = utility.run('library.import', {'path': str(path), 'confirm': True})
            if result['status'] != 'success':
                raise RuntimeError('fixture import failed: ' + filename)
        before = hashlib.sha256(utility.db.read_bytes()).hexdigest()
        legacy = ReadOnlyLocalLibrary(utility.db, backend='legacy')
        indexed = ReadOnlyLocalLibrary(utility.db)
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('internet forbidden')):
            baseline = _evaluate_reader(legacy, cases)
            modified = _evaluate_reader(indexed, cases)
        after = hashlib.sha256(utility.db.read_bytes()).hexdigest()
        no_sidecar = not any(path.name.endswith(('-wal', '-shm', '.fts5', '.index'))
                             for path in utility.base.iterdir())
    # Reuse the previously validated complete chat path on a second, isolated
    # set of temporary fixtures. Both evaluator temp databases are closed.
    chat = await chat_eval()
    return {
        'stage': 'fase4_incremento3a_busca_local',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'dataset': 'eval/v1/documentos.jsonl',
        'dataset_sha256': hashlib.sha256((DATASET/'documentos.jsonl').read_bytes()).hexdigest(),
        'method': 'FTS5-in-memory vs exact lexical baseline, identical test fixtures',
        'model_factual_accuracy': 'NOT_MEASURED_no_Ollama',
        'semantic_entailment': 'NOT_MEASURED_and_known_false_relevance',
        'kiwix': 'NOT_INTEGRATED', 'embeddings': 'NOT_INTEGRATED',
        'internet_attempts': 'blocked_during_retrieval_and_chat',
        'user_sqlite_accessed': False,
        'source_sqlite_byte_identical': before == after,
        'no_persistent_index_created': no_sidecar,
        'chat_exact_quotes_and_citations': chat['exact_quotes_and_citations'],
        'chat_model_calls': chat['model_calls_for_document_answers'],
        'baseline_legacy': baseline,
        'updated_fts5': modified,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', default='reports/fase4_inc3/baseline_busca_fts5.json')
    args = parser.parse_args()
    report = asyncio.run(evaluate())
    output = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    old, new = report['baseline_legacy'], report['updated_fts5']
    print(f'FTS5: documentos {new["docs_exact_and_cited"]}/{new["docs_total"]}; '
          f'variacoes {old["plural_variants_grounded"]}->{new["plural_variants_grounded"]}/{new["plural_variants_total"]}; '
          f'negativos {new["negative_tests_abstained"]}/{new["negative_tests_total"]}; '
          f'chat={report["chat_exact_quotes_and_citations"]}/20; '
          f'backend={new["last_backend_used"]}; relatorio={output}')
    if (new['docs_exact_and_cited'] != 20 or old['docs_exact_and_cited'] != 20 or
        new['negative_tests_abstained'] != len(NEGATIVES) or
        report['chat_exact_quotes_and_citations'] != 20 or report['chat_model_calls'] or
        not report['source_sqlite_byte_identical'] or
        not report['no_persistent_index_created']):
        raise SystemExit(2)
    if new['last_backend_used'] == 'fts5_memory' and new['plural_variants_grounded'] != len(VARIATIONS):
        raise SystemExit(2)
    if new['last_backend_used'] != 'fts5_memory':
        print('AVISO: SQLite sem FTS5; fallback legado ativo. Ganho de recall nao validado.')


if __name__ == '__main__':
    main()
