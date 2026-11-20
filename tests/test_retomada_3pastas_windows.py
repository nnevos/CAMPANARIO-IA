"""Regression: Windows migration was copied, but python -c quote parsing failed."""
from __future__ import annotations

from contextlib import closing
import importlib.util
from pathlib import Path
import sqlite3

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str):
    name = "resume_test_" + relative.replace("/", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def trees(tmp_path):
    migration = _load("tools/migrar_biblioteca_3pastas.py")
    old = tmp_path / "old"
    old.mkdir()
    (old / "documentos").mkdir()
    (old / "documentos" / "memoria.txt").write_text("conteudo privado nao deve ir para logs", encoding="utf-8")
    (old / "desenvolvimento").mkdir()
    db_path = old / "desenvolvimento" / "campanario.db"
    db = sqlite3.connect(db_path)
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE memoria (chave TEXT PRIMARY KEY, texto TEXT)")
        db.execute("INSERT INTO memoria VALUES ('foo', 'valor secreto original')")
        db.commit()
        dest = tmp_path / "CAMPANARIO-DATABASE" / "dados"
        copied = migration.migrate(old, dest, apply=True)
        assert copied["applied"]
        yield old, dest
    finally:
        db.close()


def test_verify_existing_sqlite_wal_and_hashes_without_modification(trees):
    tool = _load("tools/verificar_copia_3pastas.py")
    old, dest = trees
    source_bytes = (old / "documentos" / "memoria.txt").read_bytes()
    destination_bytes = (dest / "documentos" / "memoria.txt").read_bytes()
    outcome = tool.verify_copy(old, dest)
    assert outcome["result"] == "OK"
    assert outcome["verified_files"] == 2
    assert outcome["verified_sqlite"] == 1
    assert (old / "documentos" / "memoria.txt").read_bytes() == source_bytes
    assert (dest / "documentos" / "memoria.txt").read_bytes() == destination_bytes
    assert "valor secreto" not in str(outcome)


def test_verify_blocks_different_text_file(trees):
    tool = _load("tools/verificar_copia_3pastas.py")
    old, dest = trees
    (dest / "documentos" / "memoria.txt").write_text("alterado")
    with pytest.raises(ValueError, match="Arquivo de dados divergente"):
        tool.verify_copy(old, dest)


def test_verify_blocks_sqlite_change_even_with_same_row_count(trees):
    tool = _load("tools/verificar_copia_3pastas.py")
    old, dest = trees
    with closing(sqlite3.connect(dest / "desenvolvimento" / "campanario.db")) as db:
        db.execute("UPDATE memoria SET texto='valor alterado' WHERE chave='foo'")
        db.commit()
    with pytest.raises(ValueError, match="SQLite divergente"):
        tool.verify_copy(old, dest)


def test_verify_blocks_extra_file_without_touching_it(trees):
    tool = _load("tools/verificar_copia_3pastas.py")
    old, dest = trees
    extra = dest / "arquivo_intruso.txt"
    extra.write_text("proibido")
    with pytest.raises(ValueError, match="Lista de arquivos diferente"):
        tool.verify_copy(old, dest)
    assert extra.read_text() == "proibido"


def test_verify_blocks_nested_destination(trees):
    tool = _load("tools/verificar_copia_3pastas.py")
    old, _ = trees
    with pytest.raises(ValueError, match="sobrepor"):
        tool.verify_copy(old, old / "nest")


def test_config_file_verifier_respects_env_without_db_side_effects(tmp_path, monkeypatch):
    tool = _load("tools/verificar_caminhos_3pastas.py")
    data = tmp_path / "CAMPANARIO-DATABASE" / "dados"
    zim = tmp_path / "CAMPANARIO-DATABASE" / "zim"
    data.mkdir(parents=True)
    zim.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CAMPANARIO_DATA_DIR", str(data))
    monkeypatch.setenv("CAMPANARIO_ZIM_DIR", str(zim))
    good, msg = tool.verify(data, zim)
    assert good and "CONFIGURACAO EXTERNA OK" in msg
    assert not (data / "desenvolvimento" / "campanario.db").exists()
    good, msg = tool.verify(tmp_path / "outra", zim)
    assert not good and "divergente" in msg


def test_powershell_scripts_no_python_c_and_resume_has_safety_check():
    activate = (ROOT / "ATIVAR_SEPARACAO.ps1").read_text(encoding="utf-8")
    test = (ROOT / "TESTAR_3_PASTAS.ps1").read_text(encoding="utf-8")
    for script in (activate, test):
        assert "& $newPython -c " not in script
        assert "& $python -c " not in script
        assert "verificar_caminhos_3pastas.py" in script
    assert "[switch]$Resume" in activate
    assert "if (!$Resume -and $dataExists)" in activate
    assert "RETOMADA BLOQUEADA" in activate
    assert "verificar_copia_3pastas.py" in activate
    assert "Move-Item -LiteralPath $tempEnv" in activate
    assert "Copy-Item -LiteralPath (Join-Path $backupDir '.env')" in activate


def test_verifier_cli_outputs_no_private_data(trees, capsys):
    tool = _load("tools/verificar_copia_3pastas.py")
    old, dest = trees
    code = tool.main(["--source", str(old), "--destination", str(dest)])
    out = capsys.readouterr().out
    assert code == 0
    assert '"result": "OK"' in out
    assert "valor secreto original" not in out
    assert "conteudo privado" not in out
