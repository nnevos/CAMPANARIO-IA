"""Guard against the PowerShell -c quoting regression on Windows."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def _smoke():
    path = ROOT / 'tools' / 'testar_imports_voz_unificado.py'
    spec = importlib.util.spec_from_file_location('testar_imports_voz_unificado', path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_windows_powershell_calls_file_not_inline_python():
    source = (ROOT / 'TESTAR_PYTHON_UNIFICADO.ps1').read_text(encoding='utf-8')
    assert "& $python $voiceSmoke" in source
    assert "tools\\testar_imports_voz_unificado.py" in source
    assert "& $python -c" not in source
    assert "& $python -m pytest @tests -q" in source


def test_import_smoke_success_with_fixtures(monkeypatch, capsys):
    voice = ModuleType('campanario.voice25')
    voice._piper_executable = lambda: 'C:/dummy/piper.exe'
    monkeypatch.setitem(sys.modules, 'campanario.voice25', voice)
    piper = ModuleType('piper')
    piper.__path__ = []
    voice_module = ModuleType('piper.voice')
    voice_module.PiperVoice = object
    monkeypatch.setitem(sys.modules, 'piper', piper)
    monkeypatch.setitem(sys.modules, 'piper.voice', voice_module)
    pocket = ModuleType('pocket_tts')
    pocket.TTSModel = object
    monkeypatch.setitem(sys.modules, 'pocket_tts', pocket)
    torch = ModuleType('torch')
    torch.__version__ = '2.14.1+cu130'
    torch.version = SimpleNamespace(cuda='13.0')
    torch.cuda = SimpleNamespace(is_available=lambda: True)
    monkeypatch.setitem(sys.modules, 'torch', torch)
    assert _smoke().main() == 0
    output = capsys.readouterr().out
    assert 'PIPER API: OK' in output
    assert 'POCKET TTS: import OK' in output
    assert 'GPU disponivel: True' in output


def test_import_smoke_fails_closed(monkeypatch, capsys):
    voice = ModuleType('campanario.voice25')
    voice._piper_executable = lambda: None
    monkeypatch.setitem(sys.modules, 'campanario.voice25', voice)
    piper = ModuleType('piper')
    piper.__path__ = []
    voice_module = ModuleType('piper.voice')
    voice_module.PiperVoice = object
    monkeypatch.setitem(sys.modules, 'piper', piper)
    monkeypatch.setitem(sys.modules, 'piper.voice', voice_module)
    pocket = ModuleType('pocket_tts')
    # Missing TTSModel must reject the environment.
    monkeypatch.setitem(sys.modules, 'pocket_tts', pocket)
    assert _smoke().main() == 1
    assert 'IMPORTS DE VOZ: FALHA' in capsys.readouterr().err
