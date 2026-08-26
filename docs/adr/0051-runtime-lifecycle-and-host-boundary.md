# ADR 0051 — Runtime Lifecycle and Host Boundary (PF1b)

## Status
Accepted for F3 / PF1b implementation.

## Context
PF1a separated the logical `CampanarioRuntime` from FastAPI/Web composition, but runtime construction still implied an already-running instance and the API consumed the legacy `get_chat_service()` compatibility facade. There was no explicit owner for process lifecycle and no headless hosting proof independent from FastAPI.

## Decision
Add an explicit runtime lifecycle (`start`, `stop`, running/stopped state) and a transport-agnostic `RuntimeHost` that owns exactly one active runtime per process. `build_runtime()` remains backward-compatible with `autostart=True`, while hosts can compose with `autostart=False` and own startup explicitly.

FastAPI lifespan now starts/stops the process-local `RuntimeHost`, and API handlers resolve the runtime boundary directly through `get_runtime()` before accessing `runtime.conversation`. `get_chat_service()` remains only as a legacy compatibility accessor.

Add a plain Python headless process entrypoint (`campanario-runtime`) to prove that Campanario can remain alive without browser/FastAPI. This is **not** a Windows service, tray application, remote gateway or second Campanario instance. Until the Realtime Gateway exists, Web hosting and headless hosting are alternative process hosts, not two simultaneously connected clients.

## Consequences
- browser lifecycle is no longer conceptually tied to runtime lifecycle;
- repeated client/API access inside one host process resolves the same runtime identity;
- stopping and restarting a host creates a fresh runtime process identity while persisted sessions remain in the shared database;
- API/runtime dependency is explicit and testable;
- native service, Event Bus and network transport remain deferred to later gates;
- Personality / Social / Long-Call Baseline v1 is unchanged.
