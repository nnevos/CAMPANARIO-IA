"""V9.1: actual facts from test fixtures, with hostile providers and typed contracts."""
from __future__ import annotations

from uuid import uuid4
import pytest
from pydantic import ValidationError

from campanario.agents.profiles import MORGANA, TODD
from campanario.chat.canonical_answer import (
    AnswerMode, CanonicalAnswer, CanonicalFact, SourceRecord, ToolExecution,
    VerificationStatus, build_canonical, choose_mode,
)
from campanario.chat.fact_sheet import FactClaim, FactSource, TurnFactSheet
from campanario.chat.grounded_expression import (
    GroundedExpressionEngine, validate_expression,
)
from campanario.chat.data_intent import DataAnalysisResult
from campanario.chat.local_library import LibraryQuote, LocalFactSheet, ReadOnlyLocalLibrary
from campanario.chat.service import ChatService
from campanario.chat.context import RecentMessagesContextManager
from campanario.model.protocol import ModelChunk
from campanario.utilities.service import UtilityService
from test_chat_service import InMemoryMessages, InMemorySessions


def sheet_with(text: str, *, status='supported', sources=1):
    source_records = tuple(FactSource(f'library:real-{n}', 'imported_document',
                         f'Documento {n}.txt', f'Documento {n}.txt, página {n}', text)
                           for n in range(sources))
    claims = tuple(FactClaim(text, (s.id,)) for s in source_records)
    return TurnFactSheet(uuid4(), 'Qual é o benefício?', 'benefício', status, 'library',
                         source_records, claims, (), text if status == 'supported' else None)


def canonical(text: str) -> CanonicalAnswer:
    quote = LibraryQuote(document_id='real-0', name='Documento 0.txt',
                         sha256='a'*64, page=1, excerpt=text, score=8.0,
                         evidence_id='library:real-0')
    return build_canonical(sheet_with(text), LocalFactSheet(text, text, quote, read_count=1))


class ScriptedProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
        self.requests = []

    async def health(self): return True

    async def stream(self, request):
        self.requests.append(request)
        answer = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        yield ModelChunk(text=answer)
        yield ModelChunk(text='', done=True)


def test_contract_rejects_dangling_and_duplicate_evidence():
    with pytest.raises(ValidationError, match='missing source'):
        CanonicalAnswer(request_id=uuid4(), query='q', intent='lookup',
            mode='grounded', status='partially_verified',
            facts=(CanonicalFact(fact_id='a', statement='X', source_ids=('inventado',)),),
            canonical_answer='X')
    with pytest.raises(ValidationError, match="recorded successful source read"):
        CanonicalAnswer(request_id=uuid4(), query='q', intent='lookup',
            mode='grounded', status='verified', canonical_answer='X')
    with pytest.raises(ValidationError):
        CanonicalAnswer(request_id=uuid4(), query='q', intent='lookup',
            mode='grounded', status='verified',
            facts=(CanonicalFact(fact_id='a', statement='O valor 3', classification='source_assertion',
                                 source_ids=('file-1',)),),
            sources=(SourceRecord(source_id='file-1', kind='file',
                                  title='Real.txt', locator='Real.txt', excerpt='O valor 3'),),
            tool_executions=(ToolExecution(operation='library.retrieve', status='success',
                                           source_ids=('file-1',)),), canonical_answer='O valor 3')




def test_arbitrary_unexecuted_guard_cannot_fake_tool_success():
    record = build_canonical(sheet_with('A senha do cofre é 123.'), object())
    assert record.status == VerificationStatus.NOT_FOUND
    assert not record.facts and not record.tool_executions
    assert '123' not in record.canonical_answer


def test_numeric_fidelity_and_extra_number():
    record = canonical('O valor total é R$ 15.000.')
    assert record.status == VerificationStatus.PARTIALLY_VERIFIED
    assert validate_expression(record, 'O valor total é R$ 15.000.').accepted
    assert 'missing_critical_values' in validate_expression(record, 'O valor total é R$ 16.000.').violations
    assert 'invented_numeric_value' in validate_expression(record, 'O valor total é R$ 16.000.').violations


def test_conditions_cannot_be_removed_or_reversed():
    record = canonical('O benefício é concedido somente após aprovação.')
    assert validate_expression(record, 'O benefício é concedido somente após aprovação.').accepted
    assert 'missing_or_changed_condition' in validate_expression(record,
                  'O benefício é concedido sem aprovação.').violations
    assert 'missing_or_changed_condition' in validate_expression(record,
                  'O benefício é concedido após aprovação.').violations


