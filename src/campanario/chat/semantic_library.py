"""Optional, loopback-only semantic candidate discovery for imported documents.

The FTS5 retrieval remains authoritative for the current extractive-answer path.
A semantic hit must separately pass the same conservative explicit-answer gate
as lexical hits before it is even SHOWN as a candidate. A cosine similarity, or
passing this necessary-condition gate, NEVER promotes it to supported facts.

All vectors live in process RAM. User SQLite is read-only and untouched.
"""
from __future__ import annotations

from collections.abc import Sequence
import logging
import math
import re
from pathlib import Path
from time import monotonic
from typing import Protocol
from urllib.parse import urlsplit

import httpx

from campanario.chat.local_library import (
    LibraryQuote, LocalFactSheet, ReadOnlyLocalLibrary, _tokens,
)

logger = logging.getLogger(__name__)


def _explicit_name_anchors(question: str) -> set[str]:
    """Infer only explicit capitalized names from user text, never invented IDs.

    The names must occur in the literal source excerpt. A topic label is an
    anchor for *retrieval*, not a claim that the excerpt answers the question.
    """
    ignored = {'morgana', 'todd', 'qual', 'quais', 'quem', 'onde', 'como',
               'quando', 'quanto', 'porque', 'projeto', 'protocolo',
               'guia', 'obra', 'livro', 'arquivo', 'reuniao'}
    words = re.findall(r'[\w\u00c0-\u00ff]+', question)
    return {token for word in words if word[0].isupper()
            for token in _tokens(word) if token not in ignored}


