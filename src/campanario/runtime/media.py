from __future__ import annotations

import asyncio
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Protocol

from campanario.runtime.voice import SttSegment, TtsChunk


@dataclass(frozen=True, slots=True)
class PcmFormat:
    sample_rate: int = 16000
    channels: int = 1
    sample_width: int = 2


class StreamingSpeechToText(Protocol):
    async def push(self, audio: bytes, *, final: bool = False) -> SttSegment | None: ...
    async def reset(self) -> None: ...


class StreamingTextToSpeech(Protocol):
    async def synthesize(self, text: str, *, agent_id: str): ...
    async def cancel(self) -> None: ...


class EnergyVad:
    """Small provider-independent PCM VAD suitable as a local fallback/gate.

    It is intentionally not sold as production speech detection. A stronger VAD can implement
    the same adapter boundary without changing Conversation Runtime.
    """
    def __init__(self, *, threshold: int = 450, sample_width: int = 2) -> None:
        self.threshold = threshold
        self.sample_width = sample_width

    async def detect(self, audio: bytes) -> bool:
        if not audio:
            return False
        if self.sample_width != 2:
            raise ValueError("EnergyVad currently requires signed 16-bit PCM")
        usable = len(audio) - (len(audio) % 2)
        if usable == 0:
            return False
        samples = memoryview(audio[:usable]).cast("h")
        rms = math.sqrt(sum(int(sample) * int(sample) for sample in samples) / len(samples))
        return rms >= self.threshold


@dataclass(slots=True)
class UtteranceBuffer:
    """VAD boundary that preserves pre-roll and natural intra-utterance pauses.

    The previous F5c path kept only frames that individually crossed the energy threshold. That
    could clip soft initial consonants and delete low-energy syllables inside a sentence before
    Whisper ever saw them. This buffer uses VAD only to decide start/end boundaries; once speech
    starts, every frame is retained until the configured hangover expires.
    """
    preroll_frames: int = 6
    silence_frames_to_finalize: int = 45
    _preroll: deque[bytes] = field(default_factory=deque, init=False)
    _audio: bytearray = field(default_factory=bytearray, init=False)
    _silence_frames: int = field(default=0, init=False)
    _speech_bytes: int = field(default=0, init=False)

    @property
    def active(self) -> bool:
        return bool(self._audio)

    @property
    def speech_bytes(self) -> int:
        return self._speech_bytes

    def push(self, frame: bytes, *, speaking: bool) -> bytes | None:
        if not self.active:
            if not speaking:
                if self.preroll_frames > 0:
                    self._preroll.append(frame)
                    while len(self._preroll) > self.preroll_frames:
                        self._preroll.popleft()
                return None
            for item in self._preroll:
                self._audio.extend(item)
            self._preroll.clear()
            self._audio.extend(frame)
            self._speech_bytes += len(frame)
            self._silence_frames = 0
            return None

        # Once speech starts, retain all frames. VAD is a boundary detector, not an audio filter.
        self._audio.extend(frame)
        if speaking:
            self._speech_bytes += len(frame)
            self._silence_frames = 0
            return None
        self._silence_frames += 1
        if self._silence_frames < self.silence_frames_to_finalize:
            return None
        return self.finalize()

    def finalize(self) -> bytes:
        value = bytes(self._audio)
        self._audio.clear()
        self._silence_frames = 0
        self._speech_bytes = 0
        self._preroll.clear()
        return value

    def reset(self) -> None:
        self._audio.clear()
        self._preroll.clear()
        self._silence_frames = 0
        self._speech_bytes = 0


@dataclass(slots=True)
class VoiceMediaRuntime:
    stt: StreamingSpeechToText
    tts: StreamingTextToSpeech
    vad: EnergyVad
    pcm: PcmFormat = PcmFormat()
    silence_frames_to_finalize: int = 45
    preroll_frames: int = 6
    min_speech_ms: int = 300
    fragment_hold_ms: int = 1200
    stt_ready: bool = True
    tts_ready: bool = True

    @property
    def min_speech_bytes(self) -> int:
        bytes_per_second = self.pcm.sample_rate * self.pcm.channels * self.pcm.sample_width
        return max(1, int(bytes_per_second * (self.min_speech_ms / 1000.0)))


class UnconfiguredStt:
    async def push(self, audio: bytes, *, final: bool = False) -> SttSegment | None:
        raise RuntimeError("STT adapter is not configured")
    async def reset(self) -> None:
        return None


class UnconfiguredTts:
    async def synthesize(self, text: str, *, agent_id: str):
        raise RuntimeError("TTS adapter is not configured")
        yield TtsChunk(agent_id=agent_id, audio=b"", final=True)
    async def cancel(self) -> None:
        return None


def unconfigured_voice_media() -> VoiceMediaRuntime:
    return VoiceMediaRuntime(
        stt=UnconfiguredStt(),
        tts=UnconfiguredTts(),
        vad=EnergyVad(),
        stt_ready=False,
        tts_ready=False,
    )
