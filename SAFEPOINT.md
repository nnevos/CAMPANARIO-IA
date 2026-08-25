# SAFEPOINT — Presence UI -> Agent Personality Foundation

Data do checkpoint: 2026-08-24/25 (sessao atual).

## Motivo

Este checkpoint existe para permitir retomar o projeto em outro chat ou apos falha sem depender da memoria da conversa.

## Baseline que nao deve ser perdido

- Campanario = sistema/ambiente;
- Morgana/Todd = IAs/agentes que habitam o sistema e fazem a ponte com o usuario;
- Morgana = primary/default speaker, nao "modo ativo" exclusivo;
- ambos podem participar, complementar, discordar e falar um com o outro;
- Presence UI deve transmitir "entrar numa call com o Campanario";
- usuario expressa intencao; Campanario coordena;
- Gemma 3 12B e baseline recomendado;
- foundation conversacional nao deve ser reaberta sem evidencia de regressao.

## Proximo trabalho

1. personalidade-core estruturada de Morgana/Todd;
2. teste rapido de personalidade;
3. ajustes por classes de comportamento, nao respostas decoradas;
4. mega teste de personalidade;
5. dialogo multiagente e continuidade longa;
6. congelar personality baseline;
7. Experience/Learning Layer com proveniencia e anti-drift;
8. so depois: modo call/voz (wake, STT, TTS separado por agente, barge-in, background presence).

## Emergencia / rollback

Se uma nova mudanca quebrar a foundation:

- nao tente corrigir apagando historico;
- compare com este safepoint;
- rode standard E2E com Gemma 3 12B;
- preserve banco do usuario separadamente do codigo;
- prefira rollback do codigo a migration destrutiva;
- leia `RECOVER_FIRST.md` e `PROJECT_STATE.md` antes de qualquer patch.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.
