"""Regression: short vocatives are not public-fact lookups.

Reproduces the user-visible failure where 'todd?' was routed to Todd but
answered with 'A pesquisa está desligada...' instead of conversationally.
"""
from dataclasses import replace

import pytest

from campanario.agents.addressing import standalone_wake_target
from campanario.agents.profiles import default_agent_registry
from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.chat.service import ChatService
from campanario.model.protocol import ModelChunk
from test_chat_service import InMemoryMessages, InMemorySessions


class ReplyProvider:
    def __init__(self):
        self.calls = 0
        self.requests = []

    async def health(self):
        return True

    async def stream(self, request):
        self.calls += 1
        self.requests.append(request)
        yield ModelChunk(text='Oi, estou aqui. Pode falar!', done=True)


class SpyLibrary(ReadOnlyLocalLibrary):
    def __init__(self, path):
        super().__init__(path)
        self.calls = 0

    def search(self, question, *, subject=''):
        self.calls += 1
        return super().search(question, subject=subject)


def _service(tmp_path, *, web=False):
    library = SpyLibrary(tmp_path/'biblioteca_que_nao_existe.sqlite3')
    provider = ReplyProvider()
    service = ChatService(
        InMemorySessions(), InMemoryMessages(), provider,
        RecentMessagesContextManager(10), 'fake',
        local_library=library, web_auto_search=web,
    )
    return service, provider, library


@pytest.mark.parametrize('message,target', [
    ('todd?', 'todd'), (' Todd ? ', 'todd'), ('Morgana!', 'morgana'),
    ('ei, Todd?', 'todd'), ('oi morgana', 'morgana'),
    ('Campanário?', 'campanario'), ('Ola, Campanario!', 'campanario'),
])
def test_standalone_call_is_only_a_registered_wake(message, target):
    assert standalone_wake_target(message, default_agent_registry().list()) == target


@pytest.mark.parametrize('message', [
    'Todd, quem foi Ada Lovelace?',
    'Todd, qual a senha do Projeto Faro?',
    'e Todd?',  # factual follow-up, not a greeting
    '/pesquisar Todd',
    'O Todd disse que vai ajudar',
    'Morgana e Todd, quem foi Ada Lovelace?',
    'Oi, o que e o projeto Todd?',
])
def test_knowledge_questions_are_not_a_wake(message):
    assert standalone_wake_target(message, default_agent_registry().list()) is None


def test_wake_uses_registry_not_foreign_entity_allowlist():
    registry = default_agent_registry()
    future = replace(registry.get('morgana'), id='iris', name='Iris')
    assert standalone_wake_target('Iris?', registry.list() + (future,)) == 'iris'
    assert standalone_wake_target('Pessoa Desconhecida?', registry.list()) is None


@pytest.mark.asyncio
@pytest.mark.parametrize('wake,expected_speaker', [
    ('todd?', 'todd'), ('Morgana?', 'morgana'), ('Campanário?', 'morgana'),
    ('ei, Todd?', 'todd'),
])
async def test_short_agent_call_uses_chat_not_search(tmp_path, wake, expected_speaker):
    chat, provider, library = _service(tmp_path, web=True)
    session = chat.create_session()
    events = [event async for event in chat.stream_turn(session.id, wake)]
    answer = ''.join(event.text for event in events if event.type == 'token')
    assert answer == 'Oi, estou aqui. Pode falar!'
    assert 'pesquisa está desligada' not in answer
    assert library.calls == 0
    assert provider.calls == 1
    assert [event.agent_id for event in events if event.type == 'speaker_start'] == [expected_speaker]
    assert chat.get_messages(session.id)[-1].agent_id == expected_speaker
    assert 'CHAMADA CONVERSACIONAL' in provider.requests[0].messages[0].content


@pytest.mark.asyncio
async def test_exact_reproduction_morgana_then_todd(tmp_path):
    chat, provider, library = _service(tmp_path)
    session = chat.create_session()
    first = [ev async for ev in chat.stream_turn(session.id, 'oie')]
    second = [ev async for ev in chat.stream_turn(session.id, 'todd?')]
    assert [e.agent_id for e in first if e.type == 'speaker_start'] == ['morgana']
    assert [e.agent_id for e in second if e.type == 'speaker_start'] == ['todd']
    assert chat._sessions.get(session.id).primary_agent_id == 'todd'
    assert provider.calls == 2
    assert library.calls == 0
    assert chat.get_messages(session.id)[-1].content == 'Oi, estou aqui. Pode falar!'


@pytest.mark.asyncio
async def test_real_factual_question_addressed_to_todd_is_still_guarded(tmp_path):
    chat, provider, library = _service(tmp_path)
    session = chat.create_session()
    events = [ev async for ev in chat.stream_turn(
        session.id, 'Todd, quem foi Pessoa Imaginaria Flaus?',
    )]
    answer = ''.join(ev.text for ev in events if ev.type == 'token')
    assert [ev.agent_id for ev in events if ev.type == 'speaker_start'] == ['todd']
    assert 'não consegui confirmar' in answer.casefold()
    assert provider.calls == 0
    assert library.calls == 1


@pytest.mark.asyncio
async def test_missing_objective_fact_still_abstains(tmp_path):
    chat, provider, library = _service(tmp_path)
    session = chat.create_session()
    events = [ev async for ev in chat.stream_turn(
        session.id, 'Todd, qual a senha do Projeto Faro?',
    )]
    answer = ''.join(ev.text for ev in events if ev.type == 'token')
    assert 'Não encontrei na biblioteca local' in answer
    assert provider.calls == 0
    assert library.calls == 1


@pytest.mark.asyncio
async def test_unknown_bare_name_does_not_bypass_factual_guard(tmp_path):
    chat, provider, _ = _service(tmp_path)
    session = chat.create_session()
    events = [ev async for ev in chat.stream_turn(session.id, 'Xandrel?')]
    assert 'não consegui confirmar' in ''.join(
        ev.text for ev in events if ev.type == 'token'
    ).casefold()
    assert provider.calls == 0
