from functools import lru_cache

from campanario.chat.service import ChatService
from campanario.composition import build_runtime
from campanario.config import get_settings
from campanario.runtime.core import CampanarioRuntime
from campanario.runtime.hosting import RuntimeHost


@lru_cache
def get_runtime_host() -> RuntimeHost:
    """Process-local host. Client adapters must not own or rebuild the runtime themselves."""
    return RuntimeHost(lambda: build_runtime(get_settings(), autostart=False))


def get_runtime() -> CampanarioRuntime:
    """Return the single active process runtime, starting it lazily when necessary."""
    return get_runtime_host().start()


def shutdown_runtime() -> None:
    get_runtime_host().stop()


def get_chat_service() -> ChatService:
    """Legacy compatibility accessor. New client adapters should depend on get_runtime()."""
    return get_runtime().conversation
