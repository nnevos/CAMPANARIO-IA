"""R3.0 source-specific, adversarial factual consolidation tests."""
from dataclasses import replace
from uuid import uuid4

import pytest

from campanario.chat.canonical_answer import SourceRecord, build_canonical, VerificationStatus
from campanario.chat.evidence_reconciliation import reconcile_numeric_evidence
from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.local_library import LibraryQuote, LocalFactSheet


def _source(label, sentence, *, doc=None, locator=None):
    return SourceRecord(source_id=label, kind='imported_document', title=label,
                        locator=locator or label, document_id=doc or label, excerpt=sentence)


@pytest.mark.parametrize('left,right,expected', [
    ('O prazo contratual acordado é 20 dias.', 'O prazo contratual acordado é 30 dias.', True),
    ('O limite mensal aprovado é 20%.', 'O limite mensal aprovado é 90%.', True),
    ('O custo mensal previsto é R$ 200.', 'O custo mensal previsto é R$ 500.', True),
    ('O prazo contratual acordado é 20 dias.', 'O custo contratual acordado é 30 dias.', False),
    ('O limite mensal aprovado é 20%.', 'O limite semanal aprovado é 90%.', False),
    ('O prazo contratual acordado é 20 dias.', 'O prazo contratual acordado é 20 dias.', False),
    ('O valor informado mudou recentemente.', 'O valor informado mudou recentemente.', False),
    ('O prazo é 20 dias.', 'O prazo é 30 dias.', False),
    ('O custo mensal aprovado é 100 reais.', 'O custo mensal aprovado é 1000 reais.', True),
    ('O prazo contratual é 20 dias.', 'O prazo contratual é 30 dias.', True),
])
def test_r30_exact_frame_conflict_only(left, right, expected):
    findings = reconcile_numeric_evidence((_source('a', left), _source('b', right)))
    assert bool(findings) is expected
    if findings:
        assert findings[0].source_ids == ('a', 'b')
        assert findings[0].excerpts == (left, right)


def test_r30_two_pages_of_same_document_do_not_count_as_independent_sources():
    sources = (_source('page1', 'O prazo contratual acordado é 20 dias.', doc='same'),
               _source('page2', 'O prazo contratual acordado é 30 dias.', doc='same'))
    assert not reconcile_numeric_evidence(sources)


def test_r30_read_only_never_mutates_sources():
    sources = (_source('a', 'O limite mensal aprovado é 20%.'),
               _source('b', 'O limite mensal aprovado é 90%.'))
    before = [s.model_dump() for s in sources]
    reconcile_numeric_evidence(sources)
    assert [s.model_dump() for s in sources] == before


def test_r30_rejects_invalid_limit():
    with pytest.raises(ValueError):
        reconcile_numeric_evidence((), limit=0)
    with pytest.raises(ValueError):
        reconcile_numeric_evidence((), limit=26)


def _quote(key, text):
    return LibraryQuote(key, key + '.txt', key * 64, 1, text, 10,
                        evidence_id='library:' + key)


def test_r30_contradictory_documents_cannot_publish_a_chosen_value():
    guard = LocalFactSheet('prazo', 'Qual o prazo contratual?',
                           _quote('a', 'O prazo contratual acordado é 20 dias.'),
                           conflicts=(_quote('b', 'O prazo contratual acordado é 30 dias.'),))
    sheet = build_turn_fact_sheet(uuid4(), guard.query, guard)
    canonical = build_canonical(sheet, guard, brain_ids=('knowledge',))
    assert canonical.status == VerificationStatus.CONFLICTING
    assert 'não vou escolher um valor' in canonical.canonical_answer
    assert '20' not in canonical.canonical_answer
    assert '30' not in canonical.canonical_answer
    assert 'library:a' in canonical.contradictions[0]
    assert len(canonical.sources) == 2


def test_r30_single_source_keeps_exact_provenance():
    guard = LocalFactSheet('prazo', 'Qual o prazo?',
                           _quote('a', 'O prazo contratual acordado é 20 dias.'))
    sheet = build_turn_fact_sheet(uuid4(), guard.query, guard)
    canonical = build_canonical(sheet, guard, brain_ids=('knowledge',))
    assert canonical.status == VerificationStatus.PARTIALLY_VERIFIED
    assert canonical.contradictions == ()


def test_r30_no_brain_result_is_not_promoted_by_reviewer():
    guard = LocalFactSheet('prazo', 'Qual o prazo?',
                           _quote('a', 'O prazo contratual acordado é 20 dias.'),
                           conflicts=(_quote('b', 'O prazo contratual acordado é 30 dias.'),))
    sheet = build_turn_fact_sheet(uuid4(), guard.query, guard)
    canonical = build_canonical(sheet, guard)
    # This feature is explicitly opt-in for a traced, first-party brain path.
    assert canonical.status == VerificationStatus.PARTIALLY_VERIFIED


def test_r30_multi_number_sentence_is_not_compared():
    left = _source('a', 'O projeto terá 20 pessoas e 5 salas.')
    right = _source('b', 'O projeto terá 30 pessoas e 5 salas.')
    assert reconcile_numeric_evidence((left, right)) == ()
