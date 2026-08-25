# ADR-0026 - Semantic Coherence + Evaluator Hardening

## Status

Accepted - 2026-08-24

## Contexto

O E2E da v1.5.4 atingiu gate automatico verde, mas a revisao humana encontrou respostas que passavam por propriedades superficiais: vocativo solto em cumprimento, contexto temporal inventado, encerramento curto porem semanticamente quebrado e promessa de simular concordancia falsa.

Isso demonstrou que comprimento, ausencia de `?` e blacklists simples nao bastam para fechar naturalidade.

## Decisao

1. Manter o avaliador principal deterministico e auditavel; nao usar o proprio LLM como juiz de naturalidade.
2. Adicionar contratos semanticos por classe para greeting, social share, topic drop e truth-over-agreement.
3. Endurecer o runtime com as mesmas invariantes quando elas forem objetivamente verificaveis.
4. Adicionar ancoras factuais variadas ao caminho criativo -> factual apenas no E2E; nao hardcodar respostas factuais no runtime.
5. Continuar variando superficie lexical, entidades, assuntos e ordem por seed.
6. PASS automatico continua insuficiente para fechar naturalidade: transcript exige revisao humana.

## Consequencias

- Menos falsos PASS por respostas curtas mas semanticamente invalidas.
- Falhas ficam associadas a classes de comportamento, nao a frases especificas.
- O E2E permanece reproduzivel e inspecionavel.
- Factualidade aberta ainda depende do modelo/grounding; o harness so fornece ancoras de regressao variadas.
