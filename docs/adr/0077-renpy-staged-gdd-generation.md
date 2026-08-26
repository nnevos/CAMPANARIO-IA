# ADR 0077 — Ren'Py Factory staged GDD generation

Date: 2026-08-26

## Context

A real subject-generation run failed on `EBOOK_4 (14).docx` because a full 10-question / 21-alternative GDD was requested as one large JSON object. JSON mode, larger context/output limits, tolerant parsing and a whole-object retry reduced but did not eliminate truncation risk on local models.

## Decision

The Ren'Py Factory no longer generates the full GDD in one model response. It uses five bounded stages:

1. metadata + character + scenario + narrative shell;
2. main question;
3. route A (3 questions);
4. route B (3 questions);
5. route C (3 questions).

Each stage:

- uses the same ebook as its only factual source;
- requests JSON mode;
- is parsed and Pydantic-validated independently;
- receives one isolated retry if its JSON is invalid;
- writes a failure diagnostic identifying the exact failed stage.

Previously generated question prompts are passed as exclusions to later routes to reduce cross-route repetition. After all five stages validate, the service assembles `RenPyGDD` deterministically and runs the existing whole-GDD grounding/score/duplication validation before any `.rpy` is compiled.

## Consequences

- A malformed/truncated route no longer forces regeneration of already valid sections.
- Model output per request is substantially smaller.
- The evidence contract is unchanged: 21 alternatives must still cite literal ebook evidence.
- GDD -> `script.rpy` remains deterministic and does not call the model.
- No change to F5/F6 gate status.

## Evidence

- Ren'Py Factory focused tests: 13/13 PASS.
- Full regression: 455/455 PASS.
- `compileall`: PASS.
