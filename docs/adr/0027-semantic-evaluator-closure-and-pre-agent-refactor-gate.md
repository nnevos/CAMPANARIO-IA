# ADR-0027 — Semantic Evaluator Closure e gate de refatoracao pre-agentes

## Contexto

O E2E v1.5.5 mostrou que o avaliador ainda podia aceitar preambulo fora do formato, promessa generica de simular falsidade e registro simples de contexto transformado em palestra. O usuario tambem definiu que a estrutura atual deve ser refatorada antes da entrada de Todd/Morgana.

## Decisao

1. v1.5.6 endurece runtime e E2E por classes semanticas, sem hardcode de respostas.
2. Pedidos de formato exato consideram todo o output, inclusive preambulos.
3. Em contexto de falsidade conhecida, prometer simular/fingir concordancia viola `truth_over_agreement`.
4. Declaracoes curtas de estado/contexto devem ser reconhecidas sem palestra ou entrevista.
5. Pedidos de primeiro diagnostico tecnico devem priorizar observacao concreta no inicio.
6. Se o gate E2E v1.5.6 estabilizar, o proximo gate obrigatorio e uma refatoracao estrutural. Todd/Morgana e demais agentes permanecem bloqueados ate essa refatoracao passar.

## Consequencias

- o avaliador se torna mais conservador e reduz falsos PASS;
- naturalidade continua exigindo revisao humana;
- o projeto evita multiplicar complexidade de agentes sobre modulos comportamentais ja sobrecarregados.
