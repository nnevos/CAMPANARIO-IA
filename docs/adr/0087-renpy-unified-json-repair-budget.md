# ADR 0087 — Unified JSON Repair Budget for Ren'Py Factory

Date: 2026-08-26
Status: Accepted

## Context

A real multi-unit run reached a surgical C3 repair and failed with `route_c_q3_surgical_repair_1` after only two malformed-JSON attempts. This contradicted ADR 0086: the outer convergence loop allowed eight local attempts, but hidden inner JSON-producing helpers still used the old two-attempt default.

## Decision

All question-level surgical repair calls now pass `MAX_STAGE_ATTEMPTS` explicitly. The same retry budget is used by the general pedagogical audit and the choice-consistency audit. Retry prompts ask for minimal JSON-only output after the first malformed response.

The whole-route JSON block intentionally remains limited to two attempts because its designed recovery path is better: after two failures the factory decomposes the route into three independently generated questions, each with the expanded retry budget.

## Result

A recoverable malformed JSON response inside A1/B2/C3 repair no longer terminates a unit after two attempts. The factory can recover later in the same surgical repair and record that recovery in `repair_history`.

## Evidence

- focused Ren'Py Factory tests: 44/44 PASS;
- new regression proves a surgical C3 repair can fail JSON four times and recover on the fifth;
- full regression: 487/487 PASS;
- `compileall`: PASS.

No roadmap gate advancement. Ebook inputs remain transient and are never persisted.
