# ADR 0056 — Permission / Trust Layer (PF6)

## Status
Accepted for F3 / PF6 implementation.

## Context
PF4 identifies devices and PF5 discovers/executes semantic capabilities, but availability is not authorization. A stable `device_id` cannot be treated as a credential, and a provider being online cannot imply that camera, location, messaging, file deletion or computer control may run.

## Decision
Add a runtime-owned `TrustManager` and `PermissionPolicy` before capability provider invocation.

Device trust is persisted separately from the PF4 `Device` contract. Pairing issues a high-entropy credential once; only its SHA-256 digest is persisted. Revocation clears the credential and marks the trust record revoked. `device_id` remains registry identity only.

Permission modes are explicit: `ALLOW`, `ALLOW_WHILE_SESSION`, `ALLOW_WHILE_CALL`, `ASK`, `CONFIRM`, `SCOPED_CONFIRM`, and `DENY`. Undefined permissions deny by default for external/device principals. Internal runtime calls remain an explicit trusted-system path so PF5 internal composition stays compatible.

Confirmation is one-shot, bound to principal/device and optionally scope. Approval yields a short-lived process-local token which is consumed on successful authorization. PF6 does not persist reusable confirmation tokens.

Capability execution evaluates every declared permission before `TOOL_REQUESTED` or provider invocation. A denial/confirmation requirement therefore cannot accidentally start the tool.

Security decisions, pairing/authentication attempts, confirmation and revocation are written to a persistent `security_audit` table. Raw credentials and credential hashes are never returned by read APIs or audit APIs.

Local API adds explicit pairing/revocation and audit inspection. The server remains bound to localhost; PF6 does not claim LAN/WAN exposure is production-ready.

## Consequences
- capability availability and authorization are structurally separate;
- untrusted/revoked devices cannot authorize capability execution;
- confirmation can be required without teaching Todd/Morgana provider/security internals;
- revocation takes effect immediately;
- security-relevant decisions have persistent provenance/audit;
- PF4 Device identity contract remains free of credentials/trust semantics;
- PF7 can now build authenticated client-independent sessions on top of this boundary;
- Personality / Social / Long-Call Baseline v1 remains unchanged.
