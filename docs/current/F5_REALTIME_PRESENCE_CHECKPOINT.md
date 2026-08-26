# F5 Realtime Presence / Call / Multi-client — checkpoint

Implemented and testable now:
- runtime-owned `present` / `attentive` / `engaged` state;
- 45s conversational attention window;
- wake/address parsing for Campanario, Todd and Morgana;
- ambient speech outside attention does not become a user turn;
- semantic Call remains on the shared Conversation Runtime;
- authenticated PC/mobile call handoff preserves `call_id` + `session_id`;
- cooperative gateway task interruption plus `AGENT_INTERRUPTED` provenance;
- PF8 mobile/client-independent session contracts remain compatible.

Still required before F5 freeze:
- real VAD + streaming STT adapter proof;
- real per-agent TTS/audio output proof;
- media-level barge-in (stop playback + cancellation behavior);
- background audio/service lifecycle proof;
- real multi-client Call E2E across PC/mobile media endpoints;
- decide desktop/tray/hotkey only after the media boundary is stable.

Therefore this checkpoint is functional/testable at orchestration level but must not be described as final voice.
