# ADR 0049 — Personality / Social / Long-Call Baseline v1 Freeze

## Status
Accepted — F2 frozen on 2026-08-25.

## Evidence
The P2.4.4 Long Call revalidation (`agent_long_call`, seed `1787683779`, Gemma 3 12B) completed 36 turns with **253 PASS / 2 WARN / 0 FAIL**, scenarios **2 PASS / 1 WARN / 0 FAIL**. Local regression after the freeze-gate fixes was 335/335.

Human review accepts the two WARNs as contextual rather than structural: the prompt `discordem de mim se precisarem` is conditional, and Todd supplied the useful dissent without requiring Morgana to manufacture a second disagreement. Speaker provenance, factual correction, binding, continuity, closure and anti-overtalk remained green.

## Decision
Freeze **Personality / Social / Long-Call Baseline v1** at P2.4.4. Personality Core, Social Protocol v1, Dialogue State/Answer Contract and the existing participation semantics are now regression baselines, not active tuning targets.

F3 **Platform Foundation / Runtime v2** is released as the next gate. Any later change that alters the frozen conversational behavior requires explicit regression evidence and an ADR rather than incidental platform work.
