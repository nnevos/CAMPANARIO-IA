# ADR 0050 — Runtime Persistent Boundary (PF1)

## Status
Accepted for F3 / PF1 implementation.

## Context
The pre-F3 composition root built `ChatService` directly for FastAPI/E2E, and `bootstrap.get_chat_service()` made the web/API hosting path the visible application boundary. Platform Foundation requires Campanario itself to exist independently from any client surface.

## Decision
Introduce a logical `CampanarioRuntime` boundary that owns the shared conversation service and client-independent session facade. `build_runtime()` becomes the canonical runtime composition root; FastAPI remains a client/host adapter and its legacy `get_chat_service()` accessor delegates to the runtime for incremental compatibility.

Add explicit interfaces for `RuntimeState`, `ConversationService`, `SessionManager`, `AgentRuntime`, `ToolRuntime` and `DeviceRuntime`. PF1 does **not** create a Windows service, tray process, Event Bus, device/tool registry or remote listener yet.

## Consequences
- runtime can be composed and maintain sessions without importing/starting FastAPI or opening the Web UI;
- API and E2E can migrate incrementally without a big-bang rewrite;
- Todd/Morgana, repositories, provider and conversation state remain single/shared;
- native process persistence remains a later hosting decision after the logical boundary stabilizes.
