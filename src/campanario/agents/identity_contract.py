"""Immutable agent identities: the core is authored, development is reviewed.

Agent identity describes a conversational role, not verified sentience or a human life.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentIdentity:
    id: str
    name: str
    version: str
    self_description: str
    individuality: tuple[str, ...]
    relational_intent: str
    development_contract: tuple[str, ...]

    def render_prompt(self) -> str:
        return (
            self.self_description + "\n"
            + "INDIVIDUALIDADE INICIAL (TENDENCIAS, NAO LIMITES):\n"
            + "\n".join(f"- {item}" for item in self.individuality)
            + "\nRELACOES E CONTINUIDADE:\n" + self.relational_intent
            + "\nDESENVOLVIMENTO CONTROLADO:\n"
            + "\n".join(f"- {item}" for item in self.development_contract)
        )
