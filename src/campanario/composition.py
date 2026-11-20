from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from campanario.agents.profiles import default_agent_registry
from campanario.chat.behavior import BehaviorContextManager
from campanario.chat.prompts import COMPACT_BEHAVIOR_PROMPT, BALANCED_BEHAVIOR_PROMPT
from campanario.chat.context import RecentMessagesContextManager, SummarizingContextManager
from campanario.chat.service import ChatService
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.chat.zim_wikipedia import OfflineWikipediaZim
from campanario.chat.semantic_library import HybridLocalLibrary, LoopbackOllamaEmbeddings
from campanario.config import Settings
from campanario.model.protocol import ModelProvider
from campanario.model.adapters.ollama import OllamaProvider
from campanario.model.runtime import build_model_provider
from campanario.response.guard import BehaviorResponseGuardProvider
from campanario.runtime.capabilities import CapabilityRegistry
from campanario.runtime.core import CampanarioRuntime
from campanario.runtime.devices import DeviceRegistry
from campanario.runtime.events import RuntimeEventBus
from campanario.runtime.experience import ExperienceLayer
from campanario.runtime.semantic_index import OllamaEmbeddingProvider, SemanticMemoryIndex
from campanario.runtime.memoryllm_chroma import MemoryLLMChromaIndex
from campanario.runtime.permissions import PermissionMode, PermissionPolicy, TrustManager
from campanario.runtime.telemetry import RuntimeTelemetry
from campanario.runtime.presence import PresenceManager
from campanario.modules.audio import build_voice_media
from campanario.response.prompt_safety import PromptLeakGuardProvider, StreamingPromptLeakGuardProvider
from campanario.storage.database import Base, build_engine, build_session_factory
from campanario.storage.repositories import (
    SqlAlchemyChatSessionRepository, SqlAlchemyContextSummaryRepository, SqlAlchemyDeviceRepository, SqlAlchemyMessageRepository, SqlAlchemyTrustRepository, SqlAlchemyExperienceRepository,
)

def build_chat_stack(
    settings: Settings,
    *,
    database_url: str | None = None,
    create_schema: bool = False,
    event_bus: RuntimeEventBus | None = None,
    session_factory=None,
    telemetry: RuntimeTelemetry | None = None,
    experience: ExperienceLayer | None = None,
) -> tuple[ChatService, ModelProvider]:
    """Canonical composition root for API and E2E.

    Returns the chat service plus the raw provider for health/profiling. Model family names never
    enter behavior modules; they remain in Settings/ModelRuntimeConfig.
    """
    if session_factory is None:
        engine = build_engine(database_url) if database_url else build_engine()
        if create_schema:
            Base.metadata.create_all(engine)
        session_factory = build_session_factory(engine)
    runtime = settings.model_runtime
    raw_provider = build_model_provider(runtime)
    if settings.low_latency_mode and settings.live_streaming:
        safe_provider = StreamingPromptLeakGuardProvider(raw_provider)
    else:
        safe_provider = PromptLeakGuardProvider(raw_provider)
    # The old response pipeline could replace spontaneous replies with hard-coded
    # phrases ('Opa.', 'Certo.') and trigger extra full model regenerations.
    response_provider = safe_provider if settings.low_latency_mode else BehaviorResponseGuardProvider(safe_provider)
    recent_context = RecentMessagesContextManager(settings.context_max_messages)
    stored_context = (
        SummarizingContextManager(
            max_messages=settings.context_max_messages,
            summaries=SqlAlchemyContextSummaryRepository(session_factory),
            model_provider=safe_provider, model=runtime.model,
            max_summary_chars=settings.context_summary_max_chars,
        ) if settings.context_auto_summarize else recent_context
    )
    service = ChatService(
        sessions=SqlAlchemyChatSessionRepository(session_factory),
        messages=SqlAlchemyMessageRepository(session_factory),
        model_provider=response_provider,
        context_manager=BehaviorContextManager(
            stored_context,
            prompt=COMPACT_BEHAVIOR_PROMPT if settings.low_latency_mode else BALANCED_BEHAVIOR_PROMPT,
            compact=settings.low_latency_mode,
        ),
        default_model=runtime.model,
        agent_registry=default_agent_registry(),
        participation_provider=safe_provider if settings.participation_arbiter_enabled else None,
        low_latency_mode=settings.low_latency_mode,
        live_streaming=settings.live_streaming,
        web_auto_search=settings.web_auto_search,
        grounded_synthesis=settings.grounded_expression_enabled,
        grounded_expression_retries=settings.grounded_expression_retries,
        local_library=(HybridLocalLibrary(
            settings.data_dir / settings.memory_environment / 'utilidades' / 'utilidades.sqlite3',
            embeddings=LoopbackOllamaEmbeddings(
                url=runtime.base_url, model=settings.library_semantic_model,
                timeout=settings.library_semantic_timeout_seconds,
            ),
            min_similarity=settings.library_semantic_min_similarity,
            max_semantic_segments=settings.library_semantic_max_segments,
        ) if settings.library_semantic_enabled else ReadOnlyLocalLibrary(
            settings.data_dir / settings.memory_environment / 'utilidades' / 'utilidades.sqlite3',
        )),
        zim_library=(OfflineWikipediaZim(
            settings.zim_dir or (settings.data_dir.parent / 'zim'),
            base_url=settings.zim_base_url,
            book_name=settings.zim_book_name,
            timeout_seconds=settings.zim_timeout_seconds,
        ) if settings.zim_enabled else None),
        web_planner_provider=safe_provider if isinstance(raw_provider, OllamaProvider) else None,
        event_bus=event_bus,
        telemetry=telemetry,
        experience=experience,
    )
    if settings.brains_v9_enabled:
        from campanario.brains import BrainRegistry, CapabilityRouter, BrainExecutor
        from campanario.brains.store import BuildStore
        # Use the existing local library Database, never a parallel ingestion store.
        db_path = (service._local_library.database if service._local_library is not None
                   else None)
        builds = BuildStore(session_factory)
        from campanario.brains.agents import make_agent_profile
        from sqlalchemy.exc import SQLAlchemyError
        try:
            for build in builds.list_builds():
                if build.agent_id not in {'morgana', 'todd'}:
                    service._agents.register(make_agent_profile(build))
        except SQLAlchemyError:
            # The existing chat still starts if V9 tables need migration.
            pass
        service.configure_brains(
            BrainExecutor(BrainRegistry.local(db_path), audit=builds.record_run),
            CapabilityRouter(), builds,
            timeout_seconds=settings.brains_v9_timeout_seconds,
            max_memory_mb=settings.brains_v9_max_memory_mb,
        )
    return service, raw_provider


