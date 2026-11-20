#!/usr/bin/env python3
"""Inc.3B: FTS5 versus opt-in semantic candidates, synthetic documents only.

--engine fixture verifies plumbing using a handcrafted fake vector provider.
--engine ollama measures the REAL local embeddinggemma and may return fewer hits.
Since Inc.3B.2, synonym-only hits can be discovered by the embedding engine
but are suppressed by the conservative answerability gate. This script now
measures *exposed* candidates, not raw similarity (see 3B.2 evaluator for both).
Neither engine scores semantic entailment or Qwen factual correctness.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys
import tempfile
from time import perf_counter
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))

from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.chat.semantic_library import HybridLocalLibrary, LoopbackOllamaEmbeddings
from eval_fase4_inc1 import _TemporaryUtilityService
from eval_fase4_inc3 import evaluate as baseline3a

DATASET = ROOT / 'eval' / 'v1'

# Real queries are paraphrases, not target excerpts copied verbatim.
# All expected fragments are fixed before the embedding search is run.
PARAPHRASES = [
    ('S001', 'Qual o tempo entre inspecoes no Rumo?', 'Rumo', 'guia_rumo.md', '18 minutos'),
    ('S002', 'Qual a tonalidade do identificador de Ponte?', 'Ponte', 'protocolo_ponte.md', 'cor marfim'),
    ('S003', 'Em que recinto ocorre a reuniao de inspecao de Ponte?', 'Ponte', 'protocolo_ponte.md', 'sala T12'),
    ('S004', 'Qual a designacao do material-base para consultar Faro?', 'Faro', 'manual_faro.md', 'faro_referencia.md'),
    ('S005', 'Em qual recipiente estao guardadas as cartas geograficas de Rumo?', 'Rumo', 'guia_rumo.md', 'caixa 42'),
]
NEGATIVES = [
    ('N001', 'Quem foi Ada Lovelace?', 'Ada Lovelace'),
    ('N002', 'Quem foi Celia Vornacz?', 'Celia Vornacz'),
    ('N003', 'Qual documento prova que Zeus autorizou o Faro?', 'Zeus'),
    ('N004', 'Qual a cor dos olhos do suposto unicorno de Ponte?', 'unicorno'),
]


class FixtureEmbeddings:
    """Scripted routing vectors: tests integration, NOT model performance."""
    calls = 0
    def embed(self, texts):
        self.calls += 1
        result = []
        for text in texts:
            t = text.casefold()
            tag = None
            if ('rumo' in t and any(x in t for x in ('intervalo', 'revisao', 'inspecoes', 'tempo entre'))):
                tag = 0
            elif 'ponte' in t and any(x in t for x in ('etiqueta', 'identificador', 'tonalidade', 'marfim')):
                tag = 1
            elif 'ponte' in t and any(x in t for x in ('encontro', 'reuniao', 'recinto', 'sala t12')):
                tag = 2
            elif 'faro' in t and any(x in t for x in ('referencia', 'material-base', 'consultas', 'se chama')):
                tag = 3
            elif 'rumo' in t and any(x in t for x in ('mapas', 'cartas geograficas', 'caixa 42', 'guardadas')):
                tag = 4
            # Isolate negatives; disallow a generic topic-match as fake success.
            if any(x in t for x in ('zeus', 'unicorno', 'lovelace', 'vornacz')):
                tag = None
            vec = [0.0] * 8
            vec[tag if tag is not None else 7] = 1.0
            result.append(vec)
        return result


def _check(reader, question, subject):
    start = perf_counter()
    hit = reader.search(question, subject=subject)
    return hit, round(1000 * (perf_counter() - start), 3)


def _cases(reader):
    positive = []
    for caseid, question, subject, expected_doc, expected_value in PARAPHRASES:
        hit, ms = _check(reader, question, subject)
        sheet = build_turn_fact_sheet(uuid4(), question, hit, fact_lookup_requested=True)
        correct_quote = bool(hit and hit.quote.name == expected_doc and
                             expected_value in hit.quote.excerpt)
        # Only lexical hits are allowed to be called 'supported'.
        semantically_flagged = bool(hit and hit.status == 'semantic_candidate' and
                                    sheet.status == 'insufficient' and not sheet.claims)
        positive.append({
            'id': caseid, 'correct_quote_and_source': correct_quote,
            'semantic_candidate_not_promoted': semantically_flagged,
            'sheet_status': sheet.status, 'ms': ms,
            'source_name': hit.quote.name if hit else None,
            'excerpt': hit.quote.excerpt if hit else None,
        })
    negative = []
    for caseid, question, subject in NEGATIVES:
        hit, ms = _check(reader, question, subject)
        sheet = build_turn_fact_sheet(uuid4(), question, hit, fact_lookup_requested=True)
        negative.append({
            'id': caseid, 'no_supported_claim': sheet.status != 'supported',
            'no_quote': hit is None, 'ms': ms,
        })
    return {
        'positive_correct_source': sum(p['correct_quote_and_source'] for p in positive),
        'positive_total': len(positive),
        'positive_semantic_candidate_only': sum(p['semantic_candidate_not_promoted'] for p in positive),
        'negatives_no_supported_claim': sum(n['no_supported_claim'] for n in negative),
        'negatives_no_quote': sum(n['no_quote'] for n in negative),
        'negative_total': len(negative),
        'positive': positive, 'negative': negative,
        'query_median_ms': round(statistics.median([row['ms'] for row in positive]), 3),
    }


async def evaluate(engine='fixture', model='embeddinggemma', url='http://127.0.0.1:11434', timeout=5.0):
    # The old benchmark is rerun unchanged to make regressions detectable.
    old = await baseline3a()
    cases = [json.loads(line) for line in (DATASET / 'documentos.jsonl').read_text(
        encoding='utf-8').splitlines() if line.strip()]
    with tempfile.TemporaryDirectory(prefix='campanario_fase4_inc3b_') as folder:
        utility = _TemporaryUtilityService(Path(folder) / 'utilities')
        for name in sorted({c['document'] for c in cases}):
            source = DATASET / 'fixtures' / name
            path = utility.roots[0] / name
            path.write_bytes(source.read_bytes())
            assert utility.run('library.import', {'path': str(path), 'confirm': True})['status'] == 'success'
        before = hashlib.sha256(utility.db.read_bytes()).hexdigest()
        baseline = _cases(ReadOnlyLocalLibrary(utility.db))
        provider = (FixtureEmbeddings() if engine == 'fixture' else
                    LoopbackOllamaEmbeddings(url=url, model=model, timeout=timeout))
        hybrid = HybridLocalLibrary(utility.db, embeddings=provider,
                                    build_budget_seconds=30.0)
        modified = _cases(hybrid)
        # All original 20 exact-source cases must continue to use lexical FTS5.
        preserved = 0
        for case in cases:
            hit = hybrid.search(case['question'])
            preserved += bool(hit and hit.status == 'grounded' and
                              hit.quote.name == case['document'] and
                              case['expected_quote'] in hit.quote.excerpt)
        unchanged = hashlib.sha256(utility.db.read_bytes()).hexdigest() == before
    return {
        'stage': 'fase4_incremento3b2_legacy_benchmark_guarded',
        'semantic_sufficiency_gate': 'active_fail_closed',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'engine': engine, 'embedding_model': model if engine == 'ollama' else 'fixture_not_real_model',
        'dataset_sha256': hashlib.sha256((DATASET/'documentos.jsonl').read_bytes()).hexdigest(),
        'internet_authorized': False,
        'user_sqlite_accessed': False, 'temp_sqlite_unchanged': unchanged,
        'corpus': 'eval/v1 synthetic; fixture vectors are intentionally scripted',
        'real_embedding_accuracy': 'measured_only_if_engine_ollama',
        'semantic_entailment': 'NOT_MEASURED', 'qwen_factual_accuracy': 'NOT_MEASURED',
        'gpu_vram_peak_mb': 'NOT_MEASURED',
        'original_fts5_benchmark': {
            'docs_correct': old['updated_fts5']['docs_exact_and_cited'],
            'docs_total': old['updated_fts5']['docs_total'],
            'negative_abstentions': old['updated_fts5']['negative_tests_abstained'],
        },
        'existing_docs_still_correct': preserved,
        'baseline_fts5_paraphrases': baseline,
        'hybrid_semantic_paraphrases': modified,
        'semantic_cache_builds': hybrid.semantic_build_count,
        'semantic_status_last': hybrid.last_semantic_status,
        'fixture_provider_calls': provider.calls if engine == 'fixture' else None,
        'shadow_activation': 'default_off; opt_in_env_only',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', choices=('fixture', 'ollama'), default='fixture')
    parser.add_argument('--model', default='embeddinggemma')
    parser.add_argument('--url', default='http://127.0.0.1:11434')
    parser.add_argument('--timeout', type=float, default=5.0)
    parser.add_argument('--report', default=None)
    args = parser.parse_args()
    result = asyncio.run(evaluate(args.engine, args.model, args.url, args.timeout))
    target = Path(args.report or f'reports/fase4_inc3b/baseline_{args.engine}.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                      encoding='utf-8')
    earlier, new = result['baseline_fts5_paraphrases'], result['hybrid_semantic_paraphrases']
    print(f'3B ({args.engine}): FTS5={earlier["positive_correct_source"]}/{earlier["positive_total"]}; '
          f'semantica={new["positive_correct_source"]}/{new["positive_total"]} '
          f'(candidatos, NAO fatos); controles={new["negatives_no_supported_claim"]}/{new["negative_total"]}; '
          f'docs antigos={result["existing_docs_still_correct"]}/20; relatorio={target}')
    if (result['existing_docs_still_correct'] != 20 or not result['temp_sqlite_unchanged'] or
        new['negatives_no_supported_claim'] != new['negative_total']):
        raise SystemExit(2)
    if args.engine == 'ollama' and result['semantic_cache_builds'] == 0:
        print('NAO MEDIDO: Ollama local indisponivel ou embeddings invalidos; '
              'o baseline real nao foi executado. Verifique ollama list/logs.')
        raise SystemExit(3)
    # These five synonym-only queries are intentionally withheld by the
    # conservative gate. Discovery remains benchmarked in the 3B.2 evaluator.
    if args.engine == 'fixture' and (new['positive_correct_source'] != 0 or
                                    new['positive_semantic_candidate_only'] != 0):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
