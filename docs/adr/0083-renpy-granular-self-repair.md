# ADR 0083 — Ren'Py Factory granular self-repair

Date: 2026-08-26

## Context

The route-quality validator could identify an exact duplicated/reused question such as `route_c.questions[3]`, but the repair path could still regenerate too much or accept a first repair that repeated the same concept again. This created avoidable rejected drafts even though the validator already knew the precise field that was wrong.

## Decision

Treat exact question-level validation paths as repair instructions. For cross-route duplicate questions and repeated explicit concepts, repair only the offending question. The factory rebuilds the current exclusion list and forbidden-concept list from every other accepted question, asks for only that one `QuestionSpec`, then revalidates the complete GDD immediately. If the same question still collides, retry that same question up to three times, feeding the newest validator messages into the next attempt. No other question or route is regenerated.

If the item is still invalid after the bounded repair loop, the existing rejected-draft behavior remains fail-closed and preserves the GDD/AUDIT_REPORT for human review.

## Consequences

- A defect in C3 no longer regenerates C1/C2 or route C as a whole.
- The first bad repair does not silently pass; full-bank validation runs after every surgical attempt.
- Source-first evidence, score/cardinality rules and pedagogical audit remain unchanged.
- Ebook uploads remain transient and are never persisted with the run.
- No roadmap gate advancement.

## Evidence

- Focused Ren'Py Factory suite: 35/35 PASS.
- Full regression: 478/478 PASS.
- `python -m compileall -q src`: PASS.
