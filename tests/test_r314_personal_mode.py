"""R3.14 personal-only local UX: no PF6 prompts, legacy cases stay readable,
origin boundaries and original evidence integrity remain in place.
"""
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from campanario.app.security import LocalOnlyBoundary
from campanario.brains import casework_api as cases
from campanario.brains.casework import CaseWorkspace
from campanario.utilities import api as utility_api
from campanario.utilities.service import UtilityService


def setup(monkeypatch, tmp_path, personal=True):
    data = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    data.mkdir(parents=True)
    workspace = CaseWorkspace(data)
    util = UtilityService(data / 'utilidades')
    monkeypatch.setattr(cases, '_workspace', lambda: workspace)
    monkeypatch.setattr(utility_api, 'service', lambda: util)
    settings = SimpleNamespace(local_personal_mode=personal, brains_v9_enabled=True)
    monkeypatch.setattr('campanario.config.get_settings', lambda: settings)
    monkeypatch.setattr(cases, 'get_settings', lambda: settings)
    monkeypatch.setattr(utility_api, '_owner_enabled', lambda: True)
    monkeypatch.setattr(utility_api, '_identities', lambda: {'alice': 'opaque-test-verifier'})
    app = FastAPI()
    app.include_router(cases.router)
    app.include_router(utility_api.router)
    app.add_middleware(LocalOnlyBoundary)
    return TestClient(app), workspace, util


def test_old_pf6_cases_open_without_identity_and_new_case_is_personal(monkeypatch, tmp_path):
    client, workspace, _ = setup(monkeypatch, tmp_path)
    old = workspace.create('Legacy', 'Historic evidence', 'pf6-user:old')
    response = client.get('/api/v1/cases/mode')
    assert response.status_code == 200
    assert response.json() == {'solo_local': True, 'requires_pf6': False}
    assert old in {c['case_id'] for c in client.get('/api/v1/cases').json()['items']}
    assert client.get('/api/v1/cases/' + old).status_code == 200
    created = client.post('/api/v1/cases', json={'title': 'Pessoal', 'objective': 'Conferir originais'})
    assert created.status_code == 201, created.text
    assert workspace.read(created.json()['case_id'])['authorized_by'] == 'loopback-utilities'
    # Original ledger of old case is not silently changed.
    assert workspace.read(old)['authorized_by'] == 'pf6-user:old'


def test_personal_stream_case_import_without_login_and_hash_preserved(monkeypatch, tmp_path):
    client, workspace, _ = setup(monkeypatch, tmp_path)
    cid = workspace.create('Importação', 'Checagem', 'pf6-user:legacy')
    payload = b'evento,valor\n2026-01-01,123\n' * 32
    result = client.post('/api/v1/cases/' + cid + '/evidence', content=payload, headers={
        'Content-Type': 'application/octet-stream',
        'x-case-filename': 'dados.csv', 'x-case-origin': 'Operador',
    })
    assert result.status_code == 201, result.text
    assert workspace.verify(cid)['integrity_ok'] is True
    assert workspace.read(cid)['evidence'][0]['size'] == len(payload)


def test_personal_utilities_invoke_and_upload_ignore_old_pf6(monkeypatch, tmp_path):
    client, _, util = setup(monkeypatch, tmp_path)
    r = client.post('/api/v1/utilities/invoke', json={'tool': 'notes.save', 'arguments': {'title': 'Local'}})
    assert r.status_code == 200, r.text
    assert r.json()['status'] == 'success'
    uploaded = client.post('/api/v1/utilities/upload-stream?filename=prova.pdf', content=b'%PDF text',
                           headers={'Content-Type': 'application/octet-stream'})
    assert uploaded.status_code == 200, uploaded.text
    assert (util.roots[0] / 'prova.pdf').read_bytes() == b'%PDF text'
    catalog = client.get('/api/v1/utilities/catalog').json()
    assert not next(c for c in catalog if c['id'] == 'notes.save')['requires_confirmation']


def test_personal_still_blocks_cross_origin_and_overwrite(monkeypatch, tmp_path):
    client, workspace, util = setup(monkeypatch, tmp_path)
    headers = {'Content-Type': 'application/octet-stream'}
    uri = '/api/v1/utilities/upload-stream?filename=log.txt'
    assert client.post(uri, content=b'abc', headers={**headers, 'Origin': 'https://outside.example'}).status_code == 403
    assert client.post(uri, content=b'abc', headers=headers).status_code == 200
    assert client.post(uri, content=b'def', headers=headers).status_code == 409
    assert (util.roots[0] / 'log.txt').read_bytes() == b'abc'
    assert client.post('/api/v1/cases', json={'title': 'Fora', 'objective': 'Origem'},
                       headers={'Sec-Fetch-Site': 'cross-site'}).status_code == 403


def test_protected_mode_can_still_be_selected(monkeypatch, tmp_path):
    client, workspace, util = setup(monkeypatch, tmp_path, personal=False)
    assert client.get('/api/v1/cases/mode').status_code in (401, 403, 503)
    result = client.post('/api/v1/utilities/upload-stream?filename=blocked.pdf', content=b'abc',
                         headers={'Content-Type': 'application/octet-stream'})
    assert result.status_code in (401, 403, 503), result.text
    assert not (util.roots[0] / 'blocked.pdf').exists()
