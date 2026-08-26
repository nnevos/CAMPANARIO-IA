# Voice Media F5b

F5b extends `/ws/v1/call` without creating a second chat pipeline. Authenticated microphone devices may send signed 16-bit PCM binary frames. The configured media runtime performs VAD/STT; only final recognized speech enters the shared conversation. Agent output emits the existing `tts_text` directive and, when a TTS adapter is configured, `tts_audio` metadata followed by binary audio bytes.

This package intentionally ships with unconfigured STT/TTS adapters. It is a media/runtime contract checkpoint, not a promise that a fresh install can already hear or speak. The next F5 host integration selects and validates actual local engines and devices.
