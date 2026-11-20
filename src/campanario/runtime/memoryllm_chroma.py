"""MemoryLLM ChromaDB retrieval adapted to Campanario's provenance and scopes.

Based on MemoryLLM-main/memory/vector_store.py and memory/retriever.py.
Chroma stores a disposable search index; ExperienceRepository remains authoritative.
"""
from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from uuid import UUID

from campanario.runtime.semantic_index import EmbeddingProvider, _index_text

log = logging.getLogger(__name__)


class MemoryLLMChromaIndex:
    """Persistent Chroma cosine retrieval with externally supplied local Ollama embeddings."""

    def __init__(self, path: Path, provider: EmbeddingProvider, *, model_name: str,
                 min_similarity: float = 0.43, batch_size: int = 32, retry_seconds: float = 90.0):
        import chromadb
        from chromadb.config import Settings
        self._client = chromadb.PersistentClient(
            path=str(path), settings=Settings(anonymized_telemetry=False))
        self._collection = self._client.get_or_create_collection(
            name='campanario_memories', metadata={'hnsw:space': 'cosine'})
        self._provider = provider
        self._model = model_name
        self._minimum = min_similarity
        self._batch_size = max(1, min(64, batch_size))
        self._retry_seconds = retry_seconds
        self._retry_after = 0.0
        self._lock = threading.RLock()

    def forget(self, memory_id: UUID) -> None:
        with self._lock:
            self._collection.delete(ids=[str(memory_id)])

    def search(self, query: str, candidates: Sequence, *, limit: int = 8) -> dict[UUID, float]:
        if not query.strip() or not candidates or time.monotonic() < self._retry_after:
            return {}
        try:
            with self._lock:
                return self._search(query, candidates, limit)
        except Exception as exc:
            self._retry_after = time.monotonic() + self._retry_seconds
            log.warning('MemoryLLM Chroma unavailable, lexical fallback: %s', exc)
            return {}

    def _search(self, query: str, candidates: Sequence, limit: int) -> dict[UUID, float]:
        # Never trust a Chroma result without resolving it against current authorized
        # ACTIVE records. Stale records cannot leak, even after an interrupted deletion.
        allowed = {str(m.id): m for m in candidates}
        existing = self._collection.get(ids=list(allowed), include=['metadatas'])
        hashes = {}
        for id_, metadata in zip(existing['ids'], existing['metadatas'] or []):
            hashes[id_] = metadata or {}
        missing = []
        for memory in candidates:
            digest = hashlib.sha256(_index_text(memory).encode('utf-8')).hexdigest()
            if hashes.get(str(memory.id), {}).get('digest') != digest or hashes.get(str(memory.id), {}).get('model') != self._model:
                missing.append((memory, digest))
        for offset in range(0, len(missing), self._batch_size):
            batch = missing[offset:offset + self._batch_size]
            texts = [_index_text(m) for m, _ in batch]
            vectors = self._provider.embed(texts)
            if len(vectors) != len(batch):
                raise ValueError('Invalid embedding batch')
            self._collection.upsert(
                ids=[str(m.id) for m, _ in batch], documents=texts,
                embeddings=vectors,
                metadatas=[{'digest': digest, 'model': self._model,
                            'kind': m.kind.value, 'source': m.source.value} for m, digest in batch],
            )
        # Explicit embeddings avoid Chroma's implicit online model download.
        vector = self._provider.embed([query])[0]
        result = self._collection.query(
            query_embeddings=[vector], n_results=min(max(1, limit * 3), self._collection.count()),
            include=['distances'], where={'model': self._model},
        )
        scores = {}
        for id_, distance in zip(result['ids'][0], result['distances'][0]):
            if id_ not in allowed:
                continue
            similarity = 1.0 - float(distance)
            if similarity >= self._minimum:
                scores[UUID(id_)] = similarity
            if len(scores) >= limit:
                break
        return scores
