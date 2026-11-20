"""Fase 4, Inc.3A: FTS5 RAM-only, accurate citations and safe fallback."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.utilities.service import UtilityService


class _TemporaryUtilityService(UtilityService):
    """Only synthetic test data; close SQLite handles before Windows temp cleanup."""
    @contextmanager
    def connect(self):
        conn = super().connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'eval' / 'v1'


def _fts_available():
    try:
        with sqlite3.connect(':memory:') as db:
            db.execute('CREATE VIRTUAL TABLE test_fts USING fts5(body)')
        return True
    except sqlite3.OperationalError:
        return False


@pytest.fixture
def synthetic(tmp_path):
    service = _TemporaryUtilityService(tmp_path / 'utilities')
    cases = [json.loads(line) for line in (DATA / 'documentos.jsonl').read_text(
        encoding='utf-8').splitlines() if line.strip()]
    for name in sorted({case['document'] for case in cases}):
        path = service.roots[0] / name
        path.write_bytes((DATA / 'fixtures' / name).read_bytes())
        assert service.run('library.import', {'path': str(path), 'confirm': True})['status'] == 'success'
    return service, cases


def test_fts5_default_preserves_20_exact_documents_and_quotes(synthetic):
    service, cases = synthetic
    before = hashlib.sha256(service.db.read_bytes()).digest()
    reader = ReadOnlyLocalLibrary(service.db)
    for case in cases:
        result = reader.search(case['question'])
        assert result is not None, case['id']
        assert result.quote.name == case['document'], case['id']
        assert case['expected_quote'] in result.quote.excerpt, case['id']
        sheet = build_turn_fact_sheet(uuid4(), case['question'], result)
        assert sheet.origin == 'library' and sheet.sources[0].title == case['document']
        assert sheet.claims[0].certainty == 'source_assertion'
    assert hashlib.sha256(service.db.read_bytes()).digest() == before
    if _fts_available():
        assert reader.last_backend_used == 'fts5_memory'
        assert reader.index_build_count == 1  # one build, twenty questions


def test_legacy_reference_also_preserves_20_exact_documents(synthetic):
    service, cases = synthetic
    reader = ReadOnlyLocalLibrary(service.db, backend='legacy')
    assert all((result := reader.search(case['question'])) is not None
               and case['expected_quote'] in result.quote.excerpt
               and result.quote.name == case['document'] for case in cases)
    assert reader.index_build_count == 0


@pytest.mark.skipif(not _fts_available(), reason='SQLite Python sem FTS5; fallback testado')
@pytest.mark.parametrize('question,expected_name,expected_fragment', [
    ('Quais arquivos de Horizonte?', 'guia_horizonte.md', 'arquivo norte.csv'),
    ('Quais etiquetas de Ponte?', 'protocolo_ponte.md', 'cor marfim'),
    ('Quais símbolos de Horizonte?', 'guia_horizonte.md', 'círculo verde'),
    ('Quais inventários de Aurora?', 'diario_aurora.md', '14 amostras'),
    ('Quais checklists de Ponte?', 'protocolo_ponte.md', 'versão 7'),
    ('E as revisões de Rumo?', 'guia_rumo.md', '18 minutos'),
])
def test_plural_singular_variant_can_recover_literal_evidence(
        synthetic, question, expected_name, expected_fragment):
    service, _ = synthetic
    legacy = ReadOnlyLocalLibrary(service.db, backend='legacy').search(question)
    assert legacy is None  # confirmed measurable recall gain over Inc.2
    reader = ReadOnlyLocalLibrary(service.db)
    modern = reader.search(question)
    assert modern is not None
    assert modern.quote.name == expected_name
    assert expected_fragment in modern.quote.excerpt
    assert reader.last_backend_used == 'fts5_memory'


@pytest.mark.parametrize('question', [
    'Quem foi Ada Lovelace?',
    'Quem foi Célia Vornacz?',
    'Os assinantes de Rumo?',  # NOT the same as protocol signatures
    'Quem criou o Projeto Rumo no século XII?',
    'Onde fica a marca secreta de Ponte?',
])
def test_no_unsupported_identity_or_approximate_word_claim(synthetic, question):
    service, _ = synthetic
    assert ReadOnlyLocalLibrary(service.db).search(question) is None


def test_partial_overlap_false_relevance_is_now_rejected(synthetic):
    # Inc.3B.1 guards the requested attribute, not merely the topic.
    service, _ = synthetic
    question = 'O Projeto Faro teve autorização de Zeus?'
    previous = ReadOnlyLocalLibrary(service.db, backend='legacy').search(question)
    modern = ReadOnlyLocalLibrary(service.db, backend='fts5').search(question)
    assert previous is None and modern is None


@pytest.mark.skipif(not _fts_available(), reason='SQLite Python sem FTS5')
def test_index_reused_then_invalidated_after_document_import(synthetic):
    service, _ = synthetic
    reader = ReadOnlyLocalLibrary(service.db)
    assert reader.search('Quais etiquetas de Ponte?') is not None
    assert reader.index_build_count == 1
    assert reader.search('Quais símbolos de Horizonte?') is not None
    assert reader.index_build_count == 1
    path = service.roots[0] / 'novo_arquivo.md'
    path.write_text('O mapa do Projeto Jasmim fica na estante 87.', encoding='utf-8')
    assert service.run('library.import', {'path': str(path), 'confirm': True})['status'] == 'success'
    result = reader.search('Onde fica o mapa do Projeto Jasmim?', subject='Projeto Jasmim')
    assert result is not None and 'estante 87' in result.quote.excerpt
    assert reader.index_build_count == 2


def test_fallback_to_original_read_only_scan_if_fts_unavailable(synthetic, monkeypatch):
    service, _ = synthetic
    reader = ReadOnlyLocalLibrary(service.db)
    def unavailable(stamp):
        raise sqlite3.OperationalError('no such module: fts5')
    monkeypatch.setattr(reader, '_ensure_index', unavailable)
    result = reader.search('Qual intervalo padrão de revisão em Rumo?')
    assert result and '18 minutos' in result.quote.excerpt
    assert reader.last_backend_used == 'legacy'


def test_missing_database_is_not_created_and_no_sidecar_files(tmp_path):
    database = tmp_path / 'missing.sqlite3'
    assert ReadOnlyLocalLibrary(database).search('Quem foi Ada Lovelace?') is None
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(not _fts_available(), reason='SQLite Python sem FTS5')
def test_parallel_queries_share_one_locked_memory_index(synthetic):
    service, _ = synthetic
    reader = ReadOnlyLocalLibrary(service.db)
    questions = ['Quais arquivos de Horizonte?', 'Quais etiquetas de Ponte?',
                 'Quais símbolos de Horizonte?', 'Quais inventários de Aurora?']
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(reader.search, questions * 4))
    assert all(result and result.status == 'grounded' for result in results)
    assert reader.index_build_count == 1


def test_conflicting_sources_do_not_autoselect_in_fts5(tmp_path):
    service = _TemporaryUtilityService(tmp_path / 'utilities')
    for name, text in [('a.md', 'A cor da etiqueta Ponte é marfim.'),
                       ('b.md', 'A cor da etiqueta Ponte é vermelha.')]:
        path = service.roots[0] / name
        path.write_text(text, encoding='utf-8')
        assert service.run('library.import', {'path': str(path), 'confirm': True})['status'] == 'success'
    reader = ReadOnlyLocalLibrary(service.db)
    result = reader.search('Qual a cor da etiqueta Ponte?')
    assert result is not None and result.status == 'ambiguous'
    assert len(result.conflicts) == 1
    assert 'não posso escolher' in result.verified_answer


def test_source_db_byte_identical_after_repeated_queries(synthetic):
    service, _ = synthetic
    digest = hashlib.sha256(service.db.read_bytes()).hexdigest()
    files_before = sorted(p.name for p in service.base.iterdir())
    reader = ReadOnlyLocalLibrary(service.db)
    for _ in range(4):
        reader.search('Quais arquivos de Horizonte?')
    assert hashlib.sha256(service.db.read_bytes()).hexdigest() == digest
    assert sorted(p.name for p in service.base.iterdir()) == files_before


def test_full_inc3_evaluator_subprocess_finishes_and_closes_windows_tempdb(tmp_path):
    """Windows must be able to delete ALL temporary utility databases on exit."""
    import subprocess
    import sys
    report = tmp_path / 'results.json'
    run = subprocess.run(
        [sys.executable, str(ROOT / 'tools' / 'eval_fase4_inc3.py'),
         '--report', str(report)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=90,
    )
    assert run.returncode == 0, run.stdout + '\n' + run.stderr
    data = json.loads(report.read_text(encoding='utf-8'))
    assert data['updated_fts5']['docs_exact_and_cited'] == 20
    assert data['chat_exact_quotes_and_citations'] == 20
    assert data['source_sqlite_byte_identical']
    assert data['no_persistent_index_created']
