"""R2.11: source relevance/conflict and evidence-audit contract regression.

These checks do not claim semantic truth or external corroboration.
"""
from dataclasses import replace
from uuid import uuid4

import pytest

from campanario.chat.canonical_answer import VerificationStatus, build_canonical
from campanario.chat.evidence_gate import assess_explicit_answer
from campanario.chat.fact_sheet import FactClaim, build_turn_fact_sheet
from campanario.chat.local_library import LibraryQuote, LocalFactSheet
from campanario.chat.memory_grounding import verdict_supported, unlicensed_personal_strength


def _guard(*, text='A regra exige autorização prévia de 20%.', conflicts=(), status='grounded'):
    primary = LibraryQuote('doc-one', 'regras.txt', 'a' * 64, 1, text, 7.0,
                           evidence_id='library:doc-one')
    return LocalFactSheet('regra', 'Qual é a regra?', primary,
                          status=status, conflicts=conflicts, read_count=1 + len(conflicts))


def test_local_evidence_can_answer_requested_attribute_but_not_unrelated_one():
    source = 'O selo do documento é azul.'
    assert assess_explicit_answer('Qual é a cor do selo?', 'selo', source).sufficient
    unrelated = assess_explicit_answer('Qual é a senha do documento?', 'documento', source)
    assert not unrelated.sufficient
    assert unrelated.reason in {'requested_attribute_absent', 'requested_qualifier_absent'}


def test_source_text_cannot_be_replaced_by_different_claim_even_with_real_id():
    guard = _guard()
    sheet = build_turn_fact_sheet(uuid4(), 'Qual é a regra?', guard)
    source_id = sheet.sources[0].id
    tampered = replace(sheet, claims=(FactClaim('A regra exige autorização prévia de 90%.', (source_id,)),))
    canonical = build_canonical(tampered, guard, brain_ids=('knowledge',))
    assert canonical.status == VerificationStatus.NOT_FOUND
    assert canonical.facts == ()
    assert '90%' not in canonical.canonical_answer


def test_conflicting_documents_are_not_promoted_to_verified_claims():
    other = LibraryQuote('doc-two', 'outro.txt', 'b' * 64, 2,
                         'A regra dispensa autorização prévia.', 7.0,
                         evidence_id='library:doc-two')
    guard = _guard(conflicts=(other,), status='ambiguous')
    sheet = build_turn_fact_sheet(uuid4(), 'Qual é a regra?', guard)
    canonical = build_canonical(sheet, guard, brain_ids=('knowledge',))
    assert canonical.status == VerificationStatus.CONFLICTING
    assert len(canonical.sources) == 2
    assert canonical.status != VerificationStatus.VERIFIED
    assert 'divergent' in canonical.canonical_answer.casefold()


def test_missing_evidence_cannot_succeed_even_with_model_approval():
    assert not verdict_supported('{"supported":true,"quotes":[]}', evidence=(), answer='Você mora em Recife.')
    assert unlicensed_personal_strength('É seu único editor.', ('- uso o editor Helix',))


@pytest.mark.parametrize('text', ['not_a_verdict', '{"supported":true}', '{"supported":false,"quotes":[]}'])
def test_invalid_model_audits_do_not_authorize_claims(text):
    assert not verdict_supported(text, evidence=('- uso o editor Helix',), answer='Você usa Helix.')
