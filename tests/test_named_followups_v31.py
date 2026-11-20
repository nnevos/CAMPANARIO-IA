"""Regressions for short named follow-ups and explicit type corrections."""
from datetime import UTC, datetime
from uuid import uuid4
import pytest
from campanario.utilities.web_intent import direct_decision, short_entity_decision
from campanario.chat.service import ChatService
from campanario.chat.context import RecentMessagesContextManager
from campanario.model.protocol import FakeModelProvider
from campanario.utilities.web_chat import ResearchResult
from campanario.utilities import web_chat
from test_chat_service import InMemorySessions, InMemoryMessages


def test_short_named_subject_is_not_mistaken_for_previous_topic():
    result = direct_decision('e cellbit?')
    assert result.search and result.subject == 'cellbit'
    assert result.reason == 'novo_assunto_curto'
    result = direct_decision('cellbit twitch streamer?')
    assert result.search and result.subject == 'cellbit'
    assert result.category == 'criador de conteúdo'
    assert direct_decision('e underscore?').subject == 'underscore'


def test_do_not_search_social_smalltalk_or_explicit_optout():
    assert short_entity_decision('e você?') is None
    assert short_entity_decision('e agora?') is None
    assert short_entity_decision('e aí?') is None
    assert not direct_decision('não pesquise na internet: e cellbit?').search


@pytest.mark.asyncio
async def test_short_subject_reaches_actual_research_and_abstains_if_failed(monkeypatch):
    calls = []
    def lookup(query, **kw):
        calls.append((query, kw))
        return ResearchResult('failed', kw['subject'], kw['category'], query,
                              'BUSCA SEM RESULTADO CONFIRMADO')
    monkeypatch.setattr(web_chat, 'research_entity', lookup)
    sessions, messages = InMemorySessions(), InMemoryMessages()
    svc = ChatService(sessions, messages, FakeModelProvider('Cellbit é uma banda inventada.'),
                      RecentMessagesContextManager(20), 'fake', web_auto_search=True)
    session = svc.create_session()
    for question in ('e cellbit?', 'cellbit twitch streamer?'):
        events = [event async for event in svc.stream_turn(session.id, question)]
        answer = ''.join(e.text for e in events if e.type == 'token')
        assert 'banda inventada' not in answer
        assert 'não consegui' in answer.lower()
    assert [call[1]['subject'] for call in calls] == ['cellbit', 'cellbit']
    assert calls[1][1]['category'] == 'criador de conteúdo'
