"""R3.12: deterministic acceptance gate for *real loopback Ollama* classification.

The corpus is synthetic and small: passing means only a bounded technical gate,
NOT production homologation or comprehensive semantic understanding. Missing real
Ollama fails closed (exit 3); substandard scores fail (exit 2).
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time

from evaluate_semantic_relations import CORPUS, CLASSES, classify_from_model, score

# A supplement emphasizing temporal scope, negation, attribution, and modality.
# Each example is fictional; answer labels were annotated in advance.
CHALLENGES = [
    ('O pagamento foi aprovado ontem.', 'O pagamento foi rejeitado ontem.', 'possible_contradiction'),
    ('A entrega ocorreu em março.', 'A entrega aconteceu no mês de março.', 'possible_paraphrase'),
    ('O servidor caiu às 10h.', 'O servidor ficou indisponível às 10h.', 'possible_paraphrase'),
    ('O envio estava previsto para segunda-feira.', 'O envio ocorreu na segunda-feira.', 'none'),
    ('A comissão talvez aprove a licença.', 'A comissão aprovou a licença.', 'none'),
    ('Segundo Paulo, a máquina foi desligada.', 'A máquina foi desligada.', 'none'),
    ('O documento diz que Ana alterou o arquivo.', 'Ana alterou o arquivo.', 'none'),
    ('O equipamento estava ativo às 8h.', 'O equipamento estava inativo às 8h.', 'possible_contradiction'),
    ('A taxa subiu de 10% para 12%.', 'A taxa foi inicialmente 10%.', 'none'),
    ('O contrato terminou em 2023.', 'O contrato expirou em 2023.', 'possible_paraphrase'),
    ('Não se confirmou a presença de Carla.', 'Carla estava ausente.', 'none'),
    ('O relatório cita 12 unidades em janeiro.', 'O relatório registra 15 unidades em janeiro.', 'possible_contradiction'),
    ('O evento ocorreu dia 4.', 'O evento ocorreu dia 5.', 'possible_contradiction'),
    ('A máquina falhou porque o cabo se rompeu.', 'O cabo estava rompido.', 'none'),
    ('A conta possui saldo de 500 reais.', 'O saldo da conta é de R$ 500.', 'possible_paraphrase'),
    ('O projeto foi aprovado sob condição de auditoria.', 'O projeto foi aprovado sem condições.', 'possible_contradiction'),
]
CORPUS_FULL = CORPUS + CHALLENGES
THRESHOLDS = {'accuracy': 0.85, 'macro_f1': 0.80,
              'contradiction_recall': 0.85, 'repeat_agreement': 0.95,
              'false_contradictions_on_noncontradictions': 0}


def corpus_sha256():
    raw = json.dumps(CORPUS_FULL, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def compute_gate(gold: list[str], runs: list[list[str]]) -> dict:
    """Refuse incomplete/invalid labels; require repeat consistency and safety."""
    if len(runs) != 2 or not gold or any(len(run) != len(gold) for run in runs):
        raise ValueError('requires two complete prediction runs')
    if any(label not in CLASSES for run in runs for label in run):
        raise ValueError('unknown predicted label')
    metrics = score(gold, runs[0])
    macro_f1 = sum(metrics['by_class'][label]['f1'] for label in CLASSES) / len(CLASSES)
    repeat_agreement = sum(a == b for a, b in zip(*runs)) / len(gold)
    false_contradictions = sum(g != 'possible_contradiction' and p == 'possible_contradiction'
                               for g, p in zip(gold, runs[0]))
    observed = {
        'accuracy': metrics['accuracy'], 'macro_f1': round(macro_f1, 4),
        'contradiction_recall': metrics['by_class']['possible_contradiction']['recall'],
        'repeat_agreement': round(repeat_agreement, 4),
        'false_contradictions_on_noncontradictions': false_contradictions,
    }
    reasons = [f'{name}: observado {observed[name]}, exigido {minimum}'
               for name, minimum in THRESHOLDS.items()
               if (observed[name] > minimum if name == 'false_contradictions_on_noncontradictions'
                   else observed[name] < minimum)]
    return {'technical_gate': 'PASS' if not reasons else 'BLOCKED',
            'reasons': reasons, 'observed': observed, 'thresholds': THRESHOLDS,
            'score': metrics, 'second_run_score': score(gold, runs[1]),
            'distribution': dict(Counter(gold))}


def measure_model(model: str, predict=classify_from_model) -> dict:
    """Test real model twice; no simulated model is accepted by the CLI."""
    if not re.fullmatch(r'[a-zA-Z0-9_.:/-]{1,90}', model):
        raise ValueError('invalid model identifier')
    runs = []
    started = time.monotonic()
    for _ in range(2):
        predictions = []
        for left, right, _ in CORPUS_FULL:
            predictions.append(predict(left, right, model))
        runs.append(predictions)
    result = compute_gate([row[2] for row in CORPUS_FULL], runs)
    result.update({'model': model, 'sample_count': len(CORPUS_FULL),
                   'elapsed_seconds': round(time.monotonic()-started, 2),
                   'corpus_sha256': corpus_sha256(),
                   'run_type': 'live_loopback_ollama',
                   'scope': 'synthetic semantic relation classification only',
                   'production_homologation': False,
                   'limitations': ['Não mede veracidade externa, OCR, raciocínio completo, Windows/Database ou documentos reais',
                                   'PASS não autoriza promover afirmações do modelo a fatos',
                                   'Exige revisão humana independente e ensaio real para homologação final']})
    return result


def save_report(report: dict, output_dir: Path, repo_root: Path) -> Path:
    """Only save generated test reports under sibling CAMPANARIO-DATABASE.

    Refuse symlinked database roots and destinations escaping that repository.
    Never create a second database or write inside CAMPANARIO-IA.
    """
    expected = repo_root.resolve().parent / 'CAMPANARIO-DATABASE'
    if not expected.is_dir() or expected.is_symlink():
        raise ValueError('external CAMPANARIO-DATABASE not available')
    base = expected.resolve()
    dest = output_dir.resolve()
    if not dest.is_relative_to(base) or dest == base:
        raise ValueError('reports must remain inside CAMPANARIO-DATABASE')
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    name = f'R312_HOMOLOGACAO_{stamp}_{report["corpus_sha256"][:8]}.json'
    path = dest / name
    with path.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description='Gate factual R3.12 com Ollama loopback real')
    ap.add_argument('--model', required=True, help='Nome de modelo local instalado no Ollama')
    ap.add_argument('--output-dir', type=Path, help='Diretorio de relatorios DENTRO de CAMPANARIO-DATABASE')
    args = ap.parse_args(argv)
    try:
        report = measure_model(args.model)
    except (RuntimeError, OSError, ValueError, TimeoutError, KeyError, TypeError,
            json.JSONDecodeError) as exc:
        print(json.dumps({'technical_gate': 'INCONCLUSIVE', 'production_homologation': False,
                          'reason': f'Local model unavailable or invalid: {type(exc).__name__}',
                          'corpus_sha256': corpus_sha256()}, ensure_ascii=False, indent=2))
        return 3
    if args.output_dir:
        try:
            saved = save_report(report, args.output_dir, Path(__file__).resolve().parents[1])
            print('Relatorio salvo no Database externo:', saved)
        except (OSError, ValueError) as exc:
            print('Relatorio NAO salvo:', type(exc).__name__)
            report['report_persistence'] = 'failed'
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['technical_gate'] == 'PASS' else 2


if __name__ == '__main__':
    sys.exit(main())
