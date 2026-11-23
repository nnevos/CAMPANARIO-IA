"""R3.11 benchmark: annotated artificial text only, optionally real loopback Ollama.

Exit code 3 means model unavailable, not a passed live evaluation. All numbers
refer to this tiny artificial sample, not general-language performance.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from campanario.brains.case_semantic_review import _local_model  # noqa: E402

CORPUS = [
    ('O contrato foi aprovado pela comissão.', 'A comissão aprovou o contrato.', 'possible_paraphrase'),
    ('O contrato foi aprovado pela comissão.', 'A comissão rejeitou o contrato.', 'possible_contradiction'),
    ('A licença foi renovada em julho.', 'A licença continua válida após a renovação de julho.', 'possible_support'),
    ('O pagamento foi suspenso.', 'O pagamento foi interrompido.', 'possible_paraphrase'),
    ('O servidor estava ativo às 18h.', 'Às 18h, o servidor estava desligado.', 'possible_contradiction'),
    ('A empresa foi fundada em 2019.', 'A empresa foi criada no ano de 2019.', 'possible_paraphrase'),
    ('O funcionário poderia ter saído mais cedo.', 'O funcionário saiu mais cedo.', 'none'),
    ('O pagamento não foi autorizado ontem.', 'O pagamento foi autorizado hoje.', 'none'),
    ('Segundo a testemunha, o carro era azul.', 'O carro era azul.', 'none'),
    ('O relatório afirma que o arquivo foi apagado.', 'O arquivo foi apagado.', 'none'),
    ('O prazo terminou em maio.', 'O prazo começou em maio.', 'none'),
    ('O documento foi assinado por Ana.', 'Ana assinou o documento.', 'possible_paraphrase'),
    ('A taxa contratada é de 10%.', 'A taxa contratada é de 20%.', 'possible_contradiction'),
    ('Não há confirmação de acesso.', 'Houve acesso confirmado.', 'none'),
    ('Um exame encontrou um erro no arquivo.', 'O arquivo apresenta um erro encontrado em exame.', 'possible_paraphrase'),
    ('A câmera parou de gravar às 18h39.', 'A gravação da câmera foi interrompida às 18h39.', 'possible_paraphrase'),
    ('O portão estava aberto às 21h.', 'O portão estava fechado às 21h.', 'possible_contradiction'),
    ('A reunião estava agendada para terça-feira.', 'A reunião aconteceu na terça-feira.', 'none'),
]
CLASSES = ('possible_paraphrase', 'possible_contradiction', 'possible_support', 'none')


def score(gold: list[str], predicted: list[str]) -> dict:
    if len(gold) != len(predicted):
        raise ValueError('incomplete predictions')
    confusion = {name: dict(Counter(p for g, p in zip(gold, predicted) if g == name)) for name in CLASSES}
    metrics = {}
    for label in CLASSES:
        tp = sum(g == label and p == label for g, p in zip(gold, predicted))
        fp = sum(g != label and p == label for g, p in zip(gold, predicted))
        fn = sum(g == label and p != label for g, p in zip(gold, predicted))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        metrics[label] = {'support': sum(g == label for g in gold), 'precision': round(precision, 3),
                          'recall': round(recall, 3), 'f1': round(2*precision*recall/(precision+recall), 3) if precision+recall else 0.0}
    return {'total': len(gold), 'correct': sum(g == p for g, p in zip(gold, predicted)),
            'accuracy': round(sum(g == p for g, p in zip(gold, predicted))/len(gold), 3),
            'by_class': metrics, 'confusion': confusion}


def classify_from_model(left: str, right: str, model: str) -> str:
    try:
        result = _local_model({'quotes': [{'id': 0, 'text': left}, {'id': 1, 'text': right}]}, model)
    except (OSError, ValueError, TimeoutError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError('modelo local indisponivel ou resposta invalida') from exc
    pairs = result.get('pairs') if isinstance(result, dict) else None
    if not isinstance(pairs, list):
        raise RuntimeError('modelo retornou JSON fora do contrato')
    labels = [p.get('kind') for p in pairs if isinstance(p, dict)
              and {p.get('left'), p.get('right')} == {0, 1}
              and p.get('kind') in CLASSES[:-1]]
    # Ambiguous multi-label output must NOT be arbitrarily judged correct.
    return labels[0] if len(set(labels)) == 1 else 'none'


def main(argv=None):
    ap = argparse.ArgumentParser(description='Avaliacao semantica artificial e local, sem dados pessoais')
    ap.add_argument('--model', default='', help='modelo instalado no Ollama; vazio testa so avaliador offline')
    args = ap.parse_args(argv)
    gold = [row[2] for row in CORPUS]
    print('R3.11: corpus sintetico, sem dados privados; n=', len(gold))
    print('Distribuicao anotada:', dict(Counter(gold)))
    if not args.model:
        print('AVALIADOR OFFLINE: pronto. Nenhuma taxa de acerto de LLM foi medida.')
        print(json.dumps(score(gold, gold), ensure_ascii=False))
        return 0
    predicted = []
    for idx, (left, right, _) in enumerate(CORPUS, 1):
        try:
            predicted.append(classify_from_model(left, right, args.model))
        except RuntimeError as exc:
            print(f'INCONCLUSIVO: {exc} no exemplo {idx}; nenhum score parcial e aprovado.')
            return 3
    print('TESTE AO VIVO COM MODELO LOCAL:', args.model)
    print(json.dumps(score(gold, predicted), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
