# ADR 0045 — Answer Contract binding after Dialogue State

## Status

Accepted for P2.4.1 validation.

## Context

The P2.4 Long Call revalidation (`agent_long_call`, seed `1787680836`) finished with 244 PASS / 12 WARN / 0 FAIL. The typed `DialogueStateCompiler` improved structure, but the model could still treat the resolved state as descriptive background rather than as the exact obligation of the current answer. Examples included asking again for the question in `mesma pergunta`, losing `aterrissa isso`, answering a generic methodology instead of the requested short latency sequence, and drifting from user-owned product choices.

## Decision

Introduce a separate, deterministic `AnswerContract` derived from `DialogueState`.

The contract is appended to the system message **after** persona, Social Protocol, speaker-output rules and participation notes. It contains:

- exact resolved request;
- already-resolved subject/referent;
- immediately relevant evidence when needed;
- lightweight topical anchors for critical bindings;
- explicitly forbidden meta/role detours for product decisions;
- `no clarification` when the necessary referent already exists;
- `no new question` for acknowledgement/closure turns.

Critical contract properties are validated locally after generation. If the model asks for already-resolved context, loses the required subject, enters a forbidden meta-topic, or opens a new question on closure, the runtime performs one local regeneration with the same contract. This is not a second interpretive model call: no model is used to infer dialogue state or judge semantics.

## Consequences

- Dialogue interpretation and answer obligation become separate runtime boundaries.
- Personality Core remains untouched.
- No persistent memory is added.
- No provider/model lock-in is introduced.
- Some turns may pay one retry when Gemma ignores a critical binding; latency must continue to be measured in Long Call.
- The E2E gate treats reference/answer-binding failures as hard failures where the expected referent is objectively available; creative participation-count differences remain contextual/WARN-only.
