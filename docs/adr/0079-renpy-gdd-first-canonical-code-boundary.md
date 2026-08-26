# ADR 0079 — Ren'Py Factory GDD-first canonical code boundary

Date: 2026-08-26

## Context

Physical use of the Factory showed that automating subject/workspace/images/Web build before the core artifact contract was trustworthy made failures hard to diagnose. The production workflow historically treats the GDD as the reference artifact and then derives `script.rpy` from it. The user also provided canonical Ren'Py `screens.rpy` and `options.rpy` files whose changes are minimal and should not be re-authored by the model.

## Decision

The Factory is reduced to two explicit stages until this core is approved:

1. **Ebook -> GDD**: generate, ground and expose `GDD.docx`, `GDD.md` and `gdd.json`. The production GDD follows the 10-question/21-alternative structure and includes the three narrative endings plus a complete Section 7 Ren'Py code block.
2. **Approved GDD -> code**: compile `script.rpy` deterministically from the persisted `gdd.json`. The exact script text embedded in GDD Section 7 is produced by the same compiler, so GDD and `script.rpy` are directly comparable and cannot drift through a second LLM call.

`screen.rpy` is not generated: the canonical `screens.rpy` is copied byte-for-byte from the user's template. `options.rpy` starts from the same canonical template and changes only `config.name`, `build.name` and `config.save_directory`; `config.version` stays `1.0` unless a future explicit requirement changes it.

Evidence citations remain in `EVIDENCE_REPORT.md`/`gdd.json`, not in the production-facing GDD body, so the GDD matches the user's normal format while retaining auditability separately.

Subject multi-unit orchestration, image workflow and Web build remain implemented code paths but are deliberately removed from the active Factory UI until the GDD/script contract is accepted.

## Consequences

- GDD becomes the visible canonical artifact instead of an internal intermediate.
- The exact `script.rpy` can be compared inside `GDD.docx`/`GDD.md` before downloading/using the compiled project.
- No model can invent a second version of the code after GDD approval.
- `screens.rpy` and nearly all of `options.rpy` remain stable template infrastructure.
- Existing ebook transient-input/source-first evidence rules remain unchanged.

## Evidence

- Ren'Py Factory focused tests: 20/20 PASS.
- Full regression: 462/462 PASS.
- Canonical template check: `screens.rpy` and `options.rpy` match the supplied UN01 reference before the three allowed options substitutions.
- F5 call remains open/paused; F6 remains blocked.
