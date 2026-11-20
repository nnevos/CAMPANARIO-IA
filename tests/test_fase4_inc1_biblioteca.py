"""Fase 4 incremento 1: biblioteca real por SQLite isolado, 100% offline."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.chat.service import ChatService
from campanario.model.protocol import ModelChunk
from campanario.utilities.service import UtilityService
from test_chat_service import InMemorySessions, InMemoryMessages


class CountingProvider:
    def __init__(self):
        self.calls = 0
    async def health(self):
        return True
    async def stream(self, request):
        self.calls += 1
        yield ModelChunk(text='ALUCINACAO_DO_MODELO_NAO_PERMITIDA')
        yield ModelChunk(text='', done=True)


class CountingLibrary(ReadOnlyLocalLibrary):
    def __init__(self, database):
        super().__init__(database)
        self.calls = 0
    def search(self, question, *, subject=''):
        self.calls += 1
        return super().search(question, subject=subject)


@pytest.fixture
def library(tmp_path):
    util = UtilityService(tmp_path / 'utilities')
    for name, content in {
        'manual_faro.md': (
            '# Manual de Faro\n\n'
            'O Projeto Faro opera apenas com relatórios locais e não consulta serviços externos por padrão.\n'
            'O índice do Projeto Faro é atualizado manualmente às quartas-feiras.\n'
        ),
        'guia_rumo.md': (
            '# Guia de Rumo\n\n'
            'O selo de conferência do Guia Rumo é azul.\n'
            'O intervalo padrão da revisão em Rumo é de 18 minutos.\n'
        ),
    }.items():
        path = util.roots[0] / name
        path.write_text(content, encoding='utf-8')
        result = util.run('library.import', {'path': str(path), 'confirm': True})
        assert result['status'] == 'success'
    return util


def _chat(source, provider=None, *, web=False):
    provider = provider or CountingProvider()
    chat = ChatService(
        InMemorySessions(), InMemoryMessages(), provider,
        RecentMessagesContextManager(10), 'fake',
        local_library=source, web_auto_search=web,
        low_latency_mode=True, grounded_synthesis=False,
    )
    return chat, provider


async def _ask(chat, question, *, agent_id=None, group=False):
    session = chat.create_session(agent_id=agent_id)
    events = [ev async for ev in chat.stream_turn(
        session.id, question, independent_group_turn=group,
    )]
    return events, chat.get_messages(session.id)


@pytest.mark.asyncio
async def test_chat_reads_real_imported_document_instead_of_hallucinating(library):
    db = library.db
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    provider = CountingProvider()
    chat, _ = _chat(ReadOnlyLocalLibrary(db), provider)
    events, history = await _ask(chat, 'O Projeto Faro usa serviços externos por padrão?')
    answer = ''.join(ev.text for ev in events if ev.type == 'token')
    assert 'não consulta serviços externos por padrão.' in answer
    assert 'Fonte: manual_faro.md' in answer
    assert 'ALUCINACAO_DO_MODELO' not in answer
    assert provider.calls == 0
    assert history[-1].content == answer
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before


@pytest.mark.asyncio
async def test_second_agent_reuses_one_local_snapshot(library):
    counted = CountingLibrary(library.db)
    chat, provider = _chat(counted)
    events, history = await _ask(
        chat, 'Morgana e Todd, o Projeto Faro usa serviços externos por padrão?', group=True,
    )
    speakers = [event.agent_id for event in events if event.type == 'speaker_start']
    answers = [message.content for message in history if message.agent_id]
    assert speakers == ['morgana', 'todd']
    assert len(answers) == 2
    assert all('não consulta serviços externos por padrão' in answer for answer in answers)
    assert all('Fonte: manual_faro.md' in answer for answer in answers)
    assert counted.calls == 1
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_local_precedes_web_auto_search(library, monkeypatch):
    import campanario.utilities.web_chat as web_chat
    def internet_broken(*args, **kwargs):
        raise AssertionError('external network should not have been requested')
    monkeypatch.setattr(web_chat, 'research_entity', internet_broken)
    monkeypatch.setattr(web_chat, 'research_topic', internet_broken)
    chat, provider = _chat(ReadOnlyLocalLibrary(library.db), web=True)
    # Verify the legacy mode is still available when explicitly requested.
    chat._research_priority = 'local_first'
    _, history = await _ask(chat, 'Quando é atualizado o índice do Projeto Faro?')
    assert 'quartas-feiras' in history[-1].content
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_ordinary_chat_unchanged_and_missing_database_not_created(tmp_path):
    db = tmp_path / 'not_created.sqlite3'
    chat, provider = _chat(ReadOnlyLocalLibrary(db))
    _, history = await _ask(chat, 'Oi, tudo bem?')
    assert history[-1].content == 'ALUCINACAO_DO_MODELO_NAO_PERMITIDA'
    assert provider.calls >= 1
    assert not db.exists()


@pytest.mark.asyncio
async def test_no_library_evidence_preserves_existing_factual_guard(tmp_path):
    chat, provider = _chat(ReadOnlyLocalLibrary(tmp_path / 'absent.sqlite3'))
    _, history = await _ask(chat, 'Quem foi Pessoa Imaginária Flaus?')
    assert 'não consegui confirmar' in history[-1].content.casefold()
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_personal_memory_not_laundered_as_document(library):
    chat, provider = _chat(ReadOnlyLocalLibrary(library.db))
    _, history = await _ask(chat, 'Qual é o meu documento favorito do Projeto Faro?')
    assert 'Fonte: manual_faro.md' not in history[-1].content
    assert provider.calls >= 1  # preexisting personal memory check has priority


def test_source_requires_multiple_relevant_terms(library):
    reader = ReadOnlyLocalLibrary(library.db)
    assert reader.search('Quem foi Ada Lovelace?', subject='Ada Lovelace') is None
    assert reader.search('Qual a profissão de alguém desconhecido?') is None
    assert reader.search('O projeto não teve autorização?') is None


def test_explicit_subject_prevents_wrong_document_identity(library):
    reader = ReadOnlyLocalLibrary(library.db)
    assert reader.search('Quem foi Aurora Faro?', subject='Aurora Faro') is None


def test_reader_never_creates_tables_or_uses_utility_operation_log(library):
    db = library.db
    with sqlite3.connect(db) as conn:
        before = conn.execute('SELECT count(*) FROM operations').fetchone()[0]
    quote = ReadOnlyLocalLibrary(db).search('Qual intervalo padrão de revisão em Rumo?')
    assert quote and '18 minutos' in quote.verified_answer
    with sqlite3.connect(db) as conn:
        after = conn.execute('SELECT count(*) FROM operations').fetchone()[0]
    assert before == after


def test_database_with_broken_schema_fails_closed(tmp_path):
    db = tmp_path / 'untrusted.sqlite3'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE mystery(x TEXT)')
    assert ReadOnlyLocalLibrary(db).search('Quando é atualizado o índice do Projeto Faro?') is None


def test_ambiguity_across_two_documents_abstains(tmp_path):
    util = UtilityService(tmp_path / 'u')
    for name, body in (
        ('protocolo_um.md', 'A cor oficial do protocolo Ponte é azul.'),
        ('protocolo_dois.md', 'A cor oficial do protocolo Ponte é vermelha.'),
    ):
        file = util.roots[0] / name
        file.write_text(body, encoding='utf-8')
        assert util.run('library.import', {'path': str(file), 'confirm': True})['status'] == 'success'
    result = ReadOnlyLocalLibrary(util.db).search('Qual a cor oficial do protocolo Ponte?')
    assert result and result.status == 'ambiguous'
    assert 'azul' in result.verified_answer and 'vermelha' in result.verified_answer


def test_pdf_page_provenance_is_preserved_in_existing_sqlite(tmp_path):
    util = UtilityService(tmp_path / 'u')
    document = 'O índice do Projeto Teste fica na sala 73.'
    with sqlite3.connect(util.db) as conn:
        conn.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?)', (
            'id-pdf', 'teste.pdf', 'geral', 'sha256-ficticio', document,
            json.dumps([{'page': 7, 'text': document}]), 'fixture.pdf', '2026-01-01',
        ))
    answer = ReadOnlyLocalLibrary(util.db).search('Onde fica o índice do Projeto Teste?')
    assert answer and 'página 7' in answer.verified_answer


def test_config_defaults_to_offline(monkeypatch):
    from campanario.config import Settings
    monkeypatch.delenv('CAMPANARIO_WEB_AUTO_SEARCH', raising=False)
    settings = Settings(_env_file=None)
    assert settings.web_auto_search is False
