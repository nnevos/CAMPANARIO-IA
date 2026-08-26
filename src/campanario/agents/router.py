from __future__ import annotations

from dataclasses import dataclass
import re

from campanario.agents.addressing import directly_addressed_agent, fold_text
from campanario.agents.profiles import AgentProfile, AgentRegistry


@dataclass(frozen=True, slots=True)
class AgentResolution:
    """Primary-speaker resolution for one user turn.

    The resolved profile gets first response priority. It is not an exclusive lock:
    other registered participants remain present and may join through the participation arbiter.
    """

    profile: AgentProfile
    source: str
    persist_primary: bool = False

    @property
    def persist_selection(self) -> bool:  # compatibility with v1.1 callers/tests
        return self.persist_primary




class AgentRouter:
    """Resolve first-speaker priority without making other agents unavailable.

    Campanario is the system wake/name, never a persona. Morgana is the default primary
    speaker. Directly addressing Todd or Morgana changes who has priority for subsequent
    turns, while both remain participants in the shared conversational space.
    """

    _DIRECT = re.compile(r"^(todd|morgana)(?:\b|\s*[:,.!?-])", re.IGNORECASE)
    _SYSTEM = re.compile(r"^campanario(?:\b|\s*[:,.!?-])", re.IGNORECASE)

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def resolve(self, text: str, current_primary_agent_id: str | None) -> AgentResolution:
        folded = fold_text(text)
        if self._SYSTEM.match(folded):
            wake_prefix = folded[:200]
            for agent_id in ("morgana", "todd"):
                if re.search(rf"\b{agent_id}\b", wake_prefix):
                    profile = self._registry.get(agent_id)
                    return AgentResolution(
                        profile=profile,
                        source="system_wake_explicit_agent",
                        persist_primary=True,
                    )
            profile = self._registry.get(current_primary_agent_id)
            return AgentResolution(profile=profile, source="system_wake_primary")

        direct_agent = directly_addressed_agent(text)
        if direct_agent:
            profile = self._registry.get(direct_agent)
            return AgentResolution(profile=profile, source="direct_agent_wake", persist_primary=True)

        profile = self._registry.get(current_primary_agent_id)
        return AgentResolution(profile=profile, source="session_primary")
