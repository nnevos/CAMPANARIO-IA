"""Verify the *already copied* Campanario library without modifying either tree.

Normal files: relative paths, file sizes, SHA256.
SQLite: PRAGMA quick_check and SHA256 of the logical dump streamed from both
connections; this also includes committed changes in an original WAL file.
Never deletes, merges or overwrites anything, and never prints database content.

This protects resume after an interruption *after* migration publication but
*before* the .env activation step on Windows PowerShell 5.1.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

DB_SUFFIXES = {".db", ".sqlite", ".sqlite3"}
SKIP_SUFFIXES = ("-wal", "-shm", "-journal")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _entries(root: Path) -> dict[Path, Path]:
    if not root.is_dir() or root.is_symlink() or (hasattr(root, "is_junction") and root.is_junction()):
        raise ValueError("Origem ou destino nao e uma pasta convencional")
    entries: dict[Path, Path] = {}
    for path in root.rglob("*"):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError("Link simbolico ou junction dentro da biblioteca: acesso recusado")
        if not path.is_file():
            continue
        if path.name.lower().endswith(SKIP_SUFFIXES):
            continue
        entries[path.relative_to(root)] = path
    return entries


def _logical_sqlite_hash(path: Path) -> tuple[str, int]:
    # Connection is explicitly closed before returning, including on Windows.
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=15)) as db:
        db.execute("BEGIN")
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("PRAGMA quick_check falhou no SQLite")
        digest = hashlib.sha256()
        lines = 0
        for sql in db.iterdump():
            digest.update(sql.encode("utf-8", errors="surrogatepass"))
            digest.update(b"\n")
            lines += 1
        db.rollback()
        return digest.hexdigest(), lines


def verify_copy(source: Path, destination: Path) -> dict[str, int | str]:
    source, destination = source.expanduser().resolve(), destination.expanduser().resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Origem e destino nao podem coincidir ou se sobrepor")
    src_files = _entries(source)
    dst_files = _entries(destination)
    if set(src_files) != set(dst_files):
        raise ValueError(
            "Lista de arquivos diferente (origem={}, destino={}); retomar bloqueado".format(len(src_files), len(dst_files))
        )
    num_sqlite = 0
    num_other = 0
    for rel in sorted(src_files):
        src, dst = src_files[rel], dst_files[rel]
        if rel.suffix.lower() in DB_SUFFIXES:
            num_sqlite += 1
            if _logical_sqlite_hash(src) != _logical_sqlite_hash(dst):
                raise ValueError("Banco SQLite divergente; retomar bloqueado")
        else:
            num_other += 1
            if src.stat().st_size != dst.stat().st_size or _sha(src) != _sha(dst):
                raise ValueError("Arquivo de dados divergente; retomar bloqueado")
    return {
        "result": "OK",
        "verified_files": num_sqlite + num_other,
        "verified_sqlite": num_sqlite,
        "verified_other": num_other,
        "source_untouched": "yes",
        "destination_untouched": "yes",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Conferir copia existente; nunca modificar dados")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify_copy(args.source, args.destination), ensure_ascii=False))
        return 0
    except (OSError, sqlite3.DatabaseError, ValueError) as exc:
        print("COPIA_NAO_VALIDADA:", str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
