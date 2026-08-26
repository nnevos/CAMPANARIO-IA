# ADR 0046 — Conversational Commitment & Contribution Contract

## Contexto

O Long Call P2.4.1 seed `1787681697` terminou com 254 PASS / 2 WARN / 0 FAIL. O Answer Contract resolveu os bindings objetivos que motivaram P2.4, mas a revisao humana encontrou tres lacunas nao capturadas pelo contrato anterior:

1. uma decisao explicitamente aceita (`fechado, seguimos assim`) podia ser reaberta no proprio acknowledgement;
2. `mesma pergunta, mas nao repete a Morgana` podia produzir uma parafrase quase identica;
3. exploracao criativa podia transformar uma atmosfera metaforica em fatos corporais inventados sobre Todd/Morgana.

O correction anchor tambem podia vazar linguagem do mecanismo (`enunciado`, `operandos`) mesmo preservando o fato.

## Decisao

Adicionar uma camada estreita sobre o Answer Contract existente, sem novo LLM e sem alterar Personality Core:

- `CommitmentState`: a decisao imediatamente aceita pelo usuario vira compromisso fechado para o acknowledgement atual. Sem fato novo ou pedido explicito, o agente nao reabre/reverte a decisao.
- `acknowledgement_only`: respostas de fechamento sao curtas e nao podem recomecar analise. Se a unica regeneracao ainda violar, usar `Entendido.` como fallback conversacional seguro.
- `distinct_from`: somente quando o usuario pede explicitamente para nao repetir, a contribuicao anterior entra como restricao negativa e o runtime valida sobreposicao lexical-semantica conservadora.
- Embodiment Boundary: metafora/atmosfera permanecem permitidas; afirmacoes factuais espontaneas de que Todd/Morgana possuem corpo, ocupam fisicamente o ambiente ou executam acoes corporais sao rejeitadas, salvo ficcao/roleplay explicitamente estabelecido.
- Arithmetic naturalness: resposta que reproduz linguagem do guard nao e considerada valida mesmo com os numeros corretos.

## Consequencias

- decisoes aceitas ficam socialmente estaveis;
- diferenca de contribuicao passa a ser propriedade observavel quando pedida pelo usuario, sem obrigar divergencia em todos os turnos;
- criatividade preserva atmosfera sem encenacao corporal factual;
- guards continuam invisiveis ao usuario;
- nao ha segunda inferencia nem memoria persistente;
- F3 Platform Foundation continua bloqueada ate a revalidacao Long Call e freeze de F2.
