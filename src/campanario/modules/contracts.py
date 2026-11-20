"""Small provider interfaces. Contracts, NOT a working TTS or GPS implementation."""
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SpeechChunk:
    data: bytes
    media_type: str
    agent_id: str
    final: bool = False


class SpeechProvider(Protocol):
    def speak(self, text: str, agent_id: str) -> AsyncIterator[SpeechChunk]: ...
    async def cancel(self) -> None: ...


@dataclass(frozen=True)
class Position:
    latitude: float
    longitude: float
    accuracy_m: float
    captured_at: datetime
    source: str

    def __post_init__(self):
        if not (-90 <= self.latitude <= 90 and -180 <= self.longitude <= 180):
            raise ValueError("Coordinates out of range")
        if self.accuracy_m < 0 or self.captured_at.tzinfo is None:
            raise ValueError("Accuracy and timezone are required")


class LocationProvider(Protocol):
    async def request_permission(self) -> bool: ...
    async def current_position(self) -> Position: ...
    async def stop(self) -> None: ...
