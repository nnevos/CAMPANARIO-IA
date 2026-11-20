"""Regression of no-comma vocatives and read-only Cellbit lookup via Kiwix."""
from __future__ import annotations

import httpx
import pytest

from campanario.chat.zim_wikipedia import OfflineWikipediaZim, _requested_subject
from campanario.utilities.web_intent import direct_decision

BOOK = 'wikipedia_pt_all_nopic_2026-05'
CELLBIT_HTML = '''<html><body><h1>Cellbit</h1>
<p>Rafael Lange Severino (Florianópolis, 11 de fevereiro de 1997),
mais conhecido como Cellbit, é um escritor, diretor criativo,
streamer e youtuber brasileiro conhecido por criar Ordem Paranormal.</p>
</body></html>'''


def _source(tmp_path, *, title='Cellbit', html=CELLBIT_HTML, missing=False):
    zim = tmp_path / 'zim'
    zim.mkdir()
    (zim / f'{BOOK}.zim').write_bytes(b'synthetic fixture, not an actual archive')
    requests = []

    def handler(request):
        requests.append(str(request.url))
        assert request.url.host == '127.0.0.1'
        if request.url.path == '/suggest':
            if missing:
                return httpx.Response(200, json=[])
            assert request.url.params['term'].casefold() == 'cellbit'
            return httpx.Response(200, json=[
                {'kind': 'path', 'value': title, 'path': 'A/Cellbit'},
            ])
        assert request.url.path == f'/raw/{BOOK}/content/A/Cellbit'
        return httpx.Response(200, text=html, headers={'content-type': 'text/html'})

    return OfflineWikipediaZim(zim, transport=httpx.MockTransport(handler)), requests


@pytest.mark.parametrize('question', [
    'todd quem é cellbit?',
    'Todd, quem é Cellbit?',
    'TODD: Quem é Cellbit?',
    'Morgana quem foi Cellbit?',
    'campanário, quem é Cellbit?',
    'quem é Cellbit?',
])
def test_vocative_identity_uses_local_article(tmp_path, question):
    source, seen = _source(tmp_path)
    d = direct_decision(question)
    subject = d.subject if d else ''
    fact = source.search(question, subject=subject)
    assert fact is not None, source.last_status
    assert fact.title == 'Cellbit'
    assert 'Rafael Lange' in fact.excerpt
    assert len(seen) == 2
    assert all(url.startswith('http://127.0.0.1:8181/') for url in seen)


def test_no_comma_subject_from_question_without_planner():
    assert _requested_subject('todd quem é cellbit?', '') == 'cellbit'
    assert _requested_subject('morgana quem foi Ada Lovelace?', '') == 'Ada Lovelace'


def test_question_with_different_attribute_is_not_reframed_as_identity(tmp_path):
    source, seen = _source(tmp_path)
    assert source.search('Todd qual é a senha do Cellbit?', subject='Cellbit') is None
    assert source.last_status == 'no_explicit_evidence'
    assert len(seen) == 2


def test_missing_article_does_not_invent_identity(tmp_path):
    source, seen = _source(tmp_path, missing=True)
    assert source.search('Todd quem é Cellbit?', subject='Cellbit') is None
    assert source.last_status == 'no_unique_exact_title'
    assert len(seen) == 1


def test_different_article_title_is_not_promoted(tmp_path):
    source, _ = _source(tmp_path, title='Cellbit (personagem)')
    assert source.search('Todd quem é Cellbit?', subject='Cellbit') is None
    assert source.last_status == 'no_unique_exact_title'


def test_no_identity_predicate_is_not_promoted(tmp_path):
    html = ('<h1>Cellbit</h1><p>Cellbit tem uma página na enciclopédia com detalhes. '
            'Consulte a página para obter informações adicionais.</p>')
    source, _ = _source(tmp_path, html=html)
    assert source.search('todd quem é cellbit?', subject='Cellbit') is None
    assert source.last_status == 'no_explicit_evidence'

@pytest.mark.asyncio
async def test_real_chat_pipeline_uses_cellbit_zim_without_web(tmp_path):
    from campanario.chat.context import RecentMessagesContextManager
    from campanario.chat.service import ChatService
    from campanario.chat.local_library import ReadOnlyLocalLibrary
    from campanario.model.protocol import FakeModelProvider
    from test_chat_service import InMemorySessions, InMemoryMessages

    source, seen = _source(tmp_path)
    chat = ChatService(InMemorySessions(), InMemoryMessages(),
                       FakeModelProvider('O modelo nao deve inventar identidade'),
                       RecentMessagesContextManager(12), 'fake',
                       local_library=ReadOnlyLocalLibrary(tmp_path / 'absent.sqlite3'),
                       zim_library=source, web_auto_search=False)
    session = chat.create_session()
    events = [event async for event in chat.stream_turn(session.id, 'todd quem é cellbit?')]
    answer = ''.join(event.text for event in events if event.type == 'token')
    assert 'Rafael Lange' in answer
    assert 'Fonte:' in answer
    assert 'pesquisa está desligada' not in answer.lower()
    assert len(seen) == 2
    assert [event.agent_id for event in events if event.type == 'speaker_start'] == ['todd']

