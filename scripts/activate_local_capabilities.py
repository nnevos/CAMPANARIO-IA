"""R3.11: inspect dependencies and opt in supported local, read-only features.

Only touches CAMPANARIO-IA/.env when --apply is explicitly supplied. Backups
are private and are never bundled. Never downloads models or changes Database.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / '.env'
OLLAMA = 'http://127.0.0.1:11434'
MODEL_RE = re.compile(r'[A-Za-z0-9_.:/-]{1,90}\Z')


def local_models() -> tuple[set[str], str]:
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(OLLAMA + '/api/tags', timeout=2) as reply:
            raw = reply.read(256 * 1024)
        obj = json.loads(raw)
        return {m['name'] for m in obj.get('models', []) if isinstance(m, dict) and isinstance(m.get('name'), str)}, 'ollama_loopback_ok'
    except (OSError, ValueError, TypeError, KeyError):
        return set(), 'ollama_indisponivel'


def existing_env(text: str) -> dict[str, str]:
    data = {}
    for line in text.splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            if re.fullmatch(r'CAMPANARIO_[A-Z0-9_]+', key.strip()):
                data[key.strip()] = value.strip().strip('"\'')
    return data


def pick_model(models: set[str], preferred: str, candidates: tuple[str, ...]) -> str:
    if preferred in models and MODEL_RE.fullmatch(preferred):
        return preferred
    for base in candidates:
        matched = sorted((name for name in models if name == base or name.startswith(base + ':')))
        if matched:
            return matched[0]
    return ''


def inspect(env_data: dict[str, str], models: set[str]) -> dict:
    embed = pick_model(models, env_data.get('CAMPANARIO_CASE_EMBED_MODEL', ''),
                       ('nomic-embed-text', 'embeddinggemma', 'mxbai-embed-large'))
    chat = pick_model(models, env_data.get('CAMPANARIO_CASE_CLAIMS_SEMANTIC_MODEL', '') or env_data.get('CAMPANARIO_MODEL_NAME', ''),
                      ('gemma3', 'qwen3.5', 'qwen2.5', 'llama3.2'))
    vision = pick_model(models, env_data.get('CAMPANARIO_CASE_VISION_MODEL', ''),
                        ('llava', 'gemma3', 'llama3.2-vision'))
    # OCR needs local Tesseract and Python integration available to the actual external .venv.
    ocr = bool(shutil.which('tesseract') and importlib.util.find_spec('pytesseract') and importlib.util.find_spec('PIL'))
    pdf_ocr = bool(ocr and (importlib.util.find_spec('fitz') or importlib.util.find_spec('pypdfium2')))
    zim_folder = env_data.get('CAMPANARIO_ZIM_DIR')
    zim = bool(zim_folder and Path(zim_folder).is_dir() and any(Path(zim_folder).glob('*.zim')))
    settings = {
        'CAMPANARIO_CASE_OCR_ENABLED': 'true' if ocr else 'false',
        'CAMPANARIO_CASE_SEMANTIC_ENABLED': 'true' if embed else 'false',
        'CAMPANARIO_CASE_VISION_ENABLED': 'true' if vision else 'false',
        'CAMPANARIO_CASE_CLAIMS_SEMANTIC_ENABLED': 'true' if chat else 'false',
        'CAMPANARIO_LIBRARY_SEMANTIC_ENABLED': 'true' if embed else 'false',
        'CAMPANARIO_ZIM_ENABLED': 'true' if zim else 'false',
    }
    if embed:
        settings['CAMPANARIO_CASE_EMBED_MODEL'] = embed
        settings['CAMPANARIO_LIBRARY_SEMANTIC_MODEL'] = embed
    if chat:
        settings['CAMPANARIO_CASE_CLAIMS_SEMANTIC_MODEL'] = chat
    if vision:
        settings['CAMPANARIO_CASE_VISION_MODEL'] = vision
    return {'settings': settings, 'models_found': sorted(models),
            'ocr_text_ready': ocr, 'pdf_ocr_backend_ready': pdf_ocr, 'zim_found': zim,
            'limitations': ['Nao habilita rede, ferramenta com escrita, execucao automatica ou credenciais',
                            'Disponibilidade de modelo nao prova acuracia, nem compatibilidade de visao',
                            'OCR de PDF digitalizado tambem requer backend de renderizacao',
                            'V9 experimental nao e habilitado sem homologacao do runtime']}


def update_env(text: str, changes: dict[str, str]) -> str:
    lines = text.splitlines(keepends=True)
    found = set()
    output = []
    for line in lines:
        match = re.match(r'^(CAMPANARIO_[A-Z0-9_]+)\s*=', line)
        if match and match.group(1) in changes:
            key = match.group(1)
            if key not in found:
                output.append(f'{key}={changes[key]}\n')
                found.add(key)
            # Duplicates are discarded so stale settings cannot override the new value.
        else:
            output.append(line)
    if output and not output[-1].endswith('\n'):
        output.append('\n')
    for key, value in changes.items():
        if key not in found:
            output.append(f'{key}={value}\n')
    return ''.join(output)


def apply(env: Path, settings: dict[str, str]) -> Path:
    if not env.is_file() or env.is_symlink():
        raise ValueError('Arquivo .env privado inexistente ou link; nada foi alterado')
    if env.stat().st_size > 256_000:
        raise ValueError('.env inesperadamente grande; nada foi alterado')
    raw = env.read_bytes()
    text = raw.decode('utf-8-sig')
    updated = update_env(text, settings)
    if updated == text:
        return env  # Idempotent, do not make a redundant backup.
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    backup = env.with_name(f'.env.backup_R311_{stamp}')
    with backup.open('xb') as file:
        file.write(raw)
    try:
        os.chmod(backup, 0o600)
    except OSError:
        pass
    fd, tmp = tempfile.mkstemp(prefix='.env.r311.', dir=env.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as file:
            file.write(updated)
        os.replace(tmp, env)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return backup


def main(argv=None):
    parser = argparse.ArgumentParser(description='Ativacao local verificada, sem downloads e sem PowerShell')
    parser.add_argument('--apply', action='store_true', help='Criar backup e atualizar SOMENTE .env privado existente')
    parser.add_argument('--env', type=Path, default=ENV, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not args.env.is_file():
        print('Nenhum .env privado encontrado. Crie-o a partir de .env.example preservando suas configuracoes atuais.')
        return 2
    data = existing_env(args.env.read_text(encoding='utf-8-sig'))
    models, status = local_models()
    result = inspect(data, models)
    print('R3.11 / diagnostico local:', status)
    for key, value in result['settings'].items():
        print(' ', key, '=', value)
    print('OCR PDF:', 'pronto para teste' if result['pdf_ocr_backend_ready'] else 'nao verificado')
    if args.apply:
        backup = apply(args.env, result['settings'])
        print('CONFIGURADO. Backup privado:', backup.name)
        print('Reinicie o Campanario para carregar as opcoes. Nenhum modelo foi instalado.')
    else:
        print('SOMENTE DIAGNOSTICO. Use --apply para atualizar com backup.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
