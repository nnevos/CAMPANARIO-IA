"""Inc.3B.1: topic overlap cannot be mistaken for answerable evidence.

Synthetic fixture data ONLY. No user DB, internet, model, or personal memory.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import uuid4

import pytest

from campanario.chat.evidence_gate import assess_explicit_answer, is_explicit_fact_question
from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.utilities.service import UtilityService
from test_fase4_inc1_biblioteca import _chat, _ask, CountingProvider

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from eval_fase4_inc3b_calibracao import HARD_NEGATIVES


class ClosedUtility(UtilityService):
    @contextmanager
    def connect(self):
        conn = super().connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()


@pytest.fixture
def synthetic(tmp_path):
    utility = ClosedUtility(tmp_path / 'util')
    for source in sorted((ROOT / 'eval' / 'v1' / 'fixtures').glob('*.md')):
        dest = utility.roots[0] / source.name
        dest.write_bytes(source.read_bytes())
        assert utility.run('library.import', {'path': str(dest), 'confirm': True})['status'] == 'success'
    return utility


@pytest.mark.parametrize('backend', ['fts5', 'legacy'])
def test_all_twelve_hard_negatives_refused_without_citing_unrelated_source(synthetic, backend):
    original = sha256(synthetic.db.read_bytes()).digest()
    reader = ReadOnlyLocalLibrary(synthetic.db, backend=backend)
    for name, question, subject in HARD_NEGATIVES:
        quote = reader.search(question, subject=subject)
        assert quote is None, (backend, name, quote)
        assert build_turn_fact_sheet(uuid4(), question, quote, fact_lookup_requested=True).status == 'insufficient'
    assert sha256(synthetic.db.read_bytes()).digest() == original
    assert not Path(str(synthetic.db) + '-shm').exists()
    reader._discard_index()


def test_all_twenty_cited_answers_preserved_with_original_excerpts(synthetic):
    reader = ReadOnlyLocalLibrary(synthetic.db)
    for line in (ROOT / 'eval' / 'v1' / 'documentos.jsonl').read_text(encoding='utf-8').splitlines():
        case = json.loads(line)
        hit = reader.search(case['question'])
        assert hit is not None and hit.status == 'grounded', case['id']
        assert hit.quote.name == case['document'] and case['expected_quote'] in hit.quote.excerpt
        sheet = build_turn_fact_sheet(uuid4(), case['question'], hit, fact_lookup_requested=True)
        assert sheet.status == 'supported' and len(sheet.claims) == 1
    reader._discard_index()


def test_same_attribute_different_object_not_interchangeable():
    question = 'Qual a cor do uniforme da equipe de Ponte?'
    quote = 'A etiqueta do Protocolo Ponte usa a cor marfim.'
    verdict = assess_explicit_answer(question, 'Ponte', quote, 'protocolo_ponte.md')
    assert not verdict.sufficient and verdict.reason == 'requested_qualifier_absent'
    assert assess_explicit_answer('Qual cor tem a etiqueta do Protocolo Ponte?', 'Ponte',
                                  quote, 'protocolo_ponte.md').sufficient


def test_subject_parser_must_not_erase_the_attribute_asked_for():
    q = 'Quem é a observadora do diário Aurora?'
    a = assess_explicit_answer(q, 'observadora do diário Aurora',
                                 'No diário de teste Aurora, a personagem fictícia Lia Nobre atua como observadora.',
                                 'diario_aurora.md')
    assert a.sufficient


def test_explicit_fact_question_distinguishes_opinions_and_advice():
    assert is_explicit_fact_question('Qual a senha do Projeto Faro?')
    assert is_explicit_fact_question('A que horas começa a reunião de Ponte?')
    assert is_explicit_fact_question('Quem assinou a ata de Ponte?')
    assert not is_explicit_fact_question('Qual sua opinião sobre Ponte?')
    assert not is_explicit_fact_question('Qual seria a melhor estratégia para hoje?')
    assert not is_explicit_fact_question('Oi, tudo bem?')


@pytest.mark.asyncio
async def test_chat_all_hard_negatives_abstain_without_model_or_false_citations(synthetic):
    reader = ReadOnlyLocalLibrary(synthetic.db)
    provider = CountingProvider()
    chat, _ = _chat(reader, provider)
    for case_id, question, subject in HARD_NEGATIVES:
        _, history = await _ask(chat, question)
        answer = history[-1].content.casefold()
        assert 'não encontrei na biblioteca local' in answer, (case_id, answer)
        assert 'fonte:' not in answer and 'alucinacao_do_modelo' not in answer
    assert provider.calls == 0
    reader._discard_index()


@pytest.mark.asyncio
async def test_group_turn_shares_abstention_without_inventing(synthetic):
    reader = ReadOnlyLocalLibrary(synthetic.db)
    provider = CountingProvider()
    chat, _ = _chat(reader, provider)
    events, history = await _ask(chat, 'Morgana e Todd, qual a senha de acesso do Protocolo Ponte?', group=True)
    assert [e.agent_id for e in events if e.type == 'speaker_start'] == ['morgana', 'todd']
    answers = [m.content.casefold() for m in history if m.agent_id]
    assert len(answers) == 2
    assert all('não encontrei na biblioteca local' in a and 'fonte:' not in a for a in answers)
    assert provider.calls == 0
    reader._discard_index()


@pytest.mark.asyncio
async def test_opinion_stays_ordinary_conversation(synthetic):
    reader = ReadOnlyLocalLibrary(synthetic.db)
    provider = CountingProvider()
    chat, _ = _chat(reader, provider)
    _, history = await _ask(chat, 'Qual seria a melhor estratégia para conversar com Todd?')
    assert provider.calls >= 1
    reader._discard_index()


def test_entire_evaluator_exits_without_windows_sqlite_lock(tmp_path):
    """Check actual TemporaryDirectory deletion, not only returned counters."""
    import subprocess
    path = tmp_path / 'report.json'
    completed = subprocess.run(
        [sys.executable, str(ROOT / 'tools' / 'eval_fase4_inc3b1.py'),
         '--report', str(path)],
        cwd=ROOT, capture_output=True, text=True, timeout=90,
    )
    assert completed.returncode == 0, completed.stdout + '\n' + completed.stderr
    report = json.loads(path.read_text(encoding='utf-8'))
    assert report['hard_negatives']['chat_abstained'] == 12
    assert report['hard_negatives']['no_cited_claim'] == 12
    assert report['temporary_sqlite_byte_identical']
