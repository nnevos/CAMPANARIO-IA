# 24 — Voice / Call Readiness

PF9 prepara a arquitetura de voz sem fingir que audio final ja existe.

## O que existe
- Call ligada a uma `session_id` existente;
- device autenticado com `microphone`;
- eventos de wake, speech parcial/final, call start/end e interruption;
- speech final entra na mesma conversa Web/Mobile;
- Todd/Morgana continuam usando AgentRouter, ParticipationArbiter, Social Protocol e memoria/contexto compartilhados;
- resposta produz `tts_text` com o `agent_id` correto para um sintetizador futuro.

## Canal de prova

`/ws/v1/call?session_id=...&client_id=...&device_id=...`

Exige `X-Campanario-Device-Credential`.

Frames de entrada PF9: `wake_detected`, `speech_partial`, `speech_final`, `interrupt`, `call_end`.

Frames de saida incluem `call_ready`, `call_event`, `tts_text` e `interrupt_ack`.

## O que ainda nao existe
O canal nao transporta audio bruto e nao possui VAD/STT/TTS reais. `interrupt` e apenas um sinal contratual; cancelamento seguro de geracao/TTS sera implementado somente no gate de Call real.
