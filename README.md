# Campanario IA

Sistema pessoal local, persistente e model-portable. A foundation conversacional esta validada com `gemma3:12b`.

## Conceito atual

- **Campanario** = sistema/ambiente, contexto, memoria-base, pipeline, modelos e capacidades.
- **Morgana** = participante persistente e default primary speaker.
- **Todd** = participante persistente.
- Prioridade define quem normalmente fala primeiro; nunca desliga o outro.
- O usuario expressa intencao; o Campanario coordena participacao e execucao.

## Estado de desenvolvimento

F2 Personality/Social/Long-Call esta congelada. Estamos em **F3 Platform Foundation / Runtime v2**, com PF9 Voice / Call Readiness de contratos concluido.

Leia sempre:

1. `RECOVER_FIRST.md`
2. `PROJECT_STATE.md`
3. `SAFEPOINT.md`

## Uso

No Windows execute `CAMPANARIO.bat`.

Documentacao operacional: `docs/manual/README.md`.

## Modelo

`gemma3:12b` e o baseline recomendado. A arquitetura continua preparada para Qwen/Gemma/outros adapters sem resetar o projeto.

## Build deste safepoint

A UI/API deve informar:

`Build: realtime-presence-f5c-host-voice-checkpoint`

Esse identificador existe para impedir confusao com instalacoes antigas na porta 8000.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.


## Platform Foundation

Estado atual: F3 Runtime v2 congelada (ADR 0060) e F4 Experience / Learning concluida (ADR 0061). Web/PC/Mobile/Call semantica compartilham runtime, sessao e agora memoria experiencial. Proximo gate: F5 Realtime Presence / Call / Multi-client. Consulte `RECOVER_FIRST.md` antes de alterar codigo.

## Platform Foundation / Runtime v2 — F3 frozen

F3 foi concluida no ADR 0060. F4 foi concluida no ADR 0061 com `ExperienceLayer`, memoria experiencial compartilhada, curiosidade proporcional, correcao/esquecimento e continuidade entre reinicios. O proximo gate canonico e **F5 Realtime Presence / Call / Multi-client**.


F4 Experience / Learning foi concluida no ADR 0061. O Campanario agora possui memoria experiencial compartilhada, curiosidade proporcional, correcao/esquecimento e continuidade entre reinicios. Proximo gate: F5 Realtime Presence / Call / Multi-client.


## F5c Host Voice

Host voice integration is ready for target-PC acceptance. See `docs/manual/29_HOST_VOICE_F5C.md` and `tools/windows/DIAGNOSTICO_VOZ_F5C.bat`. F5 is not frozen until physical microphone/speaker acceptance passes.

## F5c.1 — Voice stabilization checkpoint

O primeiro teste fisico confirmou o pipeline de voz e revelou baixa qualidade pt-BR/turnos de ruido. ADR 0065 adiciona idioma/prompt observaveis, teste estrutural de `-l pt`, protecao contra modelo `.en.bin`, filtro estreito de anotacoes de nao-fala, duracao minima de fala e limpeza dos launchers Windows. F5 permanece aberta ate revalidacao fisica no PC alvo.


### F5c.4 — preparar voz em um passo
Se Host Voice reportar `voice_stt_not_configured`, execute `tools\windows\PREPARAR_VOZ_F5C.bat`, reinicie `INICIAR_CAMPANARIO.bat` e so entao `INICIAR_VOZ_HOST_F5C.bat`. O cliente agora encerra no primeiro erro fatal de readiness em vez de imprimir o mesmo erro indefinidamente.

## Current freeze — F5c.4 / ADR 0067

Physical Host Voice now completes the shared Campanario runtime round trip on the target Windows PC. Portuguese STT quality is still the active blocker; F5 is open and F6 must not start yet. See `RECOVER_FIRST.md`, `SAFEPOINT.md` and ADR 0067 before continuing.

### F5c.9 — velocidade de voz

O TTS SAPI agora usa defaults mais rápidos (Todd 4 / Morgana 3) e pode ser ajustado sem editar código com `tools\windows\AJUSTAR_VELOCIDADE_VOZ.bat`. Os rates aceitam `-10..+10` via `CAMPANARIO_VOICE_TODD_RATE` e `CAMPANARIO_VOICE_MORGANA_RATE`.

### F5c.10 — entendimento contínuo e conversa de voz natural

O Host Voice agora segura apenas fragmentos STT com forte sinal de continuação por uma janela curta. Se você continuar falando, o sistema reprocessa o **áudio PCM combinado** no Whisper e só então cria o turno, em vez de mandar pedaços como `Campanario.`, `... de` ou `mais 49` separadamente aos agentes. Respostas no canal de voz recebem orientação de entrega curta/conversacional sem alterar Personality Core. Barge-in também fica mais responsivo e configurável por `CAMPANARIO_VOICE_BARGE_IN_*`.
