# ADR 0061 — Experience / Learning Baseline v1

Status: **Accepted / F4 complete**  
Date: 2026-08-25

## Context
F3 froze one persistent Campanario Runtime shared by Web/Mobile/Call, with Todd and Morgana using the same conversation, devices, capabilities and permissions. F4 must add useful continuity without letting random conversation rewrite Personality Core, invent facts about the user or silently build an invasive profile.

## Decision
Introduce one shared `ExperienceLayer` backed by SQLite table `experience_memories`.

Each memory stores kind, subject, semantic key, value, confidence, source, status, evidence, source session/message/agent provenance, supersession lineage, confirmation/recall timestamps and recall count.

Kinds are `fact`, `preference`, `plan`, `constraint`, `shared_experience`, and `inference`. Inference remains inference and is capped below factual confidence unless explicitly corrected/confirmed.

Automatic capture is intentionally conservative and deterministic. It accepts high-confidence explicit user statements, explicit remember requests, answers to recent user-specific questions, and explicit success/failure feedback about a prior agent strategy. It does not run another LLM extractor on every turn and does not automatically persist secrets/high-risk sensitive markers.

The curiosity rule is need-based: if an answer materially depends on missing user-specific context, ask one focused question rather than guessing. Do not ask questions merely to enrich a profile; if a useful general/conditional answer is possible, answer without interrogation. A concise explicit answer to such a question may become memory with USER provenance.

New explicit evidence for the same semantic key supersedes older active evidence instead of overwriting history. Memory can be inspected, corrected and forgotten through `/api/v1/memory`. Natural conversation also recognizes a narrow explicit forget request. Recalled memory is ranked by lexical relevance, confidence and recency bias, with preferences receiving a small continuity bonus and inferences penalized.

Todd and Morgana read the same store. Relationship scopes are represented by `subject` (for example `relationship.todd.user`, `relationship.morgana.user`, or `relationship.todd.morgana`) rather than duplicate fact banks.

Personality Core remains versioned and unchanged. Experience is injected as contextual evidence plus an epistemic policy; it cannot rewrite agent profiles.

## Consequences
- cross-session learned continuity survives runtime restart;
- user-specific missing information is asked for instead of invented when it truly matters;
- curiosity stays proportional instead of becoming profile harvesting;
- explicit user corrections preserve lineage and supersede stale memory;
- inference never silently becomes fact;
- users/admins can inspect, correct and forget learned memory;
- shared outcomes can teach which approaches worked or failed;
- memory remains one Campanario resource shared by Todd and Morgana;
- F5 Realtime Presence / Call is the next roadmap gate, while F7 still owns the final development-memory clean start before real daily use.
