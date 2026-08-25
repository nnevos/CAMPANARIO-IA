# Campanario IA

Sistema pessoal local, persistente e model-portable. A foundation conversacional esta validada com `gemma3:12b`.

## Conceito atual

- **Campanario** = sistema/ambiente, contexto, memoria-base, pipeline, modelos e capacidades.
- **Morgana** = participante persistente e default primary speaker.
- **Todd** = participante persistente.
- Prioridade define quem normalmente fala primeiro; nunca desliga o outro.
- O usuario expressa intencao; o Campanario coordena participacao e execucao.

## Estado de desenvolvimento

Estamos no **Agent Personality Foundation**. Antes de voz/call, devem ser fechados personalidade-core, testes rapidos/mega, continuidade e depois a Experience/Learning Layer.

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

`Build: agent-personality-safepoint-v1.3.1`

Esse identificador existe para impedir confusao com instalacoes antigas na porta 8000.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.
