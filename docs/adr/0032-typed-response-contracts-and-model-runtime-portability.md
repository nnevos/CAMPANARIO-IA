# ADR-0032 — Typed Response Contracts and Model Runtime Portability

## Status
Accepted — Conversational v1.6.1.

## Context
O E2E real da v1.6.0 mostrou que fallback de self-awareness podia substituir uma resposta criativa inteira.
O mesmo ciclo confirmou que a qualidade factual varia bastante com `llama3:latest`. O sistema precisa
preservar comportamento mesmo quando o modelo e trocado.

## Decision
1. `ResponseContract` passa a carregar `ResponseKind` explicito.
2. Reparos/fallbacks fechados sao selecionados pelo **tipo compilado do turno**, nao por uma blacklist global.
3. `creative`, `factual` e `technical` nunca podem herdar fallback de `self_aware`/social.
4. A deteccao de claims emocionais continua ativa em atos sociais/identitarios, mas nao sequestra criacao factual/tecnica.
5. Configuracao de modelo passa a usar `CAMPANARIO_MODEL_*` e `ModelRuntimeConfig`.
6. `bootstrap` e E2E constroem o adapter via `build_model_provider`; hoje Ollama e o primeiro backend.
7. Variaveis `CAMPANARIO_OLLAMA_*` permanecem somente como compatibilidade.
8. Troca de modelo exige revalidacao E2E, nao reescrita de comportamento.

## Consequences
- Falhas de um modelo ficam mais isoladas da politica do Campanario.
- A troca llama3 -> outro modelo Ollama e configuracao, nao migracao de arquitetura.
- Backends futuros podem ser adicionados atras de `ModelProvider`.
- O projeto ainda depende da qualidade epistemica do modelo para conhecimento aberto; grounding continua trilha futura.
