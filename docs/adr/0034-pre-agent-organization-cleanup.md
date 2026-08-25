# ADR-0034 — Pre-agent organization cleanup

## Status
Accepted.

## Context

The conversational foundation accumulated release notes, launchers, compatibility modules and version-specific manuals during v1.4-v1.6. Model bakeoff evidence showed `gemma3:12b` is a substantially stronger current baseline than `llama3:latest`, so continuing prompt patches was no longer the right next step. Agents would multiply this structural debt if introduced before cleanup.

## Decision

Before Todd/Morgana:

- keep only `README.md`, `RECOVER_FIRST.md`, `PROJECT_STATE.md`, `CAMPANARIO.bat` and project configuration at the root;
- move individual Windows launchers to `tools/windows/` and expose them through one menu;
- archive version-specific/manual-evolution documents under `docs/history/`;
- keep current operational documentation in `docs/manual/` and current engineering state in `docs/current/`;
- remove the `campanario.llm` compatibility package after migrating tests/imports to `campanario.model` and `campanario.response`;
- split `chat/behavior.py` into prompt, turn interpretation, audit and provenance modules;
- retain model family independence; `gemma3:12b` is recommended configuration, not an architectural dependency.

## Consequences

The project root and active docs become navigable, canonical package boundaries are enforceable, and the next agent layer can be added without duplicating memory/model/response infrastructure. Historical material remains available for audit but is no longer operational documentation.
