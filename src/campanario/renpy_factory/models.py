from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class EvidenceRef(BaseModel):
    quote: str = Field(min_length=8)
    source_hint: str = Field(default="")


class ChoiceSpec(BaseModel):
    text: str = Field(min_length=3)
    score: int
    justification: str = Field(min_length=3)
    feedback: str = Field(min_length=3)
    evidence: EvidenceRef


class QuestionSpec(BaseModel):
    prompt: str = Field(min_length=5)
    choices: list[ChoiceSpec]


class CharacterSpec(BaseModel):
    name: str
    role: str
    personality: str
    appearance: str
    speech_style: str
    narrative_goal: str


class ScenarioSpec(BaseModel):
    name: str
    pedagogical_function: str
    visual_description: str
    sound_description: str


class RouteSpec(BaseModel):
    title: str
    questions: list[QuestionSpec]


class FinalSpec(BaseModel):
    beginner: str = Field(min_length=5)
    proficient: str = Field(min_length=5)
    master: str = Field(min_length=5)


class QualityIssueSpec(BaseModel):
    path: str
    message: str


class QualityAuditSpec(BaseModel):
    passed: bool
    issues: list[QualityIssueSpec] = Field(default_factory=list)


class GDDMetadataSpec(BaseModel):
    title: str
    theme: str
    educational_objective: str
    character: CharacterSpec
    scenario: ScenarioSpec
    central_theme: str
    narrative_conflict: str
    finals: FinalSpec
    final_message: str
    intro_lines: list[str]
    character_intro_lines: list[str] = Field(default_factory=list)
    replay_prompt: str = Field(default="Deseja jogar novamente?")


class RenPyGDD(BaseModel):
    title: str
    theme: str
    educational_objective: str
    character: CharacterSpec
    scenario: ScenarioSpec
    central_theme: str
    narrative_conflict: str
    finals: FinalSpec
    final_message: str
    intro_lines: list[str]
    character_intro_lines: list[str] = Field(default_factory=list)
    replay_prompt: str = Field(default="Deseja jogar novamente?")
    main_question: QuestionSpec
    route_a: RouteSpec
    route_b: RouteSpec
    route_c: RouteSpec


@dataclass(frozen=True, slots=True)
class SourceSegment:
    source_id: str
    text: str


@dataclass(frozen=True, slots=True)
class ExtractedEbook:
    filename: str
    title_hint: str
    segments: tuple[SourceSegment, ...]
    normalized_text: str


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    path: str
    message: str
    severity: Literal["error", "warning"] = "error"


@dataclass(frozen=True, slots=True)
class ValidationReport:
    valid: bool
    issues: tuple[ValidationIssue, ...]
    checked_evidence: int
