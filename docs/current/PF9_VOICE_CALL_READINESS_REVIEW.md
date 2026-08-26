# PF9 — Voice / Call Readiness Review

## Resultado
PF9 implementa contratos e uma prova semantica de Call sobre o mesmo Campanario Runtime. Nao existe segundo ChatService, memoria de voz ou Todd/Morgana de voz.

## Fluxo provado

```text
VAD/Wake/STT adapter futuro
        ↓
/ws/v1/call (contrato semantico PF9)
        ↓
VoiceCallCoordinator
        ↓
USER_SPEECH_FINAL
        ↓
ChatService.stream_turn() existente
        ↓
AgentRouter + ParticipationArbiter
        ↓
Todd / Morgana
        ↓
AGENT_RESPONSE_* -> tts_text -> TTS adapter futuro
```

`USER_SPEECH_PARTIAL` e `WAKE_DETECTED` ficam no Event Bus e nao viram memoria. Somente `USER_SPEECH_FINAL` gera o mesmo `USER_TEXT` usado pelos outros clientes.

## Seguranca e provenance
- device precisa estar registrado, trusted/autenticado e anunciar `microphone`;
- PF6 `microphone.listen` so libera enquanto `call_active=True`;
- client_id/device_id permanecem provenance de origem; agent_id permanece quem efetivamente responde;
- `USER_TEXT` causado por voz aponta para o event id de `USER_SPEECH_FINAL`.

## Interruption / barge-in
PF9 publica `AGENT_INTERRUPTED` e possui frame `interrupt_ack` com `cancellation_mode=signal_only`. Isso e contrato de readiness, nao cancelamento real do provider. Cancelamento seguro, corte de TTS e audio full-duplex pertencem a F5 depois de Experience/Learning.

## Fora de escopo confirmado
- audio binario/stream continuo;
- VAD real;
- wake word real;
- STT real;
- TTS real;
- vozes finais Todd/Morgana;
- background call/service;
- Patrulha completa.
