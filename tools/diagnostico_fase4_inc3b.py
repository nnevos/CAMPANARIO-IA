"""Diagnostico sem escrita no nucleo: revela filtros dos cinco casos sinteticos.

Le APENAS eval/v1/fixtures, cria banco temporario e consulta Ollama em 127.0.0.1.
Nao altera a biblioteca pessoal nem habilita a busca semantica no chat.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'src'))

from eval_fase4_inc1 import _TemporaryUtilityService
from eval_fase4_inc3b import PARAPHRASES, NEGATIVES, FixtureEmbeddings
from campanario.chat.local_library import _tokens
from campanario.chat.semantic_library import (
    HybridLocalLibrary, LoopbackOllamaEmbeddings, normalize,
)


def score_candidates(reader: HybridLocalLibrary, question: str, subject: str,
                     expected_name: str = '', expected_text: str = '') -> dict:
    """Espelha os filtros de HybridLocalLibrary.search, sem mudar seus limiares."""
    start = perf_counter()
    query = normalize(reader.embeddings.embed([question[:500]])[0])
    segments = reader._semantic_segments
    vectors = reader._semantic_vectors
    if vectors and len(vectors[0]) != len(query):
        raise ValueError('Dimensoes inconsistentes entre pergunta e biblioteca')
    subject_terms = _tokens(subject)
    question_terms = _tokens(question)
    rows = []
    for quote, vector in zip(segments, vectors):
        text_terms = _tokens(quote.excerpt)
        subject_ok = subject_terms.issubset(text_terms)
        lexical_overlap = len(question_terms & text_terms)
        # Para o corpus avaliado, todas as perguntas tem subject explicito.
        anchor_ok = subject_ok if subject_terms else lexical_overlap >= 2
        sim = sum(a * b for a, b in zip(query, vector))
        rows.append({
            'document': quote.name,
            'page': quote.page,
            'similarity': round(sim, 5),
            'anchor_ok': anchor_ok,
            'lexical_overlap': lexical_overlap,
            'expected_quote': bool(quote.name == expected_name and
                                   expected_text and expected_text in quote.excerpt),
            'meets_threshold': bool(anchor_ok and sim >= reader.min_similarity),
        })
    rows.sort(key=lambda r: (-r['similarity'], r['document']))
    eligible = [r for r in rows if r['anchor_ok']]
    accepted = [r for r in rows if r['meets_threshold']]
    expected = [r for r in rows if r['expected_quote']]
    return {
        'subject': subject,
        'top_overall': rows[:3],
        'top_after_subject_filter': eligible[:3],
        'top_accepted': accepted[:3],
        'subject_eligible_count': len(eligible),
        'above_threshold_count': len(accepted),
        'expected_quote': expected[:1],
        'query_embedding_ms': round((perf_counter() - start) * 1000, 2),
    }


def run(engine: str, model: str, timeout: float, threshold: float) -> dict:
    cases = [json.loads(line) for line in (ROOT / 'eval/v1/documentos.jsonl').read_text(
        encoding='utf-8').splitlines() if line.strip()]
    with TemporaryDirectory(prefix='campanario_inc3b_diag_') as folder:
        utility = _TemporaryUtilityService(Path(folder) / 'utilities')
        for name in sorted({case['document'] for case in cases}):
            source = ROOT / 'eval/v1/fixtures' / name
            target = utility.roots[0] / name
            target.write_bytes(source.read_bytes())
            result = utility.run('library.import', {'path': str(target), 'confirm': True})
            if result.get('status') != 'success':
                raise RuntimeError('Nao foi possivel importar documento de teste: ' + name)

        embeddings = (FixtureEmbeddings() if engine == 'fixture'
                      else LoopbackOllamaEmbeddings(model=model, timeout=timeout))
        library = HybridLocalLibrary(utility.db, embeddings=embeddings,
                                     build_budget_seconds=120.0,
                                     min_similarity=threshold)
        start = perf_counter()
        stamp = library._file_stamp()
        if stamp is None:
            raise RuntimeError('Banco de teste ausente')
        library._ensure_semantics(stamp)
        build_ms = round((perf_counter() - start) * 1000, 2)
        indexed_segments = len(library._semantic_segments)
        rows = []
        for caseid, question, subject, name, expected_text in PARAPHRASES:
            stats = score_candidates(library, question, subject, name, expected_text)
            top = stats['top_after_subject_filter'][:1]
            expected = stats['expected_quote'][:1]
            stats.update({
                'id': caseid,
                'type': 'positive',
                'best_expected_document': top[0]['document'] == name if top else False,
                'best_expected_quote': bool(top and top[0]['expected_quote']),
                'expected_similarity': expected[0]['similarity'] if expected else None,
                'cause_if_no_candidate': (
                    'no_subject_match' if not stats['subject_eligible_count'] else
                    'similarity_below_threshold' if not stats['above_threshold_count'] else
                    'candidate_exists'),
            })
            rows.append(stats)
        negative_rows = []
        for caseid, question, subject in NEGATIVES:
            stats = score_candidates(library, question, subject)
            stats.update({'id': caseid, 'type': 'negative'})
            negative_rows.append(stats)
        # A unica conexao FTS5 pertence ao indice em RAM.
        library._discard_index()

    positive_success = sum(bool(r['top_accepted'] and r['top_accepted'][0]['expected_quote']) for r in rows)
    return {
        'diagnostic_version': '1.0',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'engine': engine,
        'model': model if engine == 'ollama' else 'fixture',
        'source': 'APENAS corpus sintetico eval/v1/fixtures',
        'user_sqlite_accessed': False,
        'similarity_threshold': threshold,
        'index_build_ms': build_ms,
        'indexed_segments': indexed_segments,
        'positive_expected_top_accepted': positive_success,
        'positive_total': len(rows),
        'negatives_with_accepted_candidate': sum(bool(r['top_accepted']) for r in negative_rows),
        'positive': rows,
        'negative': negative_rows,
        'note': ('Pontuacao de similaridade nao prova que o trecho responde a pergunta. '
                 'Nao se deve mudar limiar usando somente estes casos.'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', choices=('fixture', 'ollama'), default='fixture')
    parser.add_argument('--model', default='embeddinggemma')
    parser.add_argument('--timeout', type=float, default=30)
    parser.add_argument('--threshold', type=float, default=0.72)
    parser.add_argument('--report', default='reports/fase4_inc3b/diagnostico_scores.json')
    args = parser.parse_args()
    if not 0 < args.threshold <= 1:
        parser.error('threshold deve estar em (0, 1]')
    try:
        result = run(args.engine, args.model, args.timeout, args.threshold)
    except Exception as error:
        print('DIAGNOSTICO NAO CONCLUIDO:', type(error).__name__, str(error)[:160])
        raise SystemExit(2) from error
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'3B diagnostico ({args.engine}), limiar={args.threshold}, '
          f'indice={result["index_build_ms"]} ms')
    for row in result['positive']:
        best = row['top_after_subject_filter'][:1]
        if best:
            name = best[0]['document']
            score = best[0]['similarity']
            match = best[0]['expected_quote']
        else:
            name, score, match = 'SEM CORRESPONDENCIA DE ASSUNTO', None, False
        print(f'{row["id"]}: top={name}; cosine={score}; esperado={match}; '
              f'aceitos={row["above_threshold_count"]}; diagnostico={row["cause_if_no_candidate"]}')
    print(f'Negativos com candidato aceito: '
          f'{result["negatives_with_accepted_candidate"]}/{len(result["negative"])}')
    print('Relatorio:', path)

if __name__ == '__main__':
    main()
