"""V9.1: typed, agent-independent record of actual source/tool output.

Document excerpts are source assertions, NOT independent proof of reality.  This
module makes no retrievals and never asks a language model to supply facts.
"""
from __future__ import annotations

from enum import StrEnum
import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from campanario.chat.fact_sheet import TurnFactSheet
from campanario.chat.local_library import LocalFactSheet
from campanario.chat.data_intent import DataAnalysisResult
from campanario.chat.zim_wikipedia import ZimFactSheet
from campanario.utilities.web_chat import ResearchResult


class AnswerMode(StrEnum):
    GROUNDED = 'grounded'
    CONVERSATIONAL = 'conversational'
    HYBRID = 'hybrid'


class VerificationStatus(StrEnum):
    VERIFIED = 'verified'
    PARTIALLY_VERIFIED = 'partially_verified'
    UNVERIFIED = 'unverified'
    NOT_FOUND = 'not_found'
    CONFLICTING = 'conflicting'
    TOOL_ERROR = 'tool_error'


class SourceRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    source_id: str = Field(min_length=1, max_length=280)
    kind: str = Field(min_length=1, max_length=60)
    title: str = Field(min_length=1, max_length=600)
    locator: str = Field(min_length=1, max_length=1000)
    excerpt: str = Field(min_length=1)
    document_id: str | None = None
    page: int | None = Field(default=None, ge=1)
    section: str | None = None


class ToolExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    operation: str = Field(min_length=1, max_length=120)
    status: str = Field(pattern=r'^(success|not_found|error)$')
    source_ids: tuple[str, ...] = ()
    read_count: int = Field(default=0, ge=0)


class CanonicalFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    fact_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    source_ids: tuple[str, ...] = ()
    critical_values: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    classification: str = Field(default='source_assertion', pattern=r'^(source_assertion|computed)$')


