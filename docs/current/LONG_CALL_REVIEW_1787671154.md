# Long Call Review — seed 1787671154

## Resultado

- suite: `agent_long_call` / Gemma 3 12B;
- 36 turnos;
- 230 PASS / 7 WARN / 2 FAIL;
- 9 turnos multiagente / 27 solo;
- Morgana 26 participacoes / Todd 19.

## Latencia

- TTFR media 4.429s; mediana 3.695s; p95 9.25s; max 12.14s;
- turno total media 5.657s; p95 15.422s; max 15.687s;
- solo media 4.293s;
- multiagente media 9.748s;
- gap segundo agente media 4.426s;
- Morgana media 4.004s; Todd media 2.89s.

## Diagnostico

### 1. Contexto interno vazou para a fala
Morgana produziu `IDENT abre outro frame...` e depois `O frame esta fechado`. O problema nao e personalidade; o prompt de grounding descrevia sua propria implementacao de forma excessivamente literal.

### 2. Referente imediato ainda se perde
`nao quero vinte hipoteses; me deem uma sequencia curta` perdeu o diagnostico de latencia. `Todd, mesma pergunta pra voce` perdeu a pergunta anterior. `Todd, aterrissa isso` tambem pediu contexto novamente.

### 3. Factual correction entre turnos falhou
A pergunta `24 vezes 6` estava num turno anterior; no turno de correcao havia apenas `ela respondeu 142`. O anchor antigo extraia aritmetica apenas do turno atual e portanto nao foi ativado; Todd respondeu 143.

### 4. Hallucination de componentes
Na call tecnica surgiram `ferramenta de analise de dados`, `sistema de relatorios`, `componente X`, `sistema Y`, `modulo Z` sem terem sido fornecidos pelo usuario. A conversa manteve o tema macro, mas fabricou detalhes.

### 5. Sintese criativa ainda perdeu o objeto
A primeira ideia era Campanario como lugar/presenca com circulo, cores e simplicidade. A sintese final virou uma ferramenta de automacao inexistente. O root estava presente no contexto, mas a recencia de respostas dos agentes ainda dominou a geracao.

## Mudancas P2.3d

- briefing de continuidade compacto e sem vocabulario de implementacao;
- reforco de pedido anterior/fala anterior para elipses;
- anchors concretos citados pelo usuario;
- proibicao explicita de inventar componentes/requisitos;
- correction anchor cross-turn;
- guard de prompt ampliado para metadados de continuidade;
- checks do Long Call endurecidos.

## Decisao

Nao congelar a foundation conversacional ainda. Reexecutar o mesmo Long Call apos P2.3d. Platform Foundation / Runtime v2 fica registrada como fase futura imediatamente apos o congelamento do baseline conversacional; nao iniciar antes deste gate passar.
