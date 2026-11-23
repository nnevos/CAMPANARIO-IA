"""R3.0 conservative, deterministic disagreement review over *read* sources.

This does not establish truth, perform semantic inference, or execute any tool.
Only comparable sentences in independent sources, differing in one numeric
value and otherwise identical, are considered an automatic disagreement.
The review is intentionally asymmetric: missed conflicts are possible, whereas
unrelated measurements must not be presented as a contradiction.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from collections import defaultdict
from collections.abc import Sequence

from campanario.chat.canonical_answer import SourceRecord

_NUMBER = re.compile(r'(?<![\w])[-+]?\d+(?:[.,]\d+)*(?![\w])')
_SENTENCE = re.compile(r'(?<=[.!?])\s+|[\r\n]+')
_WORD = re.compile(r'\b[^\W\d_]+\b', re.UNICODE)


@dataclass(frozen=True, slots=True)
class NumericDisagreement:
    source_ids: tuple[str, str]
    excerpts: tuple[str, str]
    values: tuple[str, str]


def _normalize(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def _sentences(source: SourceRecord):
    # Bounds are enforced before regex processing, irrespective of document size.
    for sentence in _SENTENCE.split(source.excerpt[:6000]):
        sentence = sentence.strip()[:350]
        if not sentence or len([word for word in _WORD.findall(sentence) if len(word) >= 3]) < 3:
            continue
        tokens = _NUMBER.findall(sentence)
        if len(tokens) != 1:
            continue
        frame = _normalize(_NUMBER.sub('<valor>', sentence, count=1))
        yield frame, tokens[0], sentence


def reconcile_numeric_evidence(sources: Sequence[SourceRecord], *, limit: int = 8
                               ) -> tuple[NumericDisagreement, ...]:
    """Review at most 25 sources; require independent locators and exact frame.

    No claim is added, modified or promoted to VERIFIED. Source text is treated
    as untrusted data, not as instructions. Identical numeric values agree only
    textually, not necessarily in reality.
    """
    if not 1 <= limit <= 25:
        raise ValueError('invalid disagreement limit')
    frames: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)
    for source in sources[:25]:
        identity = source.document_id or source.locator
        for frame, value, sentence in _sentences(source):
            frames[frame].append((source.source_id, identity, value, sentence))
    conflicts: list[NumericDisagreement] = []
    seen: set[tuple[str, str]] = set()
    for entries in frames.values():
        for i, left in enumerate(entries):
            for right in entries[i + 1:]:
                if left[0] == right[0] or left[1] == right[1] or left[2] == right[2]:
                    continue
                pair = tuple(sorted((left[0], right[0])))
                if pair in seen:
                    continue
                seen.add(pair)
                conflicts.append(NumericDisagreement(
                    source_ids=(left[0], right[0]),
                    excerpts=(left[3], right[3]), values=(left[2], right[2]),
                ))
                if len(conflicts) >= limit:
                    return tuple(conflicts)
    return tuple(conflicts)
