from __future__ import annotations

import random

from .agent_scenarios import (
    _build_agent_integrated_scenarios,
    _build_agent_long_call_scenarios,
    _build_agent_personality_scenarios,
    _build_agent_scenarios,
)
from .standard_scenarios import build_standard_scenarios
from .human_scenarios import build_human_conversation_scenarios
from .types import ScenarioSpec


def _clone_for_batch(scenario: ScenarioSpec, suffix: str) -> ScenarioSpec:
    return ScenarioSpec(
        id=f"{scenario.id}{suffix}",
        category=scenario.category,
        description=scenario.description,
        turns=scenario.turns,
        review_focus=scenario.review_focus,
        agent_id=scenario.agent_id,
    )


def build_scenarios(seed: int, suite: str = "standard") -> list[ScenarioSpec]:
    """Build a requested E2E suite while keeping suite implementations modular.

    The public entry point remains stable. A seed determines wording and ordering, so existing
    reports stay reproducible after the structural refactor.
    """
    if suite == "agents":
        return _build_agent_scenarios(seed)
    if suite == "agent_integrated":
        return _build_agent_integrated_scenarios(seed)
    if suite == "agent_long_call":
        return _build_agent_long_call_scenarios(seed)
    if suite == "agent_personality":
        return _build_agent_personality_scenarios(seed)
    if suite == "agent_human_quick":
        return build_human_conversation_scenarios(seed, quick=True)
    if suite == "agent_human_baseline":
        return build_human_conversation_scenarios(seed, quick=False)

    if suite == "agent_mega":
        combined: list[ScenarioSpec] = []
        for batch in range(8):
            derived_seed = seed + (batch * 65537)
            combined.extend(
                _clone_for_batch(scenario, f"__agentmega{batch + 1}")
                for scenario in _build_agent_personality_scenarios(derived_seed)
            )
        random.Random(seed ^ 0xA63E17).shuffle(combined)
        return combined

    if suite == "mega":
        combined: list[ScenarioSpec] = []
        for batch in range(6):
            derived_seed = seed + (batch * 104729)
            combined.extend(
                _clone_for_batch(scenario, f"__mega{batch + 1}")
                for scenario in build_standard_scenarios(derived_seed, "full")
            )
        random.Random(seed ^ 0xC0FFEE).shuffle(combined)
        return combined

    return build_standard_scenarios(seed, suite)
