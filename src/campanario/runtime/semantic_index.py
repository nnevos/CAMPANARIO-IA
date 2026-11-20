"""Optional, local semantic index. SQLite memories are the source of truth.

The index stores only derived vectors, never a competing summary of the conversation.
It can be rebuilt after deletion or a model change. No vector is trusted without
checking the corresponding active, authorized ExperienceMemory first.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import threading
import time
from collections.abc import Callable, Sequence
from typing import Protocol
from uuid import UUID

import httpx
from sqlalchemy import Column, MetaData, String, Table, Text, delete, select, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

log = logging.getLogger(__name__)

metadata = MetaData()
vectors_table = Table(
    "experience_semantic_vectors", metadata,
    Column("memory_id", String(36), primary_key=True),
    Column("model_name", String(128), primary_key=True),
    Column("content_hash", String(64), nullable=False),
    Column("vector_json", Text, nullable=False),
)


class EmbeddingProvider(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OllamaEmbeddingProvider:
    """Use the Ollama embedding endpoint, NOT the Qwen chat endpoint."""

    def __init__(self, *, url: str, model: str, timeout: float = 7.0) -> None:
        self._url = url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = httpx.post(
            f"{self._url}/api/embed",
            json={"model": self._model, "input": list(texts), "keep_alive": "2m"},
            timeout=self._timeout,
        )
        response.raise_for_status()
        vectors = response.json().get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise ValueError("Ollama returned an invalid embedding batch")
        return [normalize_vector(vector) for vector in vectors]


def normalize_vector(vector: Sequence[float]) -> list[float]:
    if not vector or any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in vector):
        raise ValueError("Invalid embedding vector")
    magnitude = math.sqrt(sum(float(x) ** 2 for x in vector))
    if magnitude <= 0:
        raise ValueError("Zero-length embedding vector")
    return [float(x) / magnitude for x in vector]


def _index_text(memory) -> str:
    # Include the attribute (not just the value) and the speaker's original words.
    # Do not include assistant content as factual proof.
    evidence = memory.evidence.strip().replace("\n", " ")
    if memory.source.value == "user_answer" and "\n" in memory.evidence:
        evidence = f"Resposta fornecida pelo usuário: {memory.value}"
    return f"{memory.kind.value}; {memory.key.replace('.', ' ')}; {evidence or memory.value}; {memory.value}"[:1000]


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SemanticMemoryIndex:
    """Small-dataset cosine search. Incrementally backfills embeddings in SQLite.

    Bounded batches avoid a blocking full rebuild. `lookup` must be called from a
    worker thread in an async runtime. Results are scores for *supplied* active
    records; orphaned or superseded vectors can never become returned memories.
    """

    def __init__(
        self, session_factory: Callable[[], Session], provider: EmbeddingProvider, *,
        model_name: str, min_similarity: float = 0.43, batch_size: int = 32,
        retry_seconds: float = 90.0,
    ) -> None:
        self._factory = session_factory
        self._provider = provider
        self._model_name = model_name
        self._minimum = min_similarity
        self._batch_size = max(1, min(64, batch_size))
        self._retry_seconds = retry_seconds
        self._retry_after = 0.0
        self._lock = threading.RLock()
        # No schema migration of experience memories. Index table is additive.
        with self._factory() as db:
            vectors_table.create(db.get_bind(), checkfirst=True)

    def forget(self, memory_id: UUID) -> None:
        """Erase derived data when source is forgotten or superseded."""
        with self._lock, self._factory() as db:
            db.execute(delete(vectors_table).where(vectors_table.c.memory_id == str(memory_id)))
            db.commit()

    def search(self, query: str, candidates: Sequence, *, limit: int = 8) -> dict[UUID, float]:
        if not query.strip() or not candidates or time.monotonic() < self._retry_after:
            return {}
        with self._lock:
            try:
                return self._search_unlocked(query, candidates, limit)
            except (httpx.HTTPError, ValueError, OSError, TypeError, SQLAlchemyError) as exc:
                # An uninstalled model must not stall every message. Retry after a pause.
                self._retry_after = time.monotonic() + self._retry_seconds
                log.warning("Semantic index unavailable; using lexical recall: %s", exc)
                return {}

    def _search_unlocked(self, query: str, candidates: Sequence, limit: int) -> dict[UUID, float]:
        by_id = {str(memory.id): memory for memory in candidates}
        with self._factory() as db:
            rows = db.execute(select(vectors_table).where(vectors_table.c.model_name == self._model_name)).mappings().all()
        stored = {row["memory_id"]: row for row in rows if row["memory_id"] in by_id}
        # Invalidate whenever any meaningful source text changes.
        missing = [
            memory for memory in candidates
            if str(memory.id) not in stored or
            stored[str(memory.id)]["content_hash"] != _checksum(_index_text(memory))
        ]
        if missing:
            batch = missing[:self._batch_size]
            vector_batch = self._provider.embed([_index_text(memory) for memory in batch])
            if len(vector_batch) != len(batch):
                raise ValueError("Incorrect embedding batch size")
            dimensions = {len(vector) for vector in vector_batch}
            if len(dimensions) != 1:
                raise ValueError("Inconsistent embedding dimensions")
            with self._factory() as db:
                for memory, vector in zip(batch, vector_batch):
                    db.execute(delete(vectors_table).where(and_(
                        vectors_table.c.memory_id == str(memory.id),
                        vectors_table.c.model_name == self._model_name,
                    )))
                    db.execute(vectors_table.insert().values(
                        memory_id=str(memory.id), model_name=self._model_name,
                        content_hash=_checksum(_index_text(memory)), vector_json=json.dumps(vector),
                    ))
                    stored[str(memory.id)] = {
                        "memory_id": str(memory.id), "content_hash": _checksum(_index_text(memory)),
                        "vector_json": json.dumps(vector),
                    }
                db.commit()
        query_vector = self._provider.embed([query])[0]
        scores: list[tuple[float, UUID]] = []
        for memory in candidates:
            row = stored.get(str(memory.id))
            if row is None or row["content_hash"] != _checksum(_index_text(memory)):
                continue
            vector = json.loads(row["vector_json"])
            if len(vector) != len(query_vector):
                continue
            similarity = sum(x * y for x, y in zip(query_vector, vector))
            if similarity >= self._minimum:
                scores.append((similarity, memory.id))
        scores.sort(reverse=True)
        return {id_: score for score, id_ in scores[:limit]}
