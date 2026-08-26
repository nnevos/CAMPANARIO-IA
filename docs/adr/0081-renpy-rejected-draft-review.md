# ADR 0081 — Ren'Py rejected drafts remain reviewable

## Context

A failed GDD audit previously returned an error before persisting the candidate, which prevented the user from inspecting the generated text and understanding why it failed.

## Decision

A structurally materialized GDD that fails final validation or pedagogical audit is persisted as a **rejected draft**. `GDD.docx`, `GDD.md`, `gdd.json`, `EVIDENCE_REPORT.md` and `AUDIT_REPORT.md` remain available for review. The run records `approved=false` and compilation is blocked until a new run passes validation/audit.

Uploaded ebook bytes remain temporary and are not persisted in the run or diagnostics.

## Consequences

- Rejection no longer hides useful evidence from the user.
- The UI clearly distinguishes approved GDDs from rejected drafts.
- `script.rpy` cannot be compiled from a rejected draft.
- No gate advancement; this is a Ren'Py Factory quality/workflow correction only.
