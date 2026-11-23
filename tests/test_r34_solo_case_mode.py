"""R3.4: user-only local case mode works without V9/PF6 and still denies remote requests."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from campanario.brains import casework_api as api
from campanario.brains.casework import CaseWorkspace
from campanario.app.security import LocalOnlyBoundary


@pytest.fixture
def client(tmp_path, monkeypatch):
    data = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    data.mkdir(parents=True)
    monkeypatch.setattr(api, '_workspace', lambda: CaseWorkspace(data))
    monkeypatch.delenv('CAMPANARIO_PF6_USERS_JSON', raising=False)
    monkeypatch.delenv('CAMPANARIO_PF6_OWNER_TOKEN', raising=False)
    from campanario.utilities import api as utilities_api
    monkeypatch.setattr(utilities_api, '_identities', lambda: {})
    monkeypatch.setattr(utilities_api, '_owner_enabled', lambda: False)
    app = FastAPI()
    app.include_router(api.router)
    app.add_middleware(LocalOnlyBoundary)
    return TestClient(app)


def test_solo_local_without_credentials_or_v9(client):
    assert client.get('/api/v1/cases/mode').json() == {'solo_local': True, 'requires_pf6': False}
    r = client.post('/api/v1/cases', json={'title': 'Teste local', 'objective': 'Investigar logs'})
    assert r.status_code == 201, r.text
    case_id = r.json()['case_id']
    assert client.get('/api/v1/cases').json()['items'][0]['case_id'] == case_id
    q = client.post(f'/api/v1/cases/{case_id}/ask', json={'question': 'resumo', 'agent_id': 'todd'})
    assert q.status_code == 200, q.text
    assert q.json()['status'] in {'reported_only', 'limited'}


def test_solo_rejects_cross_site_and_nonlocal(client):
    assert client.post('/api/v1/cases', json={'title':'A','objective':'B'}, headers={
        'Origin': 'https://attacker.example',
    }).status_code == 403
    assert client.post('/api/v1/cases', json={'title':'A','objective':'B'}, headers={
        'Sec-Fetch-Site': 'cross-site',
    }).status_code == 403
    assert client.get('/api/v1/cases', headers={'X-Forwarded-For': '198.51.100.7'}).status_code == 403


def test_solo_does_not_grant_pf6_session_or_cross_case_user(client, monkeypatch):
    r = client.post('/api/v1/cases', json={'title':'Local','objective':'Rastreamento'})
    case_id = r.json()['case_id']
    assert client.post('/api/v1/cases/approve', json={
        'confirmation_id':'00000000-0000-4000-8000-000000000001'
    }).status_code == 409
    monkeypatch.setattr(api, '_solo_mode', lambda: False)
    from fastapi import HTTPException
    def denied(request):
        raise HTTPException(401, 'Sessão PF6 necessária')
    monkeypatch.setattr(api, '_owner_session', denied)
    assert client.get(f'/api/v1/cases/{case_id}').status_code == 401