def test_false_reference_must_be_runtime_constructed():
    record = canonical('O valor é 35.')
    assert 'reference_must_be_runtime_generated' in validate_expression(
        record, 'O valor é 35. Fonte: documento-falso.pdf, página 42.').violations


def test_new_causal_and_negation_claims_rejected():
    record = canonical('A venda foi 20.')
    assert not validate_expression(record, 'A venda foi 20 porque a loja fechou.').accepted
    assert 'new_negation' in validate_expression(record, 'A venda não foi 20.').violations


@pytest.mark.asyncio
async def test_same_facts_two_personalities_with_different_expression():
    record = canonical('O valor total é R$ 15.000.')
    morgana = ScriptedProvider(['Claro, o valor total é R$ 15.000.'])
    todd = ScriptedProvider(['O valor total é R$ 15.000.'])
    a = await GroundedExpressionEngine(morgana, model='local').express(record, MORGANA)
    b = await GroundedExpressionEngine(todd, model='local').express(record, TODD)
    assert a.accepted and b.accepted
    assert a.text != b.text
    assert 'R$ 15.000' in a.text and 'R$ 15.000' in b.text
    assert 'Morgana' in morgana.requests[0].messages[0].content
    assert 'Todd' in todd.requests[0].messages[0].content
    assert a.attempts[0].violations == ()


@pytest.mark.asyncio
async def test_extra_claim_then_fallback_after_two_failures():
    record = canonical('O valor total é R$ 15.000.')
    provider = ScriptedProvider(['O total é R$ 20.000 e a NASA pagou.', 'O total é R$ 18.000.'])
    outcome = await GroundedExpressionEngine(provider, model='local', max_retries=1).express(record, MORGANA)
    assert outcome.fallback_used and not outcome.accepted and provider.calls == 2
    assert outcome.text == record.canonical_answer
    assert 'NASA' not in outcome.text
    assert all(attempt.violations for attempt in outcome.attempts)


@pytest.mark.asyncio
async def test_contradictory_sources_never_promoted_to_verified():
    sheet = sheet_with('O selo é azul.', status='conflict', sources=2)
    a = LibraryQuote(document_id='real-0', name='Documento 0.txt', sha256='a'*64,
                     page=1, excerpt='O selo é azul.', score=7,
                     evidence_id='library:real-0')
    b = LibraryQuote(document_id='real-1', name='Documento 1.txt', sha256='b'*64,
                     page=2, excerpt='O selo é azul.', score=7,
                     evidence_id='library:real-1')
    record = build_canonical(sheet, LocalFactSheet('Selo', 'Selo', a,
                            status='ambiguous', conflicts=(b,), read_count=2))
    assert record.status == VerificationStatus.CONFLICTING
    assert len(record.contradictions) == 2
    provider = ScriptedProvider(['O selo é azul.'])
    outcome = await GroundedExpressionEngine(provider, model='local').express(record, TODD)
    assert not outcome.accepted and provider.calls == 0
    assert 'divergem' in outcome.text


@pytest.mark.asyncio
async def test_missing_document_cannot_mention_successful_search():
    sheet = TurnFactSheet(uuid4(), 'Procure o documento Teste.', 'Teste', 'insufficient', 'none')
    record = build_canonical(sheet, None)
    assert record.status == VerificationStatus.NOT_FOUND
    assert record.facts == () and record.tool_executions == ()
    provider = ScriptedProvider(['Encontrei o documento Teste.'])
    outcome = await GroundedExpressionEngine(provider, model='local').express(record, MORGANA)
    assert provider.calls == 0 and 'Não encontrei' in outcome.text


def test_computed_values_verified_only_with_real_execution():
    result = DataAnalysisResult('Calcule faturamento', 'grounded', 'Total: 300.50.',
         'vendas.csv', 'uuid-real', 'digest-real', 'sum', 'Total: 300.50.', read_count=1)
    from campanario.chat.fact_sheet import build_turn_fact_sheet
    sheet = build_turn_fact_sheet(uuid4(), 'Calcule faturamento', result)
    record = build_canonical(sheet, result)
    assert record.status == VerificationStatus.VERIFIED
    assert record.tool_executions[0].operation == 'data.sum'
    assert not validate_expression(record, 'Total: 301.50.').accepted
    assert validate_expression(record, 'Total: 300.50.').accepted


def test_mode_router_keeps_no_tools_for_chat_and_hybrid_for_analysis():
    sheet = TurnFactSheet(uuid4(), 'Olá!', 'Olá!', 'not_required', 'none')
    assert choose_mode('Olá!', sheet) == AnswerMode.CONVERSATIONAL
    assert choose_mode('Modo fundamentado: olá', sheet) == AnswerMode.GROUNDED
    assert choose_mode('Analise estes dados', sheet) == AnswerMode.HYBRID
    assert choose_mode('Modo híbrido: olá', sheet) == AnswerMode.HYBRID


