"""Export reproducible, code-only Campanario snapshot (no secrets, models or data).

This intentionally uses an allowlist: unfamiliar private/binary files are omitted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FOLDERS = ('src', 'apps', 'config', 'docs', 'eval', 'migrations', 'models', 'packaging', 'tests', 'tools', 'vozes')
SOURCE_FILES = {'pyproject.toml', 'uv.lock', '.python-version', '.gitignore', '.env.example',
                'README.md', 'LEIA_PRIMEIRO_3_PASTAS.md', 'LEIA_PRIMEIRO_V9_INTEGRADA.md', 'CAMPANARIO.bat', 'CAMPANARIO.vbs', 'PREPARAR_PC.bat',
                'DIAGNOSTICAR_CAMPANARIO.ps1', 'TESTAR_3_PASTAS.ps1', 'VERSAO.json',
                'PREPARAR_PYTHON_UNIFICADO.ps1', 'TESTAR_PYTHON_UNIFICADO.ps1', 'ATIVAR_SEPARACAO.ps1',
                'REVERTER_SEPARACAO.ps1',
                'alembic.ini'}
TEXT_SUFFIXES = {'.py', '.pyi', '.md', '.rst', '.txt', '.json', '.toml', '.yaml', '.yml',
                 '.html', '.css', '.js', '.ts', '.bat', '.ps1', '.vbs', '.ini', '.lock',
                 '.sql', '.gitignore', '.svg', '.rpy', '.xml'}
ASSET_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.ico'}
BLOCKED_NAMES = {'.env', '.env.local', '.secrets', 'credentials.json', 'token.json'}
BLOCKED_PARTS = {'.venv', 'venv', '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
                 '.ruff_cache', 'reports', 'backups', 'backup', 'data', 'databases', 'database',
                 'dist', 'build', '.cache', 'node_modules', 'private', 'segredos', 'documentos',
                 'uploads', 'downloads'}
MAX_FILE = 5 * 1024 * 1024
MAX_ARCHIVE = 100 * 1024 * 1024


def safe_to_export(path: Path, root: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    rel = path.relative_to(root)
    parts = rel.parts
    if any(p.lower() in BLOCKED_PARTS for p in parts[:-1]) or path.name.lower() in BLOCKED_NAMES:
        return False
    if parts[0] in SOURCE_FOLDERS:
        if path.suffix.lower() not in TEXT_SUFFIXES | ASSET_SUFFIXES:
            return False
        if parts[0] == 'vozes' and path.suffix.lower() not in {'.json', '.md'}:
            return False
    elif len(parts) != 1 or parts[0] not in SOURCE_FILES:
        return False
    return path.stat().st_size <= MAX_FILE


def safe_to_export_root_doc(path: Path, root: Path) -> bool:
    return path.is_file() and not path.is_symlink() and path.parent == root and path.stat().st_size <= MAX_FILE


def export(root: Path, destination: Path):
    root = root.resolve()
    destination = destination.resolve()
    if root in destination.parents and destination.name in SOURCE_FILES:
        raise ValueError('Nao sobrescrever arquivo-fonte')
    candidates = []
    for folder in SOURCE_FOLDERS:
        path = root / folder
        if path.is_dir():
            candidates.extend(p for p in path.rglob('*') if safe_to_export(p, root))
    candidates.extend(p for p in (root / n for n in SOURCE_FILES) if safe_to_export(p, root))
    candidates.extend(p for p in root.glob('LEIA_PRIMEIRO_FASE*.md') if safe_to_export_root_doc(p, root))
    candidates = sorted(set(candidates), key=lambda p: p.relative_to(root).as_posix())
    total = sum(p.stat().st_size for p in candidates)
    if total > MAX_ARCHIVE:
        raise ValueError('Exportacao excede 100 MB; revise os arquivos antes de enviar')
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        'format_version': 1,
        'origin': 'project_source_only',
        'excluded': ['.venv', '.env', 'CAMPANARIO-DATABASE', 'models Ollama', 'ZIM',
                     'SQLite', 'pesos de voz ONNX', 'logs', 'cache', 'dados pessoais'],
        'external_folders': ['CAMPANARIO-PYTHON', 'CAMPANARIO-DATABASE/dados', 'CAMPANARIO-DATABASE/zim'],
        'full_runtime_not_included': True,
    }
    state = ('# CAMPANARIO-IA - estado do projeto\n\n'
             'Base: CAMPANARIO-IA; validar no host a separacao entre IA, Python externo e Database.\n'
             'Python externo, voz e CUDA dependem de verificacao na instalacao real.\n'
             'O export nao inclui dados privados, ambiente Python, modelos e vozes ONNX.\n'
             'A consulta factual segue exigindo evidencias locais verificadas.\n'
             'P0: ver docs/current/P0_TRES_PASTAS_SEM_POWERSHELL.md; integracao completa ainda pendente.\n')
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
        for p in candidates:
            archive.write(p, p.relative_to(root).as_posix())
        archive.writestr('ESTADO_DO_PROJETO.md', state)
        archive.writestr('RECURSOS_EXTERNOS.json', json.dumps(manifest, indent=2, ensure_ascii=False))
    return {'files': len(candidates) + 2, 'bytes': destination.stat().st_size, 'path': str(destination)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT.parent / 'CAMPANARIO_FONTE_PORTATIL.zip')
    args = parser.parse_args(argv)
    try:
        result = export(args.root, args.output)
    except (OSError, ValueError) as exc:
        print(f'ERRO_EXPORTACAO: {exc}', file=sys.stderr)
        return 1
    print('EXPORTADO:', json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