class CanonicalAnswer(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    request_id: UUID
    query: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    mode: AnswerMode
    status: VerificationStatus
    facts: tuple[CanonicalFact, ...] = ()
    sources: tuple[SourceRecord, ...] = ()
    tool_executions: tuple[ToolExecution, ...] = ()
    limitations: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    canonical_answer: str = Field(min_length=1)
    brain_ids: tuple[str, ...] = ()  # V9 extension: ONLY IDs supplied by a real brain router

    @model_validator(mode='after')
    def check_evidence(self):
        source_ids = {item.source_id for item in self.sources}
        fact_ids = [item.fact_id for item in self.facts]
        if len(source_ids) != len(self.sources) or len(set(fact_ids)) != len(fact_ids):
            raise ValueError('duplicate evidence or fact identifier')
        for fact in self.facts:
            if not fact.source_ids or not set(fact.source_ids).issubset(source_ids):
                raise ValueError('fact refers to missing source')
        for execution in self.tool_executions:
            if not set(execution.source_ids).issubset(source_ids):
                raise ValueError('tool refers to missing source')
        if self.status in {VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_VERIFIED}:
            if not any(item.status == 'success' and item.read_count > 0
                       for item in self.tool_executions):
                raise ValueError('supported facts require a recorded successful source read')
        if self.status == VerificationStatus.VERIFIED:
            if not self.facts or not self.sources or not any(
                item.status == 'success' for item in self.tool_executions
            ):
                raise ValueError('verified requires actual tool evidence and facts')
            if not all(fact.classification == 'computed' for fact in self.facts):
                raise ValueError('document assertions alone are not verified calculations')
        if self.status == VerificationStatus.NOT_FOUND and self.facts:
            raise ValueError('missing evidence cannot create facts')
        return self


# Critical tokens are literal: unchanged rather than interpreted by the LLM.
_CRITICAL = re.compile(r'(?:R\$\s*)?-?\d[\d.,]*(?:\s*%|\s*(?:kg|km|mL|GB|MB|reais|dias|meses|anos))?', re.I)
_CONDITIONS = re.compile(
    r'\b(?:somente\s+se|somente\s+ap[oó]s|apenas\s+se|exceto\s+quando|'
    r'at[eé]\s+o\s+limite\s+de|a\s+partir\s+de|n[aã]o\s+se\s+aplica\s+a)'
    r'[^.;\n]*', re.I,
)


def critical_values(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(token.strip() for token in _CRITICAL.findall(value)
                               if token.strip()))


def critical_conditions(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(match.group().strip() for match in _CONDITIONS.finditer(value)))


def choose_mode(query: str, sheet: TurnFactSheet, *, override: str | None = None) -> AnswerMode:
    if override is not None:
        return AnswerMode(override)
    from campanario.chat.local_library import _fold
    normalized = _fold(query)
    if re.search(r'\b(?:modo\s+)?(?:hibrido|hibrida)\b', normalized):
        return AnswerMode.HYBRID
    if re.search(r'\b(?:modo\s+)?(?:fundamentado|fundamentada)\b', normalized):
        return AnswerMode.GROUNDED
    if re.search(r'\b(?:modo\s+)?conversacional\b', normalized):
        return AnswerMode.CONVERSATIONAL
    if re.search(r'\b(?:analise|analisa|interprete|estrategia|recomende|sugira|hipotese)\b', normalized):
        return AnswerMode.HYBRID
    if sheet.status == 'not_required':
        return AnswerMode.CONVERSATIONAL
    return AnswerMode.GROUNDED


def build_canonical(sheet: TurnFactSheet, guard: object | None, *,
                    mode: AnswerMode | None = None, brain_ids: tuple[str, ...] = ()) -> CanonicalAnswer:
    """Compile once per turn from factual retrieval output (never generated prose)."""
    mode = mode or choose_mode(sheet.question, sheet)
    computed = isinstance(guard, DataAnalysisResult) and guard.status == 'grounded'
    quotes = (guard.quote,) + guard.conflicts if isinstance(guard, LocalFactSheet) else ()
    sources = tuple(SourceRecord(
        source_id=source.id, kind=source.kind, title=source.title,
        locator=source.locator, excerpt=source.excerpt,
        document_id=(quotes[i].document_id if i < len(quotes) else
                     guard.source_id if computed else None),
        page=quotes[i].page if i < len(quotes) else None,
        section=quotes[i].section if i < len(quotes) else None,
    ) for i, source in enumerate(sheet.sources))
    status_map = {
        'supported': (VerificationStatus.VERIFIED if computed else VerificationStatus.PARTIALLY_VERIFIED),
        'conflict': VerificationStatus.CONFLICTING,
        'ambiguous': VerificationStatus.CONFLICTING,
        'insufficient': VerificationStatus.NOT_FOUND,
        'unavailable': VerificationStatus.TOOL_ERROR if guard is not None else VerificationStatus.NOT_FOUND,
        'not_required': VerificationStatus.UNVERIFIED,
    }
    status = status_map[sheet.status]
    # Do not turn an arbitrary object or a claimed but unread search result into
    # a successful tool execution. The actual retrieval adapter is the proof.
    recognized_guard = isinstance(guard, (LocalFactSheet, DataAnalysisResult,
                                           ZimFactSheet, ResearchResult))
    observed_reads = max(0, int(getattr(guard, 'read_count', 0))) if recognized_guard else 0
    if sheet.status == 'supported' and (not sources or observed_reads == 0):
        status = VerificationStatus.NOT_FOUND
    facts = tuple(
        CanonicalFact(
            fact_id=f'fact_{i:03d}', statement=(sheet.extractive_answer if computed else claim.text),
            source_ids=claim.source_ids,
            critical_values=critical_values(sheet.extractive_answer if computed else claim.text),
            conditions=critical_conditions(sheet.extractive_answer if computed else claim.text),
            classification='computed' if computed else 'source_assertion',
        ) for i, claim in enumerate(sheet.claims, start=1)
    ) if status not in {VerificationStatus.NOT_FOUND, VerificationStatus.TOOL_ERROR} else ()
    if not sheet.sources:
        tool_status = 'error' if status == VerificationStatus.TOOL_ERROR else 'not_found'
    else:
        tool_status = 'success'
    tool_executions = ()
    if recognized_guard:
        tool_executions = (ToolExecution(
            operation=('data.' + guard.operation if computed else
                       'library.retrieve' if isinstance(guard, LocalFactSheet) else
                       'source.retrieve'),
            status=tool_status, source_ids=tuple(source.source_id for source in sources),
            read_count=observed_reads,
        ),)
    if sheet.extractive_answer and status != VerificationStatus.NOT_FOUND:
        answer = sheet.extractive_answer
    elif status == VerificationStatus.NOT_FOUND:
        answer = 'Não encontrei evidências suficientes na fonte solicitada para responder com segurança.'
    elif status == VerificationStatus.TOOL_ERROR:
        answer = 'A consulta à fonte não foi concluída; não posso confirmar essa informação.'
    elif status == VerificationStatus.CONFLICTING:
        answer = 'As fontes recuperadas divergem. Não é possível escolher uma conclusão sem esclarecimento.'
    elif status == VerificationStatus.PARTIALLY_VERIFIED:
        answer = 'O material recuperado apresenta informações, mas não confirma sozinho a conclusão solicitada.'
    else:
        answer = 'Não tenho uma resposta factual verificada para esta solicitação.'
    return CanonicalAnswer(
        request_id=sheet.turn_id, query=sheet.question, intent=(
            'data_analysis' if computed else 'document_lookup' if sheet.origin == 'library' else
            'source_lookup' if sheet.origin in {'web', 'zim'} else 'general_chat'),
        mode=mode, status=status, facts=facts, sources=sources,
        tool_executions=tool_executions, limitations=sheet.limitations,
        contradictions=tuple(f.statement for f in facts) if status == VerificationStatus.CONFLICTING else (),
        missing=(sheet.question,) if status == VerificationStatus.NOT_FOUND else (),
        canonical_answer=answer, brain_ids=brain_ids,
    )
