# ADR-0019 — Pragmatic Input Runtime Integration

## Status

Accepted — 2026-08-24.

## Context

The manual Conversational v1.4.2 gate confirmed that prompt isolation and creative->factual turn isolation work, but natural language continuations still fail when literal wording is mistaken for conversational function. Examples included colloquial acknowledgements, laughter, topic drops and uncertainty/revision being explained literally or converted into follow-up questions.

A pragmatic input foundation already existed in `chat/pragmatics.py`, intentionally disconnected from runtime until continuation-only prompting had enough manual evidence.

## Decision

Connect `PragmaticInterpreter` to `ConversationTurnInterpreter` as a deterministic pre-generation interpretation layer.

The runtime pipeline becomes:

`user input -> pragmatic acts -> TurnMode/ContinuationKind -> context/evidence -> model generation`

Pragmatic acts:

- describe what the input is doing in the conversation;
- may override literal punctuation/word meaning for social functions;
- do not select persona;
- do not decide factual truth;
- do not create memory;
- do not activate tools;
- do not require an extra LLM call;
- must not force the response to imitate the user's vocabulary.

The turn boundary exposes the detected acts and confidence to generation. Audit traces record the pragmatic acts expected for each original request.

## Priority rules

1. Safety/prompt isolation remains outside and above this layer.
2. Explicit audit mode remains highest behavior mode.
3. Pragmatic close/acknowledge/correction semantics can override literal interpretation.
4. Technical/creative/discussion/factual content classification still applies to substantive requests.
5. Social questions such as greetings with `?` remain social when their pragmatic function is social.
6. Persona remains a later response layer.

## Privacy

No private conversation corpus, identifiers, names, hashes or participant data are stored or required by the runtime. Only generalized rules and anonymized regression cases remain.

## Consequences

Positive:
- improves generalization beyond phrase-specific continuation lists;
- separates understanding from response voice;
- no additional model latency;
- creates a stable seam for future user adaptation and personas.

Trade-offs:
- deterministic pragmatics can misclassify ambiguous messages;
- confidence is advisory, not epistemic certainty;
- manual Ollama validation remains mandatory before declaring naturality solved.
