"""Capability selection is independent of agents/router.py (speaker selection)."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from campanario.chat.data_intent import is_data_request


@dataclass(frozen=True, slots=True)
class BrainPlan:
    trace_id: UUID
    intent: str
    brain_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    def __post_init__(self):
        if len(self.brain_ids) > 3 or len(set(self.brain_ids)) != len(self.brain_ids):
            raise ValueError('Brain plans must contain at most three distinct brains')


class CapabilityRouter:
    """Explicit data / document intent uses deterministic routing.

    Unclear requests retain V8/V9.1 chat behavior; no speculative brain fan-out,
    recursive planning, or privileged actions. The assistant does not route speakers.
    """
    def plan(self, text: str, *, document_request=None, data_request: bool | None = None) -> BrainPlan:
        data = is_data_request(text) if data_request is None else data_request
        if document_request is not None:
            return BrainPlan(uuid4(), 'document_lookup', ('knowledge',), ('explicit_document_source',))
        if data:
            return BrainPlan(uuid4(), 'data_analysis', ('analysis',), ('deterministic_calculation',))
        return BrainPlan(uuid4(), 'conversation', (), ('no_explicit_capability_needed',))
