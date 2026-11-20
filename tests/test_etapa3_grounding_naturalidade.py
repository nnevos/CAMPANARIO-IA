"""Etapa 3: source-gated identity, natural differences, and Etapa 2 preservation.

Web sources and Ollama are simulated: not a production web/Qwen certification.
"""
from __future__ import annotations

import logging
from urllib.parse import quote

import httpx
import pytest

from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.knowledge import natural_uncertainty, sourced_definition_answer
from campanario.chat.service import ChatService
from campanario.model.adapters.ollama import OllamaProvider
from campanario.model.protocol import FakeModelProvider, ModelMessage, ModelRequest, ModelResponseError
from campanario.chat.models import MessageRole
from campanario.utilities import integration
from campanario.utilities.web_chat import research_entity
from campanario.utilities.web_intent import direct_decision

from test_etapa1_fluxos_failsafes import Sessions, Messages


def wiki(title: str, content: str):
    url = 'https://pt.wikipedia.org/wiki/' + quote(title.replace(' ', '_'))
    result = {'title': title, 'url': url, 'snippet': content[:85]}
    page = {'title': title, 'url': url, 'content': content,
            'read_method': 'wikipedia_summary', 'read_at': '2026-11-19'}
    return result, page


class FakeUtility:
    def __init__(self, entries=(), *, fail=False):
        self.entries = entries
        self.fail = fail
        self.calls = []
        self.pages = {hit['url']: page for hit, page in entries}

    def run(self, operation, arguments):
        self.calls.append((operation, dict(arguments)))
        if self.fail:
            return {'status': 'error', 'result': {'error': 'provedor indisponivel'}}
        if operation == 'web.search':
            return {'status': 'success', 'result': {'results': [hit for hit, _ in self.entries]}}
        if operation == 'web.read':
            if arguments['url'] not in self.pages:
                return {'status': 'error', 'result': {'error': 'leitura indisponivel'}}
            return {'status': 'success', 'result': self.pages[arguments['url']]}
        raise AssertionError(f'Unexpected tool {operation}')


def mock_web(monkeypatch, *entries, fail=False):
    util = FakeUtility(entries, fail=fail)
    monkeypatch.setattr(integration, 'service', lambda: util)
    return util


@pytest.mark.parametrize('sentence', [
    'me conta da minha semana', 'me fala sobre jazz',
    'você conhece alguma receita simples?',
    'vocês conhecem um bom lugar para comer?',
    'me fala sobre o que eu disse antes',
    'não pesquise sobre Ana Souza',
])
def test_ordinary_or_private_dialogue_is_not_auto_entity_web_search(sentence):
    decision = direct_decision(sentence)
    assert decision is None or not decision.search


def test_long_named_subject_does_not_trigger_unguarded_identity_search():
    decision = direct_decision('me fala sobre a Ana Maria de Almeida que minha família conheceu no passado e que a gente não vê faz anos')
    assert decision is None or not decision.search


def test_extended_wikipedia_title_is_conditional_not_certain(monkeypatch):
    body = ('Marcos Vieira de Souza (Curitiba, 1980) é um cantor e compositor brasileiro, '
            'conhecido por turnês pelo país e por composições autorais.')
    util = mock_web(monkeypatch, wiki('Marcos Vieira de Souza', body))
    result = research_entity('Marcos Vieira', subject='Marcos Vieira')
    assert result.status == 'grounded'
    # No person/entity type was inferred just because the body says "pelo país".
    assert result.candidates == ()
    for speaker in ('morgana', 'todd'):
        answer = sourced_definition_answer(speaker, result, 'quem é Marcos Vieira?')
        assert answer and 'possível correspondência' in answer
        assert 'cantor e compositor' in answer
        assert 'Fonte: https://pt.wikipedia.org/' in answer
    assert sum(op == 'web.read' for op, _ in util.calls) == 1


