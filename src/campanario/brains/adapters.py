"""Adapters around V8 library/data functions: never duplicate ingestion or math."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from campanario.brains.contracts import BrainDefinition, BrainRequest, BrainResult, BrainStatus, EvidenceRef
from campanario.chat.document_intent import DocumentRequest, search_document
from campanario.chat.data_intent import run_data_question


@dataclass(frozen=True)
class KnowledgeBrain:
    database: Path | None
    definition = BrainDefinition('knowledge', 'Conhecimento', ('document_lookup', 'evidence_retrieval'), installed=True)

    def health_check(self) -> tuple[bool, str]:
        return bool(self.database and self.database.is_file()), 'biblioteca local acessível' if self.database and self.database.is_file() else 'database documental ausente'

    def execute(self, request: BrainRequest) -> BrainResult:
        if 'library:read' not in request.permission_scopes:
            return BrainResult('knowledge', BrainStatus.FAILED, request.trace_id, 0, error='permission_denied')
        if not self.health_check()[0]:
            return BrainResult('knowledge', BrainStatus.UNAVAILABLE, request.trace_id, 0, warnings=('document_database_unavailable',))
        guard = search_document(self.database, DocumentRequest(request.query[:request.budget.max_input_chars], request.document_hint))
        if guard is None or guard.read_count < 1:
            return BrainResult('knowledge', BrainStatus.PARTIAL, request.trace_id, 0, operations=('library.retrieve',), warnings=('no_matching_excerpt',))
        quotes = (guard.quote, *guard.conflicts)
        refs = tuple(EvidenceRef(
            source_id=q.evidence_id or f'{q.document_id}:{q.page or 0}',
            document_id=q.document_id, title=q.name, page=q.page,
            section=q.section, excerpt=q.excerpt[:1800],
        ) for q in quotes[:request.budget.max_evidence])
        return BrainResult('knowledge', BrainStatus.COMPLETED, request.trace_id, 0, refs,
                           operations=('library.retrieve',), guard=guard)


@dataclass(frozen=True)
class AnalysisBrain:
    database: Path | None
    definition = BrainDefinition('analysis', 'Análise', ('csv', 'xlsx', 'statistics'), installed=True)

    def health_check(self) -> tuple[bool, str]:
        if not self.database or not self.database.is_file():
            return False, 'database documental ausente'
        try:
            import pandas  # noqa: F401
            import openpyxl  # noqa: F401
            return True, 'pandas e openpyxl disponíveis'
        except ImportError:
            return False, 'instale o extra [knowledge]'

    def execute(self, request: BrainRequest) -> BrainResult:
        if 'library:read' not in request.permission_scopes:
            return BrainResult('analysis', BrainStatus.FAILED, request.trace_id, 0, error='permission_denied')
        if not self.health_check()[0]:
            return BrainResult('analysis', BrainStatus.UNAVAILABLE, request.trace_id, 0, warnings=('analysis_dependencies_or_database_missing',))
        guard = run_data_question(self.database, request.query[:request.budget.max_input_chars])
        if guard.status != 'grounded' or guard.read_count < 1 or not guard.source_id:
            return BrainResult('analysis', BrainStatus.PARTIAL, request.trace_id, 0,
                               operations=('data.inspect',), warnings=(guard.verified_answer[:500],), guard=guard)
        evidence = EvidenceRef(
            source_id=f'analysis:{guard.source_id}:{guard.digest[:16]}', document_id=guard.source_id,
            title=guard.source_name, excerpt=guard.evidence_excerpt[:1800])
        return BrainResult('analysis', BrainStatus.COMPLETED, request.trace_id, 0,
                           (evidence,), operations=('data.inspect', 'data.' + guard.operation), guard=guard)
