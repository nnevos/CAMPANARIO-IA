from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from campanario.chat.models import MessageRole


@dataclass(frozen=True, slots=True)
class ModelMessage:
    role: MessageRole
    content: str


@dataclass(frozen=True, slots=True)
class ModelRequest:
    model: str
    messages: tuple[ModelMessage, ...]


@dataclass(frozen=True, slots=True)
class ModelChunk:
    text: str
    done: bool = False


class ModelProvider(Protocol):
    async def health(self) -> bool: ...
    def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]: ...


class FakeModelProvider:
    def __init__(self, response: str = "Olá do Campanario.") -> None:
        self.response = response

    async def health(self) -> bool:
        return True

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]:
        yield ModelChunk(text=self.response)
        yield ModelChunk(text="", done=True)