@pytest.mark.asyncio
async def test_real_import_document_three_turns_provenance_and_debug(tmp_path):
    util = UtilityService(tmp_path / 'utility')
    path = util.roots[0] / 'Ordem Paranormal Exemplo.md'
    path.write_text('# Progressão\n\n## Ocultista 20% NEX\n\nO Ocultista recebe a Marca Exemplo Q7.', encoding='utf8')
    imported = util.run('library.import', {'path': str(path), 'confirm': True})
    assert imported['status'] == 'success'
    provider = ScriptedProvider(['O Ocultista recebe a Marca Errada.'])
    chat = ChatService(InMemorySessions(), InMemoryMessages(), provider,
                       RecentMessagesContextManager(12), 'local',
                       local_library=ReadOnlyLocalLibrary(util.db), low_latency_mode=True)
    session = chat.create_session()
    prompts = ['O que Ocultista ganha em 20% de NEX?',
               'No Database existe um documento de Ordem Paranormal com essas informações.',
               'Então o que Ocultista ganha em 20% de NEX?']
    outputs = []
    for prompt in prompts:
        events = [e async for e in chat.stream_turn(session.id, prompt)]
        outputs.append(''.join(e.text for e in events if e.type == 'token'))
    assert 'Marca Exemplo Q7' in outputs[-1]
    assert 'Marca Errada' not in outputs[-1]
    assert 'Fonte:' in outputs[-1]
    trace = chat.get_factual_debug(session.id)
    assert trace['status'] == 'partially_verified'
    assert trace['sources'][0]['document_id'] == imported['result']['id']
    assert trace['sources'][0]['section'] == 'Ocultista 20% NEX'
    assert trace['tools_executed'][0]['status'] == 'success'
    assert trace['agents']['morgana']['validation'] == 'fallback'
    assert 'brain' not in trace['tools_executed'][0]['operation']


def test_sum_returns_decimal_from_imported_csv_and_missing_values_fail(tmp_path):
    util = UtilityService(tmp_path / 'utility')
    csv_path = util.roots[0] / 'faturamento.csv'
    csv_path.write_text('produto,faturamento\nLivro,100.10\nJogo,200.20\n', encoding='utf8')
    doc = util.run('library.import', {'path': str(csv_path), 'confirm': True})['result']
    outcome = util.run('data.analyze', {'document_id': doc['id'],
                                        'operation': 'sum', 'column': 'faturamento'})['result']
    assert outcome['status'] == 'computed' and outcome['result'][0]['sum'] == '300.30'
    from campanario.chat.data_intent import run_data_question
    parsed = run_data_question(util.db, 'Analise o faturamento total da planilha')
    assert parsed.status == 'grounded' and '300.30' in parsed.verified_answer
    missing_path = util.roots[0] / 'incompleto.csv'
    missing_path.write_text('produto,faturamento\nLivro,100.10\nJogo,\n', encoding='utf8')
    doc2 = util.run('library.import', {'path': str(missing_path), 'confirm': True})['result']
    failure = util.run('data.analyze', {'document_id': doc2['id'],
                                        'operation': 'sum', 'column': 'faturamento'})['result']
    assert failure['status'] == 'insufficient_data'


def test_debug_api_is_local_and_does_not_expose_nonexistent_sources(monkeypatch):
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    import campanario.api as api
    from campanario.main import app
    service = ChatService(InMemorySessions(), InMemoryMessages(),
                          ScriptedProvider(['Olá.']),
                          RecentMessagesContextManager(10), 'local')
    session = service.create_session()
    monkeypatch.setattr(api, 'get_runtime', lambda: SimpleNamespace(conversation=service))
    client = TestClient(app)
    reply = client.get(f'/api/v1/sessions/{session.id}/grounding-debug')
    assert reply.status_code == 200
    assert reply.json() == {'available': False, 'trace': None}
    assert client.get(f'/api/v1/sessions/{uuid4()}/grounding-debug').status_code == 404
    # Simulates a remote client reaching the same endpoint, without access.
    from starlette.requests import Request
    from fastapi import HTTPException
    scope = {'type': 'http', 'method': 'GET', 'path': '/', 'headers': [],
             'client': ('192.0.2.30', 40000), 'server': ('localhost', 8000),
             'scheme': 'http'}
    with pytest.raises(HTTPException) as denied:
        api._local_admin(Request(scope))
    assert denied.value.status_code == 403
