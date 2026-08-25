# 04 - Testes comportamentais

Abra `CAMPANARIO.bat`.

## Standard

Escolha **Teste comportamental standard**. Ele usa a pipeline real e o modelo configurado, mas cria um SQLite temporario isolado; suas conversas reais nao sao alteradas.

A suite varia formulacoes e ordem por seed e cobre social, reaction, acknowledgement, topic drop, correcoes, creative->factual, formato, factualidade ancora, discordancia, self-awareness e troca para modo tecnico.

## Mega

Escolha **Mega teste comportamental** quando precisar de regressao ampla. Ele roda varios lotes/seeds e deve ser usado em milestones, troca importante de modelo ou antes de congelar uma foundation.

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
