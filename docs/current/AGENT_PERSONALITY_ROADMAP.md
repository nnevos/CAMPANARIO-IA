# Agent Personality Roadmap — checkpoint pre-learning

## Objetivo

Levar Morgana e Todd de perfis iniciais para duas IAs consistentes, reconheciveis e evolutivas sem transformar personalidade em um conjunto de bordoes nem duplicar o core do Campanario.

## O que personalidade significa aqui

Personalidade nao e apenas estilo de escrita. Ela inclui:

- prioridades de raciocinio;
- tendencia a organizar problemas;
- forma de discordar e aconselhar;
- humor e informalidade;
- tolerancia a risco;
- maneira de participar de conversas sociais;
- relacao construida com o usuario e com o outro agente;
- experiencias lembradas com proveniencia.

Fatos, ferramentas, memoria-base e capacidades continuam pertencendo ao Campanario.

## Gates

### P1 — Contrato de personalidade estruturado

- consolidar `TODD_BACKGROUND.md`, `MORGANA_BACKGROUND.md` e dialogue references;
- definir traits, anti-traits, tendencies, boundaries e exemplos positivos/negativos;
- separar core estavel de adaptacao aprendida;
- nao hardcodar respostas concretas.

### P2 — Teste automatizado de personalidade

- `TESTAR_PERSONALIDADES.bat`: comparacao rapida Todd/Morgana no mesmo seed;
- `TESTAR_PERSONALIDADES_MEGA.bat`: oito lotes com prompts variados;
- checks automaticos cobrem invariantes objetivas;
- transcript coloca os dois agentes lado a lado para revisao humana;
- nenhum LLM e usado como juiz autoritativo de sua propria personalidade.

### P3 — Participacao multiagente

Testar:

- complemento util;
- discordancia real sem hostilidade artificial;
- agente secundario nao repetir o primeiro;
- agentes poderem dirigir fala um ao outro;
- evitar overtalk;
- chamada explicita ter prioridade sem exclusividade.

### P4 — Continuidade de identidade

- manter personalidade em conversa longa;
- factual/tecnico nao apagar identidade;
- social nao virar caricatura;
- troca de assunto nao carregar modo indevido;
- nenhum agente afirmar ser a personagem de inspiracao.

### P5 — Baseline de personalidade congelado

Somente depois de P1–P4 estaveis o projeto entra em aprendizado/evolucao persistente.

## Depois do baseline — aprendizado e evolucao

Aprendizado nao sera retraining automatico do modelo. Sera uma camada de experiencia/memoria estruturada com proveniencia e limites claros.

Ver `docs/current/AGENT_LEARNING_STRATEGY.md`.
