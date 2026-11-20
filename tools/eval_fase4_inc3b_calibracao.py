#!/usr/bin/env python3
"""Inc.3B calibration: same-topic missing answers vs real/fixture semantic candidate discovery.

Pure evaluation, never activates 3B or changes the configured similarity threshold.
The existing corpus is synthetic. A retrieved excerpt is NOT a verified answer.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))

from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.chat.semantic_library import HybridLocalLibrary, LoopbackOllamaEmbeddings
from eval_fase4_inc1 import _TemporaryUtilityService
from eval_fase4_inc3b import PARAPHRASES, FixtureEmbeddings
from diagnostico_fase4_inc3b import score_candidates
from uuid import uuid4

# All names exist in the fixtures, but these attributes/answers do NOT.
# Their purpose is to reveal confident, topical but unsupported suggestions.
HARD_NEGATIVES = (
    ('H001', 'Qual a senha de acesso do Protocolo Ponte?', 'Ponte'),
    ('H002', 'Quem assinou a ata do Protocolo Ponte?', 'Ponte'),
    ('H003', 'Qual o endereco da sede do Projeto Faro?', 'Faro'),
    ('H004', 'Qual o telefone do responsavel pelo Projeto Faro?', 'Faro'),
    ('H005', 'Qual o autor original do Guia Rumo?', 'Rumo'),
    ('H006', 'Qual o preco do material cartografico de Rumo?', 'Rumo'),
    ('H007', 'A que horas comeca a reuniao do Protocolo Ponte?', 'Ponte'),
    ('H008', 'Qual e a senha do arquivo de referencia de Faro?', 'Faro'),
    ('H009', 'Qual a idade da observadora Lia Nobre em Aurora?', 'Aurora'),
    ('H010', 'Qual o numero de serie do equipamento de Horizonte?', 'Horizonte'),
    ('H011', 'Quem fundou a equipe de Rumo?', 'Rumo'),
    ('H012', 'Qual a data de nascimento do criador de Ponte?', 'Ponte'),
)
THRESHOLDS = (0.72, 0.50)


def _accepted(rows: list[dict], threshold: float):
    return [row for row in rows if row['anchor_ok'] and row['similarity'] >= threshold]


def run(*, engine='fixture', model='embeddinggemma', timeout=30.0):
    if engine not in ('fixture', 'ollama'):
        raise ValueError('Invalid engine')
    dataset = ROOT / 'eval/v1'
    cases = [json.loads(line) for line in (dataset / 'documentos.jsonl').read_text(
        encoding='utf-8').splitlines() if line.strip()]
    with TemporaryDirectory(prefix='campanario_calibracao_inc3b_') as folder:
        utility = _TemporaryUtilityService(Path(folder) / 'utility')
        for name in sorted({c['document'] for c in cases}):
            src = dataset / 'fixtures' / name
            dest = utility.roots[0] / name
            dest.write_bytes(src.read_bytes())
            assert utility.run('library.import', {'path': str(dest), 'confirm': True})['status'] == 'success'
        baseline_hash = sha256(utility.db.read_bytes()).hexdigest()
        backend = (FixtureEmbeddings() if engine == 'fixture' else
                   LoopbackOllamaEmbeddings(model=model, timeout=timeout))
        reader = HybridLocalLibrary(utility.db, embeddings=backend,
                                    min_similarity=0.50, build_budget_seconds=120.0)
        started = perf_counter()
        stamp = reader._file_stamp()
        if stamp is None:
            raise RuntimeError('Temporary fixture SQLite missing')
        reader._ensure_semantics(stamp)
        index_ms = round((perf_counter() - started) * 1000, 2)
        all_rows = []
        for case_id, question, subject, name, fragment in PARAPHRASES:
            data = score_candidates(reader, question, subject, name, fragment)
            all_rows.append(('positive', case_id, question, subject, data))
        for case_id, question, subject in HARD_NEGATIVES:
            data = score_candidates(reader, question, subject)
            all_rows.append(('hard_negative', case_id, question, subject, data))
        lexical = ReadOnlyLocalLibrary(utility.db)
        report_cases=[]
        for kind, case_id, question, subject, data in all_rows:
            ranked = data['top_after_subject_filter']
            top = ranked[0] if ranked else None
            lex = lexical.search(question, subject=subject) if kind == 'hard_negative' else None
            # Regardless of cosine, a semantic candidate is never supported.
            reader.min_similarity = 0.50
            suggestion = reader.search(question, subject=subject) if kind == 'hard_negative' else None
            # Lexical false positives must be reported as such, not hidden by the
            # successful semantic-only safety contract.
            sheet = build_turn_fact_sheet(uuid4(), question, suggestion, fact_lookup_requested=True)
            report_cases.append({
                'id':case_id,'kind':kind,'question':question,'subject':subject,
                'top':top,'second':ranked[1] if len(ranked)>1 else None,
                'top_is_expected_quote':bool(top and top['expected_quote']) if kind=='positive' else None,
                'thresholds':{str(t): {'eligible_count':len(_accepted(ranked,t)),
                    'best_quote':_accepted(ranked,t)[0] if _accepted(ranked,t) else None} for t in THRESHOLDS},
                'lexical_quote_present': bool(lex) if kind == 'hard_negative' else None,
                'lexical_status':lex.status if lex else None,
                'chat_sheet_status_050':sheet.status if kind=='hard_negative' else None,
                'chat_sheet_claim_count_050':len(sheet.claims) if kind=='hard_negative' else None,
                'note': ('No ground truth answer for this question in the synthetic corpus' if kind=='hard_negative' else
                         'Positive: expected exact source and snippet'),
            })
        db_unchanged=sha256(utility.db.read_bytes()).hexdigest()==baseline_hash
        reader._discard_index()
    positives=[r for r in report_cases if r['kind']=='positive']
    negatives=[r for r in report_cases if r['kind']=='hard_negative']
    summary={}
    for threshold in THRESHOLDS:
        key=str(threshold)
        summary[key]={
            'positive_expected_top_accepted':sum(bool(p['thresholds'][key]['best_quote'] and
                p['thresholds'][key]['best_quote']['expected_quote']) for p in positives),
            'positive_total':len(positives),
            'hard_negative_cases_with_accepted_candidate':sum(bool(n['thresholds'][key]['eligible_count']) for n in negatives),
            'hard_negative_total':len(negatives),
            'lexical_hard_negative_quote_present':sum(bool(n['lexical_quote_present']) for n in negatives),
        }
    return {
        'stage':'fase4_inc3b_calibracao_negativos_dificeis',
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'engine':engine,'model':model if engine=='ollama' else 'scripted_fixture_not_real',
        'source':'ONLY synthetic eval/v1/fixtures',
        'user_sqlite_accessed':False,'temp_sqlite_unchanged':db_unchanged,
        'internet_authorized':False,'index_build_ms':index_ms,
        'dataset_sha256':sha256((dataset/'documentos.jsonl').read_bytes()).hexdigest(),
        'summary':summary,'cases':report_cases,
        'semantic_entailment':'NOT_MEASURED',
        'qwen_accuracy':'NOT_MEASURED',
        'recommendation': 'DO NOT auto-enable 0.50; check accepted hard negatives and lexical false relevance first',
        'config_changed':False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',choices=('fixture','ollama'),default='fixture')
    parser.add_argument('--model',default='embeddinggemma')
    parser.add_argument('--timeout',type=float,default=30.0)
    parser.add_argument('--report',default=None)
    args=parser.parse_args()
    report=run(engine=args.engine,model=args.model,timeout=args.timeout)
    target=Path(args.report or f'reports/fase4_inc3b/calibracao_{args.engine}.json')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for threshold, result in report['summary'].items():
        print(f'3B CALIBRACAO ({args.engine}): limiar={threshold}; positivos={result["positive_expected_top_accepted"]}/{result["positive_total"]}; negativos dificeis com candidato={result["hard_negative_cases_with_accepted_candidate"]}/{result["hard_negative_total"]}; negativos FTS5 citados={result["lexical_hard_negative_quote_present"]}/{result["hard_negative_total"]}')
    print('Somente candidatos, nunca fatos. 3B permanece desligado por padrao. Relatorio:',target)
    if not report['temp_sqlite_unchanged']:
        raise SystemExit('ERRO: SQLite temporario alterado inesperadamente')


if __name__=='__main__':
    main()