def test_multiple_extended_wikipedia_results_override_first_hit(monkeypatch):
    singer = 'Marcos Vieira de Souza é um cantor e compositor brasileiro de música popular.'
    player = 'Marcos Vieira Pereira é um jogador brasileiro de futebol que atua como goleiro.'
    mock_web(monkeypatch, wiki('Marcos Vieira de Souza', singer),
             wiki('Marcos Vieira Pereira', player))
    result = research_entity('Marcos Vieira', subject='Marcos Vieira')
    assert result.status == 'ambiguous'
    assert len(result.candidates) == 2
    for speaker in ('todd', 'morgana'):
        response = natural_uncertainty(speaker, result.subject,
                                       status=result.status, candidates=result.candidates)
        assert all(name in response for name in result.candidates)
        assert '?' in response
        assert sourced_definition_answer(speaker, result, 'quem é Marcos Vieira?') is None
    assert natural_uncertainty('todd', result.subject, status=result.status,
                               candidates=result.candidates) != natural_uncertainty(
                                   'morgana', result.subject, status=result.status,
                                   candidates=result.candidates)


def test_wikipedia_disambiguation_suffix_does_not_confirm_identity(monkeypatch):
    body = 'Marcos Vieira (personagem) é um personagem fictício de um filme brasileiro.'
    mock_web(monkeypatch, wiki('Marcos Vieira (personagem)', body))
    result = research_entity('Marcos Vieira', subject='Marcos Vieira')
    assert result.status != 'grounded'
    assert sourced_definition_answer('morgana', result, 'quem é Marcos Vieira?') is None


def test_empty_or_failed_retrieval_never_launders_snippets(monkeypatch):
    for util in (mock_web(monkeypatch, fail=True), mock_web(monkeypatch)):
        monkeypatch.setattr(integration, 'service', lambda util=util: util)
        result = research_entity('Marcos Vieira', subject='Marcos Vieira')
        assert result.requires_abstention


@pytest.mark.asyncio
async def test_two_agents_same_grounded_facts_distinct_natural_opening(monkeypatch):
    body = 'Marcos Vieira de Souza é um cantor e compositor brasileiro, reconhecido por suas gravações.'
    util = mock_web(monkeypatch, wiki('Marcos Vieira de Souza', body))
    service = ChatService(
        Sessions(), Messages(), FakeModelProvider('Biografia inventada não pode aparecer'),
        RecentMessagesContextManager(10), 'fake', web_auto_search=True,
        web_planner_provider=FakeModelProvider('{"search":false,"query":""}'),
    )
    first = service.create_session(agent_id='todd')
    second = service.create_session(agent_id='morgana')
    outputs = []
    for session in (first, second):
        events = [event async for event in service.stream_turn(session.id, 'quem é Marcos Vieira?')]
        response = ''.join(e.text for e in events if e.type == 'token')
        outputs.append(response)
        assert response == service.get_messages(session.id)[-1].content
        assert 'cantor e compositor' in response
        assert 'Biografia inventada' not in response
    assert outputs[0] != outputs[1]
    assert all('Fonte:' in r for r in outputs)
    assert any(op == 'web.read' for op, _ in util.calls)


@pytest.mark.asyncio
async def test_ollama_context_diagnostic_is_not_truncation_proof(monkeypatch, caplog):
    content = ('{"message":{"content":"Tudo bem."},"done":false}\n'
               '{"done":true,"prompt_eval_count":7800,"eval_count":3}\n')
    real_client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=content))
    monkeypatch.setattr(httpx, 'AsyncClient',
                        lambda **kwargs: real_client(transport=transport, **kwargs))
    provider = OllamaProvider('http://127.0.0.1:11434', context_window=8192)
    req = ModelRequest('fake', (ModelMessage(MessageRole.USER, 'Olá'),))
    with caplog.at_level(logging.WARNING):
        chunks = [chunk async for chunk in provider.stream(req)]
    assert ''.join(chunk.text for chunk in chunks) == 'Tudo bem.'
    assert chunks[-1].done is True
    assert 'ollama_context_near_limit' in caplog.text
    assert 'truncated' not in caplog.text


@pytest.mark.asyncio
async def test_ollama_context_diagnostic_does_not_relax_validation(monkeypatch):
    invalid = '{"message":[],"done":true,"prompt_eval_count":8200}\n'
    real_client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=invalid))
    monkeypatch.setattr(httpx, 'AsyncClient',
                        lambda **kwargs: real_client(transport=transport, **kwargs))
    provider = OllamaProvider('http://127.0.0.1:11434', context_window=8192)
    req = ModelRequest('fake', (ModelMessage(MessageRole.USER, 'Olá'),))
    with pytest.raises(ModelResponseError):
        _ = [chunk async for chunk in provider.stream(req)]
