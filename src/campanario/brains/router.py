"""R2: deterministic, bounded capability plans independent of speaker selection.

Plans describe what may run; neither the model nor imported text can grant
permission or install a brain. Only first-party read-only capabilities are
selected until the R1 sandbox gate is satisfied.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from uuid import UUID, uuid4

from campanario.chat.data_intent import is_data_request
from campanario.chat.local_library import _fold


@dataclass(frozen=True, slots=True)
class BrainStep:
    brain_id: str
    objective: str
    reason: str
    depends_on: tuple[str, ...] = ()
    required_scopes: frozenset[str] = frozenset({'library:read'})
    input_contract: str = 'user_query'
    output_contract: str = 'brain_result_v9'
    query_override: str = ''  # deterministic per-step focus, never model-generated
    # Optional: a missing source does not block independent work. Required:
    # a valid, completed upstream result with evidence is mandatory.
    dependency_policy: str = 'optional'

    def __post_init__(self):
        if not self.brain_id or not self.objective.strip() or not self.reason.strip():
            raise ValueError('brain step requires ID, objective and reason')
        if len(set(self.depends_on)) != len(self.depends_on) or self.brain_id in self.depends_on:
            raise ValueError('invalid dependencies')
        if self.dependency_policy not in {'optional', 'required'}:
            raise ValueError('unknown dependency policy')
        if self.input_contract not in {'user_query', 'user_query_plus_prior_evidence_metadata'}:
            raise ValueError('unknown step input contract')
        if self.output_contract != 'brain_result_v9':
            raise ValueError('unknown step output contract')
        if self.input_contract == 'user_query_plus_prior_evidence_metadata' and not self.depends_on:
            raise ValueError('metadata input requires dependencies')
        if len(self.query_override) > 500:
            raise ValueError('step query too long')
        if not self.required_scopes or any(not s or len(s) > 100 for s in self.required_scopes):
            raise ValueError('invalid required scopes')

    def public(self) -> dict:
        return {'brain_id': self.brain_id, 'objective': self.objective,
                'reason': self.reason, 'depends_on': list(self.depends_on),
                'required_scopes': sorted(self.required_scopes),
                'input_contract': self.input_contract, 'output_contract': self.output_contract,
                'dependency_policy': self.dependency_policy,
                'focused_query': bool(self.query_override)}


@dataclass(frozen=True, slots=True)
class BrainPlan:
    trace_id: UUID
    intent: str
    brain_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    steps: tuple[BrainStep, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if len(self.brain_ids) > 3 or len(set(self.brain_ids)) != len(self.brain_ids):
            raise ValueError('Brain plans must contain at most three distinct brains')
        if not self.intent or not isinstance(self.trace_id, UUID):
            raise ValueError('invalid plan metadata')
        if self.steps:
            if tuple(s.brain_id for s in self.steps) != self.brain_ids:
                raise ValueError('brain steps do not match selected brains')
        else:
            object.__setattr__(self, 'steps', tuple(
                BrainStep(brain_id, 'Executar capacidade explicitamente solicitada',
                          self.reasons[i] if i < len(self.reasons) else 'explicit', ())
                for i, brain_id in enumerate(self.brain_ids)))
        seen = set()
        for step in self.steps:
            if not set(step.depends_on).issubset(seen):
                raise ValueError('plan has a missing, future or cyclic dependency')
            seen.add(step.brain_id)

    def public(self) -> dict:
        return {'trace_id': str(self.trace_id), 'intent': self.intent,
                'brain_ids': list(self.brain_ids), 'reasons': list(self.reasons),
                'steps': [step.public() for step in self.steps]}


class CapabilityRouter:
    """Route only explicit local work. No extra model call for routine chat.

    A mixed request selects two read-only brains in order. The resulting
    evidence is presented separately; cross-source reasoning is not claimed.
    """
    def plan(self, text: str, *, document_request=None, data_request: bool | None = None) -> BrainPlan:
        data = is_data_request(text) if data_request is None else bool(data_request)
        # Do not launch a second brain just because the user mentions a 'table'
        # inside a document; mixed plans require an explicit spreadsheet source.
        explicit_spreadsheet = bool(re.search(r'\b(?:planilha|planilhas|csv|xlsx|excel)\b', _fold(text)))
        if document_request is not None and data and explicit_spreadsheet:
            return BrainPlan(uuid4(), 'document_and_data', ('knowledge', 'analysis'),
                             ('explicit_document_source', 'deterministic_calculation'), (
                BrainStep('knowledge', 'Recuperar trechos e fontes documentais',
                          'explicit_document_source',
                          query_override=(document_request.hint or '')[:85]),
                BrainStep('analysis', 'Calcular dados de planilha importada',
                          'deterministic_calculation', depends_on=('knowledge',),
                          input_contract='user_query_plus_prior_evidence_metadata'),
            ))
        if document_request is not None:
            return BrainPlan(uuid4(), 'document_lookup', ('knowledge',),
                             ('explicit_document_source',), (
                BrainStep('knowledge', 'Recuperar trechos e fontes documentais',
                          'explicit_document_source'),))
        if data:
            return BrainPlan(uuid4(), 'data_analysis', ('analysis',),
                             ('deterministic_calculation',), (
                BrainStep('analysis', 'Executar cálculo local reprodutível',
                          'deterministic_calculation'),))
        return BrainPlan(uuid4(), 'conversation', (), ('no_explicit_capability_needed',))
