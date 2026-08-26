# ADR 0078 — Ren'Py Factory source-first evidence catalog

Date: 2026-08-26

## Context

Physical use of the Ren'Py Factory still produced a grounded-generation failure in `route_b`: the model could understand the ebook concept but paraphrase `evidence.quote`, causing two verbatim retries to fail. The uploaded ebook must also remain transient input and must never be persisted as a project artifact or failure diagnostic.

## Decision

Question generation is now source-first. The Factory deterministically extracts a catalog of verbatim evidence snippets from the ebook and assigns stable request-local IDs (`ev_0001`, `ev_0002`, ...). For question/route stages, the model may only select an existing `evidence.source_hint` ID and returns `USE_SOURCE_HINT` as the quote placeholder. Before Pydantic/schema validation, Campanario resolves that ID to the exact source snippet and injects the verbatim quote. Unknown IDs fail only that stage and trigger its single retry.

The ebook bytes/text are not copied into generated projects. Failure diagnostics now persist only a diagnostic ID, stage and error type; they no longer persist the upload filename, raw model responses or ebook-derived prompt/output blobs.

## Consequences

- Literal-evidence failures caused only by model paraphrasing are structurally removed.
- The model still chooses which source evidence supports each pedagogical item, but cannot author the evidence text.
- Grounding remains fail-closed: selected IDs must exist and the final GDD still passes `validate_gdd()`.
- `script.rpy` remains deterministic from the validated GDD.
- Uploaded ebooks remain transient work inputs rather than project/library assets.

## Evidence

- Ren'Py Factory focused tests: 18/18 PASS.
- Full regression: 460/460 PASS.
- `compileall`: PASS.
- F5 call remains open/paused; F6 remains blocked.
