"""Tests for the scoring and safe *real model* gate; mocked tests are NOT homologation."""
from pathlib import Path
import importlib.util
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location('homologate_factual', ROOT / 'scripts/homologate_factual.py')
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_corpus_annotated_with_hard_cases():
    m = load()
    assert len(m.CORPUS_FULL) >= 30
    assert set(g for _, _, g in m.CORPUS_FULL) == set(m.CLASSES)
    assert len(m.corpus_sha256()) == 64


def test_perfect_gate_pass_is_not_production_homologation():
    m = load()
    gold = [row[2] for row in m.CORPUS_FULL]
    result = m.compute_gate(gold, [gold, gold])
    assert result['technical_gate'] == 'PASS'
    assert result['observed']['false_contradictions_on_noncontradictions'] == 0


def test_always_none_blocked():
    m = load()
    gold = [row[2] for row in m.CORPUS_FULL]
    result = m.compute_gate(gold, [['none'] * len(gold)] * 2)
    assert result['technical_gate'] == 'BLOCKED'


def test_false_contradiction_on_uncertain_evidence_blocks():
    m = load()
    gold = [row[2] for row in m.CORPUS_FULL]
    bad = gold.copy()
    bad[gold.index('none')] = 'possible_contradiction'
    result = m.compute_gate(gold, [bad, bad])
    assert result['technical_gate'] == 'BLOCKED'
    assert result['observed']['false_contradictions_on_noncontradictions'] == 1


def test_instability_blocks():
    m = load()
    gold = [row[2] for row in m.CORPUS_FULL]
    bad = gold.copy()
    bad[:3] = ['none'] * 3
    assert m.compute_gate(gold, [gold, bad])['technical_gate'] == 'BLOCKED'


def test_partial_or_unknown_labels_refused():
    m = load()
    gold = [row[2] for row in m.CORPUS_FULL]
    with pytest.raises(ValueError):
        m.compute_gate(gold, [gold])
    with pytest.raises(ValueError):
        m.compute_gate(gold, [gold, gold[:-1]])
    with pytest.raises(ValueError):
        m.compute_gate(gold, [gold, ['factual'] * len(gold)])


def test_mock_live_report_explicitly_not_homologation():
    m = load()
    answers = iter([g for _, _, g in m.CORPUS_FULL] * 2)
    result = m.measure_model('gemma3:4b', lambda a, b, model: next(answers))
    assert result['technical_gate'] == 'PASS'
    assert result['run_type'] == 'live_loopback_ollama'
    assert result['production_homologation'] is False


def test_model_missing_cli_inconclusive(monkeypatch, capsys):
    m = load()
    monkeypatch.setattr(m, 'measure_model', lambda _: (_ for _ in ()).throw(RuntimeError('offline')))
    assert m.main(['--model', 'gemma3:4b']) == 3
    assert 'INCONCLUSIVE' in capsys.readouterr().out


def test_reports_restricted_to_external_database(tmp_path):
    m = load()
    ia = tmp_path / 'CAMPANARIO-IA'
    ia.mkdir()
    db = tmp_path / 'CAMPANARIO-DATABASE'
    db.mkdir()
    report = {'corpus_sha256': 'a' * 64, 'technical_gate': 'BLOCKED'}
    with pytest.raises(ValueError):
        m.save_report(report, ia / 'reports', ia)
    saved = m.save_report(report, db / 'dados' / 'avaliacoes_factual', ia)
    assert saved.is_file()
    assert 'BLOCKED' in saved.read_text()
