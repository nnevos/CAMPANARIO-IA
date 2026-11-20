"""Offline regression coverage for the v3.2 knowledge lookup integration.

No web traffic and no Ollama required. Every external response is simulated.
"""
import json
import sqlite3

import pytest

from campanario.chat.knowledge import sourced_definition_answer
from campanario.utilities import integration, web_intent, web_research
from campanario.utilities.web_chat import ResearchResult, research_entity


@pytest.mark.parametrize('question, expected', [
    ('quem é cellbit?', 'cellbit'),
    ('o que é ordem paranormal?', 'ordem paranormal'),
    ('o que é a Ordem Paranormal?', 'Ordem Paranormal'),
    ('quem é alanzoka?', 'alanzoka'),
])
def test_definitions_trigger_neutral_search(question, expected):
    decision = web_intent.direct_decision(question)
    assert decision.search
    assert decision.subject == expected
    assert decision.query == expected
    assert decision.reason == 'verificacao_entidade'


def test_no_web_respected():
    assert not web_intent.direct_decision('quem é cellbit? sem internet').search


def test_wikipedia_search_before_duckduckgo(monkeypatch):
    calls = []

    def fake_request(url, *, params=None, **_):
        calls.append((url, params))
        if 'w/rest.php/v1/search/page' in url:
            return json.dumps({'pages': [
                {'key': 'Cellbit', 'title': 'Cellbit', 'excerpt': '<span class="searchmatch">Cellbit</span> é um streamer'},
            ]})
        raise AssertionError('DuckDuckGo should not be requested on wiki hit')

    monkeypatch.setattr(web_research, 'request', fake_request)
    data = web_research.search_results('cellbit', limit=5)
    assert data['provider'].startswith('Wikipedia API')
    assert data['results'][0]['url'] == 'https://pt.wikipedia.org/wiki/Cellbit'
    assert 'searchmatch' not in data['results'][0]['snippet']
    assert len(calls) == 1


def test_wikipedia_fallback_to_ddg_when_api_unavailable(monkeypatch):
    def fake_request(url, *, params=None, **_):
        if 'w/rest.php/v1/search/page' in url:
            raise web_research.httpx.HTTPError('simulated 403')
        if 'duckduckgo.com' in url:
            return '<a class="result__a" href="https://example.org/doc">Example</a>'
        raise AssertionError(url)

    monkeypatch.setattr(web_research, 'request', fake_request)
    monkeypatch.setattr(web_research, 'public_url', lambda value: value)
    data = web_research.search_results('cellbit')
    assert data['provider'].startswith('DuckDuckGo')
    assert data['results'][0]['url'] == 'https://example.org/doc'


class Storage:
    def __init__(self, path):
        self.path = path

    def connect(self):
        return sqlite3.connect(self.path)


def test_wikipedia_summary_is_a_real_page_read(monkeypatch, tmp_path):
    def fake_request(url, **_):
        if '/api/rest_v1/page/summary/Cellbit' in url:
            return json.dumps({
                'type': 'standard', 'title': 'Cellbit',
                'extract': 'Rafael Lange, mais conhecido como Cellbit, é um streamer brasileiro que criou Ordem Paranormal.'
            })
        raise AssertionError('Wikipedia HTML must not be requested when summary exists')

    monkeypatch.setattr(web_research, 'public_url', lambda value: value)
    monkeypatch.setattr(web_research, 'request', fake_request)
    service = web_research.WebResearch(Storage(tmp_path/'sources.sqlite'))
    result = service.execute('web.read', {'url': 'https://pt.wikipedia.org/wiki/Cellbit'})
    assert result['read_method'] == 'wikipedia_summary'
    assert 'Rafael Lange' in result['content']
    assert result['source_id']


class FakeTools:
    def __init__(self, hits, pages):
        self.hits = hits
        self.pages = pages

    def run(self, op, args):
        if op == 'web.search':
            return {'status': 'success', 'result': {'results': self.hits}}
        if op == 'web.read':
            data = self.pages.get(args['url'])
            if data is None:
                return {'status': 'failure', 'result': {'error': '403 Forbidden'}}
            return {'status': 'success', 'result': data}
        raise AssertionError(op)


