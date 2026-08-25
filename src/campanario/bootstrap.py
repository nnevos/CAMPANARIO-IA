from functools import lru_cache

from campanario.chat.service import ChatService
from campanario.composition import build_chat_stack
from campanario.config import get_settings

@lru_cache
def get_chat_service() -> ChatService:
    service, _ = build_chat_stack(get_settings())
    return service
