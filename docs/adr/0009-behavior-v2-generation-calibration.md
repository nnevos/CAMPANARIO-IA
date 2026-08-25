# ADR-0009 — Calibração comportamental v2 e temperatura configurável

**Status:** Aceito em 2026-08-24.

## Contexto

A fundação comportamental v1 melhorou idioma e uso natural de memória, mas o teste real ainda mostrou
verbosidade desproporcional, perguntas automáticas, callbacks irrelevantes, erros factuais simples e
uma autoanálise genérica que inventou características da arquitetura.

A memória source-aware passou seu gate e não deve ser alterada para resolver esses sintomas. Ativar
Todd/Morgana agora apenas vestiria o mesmo comportamento instável com personas diferentes.

## Decisão

Manter uma única camada comportamental e refiná-la em duas frentes:

1. prompt v2 com proporcionalidade, autoconsciência baseada na conversa, capacidades confirmadas do
   runtime, checagem silenciosa de consistência e redução de padrões mecânicos;
2. `CAMPANARIO_OLLAMA_TEMPERATURE` configurável, default `0.35`, enviado ao Ollama para reduzir
   criatividade em afirmações factuais sem fixar a calibração em código.

Não é adicionada segunda chamada crítica, roteador, RAG ou agente.

## Consequências

- o Context Manager e a persistência permanecem intactos;
- a calibração pode ser ajustada via `.env`;
- a temperatura também se aplica às chamadas do provider usadas na sumarização, favorecendo saída
  estruturada mais determinística;
- factualidade continua limitada pelo modelo local: este gate mede se a combinação é suficiente antes
  de considerar grounding/modelo melhor;
- Todd e Morgana permanecem somente como referências.
