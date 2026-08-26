# ADR 0048 — Freeze gate: equivalencia factual e criterio distinto

## Status
Accepted — P2.4.4.

## Contexto
O seed 1787683144 expôs dois problemas de gate sem nova falha arquitetural: checker aritmetico lexical rejeitando valor correto por extenso e contribuicao `nao repete` semanticamente repetida apesar de baixa sobreposicao lexical. Tambem mostrou despedida herdando commitment indevido.

## Decisao
- checks factuais devem aceitar representacoes semanticamente equivalentes quando o valor e o mesmo;
- `nao repete` exige ao menos um criterio semantico novo em turnos sociais explicitamente pareados;
- fechamento social de trabalho nao cria commitment da fala anterior;
- manter no maximo um retry local; sem segunda inferencia e sem alterar Personality Core.

## Consequencia
O gate final mede comportamento, nao grafia, e impede parafrase vazia sem forcar divergencia em turnos onde o usuario nao a pediu.
