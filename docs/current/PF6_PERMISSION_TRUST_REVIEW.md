# PF6 — Permission / Trust Layer Review

PF6 closes the security boundary between an available capability and an authorized action.

Implemented:
- `TrustManager` with one-time pairing credential issuance, hashed-at-rest credential, authentication and revocation;
- `PermissionPolicy` with deny-by-default external policy and explicit session/call/confirm/scoped-confirm modes;
- one-shot confirmations bound to principal/device/scope;
- Capability Registry authorization before any provider invocation or `TOOL_REQUESTED` event;
- persistent `security_audit` records;
- migration `0007_permission_trust_layer.py`;
- localhost API for pair/revoke/audit without exposing credential hashes;
- regression coverage for untrusted blocking, confirmation consumption, session-scoped allow and revocation.

Security boundary intentionally retained:
- `device_id` is not authentication;
- an advertised capability is not permission;
- remote LAN/WAN exposure is still not enabled;
- confirmation tokens are not durable grants;
- unrestricted computer control is not implemented.

Validation: focused PF4/PF5/PF6/gateway suite 19/19 PASS; full regression 367/367 PASS; Alembic 0001→0007 PASS; compileall PASS.

Next gate: PF7 — client-independent sessions.
