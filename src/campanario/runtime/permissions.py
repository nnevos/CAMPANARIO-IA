from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class PermissionDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    CONFIRM = "confirm"


class PermissionMode(StrEnum):
    ALLOW = "allow"
    ALLOW_WHILE_SESSION = "allow_while_session"
    ALLOW_WHILE_CALL = "allow_while_call"
    ASK = "ask"
    CONFIRM = "confirm"
    SCOPED_CONFIRM = "scoped_confirm"
    DENY = "deny"


class AuthorizationContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    principal_kind: str = Field(min_length=1, max_length=32)
    principal_id: str = Field(min_length=1, max_length=128)
    device_id: str | None = Field(default=None, max_length=128)
    session_id: UUID | None = None
    session_active: bool = False
    call_active: bool = False
    confirmation_token: str | None = None

    @classmethod
    def internal_system(cls) -> "AuthorizationContext":
        return cls(principal_kind="system", principal_id="campanario-runtime", session_active=True)


class PermissionCheck(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    decision: PermissionDecision
    permission: str
    reason: str
    confirmation_id: UUID | None = None


class PermissionDeniedError(RuntimeError):
    def __init__(self, permission: str, reason: str) -> None:
        super().__init__(f"permission denied: {permission}: {reason}")
        self.permission = permission
        self.reason = reason


class PermissionConfirmationRequired(RuntimeError):
    def __init__(self, permission: str, confirmation_id: UUID) -> None:
        super().__init__(f"confirmation required: {permission}")
        self.permission = permission
        self.confirmation_id = confirmation_id


class TrustRepository(Protocol):
    def get_trust(self, device_id: str): ...
    def set_trust(self, device_id: str, *, trusted: bool, credential_hash: str | None, revoked_at: datetime | None): ...
    def append_audit(self, *, action: str, principal_id: str, device_id: str | None, capability: str | None, permission: str | None, decision: str, detail: str | None): ...
    def list_audit(self, *, limit: int = 100): ...


@dataclass(slots=True)
class _Confirmation:
    id: UUID
    permission: str
    principal_id: str
    device_id: str | None
    scope: str | None
    capability: str | None
    session_id: UUID | None
    created_at: datetime
    token_hash: str | None = None
    approved: bool = False
    consumed: bool = False


# PF6 confirmations are ephemeral, never persisted or restored after restart.
CONFIRMATION_TTL = timedelta(minutes=5)
MAX_PENDING_CONFIRMATIONS = 256


class TrustManager:
    """PF6 trust boundary. Raw pairing credentials are never persisted."""
    def __init__(self, repository: TrustRepository, devices) -> None:
        self._repository = repository
        self._devices = devices

    def pair(self, device_id: str) -> str:
        if self._devices.get(device_id) is None:
            raise KeyError(device_id)
        token = secrets.token_urlsafe(32)
        self._repository.set_trust(device_id, trusted=True, credential_hash=_hash(token), revoked_at=None)
        self._repository.append_audit(action="device.paired", principal_id=device_id, device_id=device_id, capability=None, permission=None, decision="allow", detail=None)
        return token

    def authenticate(self, device_id: str, token: str) -> bool:
        device = self._devices.get(device_id)
        state = self._repository.get_trust(device_id)
        valid = bool(device and state and state["trusted"] and not state["revoked_at"] and state["credential_hash"] and secrets.compare_digest(state["credential_hash"], _hash(token)))
        self._repository.append_audit(action="device.authenticate", principal_id=device_id, device_id=device_id, capability=None, permission=None, decision="allow" if valid else "deny", detail=None)
        return valid

    def revoke(self, device_id: str) -> None:
        if self._devices.get(device_id) is None:
            raise KeyError(device_id)
        self._repository.set_trust(device_id, trusted=False, credential_hash=None, revoked_at=datetime.now(UTC))
        self._repository.append_audit(action="device.revoked", principal_id=device_id, device_id=device_id, capability=None, permission=None, decision="deny", detail="credential revoked")

    def status(self, device_id: str):
        state = self._repository.get_trust(device_id)
        if state is None:
            return None
        return {"trusted": state["trusted"], "revoked_at": state["revoked_at"]}

    def audit(self, *, limit: int = 100):
        return self._repository.list_audit(limit=limit)


class PermissionPolicy:
    """Explicit policy evaluator. Availability and authorization remain separate."""
    def __init__(self, trust: TrustManager, repository: TrustRepository) -> None:
        self._trust = trust
        self._repository = repository
        self._rules: dict[str, PermissionMode] = {}
        self._confirmations: dict[UUID, _Confirmation] = {}
        self._confirmation_lock = RLock()

    def set_rule(self, permission: str, mode: PermissionMode) -> None:
        self._rules[permission.strip().lower()] = mode

    def rule(self, permission: str) -> PermissionMode:
        return self._rules.get(permission.strip().lower(), PermissionMode.DENY)

    def check(self, permission: str, context: AuthorizationContext, *, capability: str | None = None, scope: str | None = None) -> PermissionCheck:
        permission = permission.strip().lower()
        if context.principal_kind == "system" and context.principal_id == "campanario-runtime":
            return self._record(permission, context, capability, PermissionDecision.ALLOW, "trusted internal runtime")
        if context.device_id:
            device = self._trust._devices.get(context.device_id)
            state = self._trust._repository.get_trust(context.device_id)
            if not device or not state or not state["trusted"] or state["revoked_at"]:
                return self._record(permission, context, capability, PermissionDecision.DENY, "device is not trusted")
        mode = self.rule(permission)
        if mode == PermissionMode.ALLOW:
            return self._record(permission, context, capability, PermissionDecision.ALLOW, "policy allows")
        if mode == PermissionMode.ALLOW_WHILE_SESSION and context.session_active:
            return self._record(permission, context, capability, PermissionDecision.ALLOW, "allowed while session is active")
        if mode == PermissionMode.ALLOW_WHILE_CALL and context.call_active:
            return self._record(permission, context, capability, PermissionDecision.ALLOW, "allowed while call is active")
        if mode in {PermissionMode.ASK, PermissionMode.CONFIRM, PermissionMode.SCOPED_CONFIRM}:
            with self._confirmation_lock:
                now = datetime.now(UTC)
                self._prune_confirmations(now)
                approved = self._consume_confirmation(permission, context, scope if mode == PermissionMode.SCOPED_CONFIRM else None, capability)
                if approved:
                    return self._record(permission, context, capability, PermissionDecision.ALLOW, "approved confirmation consumed")
                if len(self._confirmations) >= MAX_PENDING_CONFIRMATIONS:
                    return self._record(permission, context, capability, PermissionDecision.DENY, "too many pending confirmations")
                confirmation = _Confirmation(
                    id=uuid4(), permission=permission, principal_id=context.principal_id,
                    device_id=context.device_id,
                    scope=scope if mode == PermissionMode.SCOPED_CONFIRM else None,
                    capability=capability, session_id=context.session_id, created_at=now,
                )
                self._confirmations[confirmation.id] = confirmation
                check = self._record(permission, context, capability, PermissionDecision.CONFIRM, "explicit confirmation required")
                return check.model_copy(update={"confirmation_id": confirmation.id})
        reason = "required session/call is not active" if mode in {PermissionMode.ALLOW_WHILE_SESSION, PermissionMode.ALLOW_WHILE_CALL} else "policy denies or is undefined"
        return self._record(permission, context, capability, PermissionDecision.DENY, reason)

    def approve(self, confirmation_id: UUID, *, principal_id: str) -> str:
        """Low-level API. Caller MUST verify a human approval and principal identity.

        Do not expose this method through a browser endpoint without authentication.
        """
        with self._confirmation_lock:
            self._prune_confirmations(datetime.now(UTC))
            item = self._confirmations.get(confirmation_id)
            if item is None or item.principal_id != principal_id or item.consumed or item.approved:
                raise KeyError(confirmation_id)
            token = secrets.token_urlsafe(32)
            item.token_hash = _hash(token)
            item.approved = True
            self._repository.append_audit(action="permission.confirmed", principal_id=principal_id, device_id=item.device_id, capability=item.capability, permission=item.permission, decision="allow", detail=item.scope)
            return token

    def _prune_confirmations(self, now: datetime) -> None:
        for key, item in list(self._confirmations.items()):
            if item.consumed or now - item.created_at >= CONFIRMATION_TTL:
                del self._confirmations[key]

    def _consume_confirmation(self, permission: str, context: AuthorizationContext, scope: str | None, capability: str | None) -> bool:
        if not context.confirmation_token:
            return False
        digest = _hash(context.confirmation_token)
        for key, item in list(self._confirmations.items()):
            if (item.permission == permission and item.principal_id == context.principal_id
                    and item.device_id == context.device_id and item.session_id == context.session_id
                    and item.scope == scope and item.capability == capability
                    and item.approved and not item.consumed and item.token_hash
                    and secrets.compare_digest(item.token_hash, digest)):
                item.consumed = True
                del self._confirmations[key]
                return True
        return False

    def _record(self, permission: str, context: AuthorizationContext, capability: str | None, decision: PermissionDecision, reason: str) -> PermissionCheck:
        self._repository.append_audit(action="permission.check", principal_id=context.principal_id, device_id=context.device_id, capability=capability, permission=permission, decision=decision.value, detail=reason)
        return PermissionCheck(decision=decision, permission=permission, reason=reason)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
