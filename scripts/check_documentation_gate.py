"""Offline documentation gate for versioned CAMPANARIO-IA releases.

Non-destructive: requires synchronized checkpoint marker and key headings.
It cannot verify factual truth; developers must review against source/tests.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess

REQUIRED = (
    'docs/current/ROADMAP.md',
    'docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md',
    'docs/operations/FAILSAFE_V9_CEREBROS.md',
    'docs/governance/MANUAL_TECNICO_VIVO.md',
    'docs/governance/PROCESSO_OBRIGATORIO_DE_DESENVOLVIMENTO.md',
)
MUST_CHANGE = REQUIRED[:4]

MANUAL_SECTIONS = (
    'Três repositórios', 'Agentes', 'Oito cérebros', 'Expressão fundamentada',
    'Biblioteca Conversacional V2', 'Voz', 'Segurança PF6', 'Rollback',
    'Como desenvolver', 'Dívidas técnicas', 'Próximo passo',
)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    content: dict[str, str] = {}
    for rel in REQUIRED:
        path = root / rel
        if not path.is_file():
            errors.append(f'ausente: {rel}')
            continue
        content[rel] = path.read_text(encoding='utf-8')
    if errors:
        return errors
    manual = content['docs/governance/MANUAL_TECNICO_VIVO.md']
    for section in MANUAL_SECTIONS:
        if section.casefold() not in manual.casefold():
            errors.append(f'manual sem assunto obrigatório: {section}')
    match = re.search(r'^\*\*Checkpoint:\*\*\s*(R\d+\.\d+)\b', manual, flags=re.M)
    if not match:
        errors.append('manual sem checkpoint explícito')
        return errors
    version = match.group(1)
    for rel, text in content.items():
        if version not in text:
            errors.append(f'checkpoint {version} ausente: {rel}')
    for rel in (f'CHANGELOG_{version.replace(".", "")}.md',
                f'LEIA_PRIMEIRO_{version.replace(".", "")}.md',
                f'docs/operations/RESULTADOS_TESTES_{version.replace(".", "")}.md'):
        if not (root / rel).is_file():
            errors.append(f'artefato de entrega ausente: {rel}')
    return errors


def validate_changed_files(root: Path, base_ref: str) -> list[str]:
    """Require four canonical documents to change when source/config/tests change.

    GitHub CI passes an event-specific immutable commit SHA. Do not use this
    option without a real git checkout. A failed diff must block the gate.
    """
    if not re.fullmatch(r'[0-9a-fA-F]{40}', base_ref) or base_ref == '0' * 40:
        return ['invalid git base revision for change gate']
    try:
        changed_output = subprocess.check_output(
            ['git', '-C', str(root), 'diff', '--name-only', base_ref, 'HEAD'],
            stderr=subprocess.PIPE, text=True)
    except (OSError, subprocess.CalledProcessError):
        return ['cannot compare git revisions; documentation gate fails closed']
    changed = set(changed_output.splitlines())
    code_changed = any(name.startswith(('src/', 'tests/', 'apps/', 'scripts/', '.github/workflows/'))
                       or name in ('pyproject.toml', '.env.example') for name in changed)
    if not code_changed:
        return []
    return [f'mandatory document unchanged for code update: {name}'
            for name in MUST_CHANGE if name not in changed]


def main():
    parser = argparse.ArgumentParser(description='Gate documental obrigatório CAMPANÁRIO')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--changed-since', default='', help='base git SHA for CI change gate')
    args = parser.parse_args()
    errors = validate(args.root)
    if args.changed_since:
        errors.extend(validate_changed_files(args.root, args.changed_since))
    if errors:
        for item in errors:
            print('FALHA:', item)
        raise SystemExit(1)
    print('PASS: documentação sincronizada (checagem estrutural; exige revisão humana)')


if __name__ == '__main__':
    main()
