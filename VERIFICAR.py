"""Campanario v3.2 research smoke test, offline with mock sources.

Run with project venv from the project's root after installing the patch:
    .venv\\Scripts\\python.exe _patch_research\\VERIFICAR.py
No Ollama, Meilisearch server or external internet is required.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'src'))
os.environ['CAMPANARIO_MEILI_ENABLED'] = 'false'

from campanario.chat.knowledge import sourced_definition_answer
from campanario.chat.service import ChatService
from campanario.utilities.web_intent import direct_decision
from campanario.utilities.web_chat import research_entity

for question, subject in (
    ('quem é cellbit?', 'cellbit'),
    ('o que é ordem paranormal?', 'ordem paranormal'),
    ('quem é alanzoka?', 'alanzoka'),
):
    decision = direct_decision(question)
    assert decision is not None and decision.search and decision.query == subject


class FakeTools:
    def run(self, op, args):
        if op == 'web.search':
            return {'status': 'success', 'result': {'results': [{
                'title': 'Cellbit',
                'url': 'https://pt.wikipedia.org/wiki/Cellbit',
                'snippet': '',
            }]}}
        if op == 'web.read':
            return {'status': 'success', 'result': {
                'title': 'Cellbit',
                'url': 'https://pt.wikipedia.org/wiki/Cellbit',
                'content': ('Rafael Lange, conhecido como Cellbit, é um streamer e criador brasileiro. '
                            'Ele criou o universo de RPG Ordem Paranormal.'),
                'read_method': 'wikipedia_summary',
                'read_at': '2026-11-18',
                'source_id': 'test-source',
            }}
        raise AssertionError(op)


with patch('campanario.utilities.integration.service', return_value=FakeTools()):
    result = research_entity('cellbit', subject='cellbit')

assert result.status == 'grounded', result.status
answer = sourced_definition_answer('morgana', result, 'quem é cellbit?')
assert answer and 'Rafael Lange' in answer and 'Fonte:' in answer
assert 'personagem fictício' not in answer
assert 'Ele criou o universo' not in answer  # no unsupported extra facts or additions
assert ChatService is not None
print('VERIFICACAO OFFLINE: OK (consulta neutra, resumo simulado, citacao, imports)')
print('IMPORTANTE: API real, Ollama e o aplicativo Windows ainda precisam ser testados.')
