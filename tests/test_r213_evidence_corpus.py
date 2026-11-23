"""R2.13 offline regression corpus for answerability and conflicts.

Synthetic examples (no personal data). Necessary lexical evidence is not
logical entailment or external truth. Expected labels are reviewed by humans.
"""
from uuid import uuid4

import pytest

from campanario.chat.evidence_gate import assess_explicit_answer
from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.canonical_answer import build_canonical, VerificationStatus
from campanario.chat.local_library import LibraryQuote, LocalFactSheet


@pytest.mark.parametrize('question,excerpt,expected', [
    ('Qual é a cor do selo?', 'A cor do selo é azul.', True),
    ('Qual é a cor do selo?', 'A cor do crachá é azul.', False),
    ('Qual é a cor do uniforme?', 'A cor da etiqueta é verde.', False),
    ('Qual é a senha do arquivo?', 'O arquivo contém o resumo anual.', False),
    ('Qual é a senha do arquivo?', 'A senha do arquivo é um segredo.', True),
    ('Qual é o nome do projeto?', 'O nome do projeto é Horizonte.', True),
    ('Qual é o nome do projeto?', 'O projeto começou ontem.', False),
    ('Qual é o dia do evento?', 'O evento ocorrerá segunda-feira.', True),
    ('Qual é o dia do evento?', 'O evento mudou de local.', False),
    ('Qual é a cor do selo?', '', False),
    ('Qual é a cor do selo?', 'O selo foi emitido.', False),
    ('Qual é a data do contrato?', 'O contrato tem duas assinaturas.', False),
    ('Qual é o prazo do contrato?', 'O prazo do contrato é de cinco dias.', True),
    ('Qual é o prazo do contrato?', 'O valor do contrato é R$ 50.', False),
    ('Qual é a cor da bandeira?', 'A bandeira foi hasteada.', False),
    ('Qual é a cor da bandeira?', 'A cor da bandeira é azul.', True),
    ('Qual é o nome do livro?', 'O nome do livro é Aurora.', True),
    ('Qual é o nome do livro?', 'O livro possui dez páginas.', False),
    ('Qual é o dia da reunião?', 'A reunião será terça-feira.', True),
    ('Qual é o dia da reunião?', 'A reunião foi cancelada.', False),
])
def test_r213_literal_attribute_corpus(question, excerpt, expected):
    assert assess_explicit_answer(question, 'documento', excerpt).sufficient is expected


def _quote(doc_id, excerpt):
    return LibraryQuote(doc_id, doc_id + '.txt', ('a' if doc_id == 'A' else 'b') * 64,
                        1, excerpt, 7.0, evidence_id='library:' + doc_id)


@pytest.mark.parametrize('left,right,expected_status', [
    ('O prazo é cinco dias.', 'O prazo é sete dias.', VerificationStatus.CONFLICTING),
    ('O selo é azul.', 'O selo é verde.', VerificationStatus.CONFLICTING),
    ('A regra exige autorização.', 'A regra dispensa autorização.', VerificationStatus.CONFLICTING),
    ('A data é segunda-feira.', 'A data é quarta-feira.', VerificationStatus.CONFLICTING),
    ('O limite é 20%.', 'O limite é 90%.', VerificationStatus.CONFLICTING),
])
def test_r213_declared_conflicts_never_verify(left, right, expected_status):
    # Conflict classification is supplied by retrieval (not inferred from text).
    guard = LocalFactSheet('regra', 'Qual é a regra?', _quote('A', left),
                           status='ambiguous', conflicts=(_quote('B', right),))
    sheet = build_turn_fact_sheet(uuid4(), guard.query, guard)
    result = build_canonical(sheet, guard, brain_ids=('knowledge',))
    assert result.status == expected_status
    assert len(result.sources) == 2
    assert result.status != VerificationStatus.VERIFIED


def test_r213_no_document_evidence_stays_unverified():
    sheet = build_turn_fact_sheet(uuid4(), 'Qual é a senha?', None, fact_lookup_requested=True)
    canonical = build_canonical(sheet, None, brain_ids=('knowledge',))
    assert canonical.status == VerificationStatus.NOT_FOUND
    assert not canonical.facts


def test_r213_valid_source_ids_do_not_justify_changed_number():
    from dataclasses import replace
    from campanario.chat.fact_sheet import FactClaim
    guard = LocalFactSheet('limite', 'Qual é o limite?', _quote('A', 'O limite é 20%.'))
    sheet = build_turn_fact_sheet(uuid4(), guard.query, guard)
    forged = replace(sheet, claims=(FactClaim('O limite é 99%.', (sheet.sources[0].id,)),))
    canonical = build_canonical(forged, guard, brain_ids=('knowledge',))
    assert canonical.status == VerificationStatus.NOT_FOUND
    assert not canonical.facts
