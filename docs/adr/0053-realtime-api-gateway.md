# ADR 0053 — Realtime/API Gateway (PF3)

## Status
Accepted for F3 / PF3 implementation.

## Context
PF1 separated the persistent Campanario runtime from UI hosting and PF2 introduced a versioned internal Event Bus. The Web UI still depended on the legacy `/api` + SSE chat adapter, so future Desktop/Mobile/Call clients had no stable client-independent gateway into the same runtime.

## Decision
Introduce a versioned gateway without a big-bang rewrite:

- `/api/v1/...` is the request/response surface for runtime/session operations;
- `/ws/v1/events` is the realtime observation surface for PF2 `RuntimeEvent` envelopes;
- the WebSocket accepts optional `session_id` and `after_sequence` filters and replays the bounded process-local journal before continuing with live events;
- realtime frames are versioned (`1.0`) and transport PF2 events without inventing a second event vocabulary;
- conversation turns are submitted through `POST /api/v1/sessions/{session_id}/turn`; generation remains owned by the shared Conversation Runtime while any connected realtime client observes the same PF2 events;
- legacy `/api/...` and `/api/.../chat/stream` SSE endpoints remain available during migration;
- the current Web UI is migrated to `/api/v1` + `/ws/v1/events`, proving it is now a gateway client instead of being coupled to SSE conversation internals.

The WebSocket is intentionally observation-oriented in PF3. Device capability announcements, pairing, authorization and remote network trust remain later gates. Existing Windows hosting remains bound to `127.0.0.1`; PF3 does not authorize LAN/WAN exposure.

## Consequences
- Web and future clients can consume the same runtime events and session state;
- reconnecting with `after_sequence` can replay missed process-local events without creating another chat session;
- speaker provenance, correlation/causation and event ordering remain the PF2 contracts end-to-end;
- generation survives realtime observer replacement because request/response turn submission is separate from the WebSocket observer;
- legacy clients remain functional during incremental migration;
- PF4 Device Registry is now the next platform gate; PF3 does not implement devices/tools/permissions prematurely.
