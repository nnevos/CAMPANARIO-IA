"""Detect user-specified document questions across turns, never from agent guesses."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from campanario.chat.local_library import LibraryQuote, LocalFactSheet, _fold, _normal
from campanario.chat.models import MessageRole

_REFERENCE = re.compile(
    r'\b(?:database|biblioteca|(?:no|na|o|a|esse|essa|aquele|aquela|consulte|consultar|'
    r'procure|busque|segundo|veja|enviado|enviei)\s+(?:documento|arquivo|pdf|livro))\b', re.I)
_HINT = re.compile(r'\b(?:documento|arquivo|pdf|livro)\s+(?:de|do|da|sobre|chamado|intitulado)\s+(.{3,85})', re.I)


@dataclass(frozen=True, slots=True)
class DocumentRequest:
    question: str
    hint: str = ''


def _hint(text: str) -> str:
    match = _HINT.search(text)
    if not match:
        return ''
    name = re.split(r'\b(?:com essas|com essas informacoes|que eu enviei|que enviei|'
                    r'com as informacoes|tem essas informacoes|que tem|na biblioteca|no database)\b',
                    match.group(1), maxsplit=1, flags=re.I)[0]
    return name.strip(' \n\r!?.,:;"\'')[:85]


def document_request(current: str, messages: list) -> DocumentRequest | None:
    """Require an actual user source reference; never infer one from agent output."""
    previous = [m.content for m in messages[-14:] if m.role == MessageRole.USER]
    current_ref = bool(_REFERENCE.search(_fold(current)))
    recent_refs = [s for s in previous[-4:] if _REFERENCE.search(_fold(s))]
    if not current_ref and not recent_refs:
        return None
    prior_question = next((s for s in reversed(previous) if '?' in s), '')
    if '?' in current:
        question = current
    elif current_ref and prior_question:
        question = prior_question
    else:
        return None
    # A document named in the user's latest source reference takes priority.
    hint = _hint(current)
    if not hint:
        for message in reversed(recent_refs):
            hint = _hint(message)
            if hint:
                break
    return DocumentRequest(question[:500], hint)


def search_document(database: Path, request: DocumentRequest) -> LocalFactSheet | None:
    """Read actual SQLite pages/sections without writing to database or network."""
    if not Path(database).is_file():
        return None
    from campanario.utilities.document_v8 import retrieve

    class Reader:
        def connect(self):
            connection = sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro',
                                         uri=True, timeout=1.0)
            connection.row_factory = sqlite3.Row
            connection.execute('PRAGMA query_only=ON')
            return connection

    try:
        result = retrieve(Reader(), request.question, document_hint=request.hint, limit=8)
    except (sqlite3.Error, OSError, ValueError, TypeError):
        return None
    evidence = result['evidence']
    if not evidence:
        return None

    def quote(hit):
        return LibraryQuote(document_id=hit['document_id'], name=hit['document'],
                            sha256=hit['sha256'], page=hit['page'],
                            excerpt=hit['excerpt'], score=hit['score'],
                            section=hit['section'], method=hit['extraction_method'],
                            evidence_id=hit['evidence_id'])

    best = quote(evidence[0])
    # Do not pick a winner when sources disagree at comparable rank.
    others = [quote(hit) for hit in evidence[1:]
              if hit['document_id'] != evidence[0]['document_id']
              and hit['score'] >= evidence[0]['score'] - 0.6
              and _normal(hit['excerpt']) != _normal(evidence[0]['excerpt'])]
    return LocalFactSheet(subject=request.question, query=request.question,
                          quote=best, status='ambiguous' if others else 'grounded',
                          conflicts=tuple(others[:2]),
                          candidates=tuple([best.name] + [s.name for s in others[:2]]),
                          read_count=len(evidence))
