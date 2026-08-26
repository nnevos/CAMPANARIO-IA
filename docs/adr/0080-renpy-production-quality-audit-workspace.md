# ADR 0080 — Ren'Py Factory production-quality audit + dedicated workspace

Date: 2026-08-26
Status: Accepted as a quality refinement inside the Ren'Py production workstream. Does not close F5 or open F6.

## Context

Physical review of a generated Linux GDD/script against the user's production references exposed a gap that schema validation and literal grounding did not catch. The generated GDD could be structurally valid and fully grounded while still containing pedagogical defects: an adequate choice contradicted its own evidence, feedback used mechanical labels forbidden by the GDD, the opening read like generic marketing, the character recited metadata fields as dialogue, and finals overclaimed mastery beyond what the questions measured.

The previous UI also exposed the Factory as a narrow side panel, which made production state and review gates hard to understand.

## Decision

1. Keep GDD-first as the canonical boundary: ebook -> GDD -> deterministic script.
2. Add a source-grounded `QualityAuditSpec` after the staged GDD is assembled.
3. The audit explicitly checks score/choice/evidence consistency, true partial adequacy, choice/justification/feedback contradictions, mechanical feedback labels/emojis, topical repetition, route coherence, fictional-character requirement, opening quality and final overclaiming.
4. If the audit rejects content, only the affected stage (metadata, main question, route A/B/C) is regenerated with the audit findings. The assembled GDD is audited again; a second failure is fail-closed.
5. Deterministic quality warnings (opening length, character-introduction length, repeated route titles/choices, mechanical/too-short feedback) are merged into the same repair path.
6. Metadata now carries `character_intro_lines` and `replay_prompt`. `script.rpy` uses these approved narrative lines instead of speaking raw role/narrative-goal fields.
7. `screens.rpy` remains the canonical template; `options.rpy` keeps minimal mutation only.
8. The Factory is a dedicated top-level workspace/tab mirroring the Campanario application's visual language, with visible Source -> GDD -> Audit -> Code gates. Compilation remains disabled until the GDD/audit stage succeeds.
9. Uploaded ebooks remain transient and are not persisted in project artifacts or diagnostics.

## Consequences

- Generation uses one additional model audit, plus targeted repair calls only when needed.
- A valid JSON/evidence report is no longer presented as production-ready by itself.
- The user can see which production gate has been reached before downloading artifacts.
- Images, multi-unit workflow and Web Build remain paused until GDD/script quality is accepted.

## Evidence

- Focused Ren'Py Factory suite: 22/22 PASS.
- Full regression: 464/464 PASS.
- `compileall`: PASS.
