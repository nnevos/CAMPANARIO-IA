from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
import zipfile

import pytest

from campanario.config import Settings

ROOT = Path(__file__).resolve().parents[1]


def _load_tool(name):
    spec = importlib.util.spec_from_file_location('campanario_tool_' + name, ROOT / 'tools' / name)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_data_and_zim_paths_are_overridable(monkeypatch, tmp_path):
    data = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    zim = tmp_path / 'CAMPANARIO-DATABASE' / 'zim'
    monkeypatch.setenv('CAMPANARIO_DATA_DIR', str(data))
    monkeypatch.setenv('CAMPANARIO_ZIM_DIR', str(zim))
    conf = Settings(_env_file=None)
    assert conf.data_dir == data
    assert conf.zim_dir == zim
    assert conf.database_path == data / 'desenvolvimento' / 'campanario.db'


def test_migration_uses_sqlite_backup_with_wal_and_preserves_source(tmp_path):
    module = _load_tool('migrar_biblioteca_3pastas.py')
    old = tmp_path / 'old_data'
    old.mkdir()
    db = old / 'desenvolvimento' / 'campanario.db'
    db.parent.mkdir()
    source = sqlite3.connect(db)
    try:
        source.execute('PRAGMA journal_mode=WAL')
        source.execute('CREATE TABLE memory (id INTEGER, phrase TEXT)')
        source.execute('INSERT INTO memory VALUES (1, ?)', ('Teste privado',))
        source.commit()
        (old / 'desenvolvimento' / 'utilidades').mkdir()
        (old / 'desenvolvimento' / 'utilidades' / 'info.txt').write_text('arquivo')
        new = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
        preview = module.migrate(old, new)
        assert not preview['applied'] and not new.exists()
        result = module.migrate(old, new, apply=True)
        assert result['applied']
        assert new.joinpath('desenvolvimento', 'utilidades', 'info.txt').read_text() == 'arquivo'
        with sqlite3.connect(new / 'desenvolvimento' / 'campanario.db') as dst:
            assert dst.execute('SELECT phrase FROM memory').fetchone()[0] == 'Teste privado'
        assert db.exists()
        with pytest.raises(FileExistsError):
            module.migrate(old, new, apply=True)
    finally:
        source.close()


def test_migration_rejects_overlap(tmp_path):
    module = _load_tool('migrar_biblioteca_3pastas.py')
    parent = tmp_path / 'dados'
    parent.mkdir()
    with pytest.raises(ValueError):
        module.migrate(parent, parent / 'filho')


def test_portable_zip_excludes_private_and_heavy_files(tmp_path):
    module = _load_tool('exportar_campanario.py')
    root = tmp_path / 'CAMPANARIO-IA'
    (root / 'src' / 'campanario').mkdir(parents=True)
    (root / 'src' / 'campanario' / 'main.py').write_text('print(42)')
    (root / 'vozes').mkdir()
    (root / 'vozes' / 'morgana.onnx').write_bytes(b'VOICEWEIGHT' * 100)
    (root / '.venv' / 'Scripts').mkdir(parents=True)
    (root / '.venv' / 'Scripts' / 'python.exe').write_bytes(b'BINARY')
    (root / '.env').write_text('CAMPANARIO_TOKEN=SECRET_TOKEN_SHOULD_NOT_LEAK')
    (root / 'data').mkdir()
    (root / 'data' / 'personal.db').write_bytes(b'SECRET_DB_BYTES')
    (root / 'README.md').write_text('Projeto')
    archive = tmp_path / 'FONTE_PORTATIL.zip'
    module.export(root, archive)
    with zipfile.ZipFile(archive) as z:
        names = set(z.namelist())
        assert 'src/campanario/main.py' in names
        assert 'ESTADO_DO_PROJETO.md' in names
        assert 'RECURSOS_EXTERNOS.json' in names
        assert '.env' not in names
        assert 'data/personal.db' not in names
        assert '.venv/Scripts/python.exe' not in names
        assert 'vozes/morgana.onnx' not in names
        assert b'SECRET_TOKEN_SHOULD_NOT_LEAK' not in archive.read_bytes()


def test_windows_launcher_prefers_external_environment_and_has_fallback():
    vbs = (ROOT / 'CAMPANARIO.vbs').read_text()
    assert 'CAMPANARIO-PYTHON\\.venv\\Scripts\\pythonw.exe' in vbs
    assert 'If Not fs.FileExists(pythonw)' in vbs
    assert '.venv\\Scripts\\pythonw.exe' in vbs
    ps1 = (ROOT / 'ATIVAR_SEPARACAO.ps1').read_text()
    assert 'CAMPANARIO-DATABASE' in ps1
    assert 'CAMPANARIO-PYTHON' in ps1
    assert 'if (!$Apply)' in ps1