class EmbeddingService(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def normalize(vector: Sequence[float]) -> tuple[float, ...]:
    if (not isinstance(vector, (list, tuple)) or not vector or
            any(isinstance(v, bool) or not isinstance(v, (float, int)) or
                not math.isfinite(v) for v in vector)):
        raise ValueError('Invalid embedding values')
    length = math.sqrt(sum(float(v) * float(v) for v in vector))
    if length <= 0 or len(vector) > 4096:
        raise ValueError('Invalid embedding length')
    return tuple(float(v) / length for v in vector)


class LoopbackOllamaEmbeddings:
    """Never send library text to LAN, internet, proxy or redirect URLs."""
    def __init__(self, *, url: str = 'http://127.0.0.1:11434',
                 model: str = 'embeddinggemma', timeout: float = 5.0):
        address = urlsplit(url)
        if (address.scheme != 'http' or address.hostname not in
                {'127.0.0.1', '::1'} or address.username or address.password or
                address.path not in ('', '/') or address.query or address.fragment):
            raise ValueError('Semantic library requires HTTP Ollama on loopback IP')
        if not model or len(model) > 100 or any(c in model for c in '\r\n'):
            raise ValueError('Invalid local embedding model name')
        self._url = url.rstrip('/')
        self._model = model
        self._timeout = float(timeout)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if len(texts) > 16 or any(len(t) > 1200 for t in texts):
            raise ValueError('Embedding batch over privacy/resource budget')
        # No environment proxies, no redirects. A model is never downloaded here.
        with httpx.Client(timeout=self._timeout, trust_env=False,
                          follow_redirects=False) as client:
            response = client.post(self._url + '/api/embed', json={
                'model': self._model, 'input': list(texts), 'keep_alive': '30s',
            })
            response.raise_for_status()
            vectors = response.json().get('embeddings')
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise ValueError('Ollama returned invalid embedding batch')
        return vectors


class HybridLocalLibrary(ReadOnlyLocalLibrary):
    """FTS5 first; only on a miss, optional semantic candidate suggestions.

    - A cosine-selected passage must pass the lexical evidence sufficiency gate
      before it is shown; even then the sheet stays explicitly insufficient.
    - At most max_semantic_segments excerpts are embedded (RAM cache only).
    - On missing Ollama, malformed vectors or timeout: lexical fallback.
    - The cache rebuilds if SQLite/WAL changes, never writing there.
    """
    def __init__(self, database: Path, *, embeddings: EmbeddingService,
                 min_similarity: float = 0.72, max_semantic_segments: int = 96,
                 batch_size: int = 16, build_budget_seconds: float = 15.0,
                 retry_seconds: float = 90.0, **kwargs):
        super().__init__(database, **kwargs)
        self.embeddings = embeddings
        self.min_similarity = max(0.0, min(1.0, float(min_similarity)))
        self.max_semantic_segments = max(1, min(256, int(max_semantic_segments)))
        self.batch_size = max(1, min(16, int(batch_size)))
        self.build_budget_seconds = max(1.0, float(build_budget_seconds))
        self.retry_seconds = float(retry_seconds)
        self._semantic_stamp = None
        self._semantic_segments: tuple[LibraryQuote, ...] = ()
        self._semantic_vectors: tuple[tuple[float, ...], ...] = ()
        self._retry_after = 0.0
        self.semantic_build_count = 0
        self.last_semantic_status = 'not_used'
        self.last_semantic_ranked = 0
        self.last_semantic_rejected = 0

    def _ensure_semantics(self, stamp):
        if self._semantic_stamp == stamp:
            return
        excerpts: list[LibraryQuote] = []
        def collect(quote):
            if len(excerpts) >= self.max_semantic_segments:
                return False
            excerpts.append(quote)
        self._scan_rows(collect)
        vectors = []
        started = monotonic()
        dimensions = None
        for offset in range(0, len(excerpts), self.batch_size):
            if monotonic() - started > self.build_budget_seconds:
                raise TimeoutError('Semantic build budget exhausted')
            batch = excerpts[offset:offset + self.batch_size]
            result = self.embeddings.embed([quote.excerpt for quote in batch])
            if len(result) != len(batch):
                raise ValueError('Partial embedding result')
            for raw in result:
                normalized = normalize(raw)
                if dimensions is None:
                    dimensions = len(normalized)
                if len(normalized) != dimensions:
                    raise ValueError('Inconsistent embedding dimensions')
                vectors.append(normalized)
        self._semantic_segments = tuple(excerpts)
        self._semantic_vectors = tuple(vectors)
        self._semantic_stamp = stamp
        self.semantic_build_count += 1

    def search(self, question: str, *, subject: str = '') -> LocalFactSheet | None:
        lexical = super().search(question, subject=subject)
        self.last_semantic_ranked = 0
        self.last_semantic_rejected = 0
        if lexical is not None:
            self.last_semantic_status = 'lexical_first'
            return lexical
        if (not self.database.is_file() or len(question.strip()) < 6 or
                monotonic() < self._retry_after):
            self.last_semantic_status = 'not_available'
            return None
        # Super.search() already releases the lock. Use the same lock so a turn
        # cannot see partially rebuilt vectors from another turn.
        with self._lock:
            try:
                stamp = self._file_stamp()
                if stamp is None:
                    return None
                self._ensure_semantics(stamp)
                if not self._semantic_vectors:
                    self.last_semantic_status = 'empty_library'
                    return None
                query = normalize(self.embeddings.embed([question[:500]])[0])
                if len(query) != len(self._semantic_vectors[0]):
                    raise ValueError('Embedding dimensions changed')
                subject_words = _tokens(subject) or _explicit_name_anchors(question)
                query_words = _tokens(question)
                ranked = []
                for quote, vec in zip(self._semantic_segments, self._semantic_vectors):
                    body_words = _tokens(quote.excerpt)
                    if subject_words and not subject_words.issubset(body_words):
                        continue
                    # Without an explicit subject, a semantic resemblance alone
                    # must not match a random document in the library.
                    if not subject_words and len(query_words & body_words) < 2:
                        continue
                    similarity = sum(a * b for a, b in zip(query, vec))
                    if similarity >= self.min_similarity:
                        ranked.append((similarity, quote))
                ranked.sort(key=lambda item: (-item[0], item[1].name, item[1].document_id))
                self.last_semantic_ranked = len(ranked)
                if not ranked:
                    self.last_semantic_status = 'no_safe_candidate'
                    return None
                # Inc.3B.2: cosine + subject merely DISCOVERS passages. Before
                # exposing one to either agent, apply the same attribute/focus
                # check as the FTS5 path (3B.1). Check every eligible result,
                # not just the top one, to avoid dropping a lower-ranked but
                # textually responsive excerpt. No synonym lists or guessing.
                from campanario.chat.evidence_gate import assess_explicit_answer
                approved = []
                for similarity, passage in ranked:
                    if assess_explicit_answer(
                            question, subject, passage.excerpt, passage.name).sufficient:
                        approved.append((similarity, passage))
                self.last_semantic_rejected = len(ranked) - len(approved)
                if not approved:
                    self.last_semantic_status = 'rejected_insufficient_evidence'
                    return None
                score, best = approved[0]
                # A candidate is NOT a verified answer even after this filter:
                # the necessary-condition gate cannot prove logical entailment.
                best = LibraryQuote(best.document_id, best.name, best.sha256,
                                    best.page, best.excerpt, round(score, 4))
                self.last_semantic_status = 'candidate_only'
                return LocalFactSheet(
                    subject=subject or question[:200], query=question, quote=best,
                    status='semantic_candidate', source_kind='library',
                )
            except (httpx.HTTPError, OSError, ValueError, TypeError,
                    TimeoutError, IndexError) as exc:
                logger.warning('library_semantic_unavailable error_type=%s',
                               type(exc).__name__)
                self._semantic_stamp = None
                self._semantic_vectors = ()
                self._semantic_segments = ()
                self._retry_after = monotonic() + max(1.0, self.retry_seconds)
                self.last_semantic_status = 'failed_lexical_fallback'
                return None
