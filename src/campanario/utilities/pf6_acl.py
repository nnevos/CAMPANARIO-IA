"""R2.8: conservative, optional per-identity tool-write allowlist.

This is an additional deny-only boundary, not a replacement for PermissionPolicy.
Individual users have no HTTP write capabilities until explicitly listed in a
PRIVATE environment variable. The legacy single-owner mode is unchanged.
"""
from __future__ import annotations

import json


def load_write_acl(raw: str, known_write_tools: set[str] | frozenset[str]) -> dict[str, frozenset[str]]:
    """Parse {username: [exact tool IDs]}; empty string means deny all.

    Reject malformed, unknown, duplicate or wildcard entries. No implicit admin.
    """
    if not raw:
        return {}
    try:
        value = json.loads(raw)
        if not isinstance(value, dict) or len(value) > 32 or not value:
            raise ValueError('invalid ACL object')
        from campanario.utilities.pf6_identities import USERNAME
        result = {}
        for name, tools in value.items():
            if not isinstance(name, str) or not USERNAME.fullmatch(name):
                raise ValueError('invalid ACL identity')
            if not isinstance(tools, list) or len(tools) > len(known_write_tools):
                raise ValueError('invalid ACL list')
            if any(not isinstance(t, str) or t not in known_write_tools for t in tools):
                raise ValueError('unknown ACL tool')
            if len(set(tools)) != len(tools):
                raise ValueError('duplicate ACL tool')
            result[name] = frozenset(tools)
        return result
    except (TypeError, ValueError) as exc:
        raise ValueError('invalid PF6 write ACL configuration') from exc


def can_write(principal_id: str, tool: str, raw: str, known_write_tools: set[str] | frozenset[str]) -> bool:
    """Only users explicitly named in an exact per-tool allowlist pass.

    Denial here cannot grant permission; central PF6 still must approve.
    """
    acl = load_write_acl(raw, known_write_tools)
    if not principal_id.startswith('pf6-user:'):
        return False
    return tool in acl.get(principal_id.removeprefix('pf6-user:'), frozenset())