def test_wikipedia_exact_page_becomes_sourced_definition(monkeypatch):
    wiki = 'https://pt.wikipedia.org/wiki/Cellbit'
    body = ('Rafael Lange, mais conhecido como Cellbit, é um streamer e criador brasileiro. '
            'Ele criou o universo de RPG Ordem Paranormal.')
    fake = FakeTools(
        [{'title': 'Cellbit', 'url': wiki, 'snippet': ''}],
        {wiki: {'title': 'Cellbit', 'url': wiki, 'content': body,
                'read_method': 'wikipedia_summary', 'read_at': '2026-11-18', 'source_id': 'x'}},
    )
    monkeypatch.setattr(integration, 'service', lambda: fake)
    result = research_entity('cellbit', subject='cellbit')
    assert result.status == 'grounded'
    answer = sourced_definition_answer('morgana', result, 'quem é cellbit?')
    assert answer is not None
    assert 'Rafael Lange' in answer
    assert 'Ordem Paranormal' not in answer  # Do not invent/append the second sentence
    assert wiki in answer
    assert 'personagem fictício' not in answer


def test_other_topic_uses_a_matching_article_not_previous_answer(monkeypatch):
    wiki = 'https://pt.wikipedia.org/wiki/Ordem_Paranormal'
    body = ('Ordem Paranormal é uma websérie brasileira de RPG de mesa criada pelo streamer Rafael Lange. '
            'É transmitida pela internet.')
    fake = FakeTools(
        [{'title': 'Ordem Paranormal', 'url': wiki, 'snippet': ''}],
        {wiki: {'title': 'Ordem Paranormal', 'url': wiki, 'content': body,
                'read_method': 'wikipedia_summary', 'read_at': '2026-11-18', 'source_id': 'y'}},
    )
    monkeypatch.setattr(integration, 'service', lambda: fake)
    result = research_entity('ordem paranormal', subject='ordem paranormal')
    assert result.status == 'grounded'
    answer = sourced_definition_answer('todd', result, 'o que é ordem paranormal?')
    assert 'websérie brasileira' in answer
    assert 'Supernatural' not in answer


def test_one_irrelevant_page_is_not_verified(monkeypatch):
    url = 'https://fan-site.example/Cellbit_(personagem)'
    fake = FakeTools(
        [{'title': 'Cellbit (personagem)', 'url': url, 'snippet': ''}],
        {url: {'title': 'Cellbit (personagem)', 'url': url,
               'content': ('Cellbit é um personagem fictício. ' * 15), 'source_id': 'z'}},
    )
    monkeypatch.setattr(integration, 'service', lambda: fake)
    result = research_entity('cellbit', subject='cellbit')
    assert result.status != 'grounded'
    assert sourced_definition_answer('morgana', result, 'quem é cellbit?') is None


def test_two_independent_hosts_are_eligible_for_model_audit(monkeypatch):
    hits = [{'title': 'Test Subject', 'url': f'https://source{i}.example/Test_Subject', 'snippet': ''}
            for i in range(2)]
    pages = {hit['url']: {'title': hit['title'], 'url': hit['url'],
                          'content': 'Test Subject is a software library. ' * 15}
             for hit in hits}
    monkeypatch.setattr(integration, 'service', lambda: FakeTools(hits, pages))
    result = research_entity('Test Subject', subject='Test Subject')
    assert result.status == 'grounded'
    assert sourced_definition_answer('morgana', result, 'quem é Test Subject?') is None


def test_abstain_when_pages_are_inaccessible(monkeypatch):
    fake = FakeTools([{'title': 'Cellbit', 'url': 'https://example.org/Cellbit', 'snippet': ''}], {})
    monkeypatch.setattr(integration, 'service', lambda: fake)
    result = research_entity('cellbit', subject='cellbit')
    assert result.requires_abstention
    assert result.status in ('insufficient', 'failed')


def test_definition_requires_exact_wikipedia_title():
    result = ResearchResult('grounded', 'Cellbit', '', 'Cellbit', '',
        sources=(('[RESUMO WIKIPEDIA] Cellbit (personagem)',
                  'https://pt.wikipedia.org/wiki/Cellbit_(personagem)',
                  'Cellbit é um personagem fictício da campanha Ordem Paranormal.'),))
    assert sourced_definition_answer('morgana', result, 'quem é Cellbit?') is None

