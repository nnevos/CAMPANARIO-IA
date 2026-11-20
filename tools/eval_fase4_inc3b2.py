#!/usr/bin/env python3
"""Fase 4 Inc.3B.2: compare raw semantic discovery vs guarded display.

Uses only fresh temporary SQLite and synthetic Markdown fixtures. Embeddings
are in RAM. --engine ollama calls only Ollama HTTP on literal loopback IP.
No user database, agent memory, .env or model configuration is changed.

Similarity and explicit textual attribute compatibility are both necessary
for displaying a candidate; neither is a proof of entailment or external truth.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))

from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.chat.semantic_library import HybridLocalLibrary, LoopbackOllamaEmbeddings
from eval_fase4_inc1 import _TemporaryUtilityService
from eval_fase4_inc3 import VARIATIONS
from eval_fase4_inc3b import PARAPHRASES, FixtureEmbeddings
from eval_fase4_inc3b_calibracao import HARD_NEGATIVES
from diagnostico_fase4_inc3b import score_candidates

# Unlike the five synonym-only cases, these ask for attributes written
# LITERALLY in the retrieved excerpt. The many irrelevant extra words make
# lexical FTS5 a miss; embeddings may find the answer as a candidate.
# They are test cases, not suggestions for how users should ask questions.
GUARDED_POSITIVES = (
    ('G001', 'Qual é a cor da etiqueta usada na fase de demonstração durante a inspeção preliminar do procedimento administrativo detalhado de Ponte?',
     'Ponte', 'protocolo_ponte.md', 'cor marfim'),
    ('G002', 'Qual é o intervalo da revisão Rumo segundo uma descrição com informações adicionais desnecessárias usadas apenas para consultar a origem do trecho e não o fato?',
     'Rumo', 'guia_rumo.md', '18 minutos'),
    ('G003', 'Qual e o arquivo de referencia do Projeto Faro, levando em conta instrucoes suplementares feitas pela coordenacao geral para uma etapa experimental extensa?',
     'Faro', 'manual_faro.md', 'faro_referencia.md'),
    ('G004', 'Qual o encontro de revisão de Ponte conforme as explicações adicionais publicadas recentemente para os observadores de vários departamentos internos?',
     'Ponte', 'protocolo_ponte.md', 'sala T12'),
    ('G005', 'Qual a caixa dos mapas de Rumo conforme as descrições explicativas adicionais de uma operação complexa que se pretende repetir cuidadosamente?',
     'Rumo', 'guia_rumo.md', 'caixa 42'),
)


def run(*, engine='fixture', model='embeddinggemma', timeout=30.0,
        min_similarity=0.50) -> dict:
    if engine not in {'fixture', 'ollama'}:
        raise ValueError('Invalid engine')
    if not 0 < min_similarity <= 1:
        raise ValueError('similarity must be in (0, 1]')
    source = ROOT / 'eval/v1'
    docs = [json.loads(line) for line in (source/'documentos.jsonl').read_text(
        encoding='utf-8').splitlines() if line.strip()]
    if len(docs) != 20 or len(HARD_NEGATIVES) != 12:
        raise ValueError('Synthetic evaluation corpus incomplete')
    with TemporaryDirectory(prefix='campanario_fase4_inc3b2_') as folder:
        utility = _TemporaryUtilityService(Path(folder) / 'utilities')
        for name in sorted({case['document'] for case in docs}):
            path = source/'fixtures'/name
            target = utility.roots[0]/name
            target.write_bytes(path.read_bytes())
            result = utility.run('library.import', {'path': str(target), 'confirm': True})
            if result.get('status') != 'success':
                raise RuntimeError('Synthetic document import failed: ' + name)
        before = sha256(utility.db.read_bytes()).hexdigest()
        provider = FixtureEmbeddings() if engine == 'fixture' else LoopbackOllamaEmbeddings(
            model=model, timeout=timeout)
        # Explicit experiment setting; does not change production 0.72 or opt-in.
        reader = HybridLocalLibrary(utility.db, embeddings=provider,
                                    min_similarity=min_similarity,
                                    build_budget_seconds=120.0)
        lexical = ReadOnlyLocalLibrary(utility.db)
        first_seen = perf_counter()
        stamp = reader._file_stamp()
        if stamp is None:
            raise RuntimeError('Synthetic database missing')
        reader._ensure_semantics(stamp)
        index_ms = round((perf_counter()-first_seen)*1000, 2)
        raw = []
        admissible = []
        negatives = []
        try:
            for case_id, q, subject, name, expected in PARAPHRASES:
                data = score_candidates(reader, q, subject, name, expected)
                top = data['top_accepted'][:1]
                hit = reader.search(q, subject=subject)
                raw.append({
                    'id': case_id,
                    'raw_correct_top': bool(top and top[0]['expected_quote']),
                    'shown_to_user': hit is not None,
                    'status': reader.last_semantic_status,
                    'cosine': top[0]['similarity'] if top else None,
                })
            for case_id, q, subject, name, expected in GUARDED_POSITIVES:
                lexical_hit = lexical.search(q, subject=subject)
                started = perf_counter()
                hit = reader.search(q, subject=subject)
                elapsed = round((perf_counter()-started)*1000, 2)
                sheet = build_turn_fact_sheet(uuid4(), q, hit, fact_lookup_requested=True)
                correct = bool(hit and hit.quote.name == name and
                               expected in hit.quote.excerpt)
                admissible.append({
                    'id':case_id, 'lexical_miss':lexical_hit is None,
                    'correct_cited_candidate':correct,
                    'sourced_but_unverified':bool(correct and
                        hit.status == 'semantic_candidate' and
                        sheet.status == 'insufficient' and
                        sheet.origin == 'library' and not sheet.claims and
                        sheet.extractive_answer and 'nao comprova' in sheet.extractive_answer),
                    'selected_source':hit.quote.name if hit else None,
                    'reason':reader.last_semantic_status,
                    'ms':elapsed,
                })
            for case_id, q, subject in HARD_NEGATIVES:
                hit = reader.search(q, subject=subject)
                fact = build_turn_fact_sheet(uuid4(), q, hit, fact_lookup_requested=True)
                negatives.append({
                    'id':case_id,
                    'no_quote_exposed':hit is None,
                    'no_fact_claim':fact.status != 'supported' and not fact.claims,
                    'sheet_has_no_source':not fact.sources,
                    'reason':reader.last_semantic_status,
                    'similarity_candidates_above_threshold':reader.last_semantic_ranked,
                    'gate_rejected':reader.last_semantic_rejected,
                })
            legacy = []
            for case in docs:
                hit = reader.search(case['question'])
                legacy.append(bool(hit and hit.status == 'grounded' and
                    hit.quote.name == case['document'] and
                    case['expected_quote'] in hit.quote.excerpt))
            variations = []
            for _id, q, name, expected in VARIATIONS:
                hit = reader.search(q)
                variations.append(bool(hit and hit.status == 'grounded' and
                    hit.quote.name == name and expected in hit.quote.excerpt))
            unchanged = sha256(utility.db.read_bytes()).hexdigest() == before
        finally:
            reader._discard_index()
            lexical._discard_index()
    return {
        'stage':'fase4_inc3b2_guarded_semantic_candidates',
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'engine':engine,
        'model':model if engine == 'ollama' else 'scripted_fixture_not_model_accuracy',
        'experimental_min_similarity':min_similarity,
        'production_min_similarity_unchanged':0.72,
        'semantic_default_still_disabled':True,
        'index_build_ms':index_ms,
        'dataset_sha256':sha256((source/'documentos.jsonl').read_bytes()).hexdigest(),
        'user_sqlite_accessed':False,
        'internet_authorized':False,
        'temporary_sqlite_unchanged':unchanged,
        'raw_synonym_queries':{
            'correct_top':sum(r['raw_correct_top'] for r in raw),
            'shown_to_user':sum(r['shown_to_user'] for r in raw),
            'total':len(raw), 'cases':raw,
        },
        'explicit_answerable_queries':{
            'lexical_misses':sum(r['lexical_miss'] for r in admissible),
            'correct_cited_candidates':sum(r['correct_cited_candidate'] for r in admissible),
            'not_promoted':sum(r['sourced_but_unverified'] for r in admissible),
            'total':len(admissible),'cases':admissible,
            'median_query_ms':round(statistics.median(c['ms'] for c in admissible),2),
        },
        'hard_same_topic_negatives':{
            'without_citation':sum(r['no_quote_exposed'] for r in negatives),
            'without_fact_claim':sum(r['no_fact_claim'] for r in negatives),
            'without_source':sum(r['sheet_has_no_source'] for r in negatives),
            'total':len(negatives), 'cases':negatives,
        },
        'original_documents_grounded':sum(legacy),
        'original_documents_total':len(legacy),
        'fts5_variations_grounded':sum(variations),
        'fts5_variations_total':len(variations),
        'semantic_entailment':'NOT_MEASURED',
        'qwen_factual_accuracy':'NOT_MEASURED',
        'conclusion':('Embedding similarity retrieves candidate excerpts; the explicit '
                      'attribute gate may reject correct synonym-only pairs. '
                      'Neither the vector nor this textual gate proves entailment.'),
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',choices=('fixture','ollama'),default='fixture')
    parser.add_argument('--model',default='embeddinggemma')
    parser.add_argument('--timeout',type=float,default=30.0)
    parser.add_argument('--threshold',type=float,default=0.50)
    parser.add_argument('--report',default=None)
    args=parser.parse_args()
    result=run(engine=args.engine,model=args.model,timeout=args.timeout,
               min_similarity=args.threshold)
    path=Path(args.report or f'reports/fase4_inc3b2/baseline_{args.engine}.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    d=result['raw_synonym_queries']; a=result['explicit_answerable_queries']
    n=result['hard_same_topic_negatives']
    print(f'3B.2 ({args.engine}): raw={d["correct_top"]}/{d["total"]}; '
          f'revisados={a["correct_cited_candidates"]}/{a["total"]} '
          f'(NAO promovidos={a["not_promoted"]}); '
          f'negativos_sem_trecho={n["without_citation"]}/{n["total"]}; '
          f'docs={result["original_documents_grounded"]}/{result["original_documents_total"]}; '
          f'FTS5={result["fts5_variations_grounded"]}/{result["fts5_variations_total"]}; '
          f'indice_ms={result["index_build_ms"]}; relatorio={path}')
    if not (result['temporary_sqlite_unchanged'] and
            result['original_documents_grounded'] == 20 and
            result['fts5_variations_grounded'] == 6 and
            n['without_citation'] == n['without_fact_claim'] == n['without_source'] == 12 and
            d['shown_to_user'] == 0):
        raise SystemExit(2)
    if args.engine == 'fixture' and not (
            a['lexical_misses'] == a['correct_cited_candidates'] == a['not_promoted'] == 5 and
            d['correct_top'] == 5):
        raise SystemExit(2)
    if args.engine == 'ollama' and result['raw_synonym_queries']['correct_top'] == 0:
        print('ALERTA: nenhum caso raw reconhecido; confira Ollama e o relatorio.')
        raise SystemExit(3)

if __name__ == '__main__':
    main()
