from __future__ import annotations

import asyncio
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from campanario.bootstrap import get_runtime
from campanario.gateway.realtime import _resolve_ws_client, _session_exists
from campanario.runtime.events import EventType
from campanario.runtime.media import UtteranceBuffer
from campanario.runtime.spoken import SpokenOutputBuffer
from campanario.runtime.utterance import join_voice_pcm, likely_incomplete_voice_fragment
from campanario.runtime.voice import VoiceCallCoordinator


router = APIRouter(prefix="/ws/v1")
CALL_GATEWAY_VERSION = "1.0"


class CallReadyFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["1.0"] = CALL_GATEWAY_VERSION
    frame_type: Literal["call_ready"] = "call_ready"
    call_id: UUID
    session_id: UUID
    client_id: str
    device_id: str
    state: str
    presence_state: str = "attentive"


class CallInputFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["1.0"] = CALL_GATEWAY_VERSION
    frame_type: Literal["wake_detected", "speech_partial", "speech_final", "interrupt", "call_end"]
    text: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    phrase: str | None = None
    agent_id: str | None = Field(default=None, max_length=64)
    reason: str | None = Field(default=None, max_length=128)


class CallEventFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["1.0"] = CALL_GATEWAY_VERSION
    frame_type: Literal["call_event"] = "call_event"
    event_type: str
    sequence: int
    agent_id: str | None = None
    text: str | None = None


class TtsTextFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["1.0"] = CALL_GATEWAY_VERSION
    frame_type: Literal["tts_text"] = "tts_text"
    agent_id: str
    text: str
    event_sequence: int


class TtsAudioFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["1.0"] = CALL_GATEWAY_VERSION
    frame_type: Literal["tts_audio"] = "tts_audio"
    agent_id: str
    bytes_length: int
    final: bool = False
    audio_format: str = "pcm_s16le"


class SttFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["1.0"] = CALL_GATEWAY_VERSION
    frame_type: Literal["stt_partial", "stt_final"]
    text: str
    confidence: float | None = None


class InterruptAckFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["1.0"] = CALL_GATEWAY_VERSION
    frame_type: Literal["interrupt_ack"] = "interrupt_ack"
    accepted: bool = True
    cancellation_mode: Literal["cooperative_task"] = "cooperative_task"


