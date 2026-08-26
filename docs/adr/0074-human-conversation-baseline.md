# ADR 0074 — Human Conversation Baseline

## Status
Accepted as a quality-evaluation instrument. It does not close F5 and does not open F6.

## Context
After ADR 0073 increased turn-local personality salience, the project still lacked a dedicated way to judge ordinary human conversation: getting to know the user, casual stories, humor, topic shifts, callbacks, light disagreement, selective silence and the desire to keep talking. Existing suites were stronger at technical invariants, personality axes and long-call mechanics than at day-to-day relational naturalness.

## Decision
Add two Behavioral E2E suites:

- `agent_human_quick`: 5 persistent episodes / 40 turns.
- `agent_human_baseline`: 10 persistent episodes / 80 turns.

Four full-baseline themes run as literal Todd × Morgana pairs with identical user turns: getting-to-know, daily continuity, casual disagreement and story/follow-up. Two additional shared-room episodes run Todd and Morgana together through the real multi-agent runtime.

Automatic checks remain limited to observable invariants such as proportionality, prompt leakage, embodied role-play, institutional/robotic phrasing, contextual recall and output boundaries. Naturalness itself remains human-reviewed.

Every human-baseline run additionally emits `blind_review.md`: Todd/Morgana labels are hidden in paired transcripts until a final answer key. The reviewer scores naturalness, continuity, proportional curiosity, absence of lecture/interrogation, contextual memory, personality consistency and desire to continue the conversation.

## Non-goals
- No benchmark-specific response hardcoding.
- No automatic claim that a regex can prove human naturalness.
- No Personality Core rewrite in this ADR.
- No change to F5 voice/call status or F6 gate.

## Evidence
- Focused behavioral/layout/reporting tests: 61/61 PASS.
- Full regression: 442/442 PASS.
- `compileall`: PASS.

## Next evidence
Run `tools/windows/TESTAR_CONVERSA_HUMANA.bat` with the target local model and review `latest.blind.md` before reading the labeled report. Use transcript evidence to decide whether ADR 0073 needs calibration; do not tune personas from a single lexical miss.
