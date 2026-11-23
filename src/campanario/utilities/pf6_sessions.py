"""Ephemeral, local-only PF6 owner sessions; not individual user accounts.

Never store the owner secret, bearer tokens, or personal data on disk.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from threading import RLock
from uuid import UUID, uuid4

SESSION_TTL_SECONDS = 15 * 60
MAX_SESSIONS = 32
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 60


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode('utf-8')).digest()


@dataclass(frozen=True)
class OwnerSession:
    session_id: UUID
    secret_fingerprint: bytes
    expires_at: float
    token_digest: bytes
    principal_id: str = "loopback-utilities"


class OwnerSessions:
    def __init__(self):
        self._lock = RLock()
        self._sessions: dict[bytes, OwnerSession] = {}
        self._failures: dict[str, tuple[int, float]] = {}

    def _prune(self, now: float):
        self._sessions = {k: v for k, v in self._sessions.items() if v.expires_at > now}
        self._failures = {k: v for k, v in self._failures.items() if v[1] > now}

    def _issue(self, now: float, verifier: bytes, principal_id: str):
        if len(self._sessions) >= MAX_SESSIONS:
            raise OverflowError('too many sessions')
        bearer = secrets.token_urlsafe(48)
        hashed = _digest(bearer)
        session = OwnerSession(uuid4(), verifier, now + SESSION_TTL_SECONDS, hashed, principal_id)
        self._sessions[hashed] = session
        return bearer, session

    def login_identity(self, username: str, password: str, records: dict, *, client: str):
        """Password-based offline identity. Config stays in private .env, never persisted here."""
        from campanario.utilities.pf6_identities import authenticate_identity, identities_fingerprint
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            count, until = self._failures.get(client, (0, 0.0))
            if count >= MAX_FAILED_LOGINS and until > now:
                raise PermissionError('login temporarily locked')
            if not authenticate_identity(username, password, records):
                self._failures[client] = (count + 1, now + LOCKOUT_SECONDS)
                return None
            self._failures.pop(client, None)
            return self._issue(now, identities_fingerprint(records), 'pf6-user:' + username)

    def login(self, candidate: str, configured: str, *, client: str) -> tuple[str, OwnerSession] | None:
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            count, until = self._failures.get(client, (0, 0.0))
            if count >= MAX_FAILED_LOGINS and until > now:
                raise PermissionError('login temporarily locked')
            valid = bool(32 <= len(configured) <= 256 and not configured.isspace()
                         and hmac.compare_digest(_digest(candidate), _digest(configured)))
            if not valid:
                count += 1
                self._failures[client] = (count, now + LOCKOUT_SECONDS)
                return None
            self._failures.pop(client, None)
            return self._issue(now, _digest(configured), "loopback-utilities")

    def authenticate(self, bearer: str, configured: str, *, verifier: bytes | None = None) -> OwnerSession | None:
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            hashed = _digest(bearer)
            item = self._sessions.get(hashed)
            if not item or not hmac.compare_digest(item.secret_fingerprint, verifier if verifier is not None else _digest(configured)):
                return None
            return item

    def revoke(self, bearer: str) -> None:
        with self._lock:
            self._sessions.pop(_digest(bearer), None)

    def reset(self) -> None:
        """Force logout of all sessions (e.g., during administrative recovery)."""
        with self._lock:
            self._sessions.clear()
            self._failures.clear()


owner_sessions = OwnerSessions()
