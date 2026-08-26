# Long Call Review — seed 1787678674

## Resultado real

- suite: `agent_long_call`
- modelo: `gemma3:12b`
- 36 turnos
- cenarios: 0 PASS / 3 WARN / 0 FAIL
- checks: 233 PASS / 8 WARN / 0 FAIL

## Leitura humana

A execucao confirma melhora estrutural importante: speaker provenance, vocativo final, correction factual cross-turn, silencio seletivo e ausencia de FAILs permaneceram estaveis. A latencia tambem caiu novamente.

Os WARN remanescentes nao justificam tuning de Personality Core. Eles se concentram em binding pragmatico e semantica de call ambiente.

### 1. Referentes imediatos ainda fracos

- `Todd, se fosse sua decisao hoje...` inventou eixos nao fornecidos (fluxo de dados, modulo, seguranca) em vez de decidir sobre a arquitetura que incomoda sem estar quebrada.
- `Morgana, onde a resposta dele...` pediu contexto que ja existia.
- `sequencia curta` perdeu o diagnostico de latencia.
- `Todd, aterrissa isso...` pediu novamente qual era o conceito.
- `Todd, mesma pergunta...` perguntou qual era a pergunta.

Diagnostico: historico e Focus Stack existem, mas deiticos/follow-ups precisam de uma vinculacao curta e explicita ao referente correto, sem expor vocabulario do runtime.

### 2. Sintese/decisao ainda pode responder a funcao errada

`resume a decisao em uma frase` virou explicacao sobre condensar informacao. A call criativa tambem perdeu o conceito raiz ao sintetizar.

Diagnostico: manter o mesmo tema nao basta; o modelo precisa receber explicitamente a funcao pragmatica do pedido atual.

### 3. Produto criativo perde escolhas do usuario

O ramo criativo preservou parte do tema, mas `qual coisa cortar/preservar` ainda pode pedir contexto ou responder com trait interno. A sintese final deve partir obrigatoriamente de `Campanario como lugar/presenca`, preservando apenas escolhas do usuario como orb/circulo, cores e simplificacao de controles.

### 4. Semantica de call ambiente ainda nao esta formalizada o suficiente

No cenario social, ao dizer que nao quer chamar os agentes pelo nome a todo momento, os agentes ainda sugeriram gatilhos/invocacao. Ao falar em pensar em voz alta, surgiu a ideia errada de usar `Campanario` como sinal para nao responder.

Decisao: em call/presenca continua, nomes sao enderecamento explicito opcional, nao requisito por turno. Pensar em voz alta deve favorecer escuta/silencio por contexto; nao deve exigir palavra magica.

## Latencia

- TTFR media: 4.017s
- TTFR p95: 8.829s
- TTFR max: 9.500s
- turno total medio: 5.172s
- solo medio: 3.936s
- multiagente medio: 8.880s
- gap medio do segundo agente: 4.206s

Comparado aos primeiros Long Calls, o pior silencio percebido caiu de ~18s para <10s nesta seed. Ainda e alto para voz final, mas a tendencia e positiva.

## P2.3e — Reference Binding + Ambient Call Semantics

Implementado sem nova inferencia e sem alterar `profiles.py`:

1. binding explicito e curto para `mesma pergunta`, `resposta/ponto dele/dela`, `aterrissa isso`, `sequencia curta`, `so o essencial`;
2. perguntas `qual coisa cortar/preservar` recebem escolhas recentes definidas pelo usuario, nao traits do agente;
3. `primeira ideia` ancora obrigatoriamente a abertura da call e escolhas/restricoes do usuario;
4. `resume a decisao` e marcado como pedido de conteudo da conclusao, nao meta-explicacao;
5. quando o usuario so afirmou `arquitetura incomoda mas nao esta quebrando`, o briefing proibe inventar modulo, integracao, gargalo, seguranca, fluxo de dados etc.;
6. linguagem residual `tangente recente` foi removida do briefing ativo;
7. Social Protocol formaliza call ambiente: nomes nao sao necessarios a cada turno e pensar em voz alta nao exige palavra magica;
8. Long Call E2E ganhou checks para esses comportamentos.

Personality Core permanece intacto.

## Gate

Reexecutar `tools/windows/TESTAR_LONG_CALL.bat` com Gemma 3 12B. Se nao houver perda semantica material nos tres roteiros, congelar Personality/Social/Long-Call Baseline v1 e iniciar F3 Platform Foundation / Runtime v2.
