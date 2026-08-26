# ADR 0047 — Freeze Candidate Naturality Polish

## Status

Aceito para revalidacao P2.4.3.

## Contexto

O Long Call seed `1787682411` executou 36 turnos com 256 PASS / 3 WARN / 0 FAIL. Dialogue State, Answer Contract, Commitment State, arithmetic correction e ambient call semantics permaneceram estaveis. Os pontos restantes eram de naturalidade e validacao lexical, nao de arquitetura conversacional.

## Decisao

Aplicar um polish estreito antes do freeze de F2:

1. Sob pedido explicito `nao repete`, reduzir o limite de sobreposicao da contribuicao para exigir criterio novo. Isso nao se aplica a concordancia normal.
2. Em perguntas sociais sobre silencio/pensamento em voz alta/presenca ambiente, impedir vocabulario interno de runtime como `protocolo social`, `arbiter`, `o sistema avalia`, `Dialogue State` e `Focus Stack`.
3. Turnos aritmeticos triviais dirigidos recebem limite curto de palavras e nao abrem nova pergunta.
4. Acknowledgements simples (`valeu`, `obrigado/a`) nao abrem novo assunto.
5. O E2E reconhece formulacoes naturais equivalentes para silencio (`prefiro observar`, `nao e necessario`, `sem solicitacao`).

## Nao decidido / fora de escopo

- nao forcar ambos agentes a responder convite condicional `se precisarem`;
- nao alterar Personality Core;
- nao adicionar nova inferencia;
- nao mudar Participation Arbiter;
- nao iniciar Platform Foundation antes da ultima revalidacao Long Call.

## Consequencias

O runtime ganha apenas validacoes locais e mais estreitas. A intencao e reduzir linguagem de documentacao e parafrase sem transformar o sistema em benchmark hardcoded. Se a ultima seed mantiver estabilidade objetiva, F2 pode ser congelada por decisao explicita e F3 liberada.