@pytest.mark.asyncio
async def test_end_to_end_sourced_answer_skips_llm_and_persists_only_evidence():
    """Proves no hallucinated generation is even attempted for a verified summary."""
    from datetime import UTC, datetime
    from uuid import uuid4
    from campanario.chat.context import RecentMessagesContextManager
    from campanario.chat.models import Message, MessageRole
    from campanario.chat.service import ChatService

    class NoModel:
        async def stream(self, req):
            raise AssertionError('the language model must not invent an identity')
            yield  # pragma: no cover

    class MessageStore:
        def __init__(self):
            self.saved = []

        def append(self, message):
            self.saved.append(message)

    repo = MessageStore()
    session_id = uuid4()
    service = ChatService(
        sessions=object(), messages=repo, model_provider=NoModel(),
        context_manager=RecentMessagesContextManager(5),
        default_model='offline-test', low_latency_mode=True,
    )
    user = Message(id=uuid4(), session_id=session_id, role=MessageRole.USER,
                   content='quem é cellbit?', created_at=datetime.now(UTC))
    summary = ('Rafael Lange, mais conhecido como Cellbit, é um streamer e criador brasileiro. '
               'Ele criou Ordem Paranormal.')
    guard = ResearchResult(
        'grounded', 'cellbit', '', 'cellbit', 'resumo real simulado',
        sources=(('[RESUMO WIKIPEDIA] Cellbit', 'https://pt.wikipedia.org/wiki/Cellbit', summary),),
        searches=1, read_count=1,
    )
    profile = service._agents.get('morgana')
    events = []
    async for item in service._run_agent(
        session_id=session_id, profile=profile, history=[user],
        extra_system_note=guard.note, reason='test', correlation_id=uuid4(),
        causation_id=None, research_guard=guard,
    ):
        events.append(item)
    tokens = [e.text for e in events if e.type == 'token']
    assert len(tokens) == 1
    assert 'Rafael Lange' in tokens[0]
    assert 'personagem' not in tokens[0]
    assert 'Ele criou Ordem Paranormal' not in tokens[0]
    assert len(repo.saved) == 1 and repo.saved[0].content == tokens[0]

@pytest.mark.asyncio
async def test_planner_does_not_expand_invented_search_hypothesis():
    from types import SimpleNamespace

    class LiarPlanner:
        async def stream(self, request):
            yield SimpleNamespace(text='{"search":true,"query":"empresa Cellbit famosa em segurança corporativa"}', done=True)

    answer = await web_intent.decide('vale a pena conhecer esse projeto?', LiarPlanner(), 'local')
    assert answer.search
    assert answer.query == 'vale a pena conhecer esse projeto?'
    assert 'empresa' not in answer.query


def test_second_search_attempt_bypasses_unreadable_wikipedia(monkeypatch):
    class TwoStepTools:
        def __init__(self):
            self.searches = []

        def run(self, op, args):
            if op == 'web.search':
                self.searches.append(args)
                if not args.get('skip_wikipedia'):
                    return {'status': 'success', 'result': {'results': [
                        {'title': 'Sample author', 'url': 'https://pt.wikipedia.org/wiki/Sample_author', 'snippet': ''}
                    ]}}
                return {'status': 'success', 'result': {'results': [
                    {'title': 'Sample author', 'url': 'https://example.org/about', 'snippet': ''}
                ]}}
            if args['url'].startswith('https://pt.wikipedia.org'):
                return {'status': 'error', 'result': {'error': '403 Forbidden'}}
            return {'status': 'success', 'result': {
                'title': 'Sample author', 'url': args['url'],
                'content': 'Sample author is a Brazilian writer. ' * 15,
            }}

    tools = TwoStepTools()
    monkeypatch.setattr(integration, 'service', lambda: tools)
    result = research_entity('Sample author', subject='Sample author')
    assert len(tools.searches) == 2
    assert tools.searches[1]['skip_wikipedia'] is True
    assert result.status == 'grounded'
