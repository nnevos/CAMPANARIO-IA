"""Synthetic tests; these do not claim to measure a real Ollama model."""
from pathlib import Path
import importlib.util
import pytest

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_activation_no_model_no_ocr(monkeypatch):
    m = load('activate_local_capabilities')
    monkeypatch.setattr(m.shutil, 'which', lambda name: None)
    result = m.inspect({}, set())
    assert all(result['settings'][key] == 'false' for key in (
        'CAMPANARIO_CASE_OCR_ENABLED', 'CAMPANARIO_CASE_VISION_ENABLED',
        'CAMPANARIO_CASE_CLAIMS_SEMANTIC_ENABLED', 'CAMPANARIO_CASE_SEMANTIC_ENABLED'))
    assert 'CAMPANARIO_WEB_AUTO_SEARCH' not in result['settings']
    assert 'CAMPANARIO_BRAINS_V9_ENABLED' not in result['settings']


def test_activation_matches_model_and_prevents_duplicates():
    m = load('activate_local_capabilities')
    result = m.inspect({'CAMPANARIO_MODEL_NAME': 'gemma3:4b'},
                       {'gemma3:4b', 'embeddinggemma:latest', 'llava:7b'})
    assert result['settings']['CAMPANARIO_CASE_CLAIMS_SEMANTIC_ENABLED'] == 'true'
    assert result['settings']['CAMPANARIO_CASE_VISION_ENABLED'] == 'true'
    assert result['settings']['CAMPANARIO_CASE_SEMANTIC_ENABLED'] == 'true'
    text = '# c\nCAMPANARIO_CASE_SEMANTIC_ENABLED=false\nCAMPANARIO_CASE_SEMANTIC_ENABLED=false\nSECRET=do-not-change\n'
    updated = m.update_env(text, result['settings'])
    assert updated.count('CAMPANARIO_CASE_SEMANTIC_ENABLED=') == 1
    assert 'SECRET=do-not-change' in updated
    assert m.update_env(updated, result['settings']) == updated


def test_apply_private_backup_and_rollback(tmp_path):
    m = load('activate_local_capabilities')
    env = tmp_path / '.env'
    env.write_text('CAMPANARIO_CASE_SEMANTIC_ENABLED=false\nSECRET=private\n')
    backup = m.apply(env, {'CAMPANARIO_CASE_SEMANTIC_ENABLED': 'true'})
    assert backup.exists()
    assert 'false' in backup.read_text()
    assert 'true' in env.read_text()
    assert m.apply(env, {'CAMPANARIO_CASE_SEMANTIC_ENABLED': 'true'}) == env
    assert len(list(tmp_path.glob('.env.backup*'))) == 1


def test_no_private_env_no_creation(tmp_path):
    m = load('activate_local_capabilities')
    with pytest.raises(ValueError):
        m.apply(tmp_path / '.env', {'CAMPANARIO_CASE_OCR_ENABLED': 'true'})


def test_score_perfect_confusion_and_precision():
    m = load('evaluate_semantic_relations')
    gold = [p[2] for p in m.CORPUS]
    assert len(gold) >= 16
    perfect = m.score(gold, gold)
    assert perfect['accuracy'] == 1.0
    predictions = ['none'] * len(gold)
    result = m.score(gold, predictions)
    assert result['accuracy'] < 1.0
    assert result['by_class']['possible_paraphrase']['recall'] == 0.0
    with pytest.raises(ValueError):
        m.score(gold, predictions[:-1])


def test_model_bad_output_is_inconclusive(monkeypatch):
    m = load('evaluate_semantic_relations')
    monkeypatch.setattr(m, '_local_model', lambda *a: {'pairs': 'invalid'})
    with pytest.raises(RuntimeError):
        m.classify_from_model('Primeiro', 'Segundo', 'local')
