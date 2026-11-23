"""R3.3: native cases UI/backend, no separate app and no implicit grants."""
from __future__ import annotations
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from campanario.brains.casework import CaseWorkspace
from campanario.brains import casework_api as api
from campanario.runtime.permissions import PermissionPolicy


@pytest.fixture
def setup(tmp_path, monkeypatch):
    data = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    data.mkdir(parents=True)
    workspace = CaseWorkspace(data)
    monkeypatch.setattr(api, '_workspace', lambda: workspace)
    # These historical tests explicitly cover multi-identity PF6, not the
    # R3.14 default personal mode.
    monkeypatch.setattr(api, 'get_settings', lambda: SimpleNamespace(local_personal_mode=False))
    monkeypatch.setattr(api, '_solo_mode', lambda: False)
    principal = {'id': 'pf6-owner'}
    sid = uuid4()
    monkeypatch.setattr(api, '_session', lambda request: SimpleNamespace(principal_id=principal['id'], session_id=sid))
    monkeypatch.setattr(api, '_write_acl', lambda session: None)
    repository = Mock()
    policy = PermissionPolicy(Mock(), repository)
    from campanario import bootstrap
    monkeypatch.setattr(bootstrap, 'get_runtime', lambda: SimpleNamespace(permissions=policy))
    app = FastAPI()
    app.include_router(api.router)
    return TestClient(app), principal, workspace, policy


def submit(client, path, payload, *, content_type='application/json', headers=None):
    if content_type == 'application/json':
        import json
        content = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    else:
        content = payload
    request_headers = {'Content-Type': content_type, **(headers or {})}
    refused = client.post(path, content=content, headers=request_headers)
    assert refused.status_code == 428, refused.text
    confirmation_id = refused.json()['detail']['confirmation_id']
    approved = client.post('/api/v1/cases/approve', json={'confirmation_id': confirmation_id})
    assert approved.status_code == 200, approved.text
    token = approved.json()['confirmation_token']
    actual = client.post(path, content=content, headers={**request_headers, 'x-case-confirmation': token})
    return actual, token


def test_case_is_native_and_requires_explicit_consent(setup):
    client, _, workspace, _ = setup
    base = '/api/v1/cases'
    assert client.get(base).json() == {'items': []}
    result, token = submit(client, base, {'title': 'Operação fictícia', 'objective': 'Conferir logs'})
    assert result.status_code == 201, result.text
    cid = result.json()['case_id']
    assert client.get(base).json()['items'][0]['case_id'] == cid
    assert client.get(base+'/'+cid).status_code == 200
    # The approval token cannot create another case or repeat the same action.
    replay = client.post(base, json={'title': 'Operação fictícia', 'objective': 'Conferir logs'},
                         headers={'x-case-confirmation': token})
    assert replay.status_code == 428
    assert len(client.get(base).json()['items']) == 1
    assert workspace.read(cid)['authorized_by'] == 'pf6-owner'


def test_individual_identity_isolation(setup):
    client, principal, workspace, _ = setup
    cid = workspace.create('Caso de Alice', 'Analisar dados', 'pf6-user:alice')
    principal['id'] = 'pf6-user:bob'
    assert client.get('/api/v1/cases').json()['items'] == []
    for suffix in ['', '/review', '/dossier', '/integrity']:
        response = client.get('/api/v1/cases/'+cid+suffix)
        assert response.status_code == 404, response.text
    assert client.post('/api/v1/cases/'+cid+'/events', json={
        'date_time': '2026-11-23T18:00:00-03:00', 'description': 'Evento', 'evidence_ids': ['E123']
    }).status_code == 404
    principal['id'] = 'pf6-user:alice'
    assert client.get('/api/v1/cases/'+cid).status_code == 200


