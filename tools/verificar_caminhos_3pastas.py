"""Read-only verification of the active Campanario data/ZIM locations.

Invoked as a Python file, not ``python -c``: PowerShell 5.1 can strip nested
quotes when forwarding commands. No database is opened or created.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def verify(expected_data: Path, expected_zim: Path) -> tuple[bool, str]:
    from campanario.config import Settings

    settings = Settings()
    data = settings.data_dir.resolve()
    zim = settings.zim_dir.resolve() if settings.zim_dir is not None else None
    target_data = expected_data.resolve()
    target_zim = expected_zim.resolve()
    if data != target_data or zim != target_zim:
        return False, "Configuracao divergente: CAMPANARIO_DATA_DIR ou CAMPANARIO_ZIM_DIR nao aponta para o destino esperado"
    if not target_data.is_dir() or not target_zim.is_dir():
        return False, "Pasta externa de dados ou ZIM ausente"
    if settings.database_path.resolve() != (target_data / settings.memory_environment / "campanario.db").resolve():
        return False, "Caminho derivado do banco nao corresponde a CAMPANARIO_DATA_DIR"
    return True, "CONFIGURACAO EXTERNA OK (sem escrever bancos)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Conferir paths ativos sem abrir bancos")
    parser.add_argument("--expected-data", type=Path, required=True)
    parser.add_argument("--expected-zim", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        passed, message = verify(args.expected_data, args.expected_zim)
    except (OSError, ValueError, ImportError) as exc:
        passed, message = False, f"Falha ao ler configuracao: {type(exc).__name__}"
    print(message)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
