"""Copy a stopped Campanario data tree into a new location without deleting the source.

Standard library only. SQLite files are copied using SQLite's consistent backup API,
including committed WAL records; WAL/SHM sidecars are deliberately not copied.
The destination is published by renaming a fully verified staging directory.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import uuid

DB_SUFFIXES = {'.db', '.sqlite', '.sqlite3'}
SKIP_SUFFIXES = ('-wal', '-shm', '-journal')


def filehash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def copy_sqlite(source: Path, target: Path) -> None:
    # Read-only source URL, with a real destination connection and prompt handle closure.
    with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True, timeout=8)) as src:
        with closing(sqlite3.connect(str(target), timeout=8)) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise RuntimeError('Integridade SQLite invalida: ' + str(source))
            # Compare table counts to catch incomplete copies (without copying secrets into reports).
            table_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            tables = [item[0] for item in src.execute(table_query)]
            for name in tables:
                quoted = '"' + name.replace('"', '""') + '"'
                if src.execute('SELECT COUNT(*) FROM ' + quoted).fetchone()[0] != dst.execute('SELECT COUNT(*) FROM ' + quoted).fetchone()[0]:
                    raise RuntimeError('Tabela divergente apos copia SQLite')


def migrate(source: Path, destination: Path, *, apply: bool = False) -> dict:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError('Origem e destino nao podem se sobrepor')
    if destination.exists():
        raise FileExistsError('Destino ja existe; nunca sobrescrever dados: ' + str(destination))
    if not source.exists():
        # A new installation might have no app data yet.
        source_files = []
    else:
        if not source.is_dir():
            raise ValueError('Origem nao e pasta')
        source_files = sorted(p for p in source.rglob('*') if p.is_file())
        if any(p.is_symlink() for p in source.rglob('*')):
            raise ValueError('Links simbolicos nao sao aceitos na migracao')
    tracked = [p for p in source_files if not p.name.lower().endswith(SKIP_SUFFIXES)]
    sizes = sum(p.stat().st_size for p in tracked)
    info = {'source_file_count': len(tracked), 'source_bytes': sizes, 'destination': str(destination), 'applied': False}
    if not apply:
        return info
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = destination.parent / ('.dados_migrando_' + uuid.uuid4().hex)
    stage.mkdir()
    try:
        for p in tracked:
            rel = p.relative_to(source)
            target = stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if p.suffix.lower() in DB_SUFFIXES:
                try:
                    copy_sqlite(p, target)
                except sqlite3.DatabaseError as exc:
                    raise RuntimeError('SQLite nao pode ser copiado com seguranca: ' + str(rel)) from exc
            else:
                shutil.copy2(p, target)
                if filehash(p) != filehash(target):
                    raise RuntimeError('SHA256 divergente: ' + str(rel))
        # Atomic directory publication on the same volume.
        stage.rename(destination)
        info['applied'] = True
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return info


def main(argv=None):
    parser = argparse.ArgumentParser(description='Copia segura da biblioteca; nunca apaga a origem')
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(migrate(args.source, args.destination, apply=args.apply), ensure_ascii=False))
    except (OSError, sqlite3.Error, ValueError, RuntimeError) as exc:
        print('ERRO_MIGRACAO: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
