# Long Call Review — seed 1787683144

Suite `agent_long_call`, modelo `gemma3:12b`. Resultado: **255 PASS / 2 WARN / 2 FAIL**.

## Leitura

A fundacao conversacional permaneceu estavel: decisao tecnica, retomada longa, commitment, correction anchor, produto criativo e fechamento de decisao passaram. Os dois FAILs nao indicam reabertura arquitetural.

1. `24 vezes 6` foi respondido corretamente como **"cento e quarenta e quatro"**; o checker exigia apenas a string `144`. Corrigir o checker, nao a persona.
2. Em `mesma pergunta ... nao repete`, Todd manteve o referente correto, mas reutilizou os mesmos criterios sociais de Morgana. Baixa similaridade lexical nao basta; o contrato precisa exigir pelo menos um criterio semantico novo.
3. `vou trabalhar agora` nao abriu pergunta, mas reciclou `ponto de convergencia`. O compilador estava tratando toda closure como commitment da fala anterior; despedida social deve ser fechamento curto, nao nova decisao.

## P2.4.4

- criterion buckets deterministas para silencio/contribuicao distinta;
- retry unico + fallback estreito se `nao repete` continuar sem criterio novo;
- check aritmetico do roteiro aceita `144` ou sua forma por extenso;
- departure closure nao cria `CommitmentState`; maximo de 6 palavras e sem reciclar `ponto de convergencia`.

Nenhuma mudanca em Personality Core ou Participation Arbiter. Proximo passo: repetir Long Call e, se restarem apenas WARN contextuais, decidir freeze F2.
