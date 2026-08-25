# Roadmap canonico

## F0 — Foundation conversacional — CONCLUIDA

- [x] provider/model portavel;
- [x] Response Contract Pipeline;
- [x] pragmatica/context provenance;
- [x] standard/mega E2E;
- [x] model bakeoff;
- [x] Gemma 3 12B baseline recomendado;
- [x] reorganizacao estrutural;
- [x] standard real pos-organizacao 11/11 · 64/64.

## F1 — Sistema, participantes e Presence UI — CONCLUIDA COMO BASE

- [x] Campanario != agente;
- [x] Morgana default primary speaker;
- [x] Todd/Morgana participantes persistentes;
- [x] AgentRouter;
- [x] ParticipationArbiter;
- [x] multi-speaker/provenance;
- [x] Presence UI orientada a ambiente/call;
- [x] sem modos obrigatorios Todd/Morgana.

## F2 — Agent Personality Foundation — GATE ATUAL

- [ ] consolidar personalidade-core de Todd;
- [ ] consolidar personalidade-core de Morgana;
- [ ] definir traits / anti-traits / tendencies / boundaries;
- [ ] definir comportamento social, tecnico, criativo, discussao e urgencia para cada agente;
- [ ] evitar caricatura/bordoes;
- [ ] quick personality E2E;
- [ ] personality mega E2E;
- [ ] regressao de identidade em contexto longo;
- [ ] regressao de factualidade compartilhada;
- [ ] validar diferenca perceptivel Todd vs Morgana com mesmos prompts;
- [ ] validar multiagente: complementar, discordar, interagir e evitar overtalk;
- [ ] congelar Personality Baseline v1.

## F3 — Experience / Learning Layer

Somente depois de F2.

- [ ] memoria experiencial com source/provenance;
- [ ] preferencias de comunicacao aprendidas;
- [ ] experiencias compartilhadas usuario/agentes;
- [ ] relacao Todd<->usuario, Morgana<->usuario e Todd<->Morgana sem duplicar fatos;
- [ ] inferencia separada de fato;
- [ ] confidence/recency;
- [ ] correcao e esquecimento;
- [ ] anti-drift do core da personalidade;
- [ ] inspecao administrativa da memoria aprendida;
- [ ] testes de aprendizagem e continuidade entre reinicios.

## F4 — Presence Audio / Call Mode

Somente depois de F2 + continuidade minima de F3.

- [ ] estados PRESENTE / ATENTO / ENGAJADO no runtime;
- [ ] wake word `Campanario`;
- [ ] endereco direto `Morgana` / `Todd`;
- [ ] STT streaming;
- [ ] TTS;
- [ ] voz diferente por agente;
- [ ] barge-in;
- [ ] janela conversacional continua sem repetir wake;
- [ ] attention/participation arbiter para calls/grupos;
- [ ] audio background/service;
- [ ] shell desktop/tray/hotkey quando navegador deixar de ser suficiente.

## F5 — Conhecimento e acao ampliados

- [ ] RAG/biblioteca local;
- [ ] web/grounding;
- [ ] tools/automacao;
- [ ] proactive layer;
- [ ] integracoes externas.

## Regra de sequenciamento

**Nao iniciar F4 porque a UI ja parece pronta para voz. Primeiro fechar F2 e a base de F3.** A Presence UI prepara o destino; nao libera pular gates.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.
