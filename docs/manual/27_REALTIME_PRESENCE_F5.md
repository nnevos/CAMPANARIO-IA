# Manual 27 — F5 Realtime Presence checkpoint

A Call starts `attentive`. Saying `Campanario, ...` opens/reopens the attention window; after wake, follow-up speech can continue without repeating the wake phrase. `Todd, ...` and `Morgana, ...` remain ordinary direct-address text for the existing router. Outside the attention window, ambient speech is observable but is not committed as a conversation turn.

A second trusted device may reconnect to `/ws/v1/call` with the same `session_id` and `call_id`; this changes only the transport endpoint. It does not create a new session, memory or agent.

This checkpoint has no final microphone/STT/TTS provider. Do not enable always-on capture or expose the runtime remotely merely because the orchestration exists.
