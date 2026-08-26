from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
import stat
import sys
import wave
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from urllib.parse import urlencode
from uuid import UUID, uuid4

import httpx
import websockets

from campanario.config import get_settings
from campanario.runtime.host_voice import probe_host_voice
from campanario.runtime.media import EnergyVad, PcmFormat


@dataclass(slots=True)
class HostCredential:
    device_id: str
    credential: str


class CredentialStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> HostCredential | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return HostCredential(device_id=data["device_id"], credential=data["credential"])

    def save(self, value: HostCredential) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"device_id": value.device_id, "credential": value.credential}, indent=2), encoding="utf-8")
        if os.name != "nt":
            self.path.chmod(stat.S_IRUSR | stat.S_IWUSR)


class SoundDeviceHostAudio:
    """Physical microphone/speaker boundary using sounddevice Raw streams.

    Import is lazy so the core runtime remains usable without PortAudio/sounddevice installed.
    """

    def __init__(
        self,
        *,
        pcm: PcmFormat = PcmFormat(),
        input_device: str | int | None = None,
        output_device: str | int | None = None,
        blocksize: int = 640,
    ) -> None:
        try:
            import sounddevice as sd
        except Exception as exc:
            raise RuntimeError("sounddevice is required: run `uv sync --extra voice-host`") from exc
        self.sd = sd
        self.pcm = pcm
        self.input_device = input_device
        self.output_device = output_device
        self.blocksize = blocksize
        self.input_stream = None
        self.output_stream = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[bytes] | None = None
        self.playing = False

    def list_devices(self):
        return self.sd.query_devices()

    async def start_input(self, queue: asyncio.Queue[bytes]) -> None:
        self._loop = asyncio.get_running_loop()
        self._queue = queue

        def callback(indata, frames, time_info, status):  # noqa: ARG001
            if status:
                print(f"[audio] input status: {status}", file=sys.stderr)
            data = bytes(indata)
            if self._loop is not None and self._queue is not None:
                self._loop.call_soon_threadsafe(self._queue.put_nowait, data)

        self.input_stream = self.sd.RawInputStream(
            samplerate=self.pcm.sample_rate,
            blocksize=self.blocksize,
            device=self.input_device,
            channels=self.pcm.channels,
            dtype="int16",
            callback=callback,
        )
        self.input_stream.start()

    async def play(self, audio: bytes, *, audio_format: str) -> None:
        if not audio:
            return
        if audio_format == "wav":
            with wave.open(io.BytesIO(audio), "rb") as handle:
                channels = handle.getnchannels()
                rate = handle.getframerate()
                width = handle.getsampwidth()
                frames = handle.readframes(handle.getnframes())
            if width != 2:
                raise RuntimeError(f"unsupported WAV sample width: {width}")
            await self._play_raw(frames, sample_rate=rate, channels=channels)
            return
        if audio_format == "pcm_s16le":
            await self._play_raw(audio, sample_rate=self.pcm.sample_rate, channels=self.pcm.channels)
            return
        raise RuntimeError(f"unsupported audio format: {audio_format}")

    async def _play_raw(self, audio: bytes, *, sample_rate: int, channels: int) -> None:
        self.stop_output()
        self.output_stream = self.sd.RawOutputStream(
            samplerate=sample_rate,
            device=self.output_device,
            channels=channels,
            dtype="int16",
        )
        self.output_stream.start()
        self.playing = True
        try:
            await asyncio.to_thread(self.output_stream.write, audio)
        finally:
            self.playing = False
            self.stop_output()

    def stop_output(self) -> None:
        stream = self.output_stream
        self.output_stream = None
        if stream is None:
            return
        try:
            stream.abort()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass
        self.playing = False

    def close(self) -> None:
        self.stop_output()
        if self.input_stream is not None:
            try:
                self.input_stream.stop()
                self.input_stream.close()
            except Exception:
                pass
            self.input_stream = None


