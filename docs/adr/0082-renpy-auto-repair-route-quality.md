# ADR 0082 — Ren'Py route-quality auto-repair

Date: 2026-08-26

## Decision

Preserve the approved GDD-first structure while removing editorial blockers that do not justify rejecting a production draft.

- Duplicate route titles are repaired deterministically after assembly by preserving the generated title and adding a route-specific `Eixo A/B/C` suffix.
- Duplicate route titles therefore no longer trigger a model regeneration or block compilation.
- Explicit repeated pedagogical concepts quoted in question prompts are detected cross-route. The later question is marked as the responsible validation path so only that route is regenerated.
- Route prompts explicitly prohibit reusing the same named concept as the central target of another route.
- Grounding, score/cardinality rules and pedagogical audit remain fail-closed.

This does not alter the 10-question/21-alternative GDD structure and does not advance the global roadmap gate.

## Evidence

- Ren'Py focused tests: 33/33 PASS.
- Full regression: 476/476 PASS.
- `compileall`: PASS.
