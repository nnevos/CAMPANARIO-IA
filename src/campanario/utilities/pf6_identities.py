"""Optional PF6 individual offline identities. Private config only; no user DB.

Format CAMPANARIO_PF6_USERS_JSON={"operator": "pbkdf2_sha256$600000$<salt_hex>$<hash_hex>"}.
Generate verifiers offline with `python -m campanario.utilities.pf6_identities` and
place them in a PRIVATE .env; never commit verifiers or distribute credentials.
"""
from __future__ import annotations

import getpass
import hashlib
import hmac
import json
import os
import re
import secrets

ITERATIONS = 600_000
USERNAME = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{2,31}$')


def load_identities(raw: str) -> dict[str, str]:
    if not raw:
        return {}
    try:
        records = json.loads(raw)
        if not isinstance(records, dict) or not (1 <= len(records) <= 32):
            raise ValueError('invalid identity count')
        for name, verifier in records.items():
            if not isinstance(name, str) or not USERNAME.fullmatch(name):
                raise ValueError('invalid identity name')
            _parse(verifier)
        return records
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError('invalid PF6 individual identity configuration') from exc


def _parse(value: str):
    if not isinstance(value, str):
        raise ValueError('invalid verifier')
    parts = value.split('$')
    if len(parts) != 4 or parts[0] != 'pbkdf2_sha256' or parts[1] != str(ITERATIONS):
        raise ValueError('invalid verifier format')
    try:
        salt, digest = bytes.fromhex(parts[2]), bytes.fromhex(parts[3])
    except ValueError as exc:
        raise ValueError('invalid verifier encoding') from exc
    if len(salt) != 16 or len(digest) != 32:
        raise ValueError('invalid verifier size')
    return salt, digest


def password_verifier(password: str, *, salt: bytes | None = None) -> str:
    if not isinstance(password, str) or not (16 <= len(password) <= 512):
        raise ValueError('password length must be 16..512')
    salt = secrets.token_bytes(16) if salt is None else salt
    if len(salt) != 16:
        raise ValueError('invalid salt')
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'


def authenticate_identity(username: str, password: str, records: dict[str, str]) -> bool:
    # On unknown users, perform an equivalent PBKDF2 operation to limit timing leakage.
    value = records.get(username)
    try:
        salt, expected = _parse(value) if value else (b'\0' * 16, b'\0' * 32)
        candidate = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
        return bool(value and hmac.compare_digest(expected, candidate))
    except (UnicodeError, ValueError, AttributeError):
        return False


def identities_fingerprint(records: dict[str, str]) -> bytes:
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(',', ':')).encode()).digest()


if __name__ == '__main__':
    name = input('PF6 username (3..32, letters/digits/_/-): ').strip()
    if not USERNAME.fullmatch(name):
        raise SystemExit('Invalid username')
    password = getpass.getpass('New offline PF6 password (16+ chars): ')
    confirm = getpass.getpass('Confirm password: ')
    if password != confirm:
        raise SystemExit('Passwords differ')
    print('Keep this verifier in private CAMPANARIO_PF6_USERS_JSON only:')
    print(json.dumps({name: password_verifier(password)}))
