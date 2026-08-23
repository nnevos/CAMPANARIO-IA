from functools import lru_cache

from campanario.chat.service import ChatService
from campanario.config import get_settings
from campanario.llm.ollama import OllamaProvider
from campanario.storage.database import build_engine, build_session_factory
from campanario.storage.repositories import (
    SqlAlchemyChatSessionRepository,
    SqlAlchemyMessageRepository,
)


@lru_cache
def get_chat_service() -> ChatService:
    settings = get_settings()
    engine = build_engine()
    session_factory = build_session_factory(engine)
    return ChatService(
        sessions=SqlAlchemyChatSessionRepository(session_factory),
        messages=SqlAlchemyMessageRepository(session_factory),
        model_provider=OllamaProvider(settings.ollama_base_url, settings.ollama_timeout_seconds),
        default_model=settings.ollama_model,
    )
