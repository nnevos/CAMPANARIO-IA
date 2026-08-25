# LEIA PRIMEIRO — CAMPANARIO / SAFEPOINT POS-PRESENCE UI

> Leia este arquivo e `PROJECT_STATE.md` antes de qualquer alteracao. Considere o codigo como evidencia final. Nao pule gates.

## Estado canonico congelado

- Foundation conversacional aprovada com `gemma3:12b`.
- Regressao pos-organizacao/presence UI: 11/11 cenarios e 64/64 checks no standard real.
- Campanario e o sistema/ambiente, nunca uma persona.
- Morgana e Todd sao participantes persistentes e pontes entre Campanario e usuario.
- Morgana e a default/primary speaker, mas prioridade nunca significa exclusividade.
- Presence UI v1.3.0 representa o sistema como ambiente/call, sem modos ou seletores obrigatorios de agente.
- AgentRouter + ParticipationArbiter existem; multi-speaker e speaker provenance estao ativos.
- Model runtime e portavel; Gemma 3 12B e recomendado, nao acoplado.
- Voz, wake word, STT/TTS, barge-in e modo call constante AINDA NAO ESTAO IMPLEMENTADOS.
- Memoria cognitiva/evolucao dos agentes AINDA NAO ESTA IMPLEMENTADA.

## Leia nesta ordem

1. `PROJECT_STATE.md`
2. `SAFEPOINT.md`
3. `docs/current/ROADMAP.md`
4. `docs/current/AGENT_ARCHITECTURE.md`
5. `docs/current/AGENT_PERSONALITY_ROADMAP.md`
6. `docs/current/AGENT_TEST_STRATEGY.md`
7. `docs/current/AGENT_LEARNING_STRATEGY.md`
8. `docs/current/ARCHITECTURE.md`
9. `docs/concept/SYSTEM_CONCEPT.md`
10. `UI_UX_PRESENCE_ARCHITECTURE.md`

## Gate atual unico

**PERSONALITY FOUNDATION — Todd/Morgana antes de voz, RAG ou novas capacidades.**

Ordem obrigatoria:

1. formalizar a personalidade-core de Todd e Morgana a partir dos backgrounds e dialogue references ja existentes;
2. nao criar respostas hardcoded para benchmarks;
3. rodar `TESTAR_PERSONALIDADES.bat` com Gemma 3 12B;
4. revisar o transcript comparando os mesmos prompts entre Todd e Morgana;
5. ajustar traits/anti-traits/tendencias sem alterar verdade compartilhada;
6. rodar `TESTAR_PERSONALIDADES_MEGA.bat` com multiplos seeds;
7. validar participacao multiagente: complemento, discordancia, interacao e ausencia de overtalk;
8. congelar um baseline de personalidade;
9. somente entao implementar a camada de experiencia/aprendizado persistente;
10. somente depois da continuidade textual estar estavel iniciar voz/call/wake/STT/TTS/barge-in.

## Regras permanentes

- Campanario nunca e agente/persona;
- Morgana e default primary speaker ate ADR explicito em contrario;
- Todd e Morgana podem estar presentes ao mesmo tempo;
- usuario nao deve gerenciar agentes como modos;
- persona muda perspectiva/comunicacao, nunca fatos/evidencia;
- agentes nao duplicam banco, provider, memoria-base, tools ou knowledge core;
- personalidade-core nao deve sofrer drift silencioso;
- aprendizado futuro usa experiencia/memoria com proveniencia, nao retraining automatico a cada conversa;
- inferencia/opiniao de agente nunca vira fato automaticamente;
- voz/call reutiliza a mesma arquitetura de contexto/participacao; nao cria um segundo Campanario;
- modelos continuam substituiveis;
- nao hardcodar respostas para benchmark;
- fontes privadas brutas nao entram no repositorio;
- toda funcao de usuario atualiza `docs/manual/`;
- mudanca arquitetural relevante exige ADR;
- antes de nova fase, criar/atualizar safepoint e recovery docs.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.
