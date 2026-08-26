# ADR 0052 — Runtime Event Bus and Versioned Event Contracts (PF2)

## Status
Accepted for F3 / PF2 implementation.

## Context
PF1 established a client-independent `CampanarioRuntime` and explicit process hosting, but runtime activity was still observable only through direct method calls and the legacy SSE adapter. Platform Foundation requires future WebSocket, device, tool, mobile and call clients to observe the same Campanario without coupling UI code directly to conversation internals.

PF2 therefore needs an internal event model before any realtime transport exists. The event layer must preserve ordering, speaker/source provenance and causal grouping without spreading arbitrary dictionaries through the codebase.

## Decision
Introduce a process-local `RuntimeEventBus` owned by `CampanarioRuntime`.

Each event uses a frozen, versioned envelope containing:

- `schema_version` (`1.0` for the PF2 contract);
- `event_id`;
- monotonically increasing process-local `sequence`;
- `event_type`;
- `occurred_at`;
- `runtime_id`;
- optional `session_id`;
- `correlation_id` for one logical turn/operation;
- optional `causation_id`;
- explicit `EventProvenance` (`source_kind`, `source_id`, optional agent/client/device ids);
- payload validated against the schema registered for that event type.

The PF2 catalog includes the planned conversation, speech/wake, session, agent, device, tool, location/context, memory and call event names. Events not yet produced by runtime subsystems still have typed payload contracts so later phases do not invent transport-specific dictionaries.

The existing conversation pipeline now publishes real events for:

- `SESSION_STARTED`;
- `USER_TEXT`;
- `AGENT_SELECTED`;
- `AGENT_INTENT_TO_SPEAK`;
- `AGENT_RESPONSE_STARTED`;
- `AGENT_RESPONSE_CHUNK`;
- `AGENT_RESPONSE_FINISHED`.

`RuntimeEventBus` provides synchronous subscriptions plus a bounded in-memory journal with filtered replay by sequence/session/type. Replay is deliberately **not durable across runtime process restarts** in PF2; durable delivery and network transport belong to later gates.

`ChatService` depends only on the `EventPublisher` protocol. Web/API remains an adapter and is not migrated to WebSocket in PF2.

## Consequences
- runtime events have a stable schema before PF3 Realtime Gateway;
- order and provenance are testable independently from UI/SSE;
- Todd/Morgana speaker provenance is represented as event provenance without changing Personality Core;
- multiple future transports can subscribe to the same runtime bus rather than inserting themselves into agent logic;
- no Device Registry, Tool Registry, remote listener, WebSocket endpoint or durable broker is introduced early;
- process restart starts a fresh event sequence/journal while SQLite conversation persistence remains unchanged.
