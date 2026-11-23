"""R1 incremental: central policy, no implicit browser privilege in V9 opt-in."""
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
import pytest

import campanario.utilities.api as api
from campanario.main import app
from campanario.runtime.permissions import PermissionCheck, PermissionDecision


@pytest.fixture
def client(monkeypatch, tmp_path):
    from campanario.utilities.service import UtilityService
    util = UtilityService(tmp_path / 'test-utilities')
    monkeypatch.setattr(api, 'service', lambda: util)
    return TestClient(app), util


def test_legacy_browser_operations_unchanged(client, monkeypatch):
    http, _ = client
    monkeypatch.setattr('campanario.config.get_settings', lambda: SimpleNamespace(brains_v9_enabled=False))
    result = http.post('/api/v1/utilities/invoke', json={'tool': 'notes.save', 'arguments': {'title': 'legacy', 'confirm': True}})
    assert result.status_code == 200 and result.json()['status'] == 'success'


def test_v9_read_consults_runtime_but_writes_cannot_use_confirm_true(client, monkeypatch):
    http, util = client
    monkeypatch.setattr('campanario.config.get_settings', lambda: SimpleNamespace(brains_v9_enabled=True))
    # R3.13: this legacy test exercises the PF6-configured path; solo-local upload is separately permitted.
    monkeypatch.setattr(api, '_identities', lambda: {'pf6-user:test': object()})
    policy = Mock()
    def check(permission, authorization, *, capability, scope):
        assert authorization.principal_kind == 'local_browser'
        assert authorization.principal_id != 'campanario-runtime'
        return PermissionCheck(permission=permission, decision=(PermissionDecision.CONFIRM if permission == 'utilities.write' else PermissionDecision.ALLOW), reason='policy')
    policy.check.side_effect = check
    monkeypatch.setattr('campanario.bootstrap.get_runtime', lambda: SimpleNamespace(permissions=policy))
    read = http.post('/api/v1/utilities/invoke', json={'tool': 'notes.list', 'arguments': {}})
    assert read.status_code == 200
    write = http.post('/api/v1/utilities/invoke', json={'tool': 'notes.save', 'arguments': {'title': 'blocked', 'confirm': True}})
    assert write.status_code == 403
    assert util.run('notes.list', {})['result']['count'] == 0
    upload = http.post('/api/v1/utilities/upload?ignored=1', json={'filename': 'x.txt', 'content_base64': 'YQ=='})
    assert upload.status_code == 403
    stream = http.post('/api/v1/utilities/upload-stream?filename=x.txt', content=b'hello', headers={'content-type': 'application/octet-stream'})
    assert stream.status_code == 403
    assert not (util.roots[0] / 'x.txt').exists()
    assert policy.check.call_count == 4


def test_v9_permission_failure_fails_closed(client, monkeypatch):
    http, util = client
    monkeypatch.setattr('campanario.config.get_settings', lambda: SimpleNamespace(brains_v9_enabled=True))
    def unavailable():
        raise RuntimeError('runtime down')
    monkeypatch.setattr('campanario.bootstrap.get_runtime', unavailable)
    response = http.post('/api/v1/utilities/invoke', json={'tool': 'notes.save', 'arguments': {'title': 'no', 'confirm': True}})
    assert response.status_code == 503
    assert util.run('notes.list', {})['result']['count'] == 0


def test_v9_denied_read_does_not_execute(client, monkeypatch):
    http, _ = client
    monkeypatch.setattr('campanario.config.get_settings', lambda: SimpleNamespace(brains_v9_enabled=True))
    policy = Mock()
    policy.check.return_value = PermissionCheck(permission='utilities.read', decision=PermissionDecision.DENY, reason='denied')
    monkeypatch.setattr('campanario.bootstrap.get_runtime', lambda: SimpleNamespace(permissions=policy))
    assert http.post('/api/v1/utilities/invoke', json={'tool': 'notes.list', 'arguments': {}}).status_code == 403
