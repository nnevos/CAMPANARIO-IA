"""Inc.3B: optional semantic discovery, never automatically verified facts."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import math
from pathlib import Path
import sqlite3
import subprocess
import sys
from uuid import uuid4

import pytest

from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.chat.semantic_library import (
    HybridLocalLibrary, LoopbackOllamaEmbeddings, normalize,
)
from campanario.config import Settings
from campanario.utilities.service import UtilityService

from test_fase4_inc1_biblioteca import _chat, _ask, CountingProvider

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
sys.path.insert(0, str(TOOLS))
from eval_fase4_inc3b import FixtureEmbeddings, PARAPHRASES, NEGATIVES


class TempUtility(UtilityService):
    @contextmanager
    def connect(self):
        conn = super().connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()


@pytest.fixture
def source(tmp_path):
    util = TempUtility(tmp_path / 'utilities')
    for path in sorted((ROOT / 'eval' / 'v1' / 'fixtures').glob('*.md')):
        target = util.roots[0] / path.name
        target.write_bytes(path.read_bytes())
        assert util.run('library.import', {'path': str(target), 'confirm': True})['status'] == 'success'
    return util


def test_paraphrases_are_discovered_but_not_presented_as_evidence(source):
    from diagnostico_fase4_inc3b import score_candidates
    reader = HybridLocalLibrary(source.db, embeddings=FixtureEmbeddings(),
                                min_similarity=.50)
    original = ReadOnlyLocalLibrary(source.db)
    before = hashlib.sha256(source.db.read_bytes()).digest()
    for caseid, question, subject, name, answer in PARAPHRASES:
        assert original.search(question, subject=subject) is None, caseid
        # Discovery is measurable independently of permission to show evidence.
        reader._ensure_semantics(reader._file_stamp())
        diagnostic = score_candidates(reader, question, subject, name, answer)
        assert diagnostic['top_accepted'][0]['expected_quote'], caseid
        suggestion = reader.search(question, subject=subject)
        assert suggestion is None, caseid  # synonym relation not yet validated
        assert reader.last_semantic_status == 'rejected_insufficient_evidence'
        assert reader.last_semantic_rejected > 0
    assert reader.semantic_build_count == 1
    assert hashlib.sha256(source.db.read_bytes()).digest() == before
    reader._discard_index()


def test_rejected_semantic_hit_not_promoted_to_fact_sheet(source):
    reader = HybridLocalLibrary(source.db, embeddings=FixtureEmbeddings(),
                                min_similarity=.50)
    question = PARAPHRASES[0][1]
    suggestion = reader.search(question, subject='Rumo')
    assert suggestion is None
    sheet = build_turn_fact_sheet(uuid4(), question, suggestion,
                                  fact_lookup_requested=True)
    assert sheet.status == 'insufficient' and sheet.origin == 'none'
    assert len(sheet.sources) == 0 and len(sheet.claims) == 0
    assert not sheet.evidence_available and sheet.extractive_answer is None
    reader._discard_index()


def test_no_embedding_calls_for_supported_fts5_first(source):
    provider = FixtureEmbeddings()
    reader = HybridLocalLibrary(source.db, embeddings=provider)
    found = reader.search('Qual a cor oficial da etiqueta do Protocolo Ponte?', subject='Ponte')
    assert found is not None and found.status == 'grounded'
    assert provider.calls == 0
    assert reader.semantic_build_count == 0


@pytest.mark.parametrize('caseid,question,subject', NEGATIVES)
def test_unsupported_entities_cannot_be_facts(source, caseid, question, subject):
    reader = HybridLocalLibrary(source.db, embeddings=FixtureEmbeddings())
    found = reader.search(question, subject=subject)
    sheet = build_turn_fact_sheet(uuid4(), question, found, fact_lookup_requested=True)
    assert sheet.status != 'supported', caseid


def test_cache_reused_and_rebuilt_after_document_change(source):
    provider = FixtureEmbeddings()
    reader = HybridLocalLibrary(source.db, embeddings=provider)
    reader.search(PARAPHRASES[0][1], subject='Rumo')
    first_calls = provider.calls
    reader.search(PARAPHRASES[1][1], subject='Ponte')
    assert reader.semantic_build_count == 1
    assert provider.calls == first_calls + 1  # cached corpus; query only
    path = source.roots[0] / 'anexo_mudanca.md'
    path.write_text('O arquivo da Estacao Nebula usa o marcador lilas.', encoding='utf-8')
    assert source.run('library.import', {'path': str(path), 'confirm': True})['status'] == 'success'
    reader.search(PARAPHRASES[0][1], subject='Rumo')
    assert reader.semantic_build_count == 2


def test_model_down_falls_back_and_cools_down(source):
    class Offline:
        calls = 0
        def embed(self, texts):
            self.calls += 1
            raise OSError('ollama not running')
    backend = Offline()
    reader = HybridLocalLibrary(source.db, embeddings=backend)
    assert reader.search(PARAPHRASES[0][1], subject='Rumo') is None
    assert reader.last_semantic_status == 'failed_lexical_fallback'
    assert reader.search(PARAPHRASES[0][1], subject='Rumo') is None
    assert backend.calls == 1
    assert reader.search('Qual a cor da etiqueta de Ponte?', subject='Ponte') is not None


@pytest.mark.parametrize('broken', [[float('nan')], [float('inf')], [0.0, 0.0], [], [True, 0.0]])
def test_bad_embeddings_rejected(broken):
    with pytest.raises(ValueError):
        normalize(broken)


def test_inconsistent_embedding_batches_fail_closed(source):
    class Broken:
        def embed(self, texts):
            return [[1.0, 0.0]]  # too few vectors for full batch
    reader = HybridLocalLibrary(source.db, embeddings=Broken())
    assert reader.search(PARAPHRASES[1][1], subject='Ponte') is None
    assert reader.last_semantic_status == 'failed_lexical_fallback'
    assert reader.semantic_build_count == 0


def test_bounded_batches_and_index_size(source):
    class Spy(FixtureEmbeddings):
        batches = []
        def embed(self, texts):
            self.batches.append(len(texts))
            return super().embed(texts)
    backend = Spy()
    reader = HybridLocalLibrary(source.db, embeddings=backend,
                                 max_semantic_segments=8, batch_size=3)
    reader.search(PARAPHRASES[0][1], subject='Rumo')
    assert sum(backend.batches[:-1]) == 8
    assert all(1 <= b <= 3 for b in backend.batches)
    assert len(reader._semantic_segments) == 8


@pytest.mark.parametrize('bad_url', [
    'https://127.0.0.1:11434', 'http://192.168.1.5:11434',
    'http://localhost:11434', 'http://example.org:11434',
    'http://127.0.0.1:11434@external.example',
    'http://127.0.0.1:11434/another/path',
])
def test_real_provider_refuses_non_literal_loopback(bad_url):
    with pytest.raises(ValueError):
        LoopbackOllamaEmbeddings(url=bad_url)


def test_real_provider_disallows_proxies_redirects_and_external_calls(monkeypatch):
    calls = []
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'embeddings': [[1.0, 0.0], [0.0, 1.0]]}
    class FakeClient:
        def __init__(self, **kw):
            assert kw['trust_env'] is False and kw['follow_redirects'] is False
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, json):
            calls.append((url, json))
            return Response()
    monkeypatch.setattr('campanario.chat.semantic_library.httpx.Client', FakeClient)
    provider = LoopbackOllamaEmbeddings()
    assert provider.embed(['primeiro', 'segundo']) == [[1.0, 0.0], [0.0, 1.0]]
    assert calls[0][0] == 'http://127.0.0.1:11434/api/embed'
    assert calls[0][1]['model'] == 'embeddinggemma'
    assert calls[0][1]['input'] == ['primeiro', 'segundo']


@pytest.mark.asyncio
async def test_chat_does_not_expose_unvalidated_semantic_candidate(source):
    provider = CountingProvider()
    reader = HybridLocalLibrary(source.db, embeddings=FixtureEmbeddings())
    chat, _ = _chat(reader, provider)
    _, messages = await _ask(chat, 'Qual a tonalidade do identificador de Ponte?')
    answer = messages[-1].content
    assert 'Não encontrei na biblioteca local' in answer
    assert 'cor marfim' not in answer and 'Fonte' not in answer
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_two_agents_share_one_semantic_snapshot(source):
    provider = CountingProvider()
    reader = HybridLocalLibrary(source.db, embeddings=FixtureEmbeddings())
    chat, _ = _chat(reader, provider)
    events, history = await _ask(
        chat, 'Morgana e Todd, qual a tonalidade do identificador de Ponte?', group=True)
    answers = [m.content for m in history if m.agent_id]
    assert [e.agent_id for e in events if e.type == 'speaker_start'] == ['morgana', 'todd']
    assert len(answers) == 2 and answers[0] == answers[1]
    assert all('Não encontrei na biblioteca local' in a for a in answers)
    assert all('cor marfim' not in a for a in answers)
    assert reader.semantic_build_count == 1 and provider.calls == 0


def test_missing_database_is_not_created(tmp_path):
    db = tmp_path / 'missing.sqlite3'
    reader = HybridLocalLibrary(db, embeddings=FixtureEmbeddings())
    assert reader.search('Qual o tempo entre inspecoes no Rumo?', subject='Rumo') is None
    assert not db.exists()


def test_disabled_by_default_is_distinct_from_semantic_personal_memory():
    s = Settings(_env_file=None)
    assert s.library_semantic_enabled is False
    assert s.library_semantic_model == 'embeddinggemma'


def test_evaluator_subprocess_cleans_all_temp_databases(tmp_path):
    target = tmp_path / 'semantic_fixture.json'
    result = subprocess.run(
        [sys.executable, str(TOOLS / 'eval_fase4_inc3b.py'), '--report', str(target)],
        cwd=ROOT, text=True, capture_output=True, timeout=40,
    )
    assert result.returncode == 0, result.stdout + '\n' + result.stderr
    report = __import__('json').loads(target.read_text(encoding='utf-8'))
    assert report['existing_docs_still_correct'] == 20
    assert report['hybrid_semantic_paraphrases']['positive_correct_source'] == 0
    assert report['semantic_sufficiency_gate'] == 'active_fail_closed'
