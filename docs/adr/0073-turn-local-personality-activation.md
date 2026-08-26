# ADR 0073 — Turn-local Personality Activation

## Status
Accepted as a personality-quality refinement while F5 Call remains open/deferred.

## Context
Todd and Morgana already have a frozen Personality Core with distinct reasoning priorities. In the active runtime, however, that contract is a long static block placed before more compact and imperative `DialogueState`, participation guidance and `AnswerContract`. Physical voice testing made the effect visible: factual answers were acceptable, but open/social answers could converge toward a generic assistant style.

The problem is not lack of traits in `profiles.py`; it is salience at generation time. Adding catchphrases or hard-coded answers would violate the personality concept and would overfit tests.

## Decision
Keep `PersonalityCore` as the single stable source of identity and add a deterministic `PersonalityApplication` layer that activates the most relevant existing priorities for the current `TurnInterpretation`.

The application layer:

- is derived from the current agent plus deterministic turn/pragmatic interpretation;
- changes perspective, prioritization and participation, never facts, tools, memory or evidence;
- is appended near generation time, after participation/voice notes and before the final `AnswerContract`;
- explicitly keeps personality light on simple factual turns;
- strengthens distinct behavior on technical, creative, social and discussion turns;
- contains anti-caricature guidance so Todd does not become permanent risk/checklist mode and Morgana does not become permanent framework/essay mode;
- never contains benchmark answers or catchphrases.

Voice guidance is also changed so "spoken naturality" cannot flatten both agents into the same generic concise style. Voice still controls delivery length and spoken formatting, but persona owns conversational character.

## Consequences
The same factual core and answer obligation remain shared, while Todd should more consistently expose action/trade-off/reversibility and Morgana context/criteria/relationships when those differences are useful. Convergence remains correct on simple factual questions.

This ADR does not close F5 and does not open F6. It resumes a documented personality-quality debt without changing the gate order.
