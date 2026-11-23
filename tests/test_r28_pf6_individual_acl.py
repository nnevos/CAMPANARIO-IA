"""R2.8: deny-only individual PF6 write-tool permissions."""
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import campanario.utilities.api as api
from campanario.main import app
from campanario.runtime.permissions import PermissionMode, PermissionPolicy
from campanario.utilities.pf6_acl import can_write, load_write_acl
from campanario.utilities.pf6_identities import password_verifier
from campanario.utilities.pf6_sessions import owner_sessions
from campanario.utilities.service import UtilityService, WRITE


@pytest.fixture
def pf6(monkeypatch, tmp_path):
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
    monkeypatch.setenv('CAMPANARIO_PF6_USERS_JSON', json.dumps({
        'alice': password_verifier('correct horse battery staple'),
        'bob': password_verifier('another secure offline passphrase')}))
    monkeypatch.setenv('CAMPANARIO_PF6_OWNER_TOKEN', 'Z'*48)
    monkeypatch.delenv('CAMPANARIO_PF6_WRITE_ACL_JSON', raising=False)
    client = TestClient(app)
    def headers(name, password):
        login = client.post('/api/v1/utilities/sessions/login', json={'username': name, 'credential': password})
        assert login.status_code == 200
        return {'Authorization': 'Bearer ' + login.json()['session_token']}
    alice = headers('alice', 'correct horse battery staple')
    bob = headers('bob', 'another secure offline passphrase')
    yield client, alice, bob, monkeypatch, repo
    owner_sessions.reset()


def operation():
    return {'tool': 'notes.save', 'arguments': {'title': 'R28', 'content': 'ok', 'confirm': True}}


def test_validation_fails_closed():
    assert load_write_acl('', WRITE) == {}
    for raw in ('{', '[]', '{}', '{"alice":["*"]}',
                '{"alice":["notes.save","notes.save"]}', '{"alice":"notes.save"}',
                '{"alice":["not-a-tool"]}', '{"bad name":[]}'):
        with pytest.raises(ValueError):
            load_write_acl(raw, WRITE)
    assert not can_write('pf6-user:alice', 'notes.save', '', WRITE)
    assert not can_write('loopback-utilities', 'notes.save', '{"alice":["notes.save"]}', WRITE)


def test_default_deny_is_not_bypassed_by_valid_login(pf6):
    client, alice, _, _, _ = pf6
    r = client.post('/api/v1/utilities/confirmations/request', headers=alice, json=operation())
    assert r.status_code == 403
    assert 'não está autorizada' in r.text


def test_explicit_capability_allows_only_named_user(pf6):
    client, alice, bob, monkeypatch, repo = pf6
    monkeypatch.setenv('CAMPANARIO_PF6_WRITE_ACL_JSON', json.dumps({'alice': ['notes.save'], 'bob': []}))
    assert client.post('/api/v1/utilities/confirmations/request', headers=bob, json=operation()).status_code == 403
    pending = client.post('/api/v1/utilities/confirmations/request', headers=alice, json=operation())
    assert pending.status_code == 200, pending.text
    consent = {**operation(), 'confirmation_id': pending.json()['confirmation_id'], 'acknowledged': True}
    assert client.post('/api/v1/utilities/confirmations/approve', headers=alice, json=consent).status_code == 200
    pending2 = client.post('/api/v1/utilities/confirmations/request', headers=alice, json={'tool': 'files.delete', 'arguments': {}})
    assert pending2.status_code in (400, 403)


def test_revocation_between_approval_and_execution(pf6):
    client, alice, _, monkeypatch, _ = pf6
    monkeypatch.setenv('CAMPANARIO_PF6_WRITE_ACL_JSON', '{"alice":["notes.save"]}')
    op = operation()
    pending = client.post('/api/v1/utilities/confirmations/request', headers=alice, json=op)
    assert pending.status_code == 200
    approve = client.post('/api/v1/utilities/confirmations/approve', headers=alice,
                          json={**op, 'confirmation_id': pending.json()['confirmation_id'], 'acknowledged': True})
    assert approve.status_code == 200
    token = approve.json()['confirmation_token']
    monkeypatch.setenv('CAMPANARIO_PF6_WRITE_ACL_JSON', '{"alice":[]}')
    assert client.post('/api/v1/utilities/invoke', headers=alice,
                       json={**op, 'confirmation_token': token}).status_code == 403
    monkeypatch.setenv('CAMPANARIO_PF6_WRITE_ACL_JSON', '{')
    assert client.post('/api/v1/utilities/invoke', headers=alice,
                       json={**op, 'confirmation_token': token}).status_code == 503


def test_invalid_acl_blocks_request_and_approval(pf6):
    client, alice, _, monkeypatch, _ = pf6
    monkeypatch.setenv('CAMPANARIO_PF6_WRITE_ACL_JSON', '{"alice":["notes.save"]}')
    pending = client.post('/api/v1/utilities/confirmations/request', headers=alice, json=operation())
    assert pending.status_code == 200
    monkeypatch.setenv('CAMPANARIO_PF6_WRITE_ACL_JSON', 'broken')
    result = client.post('/api/v1/utilities/confirmations/approve', headers=alice,
                         json={**operation(), 'confirmation_id': pending.json()['confirmation_id'], 'acknowledged': True})
    assert result.status_code == 503
