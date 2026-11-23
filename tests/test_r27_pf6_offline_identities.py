"""R2.7: optional offline identities, audit principal and fail-closed config."""
import json
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
import pytest

import campanario.utilities.api as api
from campanario.main import app
from campanario.runtime.permissions import PermissionMode, PermissionPolicy
from campanario.utilities.pf6_identities import password_verifier, load_identities
from campanario.utilities.pf6_sessions import owner_sessions
from campanario.utilities.service import UtilityService


@pytest.fixture
def setup(monkeypatch, tmp_path):
    owner_sessions.reset()
    monkeypatch.setattr('campanario.config.get_settings', lambda: SimpleNamespace(brains_v9_enabled=True))
    monkeypatch.setattr(api, 'service', lambda: UtilityService(tmp_path / 'utilities'))
    repo, trust = Mock(), Mock()
    trust._repository = repo
    trust._devices = Mock()
    policy = PermissionPolicy(trust, repo)
    policy.set_rule('utilities.write', PermissionMode.SCOPED_CONFIRM)
    policy.set_rule('utilities.read', PermissionMode.ALLOW)
    monkeypatch.setattr('campanario.bootstrap.get_runtime', lambda: SimpleNamespace(permissions=policy))
    records = {'alice': password_verifier('correct horse battery staple'),
               'bob': password_verifier('another secure offline passphrase')}
    monkeypatch.setenv('CAMPANARIO_PF6_USERS_JSON', json.dumps(records))
    # R2.8: existing R2.7 consent test explicitly grants the tool under test.
    monkeypatch.setenv('CAMPANARIO_PF6_WRITE_ACL_JSON', json.dumps({'alice':['notes.save'], 'bob':['notes.save']}))
    monkeypatch.setenv('CAMPANARIO_PF6_OWNER_TOKEN', 'Z' * 48)
    yield TestClient(app), records, repo, monkeypatch
    owner_sessions.reset()


def login(client, username, password):
    return client.post('/api/v1/utilities/sessions/login', json={'username': username, 'credential': password})


def test_validation_and_no_default_credentials():
    with pytest.raises(ValueError):
        load_identities('{')
    with pytest.raises(ValueError):
        load_identities(json.dumps({'bad name': 'x'}))
    with pytest.raises(ValueError):
        load_identities('{}')
    assert load_identities('') == {}


def test_individual_login_and_legacy_bypass_blocked(setup):
    client, _, _, _ = setup
    assert login(client, 'alice', 'correct horse battery staple').status_code == 200
    assert login(client, 'bob', 'another secure offline passphrase').status_code == 200
    assert login(client, 'alice', 'another secure offline passphrase').status_code == 401
    assert client.post('/api/v1/utilities/sessions/login', json={'credential': 'Z'*48}).status_code == 401


def test_principal_audit_and_session_binding(setup):
    client, _, repo, _ = setup
    a = login(client, 'alice', 'correct horse battery staple').json()
    b = login(client, 'bob', 'another secure offline passphrase').json()
    assert a['principal_id'] == 'pf6-user:alice'
    assert b['principal_id'] == 'pf6-user:bob'
    ah = {'Authorization': 'Bearer ' + a['session_token']}
    bh = {'Authorization': 'Bearer ' + b['session_token']}
    op = {'tool':'notes.save','arguments':{'title':'audit', 'confirm':True}}
    pending = client.post('/api/v1/utilities/confirmations/request', json=op, headers=ah).json()
    consent = {'confirmation_id':pending['confirmation_id'], **op, 'acknowledged':True}
    assert client.post('/api/v1/utilities/confirmations/approve', json=consent, headers=bh).status_code == 403
    approval = client.post('/api/v1/utilities/confirmations/approve', json=consent, headers=ah)
    assert approval.status_code == 200, approval.text
    token = approval.json()['confirmation_token']
    assert client.post('/api/v1/utilities/invoke', json={**op, 'confirmation_token':token}, headers=bh).status_code == 403
    assert client.post('/api/v1/utilities/invoke', json={**op, 'confirmation_token':token}, headers=ah).status_code == 200
    audits = repo.append_audit.call_args_list
    assert any(c.kwargs.get('principal_id') == 'pf6-user:alice' for c in audits)
    assert token not in repr(audits)
    assert a['session_token'] not in repr(audits)


def test_rotation_and_invalid_config_fail_closed(setup):
    client, records, _, monkeypatch = setup
    result = login(client, 'alice', 'correct horse battery staple').json()
    h = {'Authorization':'Bearer '+result['session_token']}
    assert client.post('/api/v1/utilities/sessions/logout', headers=h).status_code == 200
    result = login(client, 'alice', 'correct horse battery staple').json()
    h = {'Authorization':'Bearer '+result['session_token']}
    monkeypatch.setenv('CAMPANARIO_PF6_USERS_JSON',json.dumps({'bob':records['bob']}))
    assert client.post('/api/v1/utilities/sessions/logout', headers=h).status_code == 401
    monkeypatch.setenv('CAMPANARIO_PF6_USERS_JSON','broken json')
    assert client.post('/api/v1/utilities/sessions/login', json={'credential':'Z'*48}).status_code == 503
    assert client.post('/api/v1/utilities/confirmations/request',json={'tool':'notes.save'}, headers=h).status_code == 503


def test_ui_username_is_plain_text_and_credentials_not_persisted():
    from pathlib import Path
    web = Path(__file__).resolve().parents[1] / 'src/campanario/web'
    html = (web / 'ferramentas.html').read_text(encoding='utf-8')
    js = (web / 'ferramentas.js').read_text(encoding='utf-8')
    assert 'id="pf6-username"' in html
    assert 'username.value.trim()' in js
    assert "details.textContent=login?'':" in js
    assert 'localStorage.setItem' not in js
    assert 'sessionStorage.setItem' not in js
