# Long Call review — seed 1787682411

Modelo: `gemma3:12b`  
Suite: `agent_long_call`  
Resultado: **1 PASS / 2 WARN / 0 FAIL**; **256 PASS / 3 WARN / 0 FAIL**; 36 turnos.

## Leitura humana

P2.4.2 fechou as falhas estruturais que motivaram Dialogue State / Answer Contract:

- retomada tecnica permaneceu no app e no prazo de entrega;
- decisao `manter arquitetura atual` sobreviveu ao fechamento `fechado, seguimos assim`;
- `sequencia curta`, `proximo passo`, `aterrissa isso`, corte/preservacao e sintese da ideia raiz mantiveram binding;
- arithmetic correction cross-turn permaneceu natural (`24 x 6 = 144`) sem vazamento do guard;
- encerramento nao abriu nova tarefa;
- embodiment factual nao apareceu na exploracao criativa.

Os WARN restantes nao justificam nova camada arquitetural:

1. `discordem de mim se precisarem` teve apenas Todd. Como o convite e condicional, forcar Morgana a entrar seria regressao de selective silence. Continua WARN/contextual.
2. O checker de silencio de Morgana estava lexicalmente estreito. A resposta `prefiro observar / input nao e necessario` e semanticamente adequada e deve ser reconhecida.
3. Todd respondeu a `mesma pergunta, mas nao repete` corretamente, mas ainda reutilizou criterios muito proximos dos de Morgana. O contrato deve exigir contribuicao realmente nova quando o usuario explicita nao repeticao.

Tambem apareceram dois pontos de naturalidade nao estruturais:

- conta simples pode receber comentario desnecessario apos o resultado;
- explicacoes sociais podem vazar vocabulario de runtime (`protocolo`, `arbiter`, `sistema avalia`) mesmo quando uma fala natural basta.

## Decisao

Aplicar apenas **P2.4.3 Freeze Candidate Polish**, sem alterar Personality Core, roteamento, Focus Stack, Dialogue State ou Participation Arbiter:

- ampliar o checker de silencio para formulacoes semanticamente equivalentes;
- apertar `distinct_from` apenas quando houver pedido explicito de nao repetir;
- respostas aritmeticas triviais dirigidas ficam curtas;
- semantica social de call rejeita jargon interno quando uma explicacao comum basta;
- `valeu/obrigado` sao acknowledgements sem abertura de nova pergunta.

Depois disso, executar **uma ultima seed Long Call**. Se os bindings objetivos permanecerem verdes e os WARN restantes forem apenas contextuais de participacao, o proximo passo e decidir o freeze de F2 e iniciar F3 Platform Foundation / Runtime v2.

## Latencia observada

- TTFR media: 4.523s
- TTFR p95: 8.016s
- TTFR max: 10.469s
- turno total medio: 5.910s
- multiagente medio: 9.713s

A latencia continua inadequada para a meta futura de voz instantanea, mas nao e blocker do freeze conversacional textual. O problema de realtime sera tratado na Platform/Call architecture, preservando estas metricas como baseline.
