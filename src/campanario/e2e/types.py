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
    agent_id: str | None = None


@dataclass(slots=True)
class CheckResult:
    label: str
    status: str
    detail: str


@dataclass(slots=True)
class SpeakerResult:
    agent_id: str
    text: str = ""
    reason: str | None = None
    start_offset_seconds: float | None = None
    first_response_offset_seconds: float | None = None
    generation_seconds: float | None = None


@dataclass(slots=True)
class TurnResult:
    user: str
    assistant: str = ""
    speaker_id: str | None = None
    error: str | None = None
    duration_seconds: float = 0.0
    time_to_first_response_seconds: float | None = None
    second_speaker_gap_seconds: float | None = None
    checks: list[CheckResult] = field(default_factory=list)
    speakers: list[SpeakerResult] = field(default_factory=list)


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

