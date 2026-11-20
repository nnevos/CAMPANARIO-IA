from __future__ import annotations

import importlib
import json
import sys
import types
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from campanario.utilities.meili_sources import CachedPage, MeiliSourceStore, enabled


def fake_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv('CAMPANARIO_MEILI_ENABLED', raising=False)
    assert not enabled()
    monkeypatch.setenv('CAMPANARIO_MEILI_ENABLED', 'true')
    assert enabled()


@pytest.mark.parametrize('url', [
    'http://evil.example:7700',
    'https://127.0.0.1:7700',
    'http://127.0.0.1:7700/redirect',
    'http://admin:password@127.0.0.1:7700',
])
def test_refuses_non_local_or_redirecting_endpoint(url):
    with pytest.raises(ValueError):
        MeiliSourceStore(url=url)


def test_index_requires_real_source_and_returns_task():
    seen = []
    def handler(req):
        seen.append(req)
        return httpx.Response(202, json={'taskUid': 7, 'status': 'enqueued'})
    store = MeiliSourceStore(client=fake_client(handler), api_key='secret')
    uid = store.index_read_page(
        title='Example article', url='https://example.org/article',
        content='A factual public page about a named subject. ' * 5,
        read_at=datetime.now(timezone.utc).isoformat(),
    )
    assert uid == 7
    req = seen[0]
    assert req.method == 'POST'
    assert '/indexes/campanario_public_sources/documents' in str(req.url)
    assert req.url.params['primaryKey'] == 'id'
    assert req.headers['authorization'] == 'Bearer secret'
    data = json.loads(req.content)
    assert len(data) == 1
    assert data[0]['url'] == 'https://example.org/article'
    assert len(data[0]['id']) == 64
    with pytest.raises(ValueError):
        store.index_read_page(title='test', url='http://127.0.0.1/private',
                              content='Many public words ' * 10,
                              read_at=datetime.now(timezone.utc).isoformat())


def test_search_only_fresh_public_sources():
    now = datetime.now(timezone.utc)
    content = 'Text describing a real public source and its subject. ' * 8
    payload = {'hits': [
        {'title': 'Fresh', 'url': 'https://example.org/fresh', 'content': content,
         'read_at': (now - timedelta(days=1)).isoformat(), '_rankingScore': 0.93},
        {'title': 'Old', 'url': 'https://example.org/old', 'content': content,
         'read_at': (now - timedelta(days=20)).isoformat()},
        {'title': 'Bad', 'url': 'http://localhost/private', 'content': content,
         'read_at': now.isoformat()},
    ]}
    def handler(req):
        assert req.method == 'POST' and req.url.path.endswith('/search')
        assert json.loads(req.content)['q'] == 'example'
        return httpx.Response(200, json=payload)
    store = MeiliSourceStore(client=fake_client(handler))
    pages = store.search('example')
    assert len(pages) == 1 and pages[0].score == 0.93
    assert pages[0].title == 'Fresh'


def test_no_web_fallback_when_cache_has_no_evidence(monkeypatch):
    mod = importlib.import_module('campanario.utilities.web_chat')
    fake_integration = types.ModuleType('campanario.utilities.integration')
    class Util:
        def run(self, name, args):
            if name == 'web.search':
                return {'status': 'success', 'result': {'results': []}}
            raise AssertionError(name)
    fake_integration.service = lambda: Util()
    monkeypatch.setitem(sys.modules, 'campanario.utilities.integration', fake_integration)
    monkeypatch.setattr(mod, '_meili_find_cached', lambda query: [])
    result = mod.research_entity('unknown example', subject='unknown example')
    assert result.requires_abstention
    assert result.read_count == 0 and not result.sources


def test_cached_entity_is_labeled_not_fresh(monkeypatch):
    mod = importlib.import_module('campanario.utilities.web_chat')
    fake_integration = types.ModuleType('campanario.utilities.integration')
    class Util:
        def run(self, name, args):
            if name == 'web.search':
                return {'status': 'success', 'result': {'results': []}}
            raise AssertionError(name)
    fake_integration.service = lambda: Util()
    monkeypatch.setitem(sys.modules, 'campanario.utilities.integration', fake_integration)
    page = CachedPage('Sample author - public profile', 'https://example.org/profile',
                      'Sample author writes books and maintains an independent website. '*6,
                      datetime.now(timezone.utc).isoformat())
    monkeypatch.setattr(mod, '_meili_find_cached', lambda q: [page])
    result = mod.research_entity('sample author', subject='Sample author')
    assert result.status == 'grounded'
    assert result.read_count == 0
    assert len(result.sources) == 1
    assert '[CACHE LOCAL' in result.sources[0][0]
    assert 'nao de uma nova verificacao online' in result.note


def test_cached_topic_is_labeled_not_fresh(monkeypatch):
    mod = importlib.import_module('campanario.utilities.web_chat')
    fake_integration = types.ModuleType('campanario.utilities.integration')
    class Util:
        def run(self, name, args):
            if name == 'web.search':
                return {'status': 'success', 'result': {'results': []}}
            raise AssertionError(name)
    fake_integration.service = lambda: Util()
    monkeypatch.setitem(sys.modules, 'campanario.utilities.integration', fake_integration)
    page = CachedPage('Observatory research', 'https://example.org/research',
                      'Observatory research is a field with astronomical instrumentation. '*7,
                      datetime.now(timezone.utc).isoformat())
    monkeypatch.setattr(mod, '_meili_find_cached', lambda q: [page])
    result = mod.research_topic('O que e observatory research?')
    assert result.status == 'grounded'
    assert result.read_count == 0
    assert '[CACHE LOCAL' in result.sources[0][0]


def test_indexing_only_after_relevant_web_read(monkeypatch):
    mod = importlib.import_module('campanario.utilities.web_chat')
    fake_integration = types.ModuleType('campanario.utilities.integration')
    calls = []
    class Util:
        def run(self, name, args):
            if name == 'web.search':
                return {'status': 'success', 'result': {'results': [
                    {'url': 'https://example.org/writer', 'title': 'Sample author', 'snippet': ''}
                ]}}
            if name == 'web.read':
                return {'status': 'success', 'result': {
                    'url': args['url'], 'title': 'Sample author',
                    'content': 'Sample author is the creator of multiple books. '*9,
                    'read_at': datetime.now(timezone.utc).isoformat(),
                }}
            raise AssertionError(name)
    fake_integration.service = lambda: Util()
    monkeypatch.setitem(sys.modules, 'campanario.utilities.integration', fake_integration)
    monkeypatch.setattr(mod, '_maybe_cache_read_source', lambda page: calls.append(page))
    monkeypatch.setattr(mod, '_meili_find_cached', lambda query: [])
    result = mod.research_entity('sample author', subject='Sample author')
    assert result.status == 'grounded'
    assert result.read_count == 1
    assert len(calls) == 1
