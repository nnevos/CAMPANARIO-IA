from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ExtractedEbook


@dataclass(frozen=True, slots=True)
class EvidenceSnippet:
    evidence_id: str
    source_id: str
    quote: str


def build_evidence_catalog(ebook: ExtractedEbook) -> tuple[EvidenceSnippet, ...]:
    """Build deterministic, verbatim evidence snippets from the uploaded ebook.

    The model never authors these snippets. It may only choose an evidence_id; the
    service resolves the exact quote from this catalog before Pydantic validation.
    """
    snippets: list[EvidenceSnippet] = []
    seen: set[str] = set()
    counter = 1
    for segment in ebook.segments:
        for unit in _split_units(segment.text):
            for quote in _quote_windows(unit):
                key = _key(quote)
                if not key or key in seen:
                    continue
                seen.add(key)
                snippets.append(EvidenceSnippet(f"ev_{counter:04d}", segment.source_id, quote))
                counter += 1
    return tuple(snippets)


def catalog_map(catalog: tuple[EvidenceSnippet, ...]) -> dict[str, EvidenceSnippet]:
    return {item.evidence_id: item for item in catalog}


def render_evidence_catalog(catalog: tuple[EvidenceSnippet, ...]) -> str:
    return "\n".join(
        f"[{item.evidence_id} | {item.source_id}] {item.quote}" for item in catalog
    )


def _split_units(text: str) -> list[str]:
    # Preserve source wording; only use boundaries to produce manageable excerpts.
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [re.sub(r"\s+", " ", part).strip() for part in parts if part.strip()]


def _quote_windows(text: str, max_words: int = 30, target_words: int = 24, overlap: int = 6) -> list[str]:
    matches = list(re.finditer(r"\S+", text))
    if len(matches) < 5:
        return []
    if len(matches) <= max_words:
        return [text.strip()]

    windows: list[str] = []
    step = max(1, target_words - overlap)
    start = 0
    while start < len(matches):
        end = min(len(matches), start + target_words)
        if end - start < 5:
            break
        quote = text[matches[start].start() : matches[end - 1].end()].strip()
        windows.append(quote)
        if end == len(matches):
            break
        start += step
    return windows


def _key(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()
