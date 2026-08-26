# Long Call Review — seed 1787679961

Modelo: `gemma3:12b`  
Suite: `agent_long_call`  
Resultado: **0 PASS / 2 WARN / 1 FAIL** · **237 PASS / 11 WARN / 1 FAIL**

## Diagnostico

O seed confirmou que speaker provenance, arithmetic correction cross-turn, participacao seletiva e semantica de call ambiente melhoraram. A latencia tambem permaneceu melhor que nas primeiras rodadas (TTFR medio 4.171s; multiagente medio 8.882s).

O problema remanescente nao e Personality Core nem ParticipationArbiter. E **estado dialogico**: o modelo ainda precisa inferir ao mesmo tempo o referente, o objeto em discussao, a funcao do turno e a resposta. Em conversa longa isso falha de maneira probabilistica mesmo quando o historico bruto contem toda a informacao.

Falhas observadas:

- Todd pediu contexto em `qual seria o proximo passo?` apesar da arquitetura ter sido descrita no turno anterior;
- Morgana perdeu o referente de `sequencia curta` logo apos a investigacao de latencia;
- Todd perdeu `mesma pergunta` e `aterrissa isso` mesmo com fala imediatamente anterior disponivel;
- `resume a decisao` virou explicacao sobre resumir, nao a decisao concreta;
- a call criativa perdeu o objeto produto e derivou para papeis/persona/metalinguagem;
- `qual coisa cortar/preservar` podia virar pergunta por contexto ou trait do agente;
- retomadas podiam trocar o app hipotetico pela arquitetura interna do Campanario;
- acknowledgements/encerramentos ainda podiam abrir uma nova pergunta.

## Decisao arquitetural

Nao adicionar outra camada de frases heuristicas ao prompt. Introduzir **P2.4 Dialogue State Compiler**: um compilador deterministico, tipado e sem chamada adicional de LLM que transforma o episodio em um estado curto antes de cada geracao.

O estado contem:

- objeto/objetivo raiz;
- assunto ativo;
- pedido atual resolvido;
- referente imediato quando houver elipse;
- escolhas/restricoes do usuario;
- troca anterior quando a funcao depende dela;
- assuntos suspensos;
- assumptions proibidas;
- sinal de acknowledgement/encerramento.

O historico bruto continua disponivel para estilo/detalhes, mas o estado compilado passa a decidir **qual problema deve ser respondido agora**.

## Gate

Reexecutar `tools/windows/TESTAR_LONG_CALL.bat` apos P2.4. Personality Core permanece intacto. Platform Foundation / Runtime v2 continua bloqueada ate o congelamento de F2.
