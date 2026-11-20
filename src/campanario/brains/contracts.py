"""V9 shared capability contracts; a brain is not an agent or a separate LLM."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable, Protocol
from uuid import UUID, uuid4


class BrainStatus(StrEnum):
    UNAVAILABLE = 'unavailable'
    READY = 'ready'
    RUNNING = 'running'
    COMPLETED = 'completed'
    PARTIAL = 'partial'
    FAILED = 'failed'


@dataclass(frozen=True, slots=True)
class ResourceBudget:
    timeout_seconds: float = 8.0
    max_evidence: int = 8
    max_input_chars: int = 1200
    max_memory_mb: int = 1024

    def __post_init__(self):
        if not 0.1 <= self.timeout_seconds <= 60 or not 1 <= self.max_evidence <= 25 or not 1 <= self.max_input_chars <= 12000 or not 128 <= self.max_memory_mb <= 4096:
            raise ValueError('Invalid resource budget')


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    source_id: str
    document_id: str | None
    title: str
    excerpt: str
    page: int | None = None
    section: str | None = None

    def __post_init__(self):
        if not self.source_id or not self.title or not self.excerpt or (self.page is not None and self.page < 1):
            raise ValueError('Evidence requires a real source, title and excerpt')


@dataclass(frozen=True, slots=True)
class BrainRequest:
    request_id: UUID
    conversation_id: UUID | None
    query: str
    intent: str
    document_hint: str = ''
    budget: ResourceBudget = field(default_factory=ResourceBudget)
    permission_scopes: frozenset[str] = frozenset({'library:read'})
    trace_id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True, slots=True)
class BrainResult:
    brain_id: str
    status: BrainStatus
    trace_id: UUID
    elapsed_ms: float
    evidence_refs: tuple[EvidenceRef, ...] = ()
    operations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    error: str | None = None
    # Internal adapter result; never accept this from the language model or client.
    guard: Any = field(default=None, repr=False, compare=False)

    def public(self) -> dict:
        return {'brain_id': self.brain_id, 'status': self.status.value,
                'trace_id': str(self.trace_id), 'elapsed_ms': self.elapsed_ms,
                'evidence_count': len(self.evidence_refs), 'operations': list(self.operations),
                'warnings': list(self.warnings), 'error': self.error,
                'evidence_refs': [
                    {'source_id': s.source_id, 'document_id': s.document_id,
                     'title': s.title, 'page': s.page, 'section': s.section}
                    for s in self.evidence_refs]}


@dataclass(frozen=True, slots=True)
class BrainDefinition:
    brain_id: str
    display_name: str
    capabilities: tuple[str, ...]
    version: str = '9.0'
    permission_scopes: frozenset[str] = frozenset({'library:read'})
    installed: bool = False
    unavailable_reason: str | None = None


class Brain(Protocol):
    definition: BrainDefinition

    def health_check(self) -> tuple[bool, str]: ...
    def execute(self, request: BrainRequest) -> BrainResult: ...
