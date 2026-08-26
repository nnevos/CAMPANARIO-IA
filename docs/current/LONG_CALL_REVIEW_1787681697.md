# Long Call review — seed 1787681697

Modelo: `gemma3:12b`  
Suite: `agent_long_call`

Resultado automatico: **WARN** — 2 PASS / 1 WARN / 0 FAIL; **254 PASS / 2 WARN / 0 FAIL**.

## O que P2.4.1 confirmou

- `proximo passo` permaneceu ligado a arquitetura em discussao;
- `sequencia curta` permaneceu ligada ao pico de latencia;
- retorno a arquitetura preservou prazo/objeto;
- resumo de decisao ficou concreto;
- `aterrissa isso` resolveu a fala anterior;
- corte/preservacao de produto ficaram ligados a controles/circulo/cores;
- sintese criativa retornou ao conceito `lugar/presenca`;
- `mesma pergunta` deixou de pedir repeticao;
- correction cross-turn manteve 24 x 6 = 144;
- ambient call semantics e despedida sem nova tarefa passaram.

## Lacunas de revisao humana

1. **Commitment consistency**: depois da decisao `priorizar entrega / nao reestruturar`, `fechado, seguimos assim` recebeu uma nova analise contraditoria e ainda desviou para papeis dos agentes.
2. **Contribution distinctness**: Todd repetiu praticamente o mesmo criterio de silencio da Morgana apesar de `nao repete`.
3. **Embodiment boundary**: na abertura criativa houve factualizacao de Todd executando acoes fisicas (`rabiscando pergaminhos`, etc.), quando o conceito permite atmosfera/metafora, nao corpos factuais espontaneos.
4. **Guard naturalness**: correction anchor apareceu na fala como linguagem de validator (`enunciado`, `preserve os operandos`).

Os 2 WARN automaticos restantes sobre ambos entrarem na discordancia criativa sao contextuais e nao justificam forcar overtalk.

## Correcao P2.4.2

Implementar Commitment State, contribution constraint explicita e Embodiment Boundary no Answer Contract. Endurecer E2E para decisao fechada e guard factual invisivel. Nao alterar persona nem adicionar nova inferencia.
