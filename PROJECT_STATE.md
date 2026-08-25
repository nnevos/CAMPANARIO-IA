# PROJECT STATE — Safepoint pre-Personality Foundation

## Status atual

A foundation conversacional e a Presence UI estao estabilizadas com Gemma 3 12B. O projeto entrou oficialmente na fase **Agent Personality Foundation**. Voz/call e aprendizado persistente ainda nao devem ser implementados.

## O que ja foi concluido

### Foundation

- runtime/model provider separado e model-portable;
- Response Contract Pipeline;
- pragmatica/continuation semantics;
- context provenance e isolamento creative->factual;
- E2E standard/mega e model bakeoff;
- Gemma 3 12B escolhido como baseline recomendado apos superar Llama 3 nos testes;
- reorganizacao estrutural pre-agents;
- standard real pos-organizacao: 11/11 cenarios, 64/64 checks.

### Sistema/agentes

- Campanario separado conceitualmente de agentes;
- Morgana = default primary speaker;
- Todd + Morgana = participantes persistentes;
- `AgentRouter` para prioridade/endereco;
- `ParticipationArbiter` para entrada secundaria conservadora;
- `messages.agent_id` registra quem falou;
- `chat_sessions.primary_agent_id` guarda prioridade, nao exclusividade;
- multi-speaker SSE/API/UI.

### UI/UX

- Presence UI v1.3.0;
- experiencia orientada a ambiente/call, nao chatbot convencional;
- sem "Modo Morgana" / "Modo Todd" como UX principal;
- agentes aparecem por participacao, nao por selecao obrigatoria;
- estados conceituais PRESENTE / ATENTO / ENGAJADO preparados visualmente;
- voz ainda e apenas arquitetura/UX preparada, nao funcionalidade simulada.

## Automacao de testes adicionada neste safepoint

- `TESTAR_AGENTES.bat`: invariantes basicas de identidade/factualidade;
- `TESTAR_PERSONALIDADES.bat`: mesmos prompts para Todd/Morgana no mesmo seed;
- `TESTAR_PERSONALIDADES_MEGA.bat`: 8 lotes variados para evitar overfitting;
- checks automaticos medem somente invariantes objetivas;
- diferenca fina de personalidade continua exigindo revisao humana do transcript.

## O que NAO esta pronto

- personalidade profunda/estavel validada de Todd/Morgana;
- aprendizado/evolucao persistente;
- memoria relacional/experiencial de agente;
- RAG/web/tools;
- wake word;
- STT/TTS;
- vozes diferentes;
- barge-in;
- call persistente/background audio;
- proactive layer.

## Gate atual unico

**Agent Personality Foundation.**

Primeiro consolidar personalidade-core + testes. Depois implementar Experience/Learning Layer. Voz/call vem somente depois.

## Modelo recomendado

`gemma3:12b`. Continua sendo configuracao substituivel.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.
