"""Tests of the architecture, not hard-coded answers to user questions."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from campanario.runtime.semantic_index import SemanticMemoryIndex, normalize_vector, vectors_table
from campanario.runtime.experience import (
    ExperienceLayer, ExperienceMemory, MemoryKind, MemorySource, MemoryStatus,
    ConservativeMemoryExtractor,
)
from campanario.chat.models import Message, MessageRole
from campanario.storage.database import Base, build_session_factory
from campanario.storage.repositories import SqlAlchemyExperienceRepository


class SemanticFixture:
    """Embeddings have no dependence on the production retrieval rule set."""
    def __init__(self, concepts):
        self.concepts = concepts
        self.calls = []
        self.fail = False

    def embed(self, texts):
        if self.fail:
            raise OSError('Ollama offline')
        self.calls.append(tuple(texts))
        output = []
        for text in texts:
            chosen = [0.0] * len(self.concepts)
            for index, words in enumerate(self.concepts):
                if any(word.lower() in text.lower() for word in words):
                    chosen[index] = 1.0
            if not any(chosen):
                chosen = [0.01] * len(self.concepts)
            output.append(normalize_vector(chosen))
        return output


def build_layer(db_path, embedder):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)
    index = SemanticMemoryIndex(factory, embedder, model_name='test-embedding', min_similarity=0.55)
    layer = ExperienceLayer(SqlAlchemyExperienceRepository(factory), semantic_index=index)
    return layer, factory


def store(layer, text):
    message = Message(id=uuid4(), session_id=uuid4(), role=MessageRole.USER, content=text, created_at=datetime.now(UTC))
    return layer.observe_user_message(history_before=[], message=message)[0]


def test_semantic_matches_paraphrases_and_survives_restart(tmp_path):
    embedder = SemanticFixture([
        ('blender', 'modelagem tridimensional'),
        ('astronomia', 'corpos celestes'),
        ('violão', 'instrumento musical'),
        ('lisboa', 'capital portuguesa'),
    ])
    db = tmp_path / 'database.db'
    layer, factory = build_layer(db, embedder)
    entries = [
        store(layer, 'estou aprendendo Blender'),
        store(layer, 'estou estudando astronomia'),
        store(layer, 'estou praticando violão'),
        store(layer, 'quero visitar Lisboa'),
    ]
    for query, expected in [
        ('Qual ferramenta de modelagem tridimensional estou estudando?', entries[0]),
        ('Que assunto sobre corpos celestes estou explorando?', entries[1]),
        ('Que instrumento musical estou praticando?', entries[2]),
        ('Qual capital portuguesa desejo conhecer?', entries[3]),
    ]:
        results = layer.recall_hybrid(query, limit=1, agent_id='morgana')
        assert results and results[0].id == expected.id
    initial_batch = sum(len(x) for x in embedder.calls)
    layer_again, factory2 = build_layer(db, embedder)
    assert layer_again.recall_hybrid('Qual ferramenta de modelagem tridimensional estou estudando?', limit=1)[0].id == entries[0].id
    assert sum(len(x) for x in embedder.calls) == initial_batch + 1  # query only, vectors reused
    with factory2() as session:
        assert session.execute(vectors_table.select()).all()


def test_correction_and_forgetting_never_resurrect_old_vectors(tmp_path):
    provider = SemanticFixture([('editor', 'ambiente de programação'), ('zed',), ('helix',)])
    layer, _ = build_layer(tmp_path / 'update.db', provider)
    old = store(layer, 'meu editor é Zed')
    assert layer.recall_hybrid('qual ambiente de programação eu uso?', limit=3)
    replacement = store(layer, 'meu editor é Helix')
    assert replacement.supersedes_id == old.id
    results = layer.recall_hybrid('qual ambiente de programação eu uso?', limit=3)
    assert results and old.id not in {m.id for m in results}
    assert replacement.id in {m.id for m in results}
    layer.forget(replacement.id)
    assert layer.recall_hybrid('qual ambiente de programação eu uso?', limit=3) == ()
    with layer._semantic_index._factory() as db:
        assert not db.execute(vectors_table.select().where(vectors_table.c.memory_id == str(replacement.id))).all()


def test_agent_inference_kept_private_even_if_semantically_similar(tmp_path):
    provider = SemanticFixture([('meteorologia', 'clima', 'previsão')])
    layer, _ = build_layer(tmp_path / 'agent.db', provider)
    shared = store(layer, 'estou estudando meteorologia')
    private = layer.create_inference(value='talvez tenha interesse em clima', evidence='hipotese de Todd', source_agent_id='todd')
    morgana = layer.recall_hybrid('Qual assunto de previsão climática o usuário estuda?', agent_id='morgana')
    todd = layer.recall_hybrid('Qual assunto de previsão climática o usuário estuda?', agent_id='todd')
    assert shared.id in {m.id for m in morgana}
    assert private.id not in {m.id for m in morgana}
    assert private.id in {m.id for m in todd}


def test_unavailable_embedding_model_degrades_without_fabricating(tmp_path):
    provider = SemanticFixture([('astronomia',)])
    layer, _ = build_layer(tmp_path / 'offline.db', provider)
    memory = store(layer, 'estou estudando astronomia')
    provider.fail = True
    results = layer.recall_hybrid('estou estudando astronomia?', limit=2)
    assert results and results[0].id == memory.id  # lexical fallback, no model selection
    assert layer.recall_hybrid('estou estudando astronomia?', limit=2)


def test_generic_first_person_capture_and_no_sensitive_details(tmp_path):
    extractor = ConservativeMemoryExtractor()
    def candidates(text):
        msg = Message(id=uuid4(), session_id=uuid4(), role=MessageRole.USER, content=text, created_at=datetime.now(UTC))
        return extractor.extract(history_before=[], message=msg)
    assert candidates('comecei um projeto sobre cerâmica artesanal')
    assert candidates('trabalho com instrumentos de medição')
    assert not candidates('qual é seu trabalho?')
    assert not candidates('minha senha é segredo-123')
    assert not candidates('tenho depressão e faço terapia')
    assert not candidates('boa tarde')


def test_ollama_embed_api_contract_and_vector_normalization(monkeypatch):
    from campanario.runtime import semantic_index as module
    import httpx
    observed = {}

    def fake_post(url, *, json, timeout):
        observed['url'] = url
        observed['body'] = json
        observed['timeout'] = timeout
        request = httpx.Request('POST', url)
        return httpx.Response(200, request=request, json={'embeddings': [[3, 4], [0, 5]]})

    monkeypatch.setattr(module.httpx, 'post', fake_post)
    provider = module.OllamaEmbeddingProvider(url='http://127.0.0.1:11434/', model='embeddinggemma')
    out = provider.embed(['primeira frase', 'outra frase'])
    assert observed['url'] == 'http://127.0.0.1:11434/api/embed'
    assert observed['body']['model'] == 'embeddinggemma'
    assert observed['body']['input'] == ['primeira frase', 'outra frase']
    assert out == [[0.6, 0.8], [0.0, 1.0]]


def test_different_embedding_models_never_share_cached_vectors(tmp_path):
    from campanario.runtime.semantic_index import SemanticMemoryIndex
    path = tmp_path / 'models.db'
    provider = SemanticFixture([('cerâmica', 'argila')])
    layer, factory = build_layer(path, provider)
    store(layer, 'comecei a estudar cerâmica')
    assert layer.recall_hybrid('trabalhos com argila?')
    second_provider = SemanticFixture([('cerâmica', 'argila')])
    second_index = SemanticMemoryIndex(factory, second_provider, model_name='new-embedding-model')
    active = layer.list_memories()
    assert second_index.search('trabalhos com argila?', active)
    assert len(second_provider.calls) == 2  # new model must re-index, then embed query
