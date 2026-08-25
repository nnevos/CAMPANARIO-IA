from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class CheckSpec:
    kind: str
    value: object | None = None
    severity: str = "fail"
    label: str = ""


@dataclass(frozen=True, slots=True)
class TurnSpec:
    user: str
    checks: tuple[CheckSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    id: str
    category: str
    description: str
    turns: tuple[TurnSpec, ...]
    review_focus: str


@dataclass(slots=True)
class CheckResult:
    label: str
    status: str
    detail: str


@dataclass(slots=True)
class TurnResult:
    user: str
    assistant: str = ""
    error: str | None = None
    duration_seconds: float = 0.0
    checks: list[CheckResult] = field(default_factory=list)


@dataclass(slots=True)
class ScenarioResult:
    id: str
    category: str
    description: str
    review_focus: str
    turns: list[TurnResult] = field(default_factory=list)
    status: str = "PASS"


@dataclass(slots=True)
class RunReport:
    generated_at: str
    model: str
    base_url: str
    seed: int
    suite: str
    scenarios: list[ScenarioResult]
    summary: dict[str, object]

