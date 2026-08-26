# Agent Learning Strategy — planejamento

## Principio

Morgana e Todd podem se adaptar e desenvolver relacoes/experiencias sem permitir que uma conversa aleatoria reescreva silenciosamente sua identidade central.

## Duas camadas

### Core personality — versionado e estavel

- identidade;
- principios centrais;
- tendencias de raciocinio;
- limites ontologicos/self-aware;
- diferencas fundamentais Todd/Morgana.

Nao muda automaticamente por conversa.

### Experience layer — adaptativa

Pode acumular, com proveniencia:

- preferencias de comunicacao observadas;
- assuntos/interesses recorrentes;
- decisoes e resultados relevantes;
- piadas/referencias relacionais uteis;
- estrategias que funcionaram ou falharam;
- experiencias compartilhadas entre usuario/Morgana/Todd;
- impressao contextual do agente, marcada como inferencia e nunca como fato bruto.

## Aprender com o usuario

O agente pode adaptar ritmo, nivel de detalhe, formas de abordagem e conhecimento relacional. Informacao sensivel ou privada segue as politicas de memoria e nao deve ser absorvida indiscriminadamente.

## Aprender um com o outro

Nao existem dois bancos de verdade. Experiencias podem ser compartilhadas pelo Campanario, preservando quem observou/disse o que. Um agente pode usar uma experiencia do outro como contexto sem copiar sua personalidade.

## Anti-drift

- core nao e reescrito automaticamente;
- inferencia nao vira fato sem evidencia;
- memoria possui source/provenance;
- contradicoes sao preservadas para resolucao, nao sobrescritas silenciosamente;
- deve existir forma futura de inspecionar, corrigir e esquecer memoria aprendida;
- mudanca forte de personalidade exige revisao/versionamento explicito.

## Gate antes de voz/call

A camada de experiencia precisa provar continuidade suficiente em texto antes de receber audio continuo, wake word e participacao em calls.

## Memory Go-Live / Clean Start

A memoria usada durante desenvolvimento nao deve virar silenciosamente a biografia inicial de Todd e Morgana em uso real. A F3 possui um gate explicito de transicao chamado **Memory Go-Live Readiness Gate**.

Quando a Experience Layer estiver funcional e validada, o projeto deve:

1. inspecionar e, se necessario, exportar evidencias/fixtures de teste que precisem ser preservadas;
2. apagar episodios, preferencias, fatos e experiencias aprendidas durante desenvolvimento/testes;
3. preservar Personality Core, contratos versionados, schemas/migrations e fixtures isoladas;
4. executar testes de boot, identidade, continuidade e anti-drift com a memoria limpa;
5. criar um snapshot `Usage Learning Baseline v1`;
6. somente entao considerar novas conversas como experiencias reais capazes de desenvolver a relacao dos agentes com o usuario e entre si.

O reset nao e um mecanismo de treinamento do modelo-base. Ele estabelece uma **origem limpa para aprendizagem por memoria/experiencia**, mantendo o modelo e o Personality Core separados da historia artificial de desenvolvimento.



## F4 Experience / Learning Baseline v1 — ADR 0061

F4 esta concluida. `ExperienceLayer` usa uma unica memoria SQLite compartilhada por Todd/Morgana, com provenance/evidence, confidence, recency/recall, facts/preferences/plans/shared experiences/inferences, supersession, correcao e esquecimento. Captura automatica e conservadora e nao usa outro LLM por turno. A regra de curiosidade e proporcional: perguntar uma informacao do usuario somente quando ela muda materialmente a resposta; nunca inventar nem interrogar para enriquecer perfil. Personality Core permanece congelada. Proximo gate unico: **F5 Realtime Presence / Call / Multi-client**.
