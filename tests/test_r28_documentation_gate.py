"""R2.8: ensure project continuity documents cannot be accidentally omitted."""
from pathlib import Path
import importlib.util


def gate_module():
    location = Path(__file__).resolve().parents[1] / 'scripts/check_documentation_gate.py'
    spec = importlib.util.spec_from_file_location('campanario_doc_gate', location)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_repository_documentation_passes():
    root = Path(__file__).resolve().parents[1]
    assert gate_module().validate(root) == []


def test_missing_fails_closed(tmp_path):
    errors = gate_module().validate(tmp_path)
    assert errors and any('ROADMAP.md' in error for error in errors)


def test_stale_checkpoint_fails_closed(tmp_path):
    gate = gate_module()
    source = Path(__file__).resolve().parents[1]
    for rel in gate.REQUIRED:
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text((source / rel).read_text(encoding='utf-8').replace('R2.8', 'R2.7'), encoding='utf-8')
    errors = gate.validate(tmp_path)
    assert any('artefato de entrega ausente' in error for error in errors)


def test_change_gate_requires_all_four_docs(monkeypatch, tmp_path):
    gate = gate_module()
    monkeypatch.setattr(gate.subprocess, 'check_output', lambda *a, **k: 'src/campanario/utilities/api.py\ndocs/current/ROADMAP.md\n')
    errors = gate.validate_changed_files(tmp_path, 'a'*40)
    assert len(errors) == 3
    assert any('FAILSAFE_V9_CEREBROS.md' in item for item in errors)
    assert gate.validate_changed_files(tmp_path, 'not-a-sha')


def test_change_gate_accepts_synced_docs(monkeypatch, tmp_path):
    gate = gate_module()
    monkeypatch.setattr(gate.subprocess, 'check_output', lambda *a, **k: 'src/campanario/utilities/api.py\n' + '\n'.join(gate.MUST_CHANGE))
    assert gate.validate_changed_files(tmp_path, 'b'*40) == []
