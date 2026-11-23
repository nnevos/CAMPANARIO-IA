"""Validate the documentation shipped in CAMPANARIO-IA, not an absent archive.

The previous assertions described a docs/history tree not present in R2.12.
Do not create duplicate obsolete manuals just to satisfy the test.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manual_redirects_to_current_version():
    text = (ROOT / 'docs/manual/README.md').read_text(encoding='utf-8')
    assert 'LEIA-ME-V08' in text
    assert 'ARQUITETURA_V08.md' in text
    assert 'não existe' in text  # documents the missing archive honestly
    assert (ROOT / 'docs/manual/29_HOST_VOICE_F5C.md').is_file()


def test_legacy_manuals_are_clearly_marked_as_historical():
    text = (ROOT / 'docs/manual/README.md').read_text(encoding='utf-8')
    assert 'legado' in text.casefold()
    assert 'não representam' in text.casefold()


def test_current_manual_distinguishes_providers_from_contracts():
    text = (ROOT / 'docs/current/ARQUITETURA_V08.md').read_text(encoding='utf-8')
    assert 'Morgana' in text and 'Todd' in text
    assert 'TTS' in text and 'GPS' in text
    assert 'nao implementados' in text
