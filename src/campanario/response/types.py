from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum

class ResponseKind(StrEnum):
    OPEN = "open"
    GREETING = "greeting"
    REACTION = "reaction"
    ACKNOWLEDGEMENT = "acknowledgement"
    TOPIC_DROP = "topic_drop"
    CONTEXT_REGISTRATION = "context_registration"
    CORRECTION = "correction"
    SELF_AWARE = "self_aware"
    TRUTH_DISCUSSION = "truth_discussion"
    TECHNICAL_FIRST_STEP = "technical_first_step"
    FACTUAL = "factual"
    CREATIVE_EXACT = "creative_exact"
    CREATIVE = "creative"
    SOCIAL_SHARE = "social_share"


@dataclass(frozen=True, slots=True)
class ResponseContract:
    kind: ResponseKind = ResponseKind.OPEN
    max_words: int | None = None
    exact_sentences: int | None = None
    max_sentences: int | None = None
    prohibit_question: bool = False
    prohibit_reaction_explanation: bool = False
    prohibit_simulated_laughter: bool = False
    prohibit_embodied_expression: bool = False
    prohibit_meta_preamble: bool = False
    prohibit_reassurance_formula: bool = False
    semantic_acknowledgement: bool = False
    semantic_greeting: bool = False
    semantic_social_share: bool = False
    semantic_topic_drop: bool = False
    preserve_campanario_identity: bool = False
    require_user_language: bool = False
    truth_over_agreement: bool = False
    semantic_context_registration: bool = False
    technical_first_step: bool = False

    @property
    def active(self) -> bool:
        return any(
            value not in (None, False)
            for value in (
                self.max_words,
                self.exact_sentences,
                self.max_sentences,
                self.prohibit_question,
                self.prohibit_reaction_explanation,
                self.prohibit_simulated_laughter,
                self.prohibit_embodied_expression,
                self.prohibit_meta_preamble,
                self.prohibit_reassurance_formula,
                self.semantic_acknowledgement,
                self.semantic_greeting,
                self.semantic_social_share,
                self.semantic_topic_drop,
                self.preserve_campanario_identity,
                self.require_user_language,
                self.truth_over_agreement,
                self.semantic_context_registration,
                self.technical_first_step,
            )
        )


@dataclass(frozen=True, slots=True)
class ContractViolation:
    code: str
    detail: str

