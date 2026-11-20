"""Real Ollama smoke test for the embeddings index, using only synthetic data.

Run from project root: uv run python tools/maintenance/DIAGNOSTICAR_BUSCA_SEMANTICA.py
No personal conversations are read or written. Nothing goes into production data.
"""
from __future__ import annotations

import sys
import subprocess
import shutil
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from campanario.chat.models import Message, MessageRole
from campanario.config import Settings
from campanario.runtime.experience import ExperienceLayer
from campanario.runtime.semantic_index import OllamaEmbeddingProvider, SemanticMemoryIndex
from campanario.runtime.memoryllm_chroma import MemoryLLMChromaIndex
from campanario.storage.database import Base, build_session_factory
from campanario.storage.repositories import SqlAlchemyExperienceRepository


def main() -> int:
    """Run Chroma in a child process so Windows releases its HNSW file handles.

    ChromaDB can keep its segment files mapped until process termination; disposing
    the SQLite engine alone is not sufficient. The parent owns the temporary folder
    and removes it only *after* the child has exited.
    """
    if len(sys.argv) == 3 and sys.argv[1] == '--diagnostic-worker':
        return _worker(Path(sys.argv[2]))

    temp_path = Path(tempfile.mkdtemp(prefix='campanario_g2_diagnostico_'))
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), '--diagnostic-worker', str(temp_path)],
            check=False,
        )
        return result.returncode
    finally:
        # Cleanup is not part of the retrieval test result. If another process
        # briefly holds a file, report it without falsely failing 4/4 retrieval.
        import time as _time
        for attempt in range(5):
            try:
                shutil.rmtree(temp_path)
                break
            except (PermissionError, OSError) as exc:
                if attempt == 4:
                    print(f'[AVISO] Indice temporario nao removido: {temp_path} ({exc})')
                else:
                    _time.sleep(0.25 * (attempt + 1))


def _worker(temp_path: Path) -> int:
    cfg = Settings()
    print(f"Embeddings Ollama: {cfg.model_runtime.base_url} | modelo: {cfg.semantic_memory_model}", flush=True)
    cases = [
        ('Estou aprendendo modelagem com o Blender.', 'Que software 3D estou estudando?'),
        ('Tenho interesse em astrofotografia.', 'Qual é meu interesse relacionado a estrelas?'),
        ('Pretendo visitar a Patagônia.', 'Para qual região planejo viajar?'),
        ('Meu instrumento musical é o violoncelo.', 'Qual instrumento eu toco?'),
    ]
    engine = create_engine(f"sqlite:///{temp_path / 'diagnostico.db'}", poolclass=NullPool)
    try:
        return _run_diagnostic(engine, cfg, cases, temp_path)
    finally:
        engine.dispose()


def _run_diagnostic(engine, cfg, cases, temp_path) -> int:
        Base.metadata.create_all(engine)
        factory = build_session_factory(engine)
        embedder = OllamaEmbeddingProvider(
            url=cfg.model_runtime.base_url, model=cfg.semantic_memory_model,
            # Cold loading an embedding model can exceed the chat timeout.
            timeout=max(120.0, cfg.semantic_memory_timeout_seconds),
        )
        # Direct ping: unlike lexical fallback, this refuses to report success
        # when the actual embeddings model is not available.
        try:
            vector = embedder.embed(['checagem de modelo de embeddings'])
            print(f"[OK] /api/embed: {len(vector[0])} dimensoes")
        except Exception as exc:
            print(f"[ERRO] /api/embed nao respondeu: {exc}")
            print("O modelo pode estar carregando, o Ollama pode estar ocupado ou sem memoria livre.")
            print("Verifique: ollama list ; ollama ps ; e tente novamente com o chat fechado.")
            return 2
        if cfg.semantic_memory_backend == 'memoryllm_chroma':
            try:
                index = MemoryLLMChromaIndex(
                    temp_path / 'memoryllm_chroma', embedder,
                    model_name=cfg.semantic_memory_model,
                    min_similarity=cfg.semantic_memory_min_similarity)
                print('[OK] Backend: MemoryLLM / ChromaDB persistente')
            except ImportError:
                print('[ERRO] ChromaDB nao instalado. Execute: uv sync --extra voice-host')
                return 4
        else:
            index = SemanticMemoryIndex(factory, embedder, model_name=cfg.semantic_memory_model,
                min_similarity=cfg.semantic_memory_min_similarity)
            print('[OK] Backend: SQLite legado')
        layer = ExperienceLayer(SqlAlchemyExperienceRepository(factory), semantic_index=index)
        expected_ids = []
        for sentence, _ in cases:
            msg = Message(id=uuid4(), session_id=uuid4(), role=MessageRole.USER,
                          content=sentence, created_at=datetime.now(UTC))
            created = layer.observe_user_message(history_before=[], message=msg)
            if not created:
                print(f'[ERRO] Captura falhou para: {sentence}')
                return 3
            expected_ids.append(created[0].id)
        successes = 0
        for (_, question), expected in zip(cases, expected_ids):
            start = time.perf_counter()
            matches = layer.recall_hybrid(question, limit=1, agent_id='morgana')
            elapsed = time.perf_counter() - start
            ok = bool(matches and matches[0].id == expected)
            successes += ok
            print(f"[{'OK' if ok else 'FALHOU'}] {question} ({elapsed:.2f} s)")
            if matches:
                print(f'  Evidencia recuperada: {matches[0].evidence}')
        print(f"Resultado: {successes}/{len(cases)} consultas com o modelo REAL.")
        print('Isso mede recuperacao, nao qualidade da resposta de Todd/Morgana.')
        return 0 if successes == len(cases) else 1


if __name__ == '__main__':
    sys.exit(main())
