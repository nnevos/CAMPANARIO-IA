"""R3.9: auditable *textual* propositions, not semantic truth judgments.

This module annotates source-backed excerpts with explicit modality and
attribution cues. A contradiction is proposed ONLY for the same literal
sentence with a narrowly positioned negation. Any conclusion needs human
review: quoted text may contain errors, irony or missing context.

Pure, bounded and offline. Never executes content or modifies evidence.
"""
from __future__ import annotations

import re
import unicodedata

MAX_CLAIMS = 16
_NEGATION = re.compile(r'\b(n[aã]o|nunca|jamais)\b', re.I)
_UNCERTAIN = re.compile(r'\b(pode(?:ria)?|poss[ií]vel|possivelmente|talvez|supostamente|alega(?:do|da|m|ram)?|teria|hip[oó]tese|suspeita|estima(?:do|da)?|prov[aá]vel)\b', re.I)
_ATTRIBUTION = re.compile(r'\b(segundo|conforme|de acordo com|relata|afirma|declarou|informou|consta no|registrou)\b', re.I)
# Strict constructions with explicit opposite polarity; words with an
# embedded 'não' elsewhere do not create a contradiction pair.
_PREDICATE = re.compile(
    r'^(.{4,110}?)\s+(n[aã]o\s+)?(est[aá]|estavam|estava|s[aã]o|[eé]|era|foram|foi|tem|tinha|possui|ocorreu|ocorreram)\s+(.{2,170})$',
    re.I,
)


def _normalized(s: str) -> str:
    s = unicodedata.normalize('NFKD', s.casefold())
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    return ' '.join(re.findall(r'[^\W_]+', s, flags=re.UNICODE))


def _proposition(text: str) -> tuple[str, bool] | None:
    """Return equivalent predicate key only in a very narrow grammar.

    Subject and complement must match *literally* after normalization.
    This is never general semantic entailment or contradiction detection.
    """
    text = text.strip().rstrip('.!?;: ')
    m = _PREDICATE.fullmatch(text)
    if not m:
        return None
    subject, no, verb, complement = m.groups()
    if _NEGATION.search(subject) or _NEGATION.search(complement):
        return None
    if _UNCERTAIN.search(text) or _ATTRIBUTION.search(text):
        return None
    if len(_normalized(subject).split()) < 2:
        return None
    key = '|'.join((_normalized(subject), _normalized(verb), _normalized(complement)))
    return key, bool(no)


def review_claims(citations: list[dict]) -> dict:
    """Annotate each exact citation. Flag explicit cross-document negations.

    Input must already be integrity-verified by the caller. Independent file
    IDs do not prove independent underlying sources or authenticity.
    """
    claims = []
    for item in citations[:MAX_CLAIMS]:
        text = ' '.join(str(item.get('quote', '')).split())[:500]
        if not text or not item.get('evidence_id') or not item.get('sha256'):
            continue
        kind = ('uncertain_or_hypothetical' if _UNCERTAIN.search(text)
                else 'attributed_statement' if _ATTRIBUTION.search(text)
                else 'explicit_negation' if _NEGATION.search(text)
                else 'reported_statement')
        parsed = _proposition(text)
        claims.append({'evidence_id': item['evidence_id'], 'filename': item.get('filename', ''),
                       'line': item.get('line'), 'sha256': item['sha256'],
                       'quote': text, 'reading': kind, 'status': 'source_statement_not_verified',
                       '_predicate': parsed})
    conflicts = []
    for i, first in enumerate(claims):
        if not first['_predicate']:
            continue
        key, negated = first['_predicate']
        for second in claims[i + 1:]:
            other = second['_predicate']
            if (other and key == other[0] and negated != other[1]
                    and first['evidence_id'] != second['evidence_id']):
                conflicts.append({'first': {'evidence_id': first['evidence_id'], 'line': first['line'],
                                            'quote': first['quote']},
                                  'second': {'evidence_id': second['evidence_id'], 'line': second['line'],
                                             'quote': second['quote']},
                                  'status': 'explicit_textual_opposition',
                                  'warning': 'Oposição textual literal; revisar contexto, origem e veracidade'})
                if len(conflicts) >= 6:
                    break
        if len(conflicts) >= 6:
            break
    for claim in claims:
        del claim['_predicate']
    return {'claims': claims, 'textual_oppositions': conflicts,
            'limitations': ['Classificação linguística por padrões; não é compreensão semântica geral',
                            'Proposição extraída não confirma autenticidade, contexto ou verdade',
                            'A ausência de oposição identificada não significa ausência de contradições']}
