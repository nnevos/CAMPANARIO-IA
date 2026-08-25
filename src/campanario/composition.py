from __future__ import annotations

from pathlib import Path

from campanario.chat.behavior import BehaviorContextManager
from campanario.chat.context import SummarizingContextManager
from campanario.chat.service import ChatService
from campanario.config import Settings
from campanario.model.protocol import ModelProvider
from campanario.model.runtime import build_model_provider
from campanario.response.guard import BehaviorResponseGuardProvider
from campanario.response.prompt_safety import PromptLeakGuardProvider
from campanario.storage.database import Base, build_engine, build_session_factory
from campanario.storage.repositories import (
    SqlAlchemyChatSessionRepository, SqlAlchemyContextSummaryRepository, SqlAlchemyMessageRepository,
)

def build_chat_stack(settings: Settings, *, database_url: str | None = None, create_schema: bool = False) -> tuple[ChatService, ModelProvider]:
    """Canonical composition root for API and E2E.

    Returns the chat service plus the raw provider for health/profiling. Model family names never
    enter behavior modules; they remain in Settings/ModelRuntimeConfig.
    """
    engine = build_engine(database_url) if database_url else build_engine()
    if create_schema:
        Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    runtime = settings.model_runtime
    raw_provider = build_model_provider(runtime)
    safe_provider = PromptLeakGuardProvider(raw_provider)
    response_provider = BehaviorResponseGuardProvider(safe_provider)
    service = ChatService(
        sessions=SqlAlchemyChatSessionRepository(session_factory),
        messages=SqlAlchemyMessageRepository(session_factory),
        model_provider=response_provider,
        context_manager=BehaviorContextManager(
            SummarizingContextManager(
                max_messages=settings.context_max_messages,
                summaries=SqlAlchemyContextSummaryRepository(session_factory),
                model_provider=safe_provider,
                model=runtime.model,
                max_summary_chars=settings.context_summary_max_chars,
            )
        ),
        default_model=runtime.model,
    )
    return service, raw_provider
