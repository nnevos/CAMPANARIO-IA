# 04 - Testes comportamentais

As suites antigas de foundation continuam disponiveis em `tools/windows/regression/conversation/`. O menu raiz agora prioriza operacao atual e F5.

## Standard (regressao historica)

Execute `tools/windows/regression/conversation/TESTAR_COMPORTAMENTO.bat`. Ele usa a pipeline real e o modelo configurado, mas cria um SQLite temporario isolado; suas conversas reais nao sao alteradas.

A suite varia formulacoes e ordem por seed e cobre social, reaction, acknowledgement, topic drop, correcoes, creative->factual, formato, factualidade ancora, discordancia, self-awareness e troca para modo tecnico.

## Mega

Execute `tools/windows/regression/conversation/TESTAR_COMPORTAMENTO_MEGA.bat` quando precisar de regressao ampla. Ele roda varios lotes/seeds e deve ser usado em milestones, troca importante de modelo ou antes de congelar uma foundation.

## Comparar modelos

Escolha **Comparar modelos** para executar candidatos contra a mesma pipeline/seed. O modelo recomendado atual e `gemma3:12b`; Qwen e outros continuam substituiveis.

## Desenvolvimento offline

```text
python -m pytest
python -m compileall src tests
```

## Regra anti-overfitting

Corrija classes de comportamento/arquitetura, nunca a frase exata que apareceu num relatorio.


## Teste de agentes

Use `CAMPANARIO.bat` -> **Testar agentes Todd/Morgana**. A suite usa o modelo configurado e verifica identidade, verdade compartilhada e amostras de estilo. Naturalidade/persona ainda exigem revisao humana do transcript.

## Personalidade Todd/Morgana — regua contextual

`TESTAR_PERSONALIDADES.bat` e `TESTAR_PERSONALIDADES_MEGA.bat` agora mostram duas leituras diferentes no mesmo relatorio:

1. **Conceito individual**: se cada agente exibiu sinais observaveis de seu proprio conceito.
2. **Comparacao pareada Todd x Morgana**: se a diferenca entre os dois foi adequada ao tipo de situacao.

Nem toda pergunta deve separar fortemente os agentes. `urgency` e `simplicity` aceitam convergencia natural; `decision`, `disagreement` e `creative` esperam mais perspectiva propria; `uncertainty`, `technical` e `social` pedem apenas assinatura leve.

Uma marcacao de convergencia no relatorio e **WARN/revisao**, nao ordem para alterar a persona. Leia o par Todd/Morgana antes de qualquer calibracao. O objetivo e evitar tanto o apagamento da personalidade pelo modelo-base quanto caricaturas artificiais.

## Long Call Behavioral E2E

Use `tools\windows\TESTAR_LONG_CALL.bat` para simular a experiencia futura de call antes de existir audio. O teste roda 3 calls textuais de 12 turnos cada, sempre com banco temporario isolado.

Ele mede continuidade, retomada de assuntos, enderecamento Todd/Morgana, participacao dos dois quando agrega valor, silencio seletivo, correcao factual e encerramento natural. O relatorio tambem mede TTFR, tempo total, geracao por speaker e gap do segundo agente.

Este teste e deliberadamente mais demorado que o Behavioral E2E curto. Nao ajuste personalidade por um unico FAIL: leia a sequencia inteira e identifique se o problema e de runtime, participacao, contexto ou personalidade.

