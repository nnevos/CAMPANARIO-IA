"""First-party read-only investigation and conditional strategy over retrieved excerpts.

Not semantic inference or proof. Each observed claim is a literal source excerpt.
The process sandbox/network restrictions are inherited from the V9 worker.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import re

from campanario.brains.contracts import BrainDefinition, BrainRequest, BrainResult, BrainStatus, EvidenceRef
from campanario.chat.document_intent import DocumentRequest, search_document
from campanario.chat.canonical_answer import SourceRecord
from campanario.chat.evidence_reconciliation import reconcile_numeric_evidence


def structured_report(kind: str, refs: tuple[EvidenceRef, ...]) -> tuple[str, ...]:
    """Derive a reproducible plan/review, never an uncited new fact."""
    if kind not in ('investigation', 'strategy') or not refs:
        return ()
    sources = [SourceRecord(source_id=r.source_id, kind='imported_document',
                            title=r.title, locator=r.title, excerpt=r.excerpt,
                            document_id=r.document_id, page=r.page, section=r.section)
               for r in refs[:8]]
    conflicts = reconcile_numeric_evidence(sources)
    independent = len({r.document_id or r.source_id for r in refs[:8]})
    if kind == 'investigation':
        lines = ['INVESTIGAÇÃO — alegações extraídas, não fatos externos confirmados',
                 f'Cobertura observada: {len(refs[:8])} trecho(s) recuperado(s), '
                 f'{independent} documento(s)/origem(ns) distinta(s). Isto não é cobertura total da biblioteca.']
        for ref in refs[:8]:
            lines.append(f'Fonte [{ref.source_id}] ({ref.title}): {ref.excerpt[:400]}')
        # Dates are literal strings observed in a quote; they are NOT evidence
        # that an event happened on that date or that chronology is complete.
        dates: set[tuple[str, str]] = set()
        for ref in refs[:8]:
            for literal in re.findall(r'(?<!\d)\d{2}/\d{2}/\d{4}(?!\d)', ref.excerpt[:1800]):
                try:
                    datetime.strptime(literal, '%d/%m/%Y')
                except ValueError:
                    continue
                dates.add((literal, ref.source_id))
        for date, source_id in sorted(dates, key=lambda item: (item[0][6:], item[0][3:5], item[0][:2]))[:4]:
            lines.append(f'Data mencionada [{source_id}]: {date} (evento/contexto não inferidos).')
        for c in conflicts:
            lines.append(f'DIVERGÊNCIA NUMÉRICA a verificar entre [{c.source_ids[0]}] e [{c.source_ids[1]}]: {c.values[0]} / {c.values[1]}')
        lines.append('Hipóteses: não confirmadas; exigir novas fontes independentes antes de concluir causa, intenção ou responsabilidade.')
        lines.append('Lacunas: confirmar autenticidade, data e contexto das fontes; ausência de contradição detectada não prova concordância.')
        return tuple(lines[:20])
    lines = ['ESTRATÉGIA — plano condicional baseado nas fontes, não execução autorizada',
             f'Base disponível: {len(refs[:8])} trecho(s), {independent} documento(s)/origem(ns) recuperados.',
             '1. Definir o objetivo e o critério de sucesso com o usuário.']
    lines.extend(f'2. Verificar a alegação de [{r.source_id}] ({r.title}) antes de tomar decisões.'
                 for r in refs[:8])
    if conflicts:
        lines.append('Risco BLOQUEANTE: valores numéricos conflitantes em fontes independentes; '
                     'não escolher cenário até verificar a divergência.')
    lines += ['3. Comparar alternativas somente após confirmar custos, prazos e restrições com fontes verificáveis.',
              '4. Registrar riscos, responsáveis e dependências; solicitar aprovação humana antes de qualquer ação.',
              'Critério de parada: fonte insuficiente, contradição não resolvida ou falta de permissão.',
              'Nenhuma ação foi executada; o plano não estabelece que uma alternativa é melhor sem dados comparativos.']
    return tuple(lines[:20])


@dataclass(frozen=True)
class InvestigationBrain:
    database: Path | None
    definition = BrainDefinition('investigation', 'Investigação', ('source_investigation', 'evidence_gaps', 'numeric_disagreements'), installed=True)

    def health_check(self) -> tuple[bool, str]:
        ok = bool(self.database and self.database.is_file())
        return ok, 'biblioteca local acessível' if ok else 'database documental ausente'

    def execute(self, request: BrainRequest) -> BrainResult:
        return _run('investigation', self.database, request)


@dataclass(frozen=True)
class StrategyBrain:
    database: Path | None
    definition = BrainDefinition('strategy', 'Estratégia', ('conditional_planning', 'risk_review', 'evidence_dependencies'), installed=True)

    def health_check(self) -> tuple[bool, str]:
        ok = bool(self.database and self.database.is_file())
        return ok, 'biblioteca local acessível' if ok else 'database documental ausente'

    def execute(self, request: BrainRequest) -> BrainResult:
        return _run('strategy', self.database, request)


def _run(kind: str, db: Path | None, request: BrainRequest) -> BrainResult:
    if 'library:read' not in request.permission_scopes:
        return BrainResult(kind, BrainStatus.FAILED, request.trace_id, 0, error='permission_denied')
    if not db or not db.is_file():
        return BrainResult(kind, BrainStatus.UNAVAILABLE, request.trace_id, 0,
                           warnings=('document_database_unavailable',))
    guard = search_document(db, DocumentRequest(request.query[:request.budget.max_input_chars], request.document_hint))
    if guard is None or guard.read_count < 1:
        return BrainResult(kind, BrainStatus.PARTIAL, request.trace_id, 0,
                           operations=('library.retrieve',), warnings=('no_matching_excerpt',))
    quotes = (guard.quote, *guard.conflicts)
    refs = tuple(EvidenceRef(source_id=q.evidence_id or f'{q.document_id}:{q.page or 0}',
                             document_id=q.document_id, title=q.name,
                             excerpt=q.excerpt[:1800], page=q.page, section=q.section)
                 for q in quotes[:request.budget.max_evidence])
    return BrainResult(kind, BrainStatus.COMPLETED, request.trace_id, 0, refs,
                       operations=('library.retrieve', f'{kind}.review'),
                       guard=guard, report=structured_report(kind, refs))