def test_upload_and_report_inside_api(setup):
    client, _, workspace, _ = setup
    cid = workspace.create('Caso', 'Checar eventos', 'pf6-owner')
    payload = b'timestamp,action\n2026-11-23T18:42:00-03:00,PC desligado\n'
    path = f'/api/v1/cases/{cid}/evidence'
    headers = {'x-case-filename': 'access.csv', 'x-case-origin': 'Exporta%C3%A7%C3%A3o%20autorizada'}
    response, _ = submit(client, path, payload, content_type='application/octet-stream', headers=headers)
    assert response.status_code == 201, response.text
    entry = response.json()
    proposals = client.get(f'{path}/{entry["id"]}/proposed-events')
    assert proposals.status_code == 200
    assert len(proposals.json()['items']) == 1
    report = client.get(f'/api/v1/cases/{cid}/dossier')
    assert entry['sha256'] in report.json()['markdown']
    assert client.get(f'/api/v1/cases/{cid}/integrity').json()['integrity_ok'] is True


def test_binds_approval_to_body_and_operation(setup):
    client, _, workspace, _ = setup
    base = '/api/v1/cases'
    content = b'{"title":"A","objective":"B"}'
    first = client.post(base, content=content, headers={'Content-Type':'application/json'})
    ident = first.json()['detail']['confirmation_id']
    token = client.post(base+'/approve', json={'confirmation_id': ident}).json()['confirmation_token']
    wrong = client.post(base, json={'title':'A','objective':'C'}, headers={'x-case-confirmation':token})
    assert wrong.status_code == 428
    assert client.get(base).json()['items'] == []
    correct = client.post(base, content=content, headers={'Content-Type':'application/json','x-case-confirmation':token})
    assert correct.status_code == 201


def test_client_paths_not_read_or_extracted(setup):
    client, _, workspace, _ = setup
    cid = workspace.create('Caso', 'Fonte', 'pf6-owner')
    base = f'/api/v1/cases/{cid}/evidence'
    for name in ('..%2Fprivate.txt','C%3A%5Csecret.txt','CON.txt','a%0Ab.txt'):
        response = client.post(base, content=b'secret', headers={'x-case-filename':name,'x-case-origin':'teste'})
        assert response.status_code == 422
    assert workspace.read(cid)['evidence'] == []


def test_view_and_script_are_embedded_not_navigation(tmp_path):
    from pathlib import Path
    src = Path(__file__).resolve().parents[1] / 'src/campanario/web'
    ws = (src/'static/workspaces.js').read_text(encoding='utf-8')
    html = (src/'index.html').read_text(encoding='utf-8')
    assert "['casos','⌕','Casos']" in ws
    assert 'CampanarioCases?.mount' in ws
    assert '/static/cases.js' in html
    assert 'location.href' not in (src/'static/cases.js').read_text(encoding='utf-8')


def test_named_user_write_acl_denies_by_default(monkeypatch):
    from campanario.config import Settings
    monkeypatch.delenv('CAMPANARIO_CASEWORK_WRITE_ACL_JSON', raising=False)
    monkeypatch.setattr(api, 'get_settings', lambda: SimpleNamespace(casework_write_acl_json=''))
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as denied:
        api._write_acl(SimpleNamespace(principal_id='pf6-user:alice'))
    assert denied.value.status_code == 403
    monkeypatch.setattr(api, 'get_settings', lambda: SimpleNamespace(casework_write_acl_json='{"alice":["casework"]}'))
    api._write_acl(SimpleNamespace(principal_id='pf6-user:alice'))
    with pytest.raises(HTTPException):
        api._write_acl(SimpleNamespace(principal_id='pf6-user:bob'))


def test_approval_cannot_cross_sessions(setup, monkeypatch):
    client, _, workspace, policy = setup
    from campanario import bootstrap
    session = {'id': uuid4()}
    monkeypatch.setattr(api, '_session', lambda request: SimpleNamespace(principal_id='pf6-owner', session_id=session['id']))
    first = client.post('/api/v1/cases', json={'title':'A','objective':'B'})
    assert first.status_code == 428
    confirmation_id = first.json()['detail']['confirmation_id']
    session['id'] = uuid4()
    assert client.post('/api/v1/cases/approve', json={'confirmation_id':confirmation_id}).status_code == 404
    assert client.get('/api/v1/cases').json() == {'items': []}
