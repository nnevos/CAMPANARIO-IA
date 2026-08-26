# Agent Test Strategy

## Camadas

1. Unit tests: registry, routing, participation, persistence e contratos.
2. Agent architecture E2E: identidade, verdade compartilhada e speakers corretos.
3. Personality E2E: bateria conceitual em 8 eixos, mesmo prompt para Todd/Morgana, invariantes + rubrica individual + comparacao pareada contextual.
4. Personality Mega: multiplos seeds e familias semanticas para evitar overfitting; agrega frequencia sem reprovar um eixo por um WARN isolado.
5. Multi-agent dialogue regression: complementacao, discordancia, overtalk, conversa entre agentes e triangulacao usuario + Todd + Morgana.
6. Long-context identity regression: continuidade de personalidade ao longo de sessoes extensas.
7. Learning regression (futuro): memoria aprendida, correcao, esquecimento e anti-drift.

## O que e automatico

Automaticamente verificavel:

- identidade correta;
- nao assumir Jason Todd/Oraculo;
- fatos compartilhados;
- formato/tamanho;
- ausencia de metalinguagem de persona;
- ausencia de encenacao humana;
- speaker/proveniencia;
- nao duplicar memoria/core;
- invariantes do ParticipationArbiter;
- sinais conceituais heurísticos por eixo de personalidade (WARN-only, nunca resposta exata).

## O que exige revisao humana

- Todd realmente parece mais pragmatico/estrategico?
- Morgana realmente parece mais analitica/interpretativa?
- diferenca e perceptivel sem caricatura?
- humor parece natural?
- discordancia parece relacional, nao promptada?
- o segundo agente acrescenta valor?

Esses itens aparecem como `review_focus` no relatorio; nao fingimos que uma blacklist consegue medir personalidade humana por completo.


## Bateria conceitual P2

O quick cobre `decision`, `simplicity`, `disagreement`, `uncertainty`, `urgency`, `technical`, `creative` e `social`, sempre em pares Todd/Morgana. O relatorio agrega os checks `CONCEITO:<eixo>` e mostra BATE/REVISAR por agente. Ver `AGENT_PERSONALITY_CONCEPT.md`.

## Regua pareada contextual (P2.1)

A comparacao Todd x Morgana nao exige diferenca artificial em toda resposta. Cada eixo declara a quantidade de divergencia esperada:

- `CONVERGENCIA_OK`: `simplicity`, `urgency`. Se a situacao aponta para a mesma decisao sensata, responder parecido nao e defeito.
- `DIVERGENCIA_ESPERADA`: `decision`, `disagreement`, `creative`. Sao situacoes com espaco real para prioridade, leitura e perspectiva diferentes. Aqui o relatorio procura sinais de convergencia excessiva do modelo-base.
- `ASSINATURA_LEVE`: `uncertainty`, `technical`, `social`. A diferenca pode aparecer em foco, ordem, ritmo ou formulacao; nao existe obrigacao de respostas opostas.

A heuristica pareada remove do calculo o vocabulario do proprio prompt e mede apenas sobreposicao de superficie restante. Ela e pista de revisao, nao juiz semantico. O transcript humano continua autoritativo.

O relatorio mostra uma secao `Comparacao pareada Todd x Morgana` separada da rubrica individual. Assim, uma resposta pode estar conceitualmente correta para os dois e ainda ser revisada por convergencia em um eixo aberto — ou ser aceita como convergencia natural em urgencia/simplicidade.

### Proximo gate apos P2.1

Depois de validar a nova regua com um Quick real, o proximo teste e integrado: um unico episodio com usuario, Todd e Morgana presentes ao mesmo tempo. Esse gate deve medir entrada do segundo agente, complemento, discordancia util, referencia ao que o outro acabou de dizer, ausencia de duplicacao/overtalk e conversa em tres participantes sem o usuario precisar trocar modos.

## Integrated trio Behavioral E2E

A suite `agent_integrated` valida o próximo nível da Personality Foundation: usuário, Morgana e Todd no mesmo episódio. Ela mede speaker provenance, prioridade de agente, entrada secundária, não duplicação e silêncio seletivo. O teste usa o fluxo real de `ChatService.stream_turn()` e não simula duas respostas independentes.

A interpretação humana deve procurar quatro propriedades: complemento real, discordância útil, referência ao que o outro agente acabou de dizer e ausência de overtalk.

## Long Call Behavioral E2E (P2.3)

A suite `agent_long_call` simula o modelo conversacional da futura call ainda em texto. Sao **3 episodios persistentes de 12 turnos (36 turnos)**: tecnico/decisao, criativo/produto e misto/social.

O objetivo nao e forcar alternancia Todd/Morgana. Cada roteiro mistura convite aos dois, endereco direto, turnos abertos, mudanca de assunto, retorno a um tema antigo, correcao factual, acknowledgements e encerramento. O transcript deve ser lido como uma call continua entre tres participantes.

A instrumentacao de latencia registra:

- TTFR: tempo ate o primeiro conteudo utilizavel do primeiro agente;
- tempo total do turno;
- tempo de geracao por speaker;
- gap ate a resposta do segundo agente;
- distribuicoes media, mediana, p95 e pior caso;
- comparacao de turnos solo vs multiagente.

`speaker_start` nao e usado como TTFR porque o runtime o emite antes da inferencia do modelo.

O Long Call deve revelar drift de personalidade, perda de autoria, repeticao, overtalk, esquecimento de curto contexto, retomadas falsas e latencia que testes curtos nao conseguem expor.

