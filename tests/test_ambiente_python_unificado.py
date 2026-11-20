"""Tests for the staged, reversible three-folder Python/voice migration."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location("verifier_unified", ROOT / "tools" / "verificar_python_unificado.py")
assert SPEC and SPEC.loader
VERIFY = module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def test_profile_preserves_original_voice_versions():
    profile = json.loads((ROOT / "config" / "ambiente_unificado.json").read_text(encoding="utf-8"))
    assert profile["python"] == "3.12.10"
    assert profile["packages_to_verify"] == {
        "piper-tts": "1.8.0", "pocket-tts": "4.0.1", "torch": "2.14.1+cu130",
        "torchaudio": "2.11.0+cu130", "torchvision": "0.29.1+cu130",
        "pytest-asyncio": "1.5.0",
    }
    assert profile["indexes"]["pytorch_cuda"].startswith("https://download.pytorch.org/")


def test_verifier_rejects_wrong_environment(tmp_path, monkeypatch):
    root = tmp_path / "CAMPANARIO-IA"
    (root / "config").mkdir(parents=True)
    (root / "config" / "ambiente_unificado.json").write_bytes((ROOT / "config" / "ambiente_unificado.json").read_bytes())
    (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (root / "uv.lock").write_text("version=1\n", encoding="utf-8")
    _, errors = VERIFY.check_environment(root, tmp_path / "CAMPANARIO-PYTHON" / ".venv")
    assert any("nao pertence" in error for error in errors)


def test_verifier_rejects_missing_pinned_packages(tmp_path, monkeypatch):
    root = tmp_path / "CAMPANARIO-IA"
    (root / "config").mkdir(parents=True)
    (root / "config" / "ambiente_unificado.json").write_bytes((ROOT / "config" / "ambiente_unificado.json").read_bytes())
    (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (root / "uv.lock").write_text("version=1\n", encoding="utf-8")
    prefix = tmp_path / "CAMPANARIO-PYTHON" / ".venv"
    monkeypatch.setattr(sys, "prefix", str(prefix))
    monkeypatch.setattr(VERIFY.metadata, "version", lambda name: (_ for _ in ()).throw(VERIFY.metadata.PackageNotFoundError(name)))
    _, errors = VERIFY.check_environment(root, prefix)
    assert any("piper-tts" in e for e in errors)
    assert any("torch" in e for e in errors)


def test_mark_required_before_any_data_migration():
    script = (ROOT / "ATIVAR_SEPARACAO.ps1").read_text(encoding="utf-8")
    before_copy = script.split("& $py @pythonArgs $migration --source $oldData --destination $newData --apply")[0]
    assert "--require-marker" in before_copy
    assert "uv pip check" in before_copy
    assert "uv sync" not in before_copy.replace("#", "")


def test_setup_is_staged_no_automatic_data_activation():
    script = (ROOT / "PREPARAR_PYTHON_UNIFICADO.ps1").read_text(encoding="utf-8")
    assert "[switch]$Apply" in script
    assert "--frozen --inexact" in script
    assert "--dry-run" in script
    assert "uv pip check" in script
    assert "--mark" in script
    assert "ATIVAR_SEPARACAO.ps1" not in script
    assert "CAMPANARIO_DATA_DIR=" not in script


def test_launcher_does_not_prune_optional_voice_packages():
    bat = (ROOT / "PREPARAR_PC.bat").read_text(encoding="utf-8")
    assert "PREPARAR_PYTHON_UNIFICADO.ps1" in bat
    assert "uv sync --extra desktop" not in bat


def test_exporter_excludes_real_data_and_contains_new_runtime_script(tmp_path):
    from tools.exportar_campanario import export

    root = tmp_path / "CAMPANARIO-IA"
    (root / "tools").mkdir(parents=True)
    (root / "tools" / "verificar_python_unificado.py").write_text("#code\n", encoding="utf-8")
    (root / "PREPARAR_PYTHON_UNIFICADO.ps1").write_text("#powershell\n", encoding="utf-8")
    (root / ".env").write_text("SECRET=yes\n", encoding="utf-8")
    (root / ".venv" / "Lib").mkdir(parents=True)
    (root / ".venv" / "Lib" / "sensitive.py").write_text("oops\n", encoding="utf-8")
    out = tmp_path / "portable.zip"
    export(root, out)
    import zipfile
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    assert "PREPARAR_PYTHON_UNIFICADO.ps1" in names
    assert "tools/verificar_python_unificado.py" in names
    assert ".env" not in names
    assert ".venv/Lib/sensitive.py" not in names


def test_previous_lock_left_unchanged_in_work_tree():
    import tomllib
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["requires-python"] == ">=3.12,<3.13"
    assert "desktop" in pyproject["project"]["optional-dependencies"]
    assert "uv.lock" in {x.name for x in ROOT.iterdir()}