class HostVoiceClient:
    def __init__(
        self,
        *,
        http_base: str,
        device_id: str,
        client_id: str,
        credential: str,
        audio: SoundDeviceHostAudio,
        barge_in_threshold: int = 1600,
        barge_in_frames: int = 2,
        barge_in_preroll_frames: int = 6,
    ) -> None:
        self.http_base = http_base.rstrip("/")
        self.ws_base = self.http_base.replace("http://", "ws://").replace("https://", "wss://")
        self.device_id = device_id
        self.client_id = client_id
        self.credential = credential
        self.audio = audio
        self.barge_vad = EnergyVad(threshold=barge_in_threshold)
        self.barge_in_frames = barge_in_frames
        self.barge_in_preroll_frames = max(1, barge_in_preroll_frames)
        self._barge_hits = 0
        self._playback_mic_preroll: deque[bytes] = deque(maxlen=self.barge_in_preroll_frames)
        self._last_stt_final_at: float | None = None
        self._first_audio_reported = False

    async def ensure_session(self, session_id: UUID | None) -> UUID:
        if session_id is not None:
            return session_id
        async with httpx.AsyncClient(base_url=self.http_base, timeout=10) as client:
            response = await client.post("/api/v1/sessions", json={})
            response.raise_for_status()
            return UUID(response.json()["id"])

    async def run(self, session_id: UUID | None = None) -> None:
        session_id = await self.ensure_session(session_id)
        query = urlencode({"session_id": str(session_id), "client_id": self.client_id, "device_id": self.device_id})
        uri = f"{self.ws_base}/ws/v1/call?{query}"
        headers = {"X-Campanario-Device-Credential": self.credential}
        mic_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=100)
        await self.audio.start_input(mic_queue)
        print(f"[Campanario] call session={session_id} device={self.device_id}")
        print("[Campanario] fale normalmente. Ctrl+C encerra.")
        device_uri = f"{self.ws_base}/ws/v1/devices"
        device_hello = {
            "schema_version": "1.0",
            "frame_type": "device_hello",
            "device_id": self.device_id,
            "name": "Campanario Host Voice",
            "device_type": "desktop",
            "capabilities": ["microphone", "speaker"],
        }
        async with websockets.connect(device_uri, additional_headers=headers) as device_ws:
            await device_ws.send(json.dumps(device_hello))
            device_ready = json.loads(await device_ws.recv())
            if not device_ready.get("authenticated"):
                raise RuntimeError("host voice device is not authenticated")
            async with websockets.connect(uri, additional_headers=headers, max_size=16 * 1024 * 1024) as websocket:
                ready = json.loads(await websocket.recv())
                print(f"[Campanario] call_id={ready.get('call_id')} presence={ready.get('presence_state')}")
                sender = asyncio.create_task(self._mic_sender(websocket, mic_queue))
                heartbeat = asyncio.create_task(self._device_heartbeat(device_ws))
                try:
                    pending_audio: dict | None = None
                    while True:
                        message = await websocket.recv()
                        if isinstance(message, bytes):
                            if pending_audio is None:
                                continue
                            before = perf_counter()
                            await self.audio.play(message, audio_format=pending_audio.get("audio_format", "pcm_s16le"))
                            if not self._first_audio_reported and self._last_stt_final_at is not None:
                                first_audio_ms = (before - self._last_stt_final_at) * 1000
                                print(f"[latencia] stt_final -> primeira reproducao: {first_audio_ms:.0f} ms")
                                self._first_audio_reported = True
                            pending_audio = None
                            continue
                        frame = json.loads(message)
                        kind = frame.get("frame_type")
                        if kind == "stt_final":
                            self._last_stt_final_at = perf_counter()
                            self._first_audio_reported = False
                            print(f"voce: {frame.get('text','')}")
                        elif kind == "tts_text":
                            print(f"{frame.get('agent_id')}: {frame.get('text','')}")
                        elif kind == "tts_audio":
                            pending_audio = frame
                        elif kind == "interrupt_ack":
                            print("[barge-in] fala interrompida")
                        elif kind == "error":
                            error_code = frame.get("error", "erro_desconhecido")
                            print(f"[ERRO VOZ] {error_code}: {frame.get('message','')}")
                            if error_code in {"voice_stt_not_configured", "voice_tts_not_configured"}:
                                print("[Campanario] Host Voice encerrado: prepare a voz local e reinicie o Campanario.")
                                return
                finally:
                    sender.cancel()
                    heartbeat.cancel()
                    self.audio.close()


    async def _device_heartbeat(self, websocket) -> None:
        while True:
            await asyncio.sleep(20)
            await websocket.send(json.dumps({"schema_version": "1.0", "frame_type": "ping"}))
            await websocket.recv()

    async def _mic_sender(self, websocket, queue: asyncio.Queue[bytes]) -> None:
        while True:
            data = await queue.get()
            if self.audio.playing:
                # Do not feed loudspeaker echo back into STT. Keep only a tiny local pre-roll so
                # a confirmed human barge-in still preserves the beginning of the interruption.
                self._playback_mic_preroll.append(data)
                speaking = await self.barge_vad.detect(data)
                if speaking:
                    self._barge_hits += 1
                else:
                    self._barge_hits = 0
                if self._barge_hits >= self.barge_in_frames:
                    self.audio.stop_output()
                    await websocket.send(json.dumps({"schema_version": "1.0", "frame_type": "interrupt", "reason": "host_barge_in"}))
                    for buffered in self._playback_mic_preroll:
                        await websocket.send(buffered)
                    self._playback_mic_preroll.clear()
                    self._barge_hits = 0
                # Until a barge-in is confirmed, playback-time microphone frames are echo/noise
                # candidates and must never become user speech on the server.
                continue
            self._playback_mic_preroll.clear()
            self._barge_hits = 0
            await websocket.send(data)


