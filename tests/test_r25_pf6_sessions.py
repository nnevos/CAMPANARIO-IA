"""R2.5 local owner session lifecycle, per-operation consent, safe denial."""
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
import pytest

from campanario.main import app
from campanario.runtime.permissions import PermissionMode, PermissionPolicy
import campanario.utilities.api as api
from campanario.utilities.pf6_sessions import OwnerSessions, owner_sessions
from campanario.utilities.service import UtilityService


@pytest.fixture
def env(monkeypatch, tmp_path):
    owner_sessions.reset()
    monkeypatch.setenv('CAMPANARIO_PF6_OWNER_TOKEN', 'Z' * 48)
    monkeypatch.setattr('campanario.config.get_settings', lambda: SimpleNamespace(brains_v9_enabled=True))
    utility = UtilityService(tmp_path / 'tools')
    monkeypatch.setattr(api, 'service', lambda: utility)
    repo = Mock()
    trust = Mock()
    trust._repository = repo
    trust._devices = Mock()
    policy = PermissionPolicy(trust, repo)
    policy.set_rule('utilities.write', PermissionMode.SCOPED_CONFIRM)
    policy.set_rule('utilities.read', PermissionMode.ALLOW)
    monkeypatch.setattr('campanario.bootstrap.get_runtime', lambda: SimpleNamespace(permissions=policy))
    yield TestClient(app), utility, policy
    owner_sessions.reset()


def login(client, key='Z' * 48):
    return client.post('/api/v1/utilities/sessions/login', json={'credential': key})


def test_session_required_and_logout_revokes_approved_operation(env):
    client, utility, _ = env
    operation = {'tool': 'notes.save', 'arguments': {'title': 'session-test', 'confirm': True}}
    assert client.post('/api/v1/utilities/confirmations/request', json=operation).status_code == 401
    token = login(client).json()['session_token']
    headers = {'Authorization': 'Bearer ' + token}
    pending = client.post('/api/v1/utilities/confirmations/request', json=operation, headers=headers)
    assert pending.status_code == 200, pending.text
    approval = client.post('/api/v1/utilities/confirmations/approve', json={**operation,
        'confirmation_id': pending.json()['confirmation_id'], 'acknowledged': True}, headers=headers)
    assert approval.status_code == 200, approval.text
    confirmation_token = approval.json()['confirmation_token']
    assert client.post('/api/v1/utilities/sessions/logout', headers=headers).status_code == 200
    assert client.post('/api/v1/utilities/invoke', json={**operation,
        'confirmation_token': confirmation_token}, headers=headers).status_code == 401
    assert utility.run('notes.list', {})['result']['count'] == 0


def test_session_swap_does_not_transfer_confirmation(env):
    client, _, _ = env
    h1 = {'Authorization': 'Bearer ' + login(client).json()['session_token']}
    h2 = {'Authorization': 'Bearer ' + login(client).json()['session_token']}
    operation = {'tool': 'notes.save', 'arguments': {'title': 'session-test', 'confirm': True}}
    pending = client.post('/api/v1/utilities/confirmations/request', json=operation, headers=h1).json()
    approval = {'confirmation_id': pending['confirmation_id'], **operation, 'acknowledged': True}
    assert client.post('/api/v1/utilities/confirmations/approve', json=approval, headers=h2).status_code == 403
    token = client.post('/api/v1/utilities/confirmations/approve', json=approval, headers=h1).json()['confirmation_token']
    assert client.post('/api/v1/utilities/invoke', json={**operation, 'confirmation_token': token}, headers=h2).status_code == 403
    assert client.post('/api/v1/utilities/invoke', json={**operation, 'confirmation_token': token}, headers=h1).status_code == 200


def test_wrong_secret_lockout_and_rotation(env, monkeypatch):
    client, _, _ = env
    for _ in range(5):
        assert login(client, 'wrong').status_code == 401
    assert login(client).status_code == 429
    owner_sessions.reset()
    token = login(client).json()['session_token']
    monkeypatch.setenv('CAMPANARIO_PF6_OWNER_TOKEN', 'Y' * 48)
    assert client.post('/api/v1/utilities/sessions/logout', headers={'Authorization': 'Bearer ' + token}).status_code == 401
    assert login(client, 'Y' * 48).status_code == 200


def test_ttl_and_in_memory_revoke(monkeypatch):
    clock = [10.0]
    monkeypatch.setattr('campanario.utilities.pf6_sessions.time.monotonic', lambda: clock[0])
    sessions = OwnerSessions()
    token, _ = sessions.login('Z' * 48, 'Z' * 48, client='127.0.0.1')
    assert sessions.authenticate(token, 'Z' * 48)
    clock[0] += 901
    assert sessions.authenticate(token, 'Z' * 48) is None
    token, _ = sessions.login('Z' * 48, 'Z' * 48, client='127.0.0.1')
    sessions.revoke(token)
    assert sessions.authenticate(token, 'Z' * 48) is None


def test_no_secret_or_session_in_audit_and_upload_blocked(env):
    client, utility, policy = env
    session = login(client).json()
    assert 'Z' * 48 not in repr(policy._repository.append_audit.call_args_list)
    assert session['session_token'] not in repr(policy._repository.append_audit.call_args_list)
    assert client.post('/api/v1/utilities/upload', json={'filename': 'file.txt', 'content_base64': 'YQ=='}, headers={'Authorization': 'Bearer ' + session['session_token']}).status_code == 403
    assert not (utility.roots[0] / 'file.txt').exists()
