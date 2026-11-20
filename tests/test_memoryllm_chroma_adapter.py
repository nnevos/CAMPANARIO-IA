"""Integration contract for the MemoryLLM-derived Chroma adapter, without network."""
from __future__ import annotations

import sys
import types
from datetime import UTC, datetime
from uuid import uuid4

from campanario.runtime.experience import ExperienceMemory, MemoryKind, MemorySource, MemoryStatus
from campanario.runtime.memoryllm_chroma import MemoryLLMChromaIndex


class FakeCollection:
    def __init__(self):
        self.rows = {}

    def get(self, *, ids, include):
        present = [x for x in ids if x in self.rows]
        return {'ids': present, 'metadatas': [self.rows[x][2] for x in present]}

    def upsert(self, *, ids, documents, embeddings, metadatas):
        for x, doc, vector, metadata in zip(ids, documents, embeddings, metadatas):
            self.rows[x] = (doc, vector, metadata)

    def delete(self, *, ids):
        for x in ids:
            self.rows.pop(x, None)

    def count(self):
        return len(self.rows)

    def query(self, *, query_embeddings, n_results, include, where):
        q = query_embeddings[0]
        rows = [(id_, 1 - sum(a*b for a, b in zip(q, v)))
                for id_, (_, v, meta) in self.rows.items() if meta['model'] == where['model']]
        rows.sort(key=lambda row: row[1])
        return {'ids': [[x for x, _ in rows[:n_results]]],
                'distances': [[d for _, d in rows[:n_results]]]}


class FakeEmbedding:
    def embed(self, texts):
        return [[1., 0.] if 'violoncelo' in text.lower() else [0., 1.] for text in texts]


def test_chroma_retrieves_only_authorized_active_records_and_forgets(monkeypatch, tmp_path):
    collection = FakeCollection()
    chroma = types.ModuleType('chromadb')
    chroma.PersistentClient = lambda **kw: types.SimpleNamespace(
        get_or_create_collection=lambda **kw: collection)
    config = types.ModuleType('chromadb.config')
    config.Settings = lambda **kw: None
    monkeypatch.setitem(sys.modules, 'chromadb', chroma)
    monkeypatch.setitem(sys.modules, 'chromadb.config', config)
    index = MemoryLLMChromaIndex(tmp_path, FakeEmbedding(), model_name='fake', min_similarity=0.5)
    now = datetime.now(UTC)
    def memory(text):
        return ExperienceMemory(id=uuid4(), kind=MemoryKind.FACT, subject='user',
            key='user.note', value=text, confidence=1.0, source=MemorySource.USER_EXPLICIT,
            status=MemoryStatus.ACTIVE, evidence=text, source_session_id=uuid4(),
            source_message_id=uuid4(), source_agent_id=None, supersedes_id=None,
            created_at=now, updated_at=now, last_confirmed_at=now)
    cello, piano = memory('Estou aprendendo violoncelo'), memory('Estou estudando piano')
    assert list(index.search('violoncelo', [cello, piano], limit=1)) == [cello.id]
    # Even if Chroma still holds an obsolete document, the repository candidate
    # allowlist prevents it from being returned.
    assert cello.id not in index.search('violoncelo', [piano], limit=2)
    index.forget(cello.id)
    assert str(cello.id) not in collection.rows