@router.websocket("/call")
async def call_channel(
    websocket: WebSocket,
    session_id: UUID = Query(...),
    client_id: str = Query(...),
    device_id: str = Query(...),
    call_id: UUID | None = Query(default=None),
) -> None:
    """PF9 semantic Call contract; no raw audio/STT/TTS engine lives here.

    The client/edge adapter supplies wake and STT text frames. Final speech is routed through the
    exact shared Conversation Runtime. `tts_text` is a synthesis directive, not synthesized audio.
    Interrupt is a versioned signal only in PF9; model cancellation/true barge-in is deferred.
    """
    runtime = get_runtime()
    if not _session_exists(runtime, session_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="session_not_found")
        return
    try:
        identity = _resolve_ws_client(runtime, websocket, client_id, device_id)
    except (ValueError, PermissionError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="device_authentication_failed")
        return

    coordinator = VoiceCallCoordinator(runtime)
    try:
        if call_id is not None:
            existing = runtime.calls.get(call_id)
            if existing is None or existing.session_id != session_id:
                raise ValueError("call_not_found")
            call = coordinator.handoff(call_id, identity)
        else:
            call = coordinator.start(session_id, identity)
    except (ValueError, PermissionError, KeyError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="voice_call_not_authorized")
        return

    await websocket.accept()
    await websocket.send_json(CallReadyFrame(
        call_id=call.call_id,
        session_id=session_id,
        client_id=identity.client_id,
        device_id=device_id,
        state=call.state.value,
        presence_state=runtime.presence.get(session_id).state.value,
    ).model_dump(mode="json"))

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    watched = {
        EventType.USER_SPEECH_PARTIAL,
        EventType.USER_SPEECH_FINAL,
        EventType.WAKE_DETECTED,
        EventType.AGENT_RESPONSE_STARTED,
        EventType.AGENT_RESPONSE_CHUNK,
        EventType.AGENT_RESPONSE_FINISHED,
        EventType.AGENT_INTERRUPTED,
        EventType.CALL_STARTED,
        EventType.CALL_ENDED,
    }

    def on_event(event) -> None:
        if event.session_id != session_id or event.event_type not in watched:
            return
        # Agent events from a cancelled/replaced voice turn must never leak into the current turn.
        if event.event_type in {
            EventType.AGENT_RESPONSE_STARTED,
            EventType.AGENT_RESPONSE_CHUNK,
            EventType.AGENT_RESPONSE_FINISHED,
            EventType.AGENT_INTERRUPTED,
        } and active_turn_correlation_id is not None and event.correlation_id != active_turn_correlation_id:
            return
        loop.call_soon_threadsafe(queue.put_nowait, event)

    subscription_id = runtime.events.subscribe(on_event, event_types=watched)
    turn_task: asyncio.Task | None = None
    active_turn_correlation_id: UUID | None = None
    spoken_output = SpokenOutputBuffer()
    tts_queue: asyncio.Queue[tuple[int, str, str]] = asyncio.Queue()
    tts_epoch = 0
    pending_fragment: tuple[bytes, object] | None = None
    pending_flush_task: asyncio.Task | None = None
    media = runtime.voice_media
    utterance_buffer = UtteranceBuffer(
        preroll_frames=media.preroll_frames,
        silence_frames_to_finalize=media.silence_frames_to_finalize,
    )
    send_lock = asyncio.Lock()

    async def send_json_safe(payload) -> None:
        async with send_lock:
            await websocket.send_json(payload)

    async def synthesize_and_send(text: str, agent_id: str, epoch: int) -> None:
        if epoch != tts_epoch:
            return
        if not media.tts_ready:
            await send_json_safe({
                "schema_version": "1.0",
                "frame_type": "error",
                "error": "voice_tts_not_configured",
                "message": "Runtime voice TTS is not configured.",
            })
            return
        async for chunk in media.tts.synthesize(text, agent_id=agent_id):
            if epoch != tts_epoch:
                return
            async with send_lock:
                await websocket.send_json(TtsAudioFrame(agent_id=agent_id, bytes_length=len(chunk.audio), final=chunk.final, audio_format=chunk.audio_format).model_dump(mode="json"))
                if chunk.audio:
                    runtime.telemetry.mark(
                        "voice_first_audio", session_id=session_id, agent_id=agent_id, client_id=identity.client_id, device_id=device_id, audio_format=chunk.audio_format
                    )
                    await websocket.send_bytes(chunk.audio)

    async def tts_worker() -> None:
        while True:
            epoch, agent_id, text = await tts_queue.get()
            try:
                await synthesize_and_send(text, agent_id, epoch)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                await send_json_safe({
                    "schema_version": "1.0",
                    "frame_type": "error",
                    "error": "voice_tts_failed",
                    "message": str(exc),
                })
            finally:
                tts_queue.task_done()

    async def queue_spoken(text: str, agent_id: str, event_sequence: int) -> None:
        if not text:
            return
        await send_json_safe(TtsTextFrame(
            agent_id=agent_id,
            text=text,
            event_sequence=event_sequence,
        ).model_dump(mode="json"))
        await tts_queue.put((tts_epoch, agent_id, text))

    def clear_tts_queue() -> None:
        while True:
            try:
                tts_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            else:
                tts_queue.task_done()

    async def cancel_active_response() -> None:
        nonlocal turn_task, tts_epoch
        tts_epoch += 1
        spoken_output.clear()
        clear_tts_queue()
        await media.tts.cancel()
        if turn_task is not None and not turn_task.done():
            turn_task.cancel()
            try:
                await turn_task
            except asyncio.CancelledError:
                pass
        turn_task = None

    async def dispatch_stt_final(segment) -> None:
        nonlocal turn_task, active_turn_correlation_id
        runtime.telemetry.mark(
            "voice_end_of_speech", session_id=session_id, client_id=identity.client_id, device_id=device_id
        )
        await send_json_safe(SttFrame(frame_type="stt_final", text=segment.text, confidence=segment.confidence).model_dump(mode="json"))
        # A confirmed new utterance supersedes any still-running response.
        if turn_task is not None and not turn_task.done():
            await cancel_active_response()
        active_turn_correlation_id = uuid4()
        turn_task = asyncio.create_task(consume_final(segment.text, segment.confidence, active_turn_correlation_id))

    async def flush_pending_fragment_after_grace() -> None:
        nonlocal pending_fragment, pending_flush_task
        try:
            await asyncio.sleep(media.fragment_hold_ms / 1000.0)
            item = pending_fragment
            if item is None:
                return
            pending_fragment = None
            pending_flush_task = None
            await dispatch_stt_final(item[1])
        except asyncio.CancelledError:
            raise

    def cancel_pending_flush() -> None:
        nonlocal pending_flush_task
        if pending_flush_task is not None and not pending_flush_task.done():
            pending_flush_task.cancel()
        pending_flush_task = None

    async def consume_audio(data: bytes) -> None:
        nonlocal pending_fragment, pending_flush_task
        if not media.stt_ready:
            await send_json_safe({
                "schema_version": "1.0",
                "frame_type": "error",
                "error": "voice_stt_not_configured",
                "message": "Runtime voice STT is not configured; verify whisper.cpp and a multilingual model before starting Host Voice.",
            })
            return
        speaking = await media.vad.detect(data)
        # New human speech during the grace window proves the previous fragment was not finished.
        if speaking and pending_fragment is not None:
            cancel_pending_flush()
        speech_bytes_before = utterance_buffer.speech_bytes
        utterance = utterance_buffer.push(data, speaking=speaking)
        if speaking:
            segment = await media.stt.push(data, final=False)
            if segment is not None and segment.text.strip():
                coordinator.speech_partial(call.call_id, segment.text, confidence=segment.confidence)
                await send_json_safe(SttFrame(frame_type="stt_partial", text=segment.text, confidence=segment.confidence).model_dump(mode="json"))
        if utterance is None:
            return
        # Count only frames classified as speech for the minimum-speech gate; pre-roll/hangover
        # remain in the WAV for recognition quality but cannot turn pure silence into a user turn.
        speech_bytes = speech_bytes_before
        if speaking:
            speech_bytes += len(data)
        if speech_bytes < media.min_speech_bytes:
            await media.stt.reset()
            return

        recognition_audio = utterance
        if pending_fragment is not None:
            previous_audio, _ = pending_fragment
            recognition_audio = join_voice_pcm(
                previous_audio, utterance,
                sample_rate=media.pcm.sample_rate, channels=media.pcm.channels, sample_width=media.pcm.sample_width,
            )
            pending_fragment = None
            cancel_pending_flush()

        segment = await media.stt.push(recognition_audio, final=True)
        await media.stt.reset()
        if segment is None or not segment.text.strip():
            return

        if media.fragment_hold_ms > 0 and likely_incomplete_voice_fragment(segment.text):
            pending_fragment = (recognition_audio, segment)
            pending_flush_task = asyncio.create_task(flush_pending_fragment_after_grace())
            return

        await dispatch_stt_final(segment)

    async def consume_final(text: str, confidence: float | None, correlation_id: UUID) -> None:
        async for _ in coordinator.speech_final(
            call.call_id, text, confidence=confidence, correlation_id=correlation_id
        ):
            pass

    tts_worker_task = asyncio.create_task(tts_worker())
    receive_task = asyncio.create_task(websocket.receive())
    event_task = asyncio.create_task(queue.get())
    try:
        while True:
            done, _ = await asyncio.wait({receive_task, event_task}, return_when=asyncio.FIRST_COMPLETED)
            if receive_task in done:
                try:
                    message = receive_task.result()
                    if message.get("type") == "websocket.disconnect":
                        raise WebSocketDisconnect(message.get("code", 1000))
                    binary = message.get("bytes")
                    if binary is not None:
                        await consume_audio(binary)
                        receive_task = asyncio.create_task(websocket.receive())
                        continue
                    raw = message.get("text")
                    import json
                    frame = CallInputFrame.model_validate(json.loads(raw or "{}"))
                except (ValidationError, ValueError, TypeError):
                    await send_json_safe({"schema_version": "1.0", "frame_type": "error", "error": "invalid_call_frame"})
                    receive_task = asyncio.create_task(websocket.receive())
                    continue

                if frame.frame_type == "wake_detected":
                    coordinator.wake(call.call_id, phrase=frame.phrase)
                elif frame.frame_type == "speech_partial":
                    coordinator.speech_partial(call.call_id, frame.text or "", confidence=frame.confidence)
                elif frame.frame_type == "speech_final":
                    if turn_task is not None and not turn_task.done():
                        await websocket.send_json({"schema_version": "1.0", "frame_type": "error", "error": "turn_in_progress"})
                    elif (frame.text or "").strip():
                        active_turn_correlation_id = uuid4()
                        turn_task = asyncio.create_task(
                            consume_final(frame.text or "", frame.confidence, active_turn_correlation_id)
                        )
                elif frame.frame_type == "interrupt":
                    if frame.agent_id:
                        coordinator.interrupt(call.call_id, agent_id=frame.agent_id, reason=frame.reason or "barge_in")
                    await cancel_active_response()
                    await websocket.send_json(InterruptAckFrame().model_dump(mode="json"))
                elif frame.frame_type == "call_end":
                    coordinator.end(call.call_id, reason=frame.reason or "client_end")
                    break
                receive_task = asyncio.create_task(websocket.receive())

            if event_task in done:
                event = event_task.result()
                payload = event.payload
                # Preserve the call contract: any final speakable remainder is queued before the
                # response-finished event becomes visible to clients.
                if event.event_type == EventType.AGENT_RESPONSE_FINISHED and payload.get("agent_id"):
                    for spoken in spoken_output.flush(payload["agent_id"]):
                        await queue_spoken(spoken, payload["agent_id"], event.sequence)
                await websocket.send_json(CallEventFrame(
                    event_type=event.event_type.value,
                    sequence=event.sequence,
                    agent_id=payload.get("agent_id"),
                    text=payload.get("text"),
                ).model_dump(mode="json"))
                if event.event_type == EventType.AGENT_RESPONSE_CHUNK and payload.get("agent_id") and payload.get("text"):
                    for spoken in spoken_output.push(payload["agent_id"], payload["text"]):
                        await queue_spoken(spoken, payload["agent_id"], event.sequence)
                event_task = asyncio.create_task(queue.get())
    except WebSocketDisconnect:
        pass
    finally:
        runtime.events.unsubscribe(subscription_id)
        cancel_pending_flush()
        for task in (receive_task, event_task):
            if not task.done():
                task.cancel()
        if turn_task is not None and not turn_task.done():
            turn_task.cancel()
            try:
                await turn_task
            except (asyncio.CancelledError, Exception):
                pass
        spoken_output.clear()
        clear_tts_queue()
        await media.tts.cancel()
        if not tts_worker_task.done():
            tts_worker_task.cancel()
            try:
                await tts_worker_task
            except asyncio.CancelledError:
                pass
        current = runtime.calls.get(call.call_id)
        if current is not None and current.state.value == "active":
            coordinator.end(call.call_id, reason="disconnect")
