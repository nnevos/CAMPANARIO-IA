"""R2.4 opt-in localhost owner approval: scoped and single-use, denied by default."""
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
import pytest

import campanario.utilities.api as util_api
from campanario.main import app
from campanario.runtime.permissions import PermissionMode, PermissionPolicy
from campanario.utilities.service import UtilityService


@pytest.fixture
def setup(monkeypatch, tmp_path):
    monkeypatch.setattr('campanario.config.get_settings', lambda: SimpleNamespace(brains_v9_enabled=True))
    util = UtilityService(tmp_path / 'utilities')
    monkeypatch.setattr(util_api, 'service', lambda: util)
    repo = Mock()
    trust = Mock()
    trust._repository = repo
    trust._devices = Mock()
    policy = PermissionPolicy(trust, repo)
    policy.set_rule('utilities.write', PermissionMode.SCOPED_CONFIRM)
    policy.set_rule('utilities.read', PermissionMode.ALLOW)
    monkeypatch.setattr('campanario.bootstrap.get_runtime', lambda: SimpleNamespace(permissions=policy))
    return TestClient(app), util, policy


def test_unconfigured_and_fake_legacy_confirmation_fail_closed(setup, monkeypatch):
    client, util, _ = setup
    monkeypatch.delenv('CAMPANARIO_PF6_OWNER_TOKEN', raising=False)
    body = {'tool': 'notes.save', 'arguments': {'title': 'blocked', 'confirm': True}}
    assert client.post('/api/v1/utilities/confirmations/request', json=body).status_code == 503
    assert client.post('/api/v1/utilities/invoke', json=body).status_code == 403
    assert util.run('notes.list', {})['result']['count'] == 0


def test_auth_bound_to_operation_and_single_use(setup, monkeypatch):
    client, util, policy = setup
    secret = 'abc' * 16
    monkeypatch.setenv('CAMPANARIO_PF6_OWNER_TOKEN', secret)
    body = {'tool': 'notes.save', 'arguments': {'title': 'authorized', 'confirm': True}}
    login = client.post('/api/v1/utilities/sessions/login', json={'credential': secret})
    assert login.status_code == 200, login.text
    headers = {'Authorization': 'Bearer ' + login.json()['session_token']}
    r = client.post('/api/v1/utilities/confirmations/request', json=body, headers=headers)
    assert r.status_code == 200, r.text
    approval = {'confirmation_id': r.json()['confirmation_id'], **body, 'acknowledged': True}
    endpoint = '/api/v1/utilities/confirmations/approve'
    assert client.post(endpoint, json=approval).status_code == 401
    assert client.post(endpoint, json=approval, headers={'Authorization': 'Bearer wrong'}).status_code == 401
    assert client.post(endpoint, json={**approval, 'arguments': {'title': 'changed'}, 'acknowledged': True}, headers=headers).status_code == 403
    result = client.post(endpoint, json=approval, headers=headers)
    assert result.status_code == 200, result.text
    token = result.json()['confirmation_token']
    assert client.post(endpoint, json=approval, headers=headers).status_code == 403
    mutated = client.post('/api/v1/utilities/invoke', json={**body, 'arguments': {'title': 'changed'}, 'confirmation_token': token}, headers=headers)
    assert mutated.status_code == 403
    accepted = client.post('/api/v1/utilities/invoke', json={**body, 'confirmation_token': token}, headers=headers)
    assert accepted.status_code == 200 and accepted.json()['status'] == 'success'
    assert client.post('/api/v1/utilities/invoke', json={**body, 'confirmation_token': token}, headers=headers).status_code == 403
    assert util.run('notes.list', {})['result']['count'] == 1
    assert token not in repr(policy._repository.append_audit.call_args_list)


def test_non_write_and_upload_stay_blocked(setup, monkeypatch):
    client, util, _ = setup
    monkeypatch.setenv('CAMPANARIO_PF6_OWNER_TOKEN', 'x' * 40)
    login = client.post('/api/v1/utilities/sessions/login', json={'credential': 'x'*40})
    assert login.status_code == 200
    assert client.post('/api/v1/utilities/confirmations/request', json={'tool': 'notes.list'}, headers={'Authorization': 'Bearer '+login.json()['session_token']}).status_code == 400
    assert client.post('/api/v1/utilities/upload', json={'filename':'safe.txt', 'content_base64':'YQ=='}).status_code == 403
    assert not (util.roots[0] / 'safe.txt').exists()


def test_short_owner_secret_is_never_accepted(setup, monkeypatch):
    client, _, _ = setup
    monkeypatch.setenv('CAMPANARIO_PF6_OWNER_TOKEN', 'too-short')
    assert client.post('/api/v1/utilities/confirmations/request', json={'tool': 'notes.save'}).status_code == 503
