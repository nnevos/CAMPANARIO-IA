"""R3.4 contractual tests: case dialogue is scoped, extrative and read-only."""
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from campanario.brains.casework import CaseWorkspace
from campanario.brains.casework_dialogue import prepare_case_answer
from campanario.brains import casework_api as api


@pytest.fixture
def case(tmp_path):
    data = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    data.mkdir(parents=True)
    ws = CaseWorkspace(data)
    cid = ws.create('Operação fictícia', 'Revisar registros', 'pf6-user:alice')
    source = tmp_path / 'log.csv'
    source.write_text('timestamp,action\n2026-11-23T18:42:00-03:00,Computador desligado\n', encoding='utf-8')
    item = ws.add_evidence(cid, source, 'exportação autorizada', 'pf6-user:alice')
    ws.add_event(cid, '2026-11-23T18:42:00-03:00', 'Computador desligado', [item['id']])
    ws.add_hypothesis(cid, 'Falha técnica', [item['id']], [], 'Conferir registro original')
    return ws, cid, item


@pytest.mark.parametrize('prompt,intent', [
    ('Qual a cronologia?', 'timeline'),
    ('Quais as hipóteses?', 'hypotheses'),
    ('Qual o próximo passo?', 'strategy'),
    ('Quais evidências temos?', 'evidence'),
    ('Resumo do caso', 'overview'),
])
def test_factual_case_queries(case, prompt, intent):
    ws, cid, item = case
    result = prepare_case_answer(ws, cid, prompt, 'todd')
    assert result['intent'] == intent
    assert result['status'] == 'reported_only'
    assert result['source'] == 'casework_verified_ledger'
    assert 'no_llm_generated_facts' in result['limitations']
    if intent in ('evidence', 'timeline', 'hypotheses', 'overview'):
        assert item['id'] in result['evidence_ids']
    assert 'culpado' not in result['answer'].lower()


def test_chat_personality_does_not_change_evidence(case):
    ws, cid, item = case
    morgana = prepare_case_answer(ws, cid, 'hipóteses', 'morgana')
    todd = prepare_case_answer(ws, cid, 'hipóteses', 'todd')
    assert morgana['evidence_ids'] == todd['evidence_ids'] == [item['id']]
    assert morgana['answer'].splitlines()[1:] == todd['answer'].splitlines()[1:]
    assert morgana['answer'].splitlines()[0] != todd['answer'].splitlines()[0]


def test_tampered_file_blocks_factual_answer(case):
    ws, cid, item = case
    file = ws._dir(cid) / 'originals' / item['stored_as']
    file.write_text('alterado', encoding='utf-8')
    response = prepare_case_answer(ws, cid, 'cronologia')
    assert response['status'] == 'limited'
    assert response['evidence_ids'] == []
    assert 'integridade' in response['answer'].lower()
    assert 'Computador desligado' not in response['answer']


def test_no_evidence_does_not_invent(case):
    ws, cid, item = case
    empty = ws.create('Caso sem provas', 'Investigar', 'pf6-user:alice')
    result = prepare_case_answer(ws, empty, 'cronologia')
    assert 'Não há eventos' in result['answer']
    assert result['evidence_ids'] == []


def test_no_writes_or_llm_calls(case, monkeypatch):
    ws, cid, item = case
    before = (ws._dir(cid) / 'case.json').read_bytes()
    prepare_case_answer(ws, cid, 'Qual a próxima verificação?')
    assert (ws._dir(cid) / 'case.json').read_bytes() == before


def test_invalid_inputs(case):
    ws, cid, item = case
    for question in ('', ' ' * 4, 'x' * 601):
        with pytest.raises(ValueError):
            prepare_case_answer(ws, cid, question)
    with pytest.raises(ValueError):
        prepare_case_answer(ws, cid, 'resumo', 'admin')


def test_owner_protected_api(case, monkeypatch):
    # Explicit protected-mode regression; personal mode is covered separately.
    monkeypatch.setattr(api, '_solo_mode', lambda: False)
    ws, cid, item = case
    principal = {'value': 'pf6-user:bob'}
    monkeypatch.setattr(api, '_workspace', lambda: ws)
    monkeypatch.setattr(api, '_session', lambda r: SimpleNamespace(principal_id=principal['value'], session_id=uuid4()))
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)
    path = f'/api/v1/cases/{cid}/ask'
    payload = {'question': 'cronologia', 'agent_id': 'morgana'}
    assert client.post(path, json=payload).status_code == 404
    principal['value'] = 'pf6-user:alice'
    r = client.post(path, json=payload)
    assert r.status_code == 200, r.text
    assert item['id'] in r.json()['evidence_ids']
    assert client.post(path, json={'question':'hi','agent_id':'unauthorized'}).status_code == 422


def test_native_chat_bridge_not_external_app():
    root = Path(__file__).resolve().parents[1] / 'src/campanario/web/static'
    cases_js = (root / 'cases.js').read_text(encoding='utf-8')
    chat_js = (root / 'chat.js').read_text(encoding='utf-8')
    assert 'window.CampanarioCases={mount,tryChat}' in cases_js
    assert 'window.CampanarioCases?.tryChat(text)' in chat_js
    assert 'renderConversationText' in chat_js
