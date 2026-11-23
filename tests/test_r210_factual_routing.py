"""R2.10: conversational routing and first-party source-claim integrity."""
from dataclasses import replace
from uuid import uuid4

import pytest

from campanario.chat.canonical_answer import build_canonical, VerificationStatus
from campanario.chat.evidence_gate import is_subjective_turn
from campanario.chat.fact_sheet import FactClaim, build_turn_fact_sheet
from campanario.chat.local_library import LibraryQuote, LocalFactSheet
from test_chamada_de_agente_sem_pesquisa import _service


@pytest.mark.parametrize('question', [
    'O que você acha de uma história de detetive?',
    'Morgana, qual sua opinião sobre um final aberto?',
    'Todd, você prefere histórias curtas ou longas?',
])
def test_subjective_questions_skip_mandatory_fact_search(question):
    assert is_subjective_turn(question)


@pytest.mark.parametrize('question', [
    'Todd, quem foi Ada Lovelace?',
    'Você acha que João venceu em 2026?',
    'Qual a sua opinião sobre o preço hoje?',
    'Qual é a senha do documento?',
])
def test_objective_questions_still_need_evidence(question):
    assert not is_subjective_turn(question)


@pytest.mark.asyncio
@pytest.mark.parametrize('web', [False, True])
async def test_subjective_chat_is_not_search_error(tmp_path, web):
    chat, provider, library = _service(tmp_path, web=web)
    session = chat.create_session()
    events = [ev async for ev in chat.stream_turn(
        session.id, 'Morgana, o que você acha de uma história de detetive?')]
    answer = ''.join(ev.text for ev in events if ev.type == 'token')
    assert answer == 'Oi, estou aqui. Pode falar!'
    assert provider.calls == 1
    assert library.calls == 0
    assert 'desativad' not in answer.casefold()


@pytest.mark.asyncio
async def test_unknown_identity_without_web_does_not_claim_research(tmp_path):
    chat, provider, library = _service(tmp_path, web=False)
    session = chat.create_session()
    events = [ev async for ev in chat.stream_turn(session.id, 'Xandrel?')]
    answer = ''.join(ev.text for ev in events if ev.type == 'token')
    assert 'não consegui confirmar' in answer.casefold()
    assert 'desativad' not in answer.casefold()
    assert provider.calls == 0
    assert library.calls == 1


def _sheet():
    quote = LibraryQuote('doc1', 'regras.md', 'sha123', 1,
                         'A regra exige autorização prévia de 20%.', 7.0)
    guard = LocalFactSheet('regras', 'Qual é a regra?', quote)
    return build_turn_fact_sheet(uuid4(), 'Qual é a regra?', guard), guard


def test_brain_fact_requires_literal_statement_in_its_cited_excerpt():
    sheet, guard = _sheet()
    real = build_canonical(sheet, guard, brain_ids=('knowledge',))
    assert real.status == VerificationStatus.PARTIALLY_VERIFIED
    altered = replace(sheet, claims=(FactClaim('A regra permite 99% sem autorização.',
                                               sheet.claims[0].source_ids),))
    result = build_canonical(altered, guard, brain_ids=('knowledge',))
    assert result.status == VerificationStatus.NOT_FOUND
    assert not result.facts
    assert '99%' not in result.canonical_answer


def test_source_ids_alone_do_not_validate_claim():
    sheet, guard = _sheet()
    ungrounded = replace(sheet, claims=(FactClaim('O documento não menciona esse fato.',
                                                 sheet.claims[0].source_ids),))
    result = build_canonical(ungrounded, guard, brain_ids=('knowledge',))
    assert result.status == VerificationStatus.NOT_FOUND
