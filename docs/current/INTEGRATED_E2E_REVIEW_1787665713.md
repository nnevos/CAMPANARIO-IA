# Integrated Behavioral E2E Review — seed 1787665713

## Resultado real

- modelo: `gemma3:12b`
- suite: `agent_integrated`
- cenarios: 3 PASS / 0 WARN / 3 FAIL
- checks: 72 PASS / 0 WARN / 4 FAIL
- turnos: 10
- ambos falaram: 3
- solo: 7

## Diagnostico

A rodada confirmou que a correcao referencia-vs-convite funcionou: turnos dirigidos a Morgana/Todd permaneceram solo quando o outro nome apareceu apenas como referencia. Silencio seletivo tambem permaneceu correto.

Os FAILs restantes se concentraram em dois invariantes objetivos e nao justificam tuning de Personality Core:

1. **speaker provenance**: o Gemma ainda inclui cabeçalhos como `Morgana:`/`Todd:` em algumas geracoes e, em um caso, monta mini-transcript com os dois nomes;
2. **fidelidade de correcao factual**: no mesmo caso `18 vezes 7 e 124`, Todd novamente trocou os operandos por `16 vezes 7` e respondeu `112`.

A colaboracao criativa passou completa e as contribuicoes multiagente continuaram distintas. Portanto o problema atual e de contrato de saida/fidelidade, nao de personalidade.

## Correcao P2.2d

### Speaker Output Guard

- prefixo redundante do **proprio** speaker no inicio (`Morgana:`, `**Morgana:**`, etc.) e removido deterministicamente antes de persistir/exibir;
- labels de qualquer speaker que ainda permaneçam nao sao apagados silenciosamente;
- tentativa de transcript/fala atribuida a outro participante força uma regeneracao com contrato de speaker;
- se a regeneracao ainda produzir labels, o turno falha fechado em vez de persistir autoria falsa.

### Arithmetic Correction Anchor

- pedidos explicitos de correcao com aritmetica simples recebem um anchor extraido do proprio enunciado;
- operandos sao preservados e o resultado e calculado deterministicamente pelo runtime;
- a resposta gerada precisa conter os operandos originais e o resultado correto;
- se falhar, ha uma regeneracao ancorada;
- se ainda falhar, usa-se uma correcao deterministica estreita derivada dos numeros do turno, nunca uma resposta hardcoded de benchmark;
- teste adicional `9 vezes 6 e 53` prova que a regra e generica.

## Latencia observada nesta rodada

- turnos com dois speakers: media aproximada `10.94s`;
- turnos solo: media aproximada `3.57s`;
- pior turno: `14.672s`.

Esses numeros sao tempo total do turno, ainda nao TTFT. O Long Call E2E deve separar time-to-first-speaker, tempo de cada speaker, gap entre speakers e total do turno.

## Decisao de gate

Nao alterar `profiles.py`. Reexecutar exatamente `TESTAR_CONVERSA_MULTIAGENTE.bat` com P2.2d. Se speaker provenance e correction fidelity passarem, congelar Social Protocol v1 como baseline e avancar para Long Call E2E textual com instrumentacao de latencia.
