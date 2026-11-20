"""Installed V9 brains and honest descriptions for future capabilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from campanario.brains.adapters import KnowledgeBrain, AnalysisBrain
from campanario.brains.contracts import Brain, BrainDefinition

_FUTURE = (
    ('investigation', 'Investigação'), ('programming', 'Programação'),
    ('strategy', 'Estratégia'), ('perception', 'Percepção'),
    ('communication', 'Comunicação'), ('creation', 'Criação'),
)


@dataclass
class BrainRegistry:
    _brains: dict[str, Brain]

    @classmethod
    def local(cls, library_path: Path | None) -> 'BrainRegistry':
        return cls({'knowledge': KnowledgeBrain(library_path), 'analysis': AnalysisBrain(library_path)})

    def get(self, brain_id: str) -> Brain | None:
        return self._brains.get(brain_id)

    def catalog(self) -> list[dict]:
        out = []
        for brain in self._brains.values():
            healthy, reason = brain.health_check()
            d = brain.definition
            out.append({'brain_id': d.brain_id, 'display_name': d.display_name,
                        'capabilities': list(d.capabilities), 'installed': True,
                        'status': 'ready' if healthy else 'unavailable', 'health': reason,
                        'version': d.version})
        for brain_id, name in _FUTURE:
            out.append({'brain_id': brain_id, 'display_name': name,
                        'capabilities': [], 'installed': False,
                        'status': 'unavailable', 'health': 'sem execução implementada', 'version': None})
        return out
