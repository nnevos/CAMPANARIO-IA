"""R2.3: PF6 token replay, scope, capability, session and expiry boundaries."""
from datetime import datetime, UTC, timedelta
from uuid import uuid4
from unittest.mock import Mock

import pytest

from campanario.runtime.permissions import (
    AuthorizationContext, PermissionDecision, PermissionMode, PermissionPolicy,
    CONFIRMATION_TTL, MAX_PENDING_CONFIRMATIONS,
)


def policy():
    repo = Mock()
    trust = Mock()
    trust._repository = repo
    trust._devices = Mock()
    permissions = PermissionPolicy(trust, repo)
    permissions.set_rule('utilities.write', PermissionMode.SCOPED_CONFIRM)
    return permissions, repo


def ask(p, auth, *, capability='notes.save', scope='notes.save'):
    result = p.check('utilities.write', auth, capability=capability, scope=scope)
    assert result.decision == PermissionDecision.CONFIRM
    return result.confirmation_id


def test_scope_capability_and_session_cannot_be_swapped():
    p, _ = policy()
    ctx = AuthorizationContext(principal_kind='device', principal_id='phone', session_id=uuid4())
    token = p.approve(ask(p, ctx), principal_id='phone')
    supplied = ctx.model_copy(update={'confirmation_token': token})
    for moved in (
        (supplied, 'other.tool', 'notes.save'),
        (supplied, 'notes.save', 'other.tool'),
        (supplied.model_copy(update={'session_id': uuid4()}), 'notes.save', 'notes.save'),
        (supplied.model_copy(update={'principal_id': 'other'}), 'notes.save', 'notes.save'),
    ):
        assert p.check('utilities.write', moved[0], capability=moved[1], scope=moved[2]).decision != PermissionDecision.ALLOW
    assert p.check('utilities.write', supplied, capability='notes.save', scope='notes.save').decision == PermissionDecision.ALLOW
    assert p.check('utilities.write', supplied, capability='notes.save', scope='notes.save').decision != PermissionDecision.ALLOW


def test_expired_confirmation_cannot_be_approved_or_consumed():
    p, _ = policy()
    auth = AuthorizationContext(principal_kind='device', principal_id='phone')
    confirmation_id = ask(p, auth)
    p._confirmations[confirmation_id].created_at = datetime.now(UTC) - CONFIRMATION_TTL - timedelta(seconds=1)
    with pytest.raises(KeyError):
        p.approve(confirmation_id, principal_id='phone')
    confirmation_id = ask(p, auth)
    token = p.approve(confirmation_id, principal_id='phone')
    p._confirmations[confirmation_id].created_at = datetime.now(UTC) - CONFIRMATION_TTL - timedelta(seconds=1)
    assert p.check('utilities.write', auth.model_copy(update={'confirmation_token': token}), capability='notes.save', scope='notes.save').decision != PermissionDecision.ALLOW


def test_double_approval_rejected_and_token_not_logged():
    p, repo = policy()
    auth = AuthorizationContext(principal_kind='device', principal_id='phone')
    confirmation_id = ask(p, auth)
    with pytest.raises(KeyError):
        p.approve(confirmation_id, principal_id='someone-else')
    token = p.approve(confirmation_id, principal_id='phone')
    with pytest.raises(KeyError):
        p.approve(confirmation_id, principal_id='phone')
    assert token not in repr(repo.append_audit.call_args_list)


def test_excess_pending_requests_fail_closed(monkeypatch):
    import campanario.runtime.permissions as mod
    monkeypatch.setattr(mod, 'MAX_PENDING_CONFIRMATIONS', 2)
    p, _ = policy()
    auth = AuthorizationContext(principal_kind='device', principal_id='phone')
    ask(p, auth)
    ask(p, auth)
    assert p.check('utilities.write', auth, capability='notes.save', scope='notes.save').decision == PermissionDecision.DENY
    assert len(p._confirmations) == 2


def test_parallel_replay_allows_exactly_one_use():
    from concurrent.futures import ThreadPoolExecutor
    p, _ = policy()
    auth = AuthorizationContext(principal_kind='device', principal_id='phone')
    token = p.approve(ask(p, auth), principal_id='phone')
    supplied = auth.model_copy(update={'confirmation_token': token})
    with ThreadPoolExecutor(max_workers=12) as pool:
        decisions = list(pool.map(lambda _: p.check('utilities.write', supplied, capability='notes.save', scope='notes.save').decision, range(12)))
    assert decisions.count(PermissionDecision.ALLOW) == 1
