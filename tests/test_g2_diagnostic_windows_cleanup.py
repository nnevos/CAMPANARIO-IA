"""Windows cleanup contract: delete Chroma only after its owning process exits."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _module():
    path = Path(__file__).resolve().parents[1] / 'tools/maintenance/DIAGNOSTICAR_BUSCA_SEMANTICA.py'
    spec = importlib.util.spec_from_file_location('g2_diagnostic_windows', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_diagnostic_runs_in_child_and_cleans_after_exit(monkeypatch, tmp_path):
    diag = _module()
    folder = tmp_path / 'diagnostic'
    folder.mkdir()
    (folder / 'data_level0.bin').write_bytes(b'fake')
    monkeypatch.setattr(diag.tempfile, 'mkdtemp', lambda **kwargs: str(folder))
    calls = []
    def run(argv, **kwargs):
        calls.append(('run', argv))
        assert (folder / 'data_level0.bin').exists()
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(diag.subprocess, 'run', run)
    assert diag.main() == 0
    assert calls[0][0] == 'run'
    assert '--diagnostic-worker' in calls[0][1]
    assert not folder.exists()


def test_diagnostic_preserves_result_if_cleanup_locked(monkeypatch, tmp_path, capsys):
    diag = _module()
    folder = tmp_path / 'locked'
    folder.mkdir()
    monkeypatch.setattr(diag.tempfile, 'mkdtemp', lambda **kwargs: str(folder))
    monkeypatch.setattr(diag.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=0))
    monkeypatch.setattr(diag.shutil, 'rmtree', lambda path: (_ for _ in ()).throw(PermissionError('locked')))
    monkeypatch.setattr(diag.time if hasattr(diag, 'time') else __import__('time'), 'sleep', lambda *_: None)
    assert diag.main() == 0
    assert '[AVISO]' in capsys.readouterr().out