async def register_and_pair(http_base: str, device_id: str, credential_store: CredentialStore) -> HostCredential:
    ws_base = http_base.rstrip("/").replace("http://", "ws://").replace("https://", "wss://")
    uri = f"{ws_base}/ws/v1/devices"
    hello = {
        "schema_version": "1.0",
        "frame_type": "device_hello",
        "device_id": device_id,
        "name": "Campanario Host Voice",
        "device_type": "desktop",
        "capabilities": ["microphone", "speaker"],
    }
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(hello))
        ready = json.loads(await ws.recv())
        if not ready.get("pairing_required") and ready.get("authenticated"):
            raise RuntimeError("device is already paired; use the existing stored credential")
    async with httpx.AsyncClient(base_url=http_base.rstrip("/"), timeout=10) as client:
        response = await client.post(f"/api/v1/devices/{device_id}/pair")
        response.raise_for_status()
        credential = response.json()["credential"]
    value = HostCredential(device_id=device_id, credential=credential)
    credential_store.save(value)
    return value


def _credential_store() -> CredentialStore:
    settings = get_settings()
    return CredentialStore(settings.data_dir / "host_voice_credential.json")


def _coerce_device(value: str | None):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Campanario F5c host voice client")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--device-id", default="host-voice-pc")
    parser.add_argument("--client-id", default=f"host-voice-{uuid4().hex[:8]}")
    parser.add_argument("--session-id")
    parser.add_argument("--input-device")
    parser.add_argument("--output-device")
    parser.add_argument("--pair", action="store_true")
    parser.add_argument("--diagnose", action="store_true")
    parser.add_argument("--list-audio-devices", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    if args.diagnose:
        probe = probe_host_voice(settings)
        print(json.dumps({
            "stt_backend": probe.stt_backend,
            "stt_ready": probe.stt_ready,
            "tts_backend": probe.tts_backend,
            "tts_ready": probe.tts_ready,
            "audio_backend_ready": probe.audio_backend_ready,
            "details": probe.details,
        }, indent=2))
        return

    audio = SoundDeviceHostAudio(input_device=_coerce_device(args.input_device), output_device=_coerce_device(args.output_device))
    if args.list_audio_devices:
        print(audio.list_devices())
        return

    store = _credential_store()
    if args.pair:
        value = asyncio.run(register_and_pair(args.server, args.device_id, store))
        print(f"[Campanario] paired {value.device_id}; credential stored in {store.path}")
        return
    credential = store.load()
    if credential is None or credential.device_id != args.device_id:
        raise SystemExit(f"No credential for {args.device_id}. Run first with --pair")
    client = HostVoiceClient(
        http_base=args.server,
        device_id=args.device_id,
        client_id=args.client_id,
        credential=credential.credential,
        audio=audio,
        barge_in_threshold=settings.voice_barge_in_threshold,
        barge_in_frames=settings.voice_barge_in_frames,
        barge_in_preroll_frames=settings.voice_barge_in_preroll_frames,
    )
    try:
        asyncio.run(client.run(UUID(args.session_id) if args.session_id else None))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