def build_runtime(
    settings: Settings,
    *,
    database_url: str | None = None,
    create_schema: bool = False,
    autostart: bool = True,
) -> CampanarioRuntime:
    """Canonical Campanario runtime composition root, independent from API/UI hosting."""
    runtime_id = uuid4()
    event_bus = RuntimeEventBus(runtime_id)
    telemetry = RuntimeTelemetry(runtime_id)
    telemetry.bind_event_bus(event_bus)
    engine = build_engine(database_url) if database_url else build_engine()
    if create_schema:
        Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    semantic_index = None
    if settings.semantic_memory_enabled:
        embedding_provider = OllamaEmbeddingProvider(
            url=settings.model_runtime.base_url,
            model=settings.semantic_memory_model,
            timeout=settings.semantic_memory_timeout_seconds,
        )
        if settings.semantic_memory_backend == "memoryllm_chroma":
            # Separate by environment; do not merge development and Point Zero.
            try:
                semantic_index = MemoryLLMChromaIndex(
                    settings.data_dir / settings.memory_environment / "memoryllm_chroma",
                    embedding_provider, model_name=settings.semantic_memory_model,
                    min_similarity=settings.semantic_memory_min_similarity,
                    batch_size=settings.semantic_memory_batch_size,
                )
            except ImportError:
                # Test/offline installations without the optional Chroma package
                # must still start. Windows uv sync installs the declared dependency.
                import logging
                logging.getLogger(__name__).warning(
                    "ChromaDB not installed; falling back to existing SQLite semantic index")
                semantic_index = SemanticMemoryIndex(
                    session_factory, embedding_provider,
                    model_name=settings.semantic_memory_model,
                    min_similarity=settings.semantic_memory_min_similarity,
                    batch_size=settings.semantic_memory_batch_size,
                )
        elif settings.semantic_memory_backend == "sqlite":
            semantic_index = SemanticMemoryIndex(
                session_factory, embedding_provider,
                model_name=settings.semantic_memory_model,
                min_similarity=settings.semantic_memory_min_similarity,
                batch_size=settings.semantic_memory_batch_size,
            )
        else:
            raise ValueError("Unknown semantic memory backend")
    experience = ExperienceLayer(
        SqlAlchemyExperienceRepository(session_factory), event_bus, semantic_index=semantic_index,
    )
    service, raw_provider = build_chat_stack(
        settings,
        event_bus=event_bus,
        session_factory=session_factory,
        telemetry=telemetry,
        experience=experience,
    )
    devices = DeviceRegistry(SqlAlchemyDeviceRepository(session_factory), event_bus)
    trust_repository = SqlAlchemyTrustRepository(session_factory)
    trust = TrustManager(trust_repository, devices)
    permissions = PermissionPolicy(trust, trust_repository)
    permissions.set_rule("location.read", PermissionMode.ALLOW_WHILE_SESSION)
    permissions.set_rule("camera.capture", PermissionMode.ASK)
    permissions.set_rule("message.send", PermissionMode.CONFIRM)
    permissions.set_rule("file.delete", PermissionMode.CONFIRM)
    permissions.set_rule("computer.execute", PermissionMode.SCOPED_CONFIRM)
    permissions.set_rule("microphone.listen", PermissionMode.ALLOW_WHILE_CALL)
    tools = CapabilityRegistry(event_bus, permissions)
    from campanario.utilities.integration import register_utilities
    register_utilities(tools)
    permissions.set_rule("utilities.read", PermissionMode.ALLOW_WHILE_SESSION)
    permissions.set_rule("library:read", PermissionMode.ALLOW_WHILE_SESSION)
    # R1: brains and platform capabilities share the same runtime policy.
    # No authorization rule is imported from an AgentBuild or talent.
    if service._brain_executor is not None:
        service._brain_executor.bind_permissions(permissions)
    permissions.set_rule("utilities.write", PermissionMode.CONFIRM)
    presence = PresenceManager(event_bus)
    voice_media = build_voice_media(settings)
    runtime = CampanarioRuntime(
        service, raw_provider, runtime_id=runtime_id, event_bus=event_bus, devices=devices, tools=tools, trust=trust, permissions=permissions, telemetry=telemetry, experience=experience, presence=presence, voice_media=voice_media
    )
    if autostart:
        runtime.start()
    return runtime
