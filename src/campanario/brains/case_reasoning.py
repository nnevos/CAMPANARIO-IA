"""R3.8: conservative, traceable case relations and verification priorities.

All inputs are ledger records or SHA-verified literal citations. Edges mean
co-reference or shared tokens, never causality, guilt or semantic entailment.
This module is pure: it does not read/write files, use LLMs or grant access.
"""
from __future__ import annotations

from campanario.brains.casework_sources import _terms

MAX_RELATIONS = 24


def prioritize_checks(question: str, hypotheses: list[dict], *, primary_supported: bool,
                      conflicts: bool = False) -> list[dict]:
    """Select registered operator checks by relevance, without inventing tasks."""
    target = _terms(question)
    ranked = []
    seen = set()
    for h in hypotheses[:32]:
        prompt = h.get('next_check', '')
        if not isinstance(prompt, str) or not prompt.strip():
            continue
        key = ' '.join(prompt.casefold().split())
        if key in seen or key == ' '.join(question.casefold().split()):
            continue
        seen.add(key)
        shared = len(target & (_terms(h.get('statement', '')) | _terms(prompt)))
        mixed = bool(h.get('supporting') and h.get('opposing'))
        # Conflicts and gaps prioritize checks, but scores only rank a queue.
        ranked.append({'question': prompt[:600], 'hypothesis_id': h.get('id', ''),
                       'priority': shared * 4 + (3 if mixed else 0) + (2 if not primary_supported else 0),
                       'reason': ('referências pró e contra cadastradas' if mixed else
                                  'pertinência lexical à pergunta' if shared else 'verificação pendente cadastrada')})
    ranked.sort(key=lambda r: (-r['priority'], r['hypothesis_id'], r['question']))
    return ranked[:8]


def relation_matrix(doc: dict, citations: list[dict]) -> dict:
    """Ground a small graph exclusively in source IDs and quoted text.

    The ledger's support/opposition links are operator *classifications*, not
    independently verified support. Textual overlap is a discovery hint only.
    """
    available = {x.get('id') for x in doc.get('evidence', [])}
    quoted = [c for c in citations[:16] if c.get('evidence_id') in available and c.get('quote')]
    links = []
    for h in doc.get('hypotheses', [])[:16]:
        hid = h.get('id', '')
        for polarity, field in (('registered_support', 'supporting'), ('registered_opposition', 'opposing')):
            for eid in h.get(field, [])[:16]:
                if eid in available and len(links) < MAX_RELATIONS:
                    links.append({'from': hid, 'to': eid, 'kind': polarity,
                                  'basis': 'classificação cadastrada pelo operador', 'verified': False})
    for ev in doc.get('events', [])[:32]:
        for eid in ev.get('evidence_ids', [])[:8]:
            if eid in available and len(links) < MAX_RELATIONS:
                links.append({'from': ev.get('id', ''), 'to': eid, 'kind': 'registered_event_source',
                              'basis': 'referência cadastrada; ocorrência não autenticada', 'verified': False})
    cross = []
    for pos, first in enumerate(quoted):
        for second in quoted[pos + 1:]:
            if first['evidence_id'] == second['evidence_id']:
                continue
            shared = sorted(_terms(first['quote']) & _terms(second['quote']))
            if len(shared) < 2:
                continue
            cross.append({'first': {'evidence_id': first['evidence_id'], 'line': first['line']},
                          'second': {'evidence_id': second['evidence_id'], 'line': second['line']},
                          'shared_terms': shared[:6], 'status': 'lexical_overlap_only'})
            if len(cross) == 8:
                break
        if len(cross) == 8:
            break
    return {'registered_links': links, 'cross_document_hints': cross,
            'warning': 'Relações de cadastro ou vocabulário; não demonstram causalidade nem veracidade'}


def hypothesis_matrix(doc: dict, citations: list[dict]) -> list[dict]:
    """Report evidence coverage of *registered* positions, never probabilities."""
    retrieved = {c['evidence_id'] for c in citations}
    result = []
    for h in doc.get('hypotheses', [])[:16]:
        pro = set(h.get('supporting', []))
        contra = set(h.get('opposing', []))
        seen_pro, seen_contra = sorted(pro & retrieved), sorted(contra & retrieved)
        if seen_pro and seen_contra:
            state = 'mixed_registered_positions'
        elif seen_pro or seen_contra:
            state = 'one_sided_registered_position'
        else:
            state = 'no_retrieved_registered_sources'
        result.append({'hypothesis_id': h.get('id', ''), 'statement': h.get('statement', ''),
                       'review_state': state, 'retrieved_supporting': seen_pro,
                       'retrieved_opposing': seen_contra, 'status': 'unverified',
                       'warning': 'Rótulos pró/contra foram informados pelo operador; não são validação semântica'})
    return result
