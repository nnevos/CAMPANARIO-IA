# ADR 0084 — Ren'Py choice consistency audit + surgical repair

Date: 2026-08-26
Status: Accepted

## Context

A real GDD passed the general pedagogical audit while containing an internal contradiction in route B question 2: the +2 alternative said the analysis should be discarded for incomplete information, while its justification and feedback explicitly said incompleteness does not invalidate the analysis. The full-GDD audit was too broad and could overlook a local score/text/justification/feedback contradiction.

## Decision

1. Keep the current GDD-first 10x21 structure unchanged.
2. Add a second, focused choice-consistency audit with a compact payload containing only the 10 questions, 21 choices and their evidence.
3. The focused audit must evaluate each choice against its score, justification, feedback and selected source evidence.
4. Paths such as `route_b.questions[2].choices[1]` are collapsed to the owning question (`B2`) and repaired surgically; the route is not regenerated.
5. Each question-level quality repair may retry up to three times, with the complete GDD revalidated/re-audited after each attempt.
6. Add a deterministic validator warning when the introduction claims every correct/adequate answer is worth +3; the frozen scoring contract is +3/+1/0 only for the main question and +2/0 for route questions.
7. Existing source-first grounding, rejected-draft preservation and fail-closed compilation remain unchanged.

## Consequences

The factory can now repair the class of defect observed in B2 without discarding the rest of a good GDD. The extra focused audit adds one model call to a normal successful GDD generation, trading a small latency increase for significantly stronger pedagogical consistency.

## Evidence

- Ren'Py focused suite: 37/37 PASS.
- Full regression: 480/480 PASS.
- `compileall` PASS.
