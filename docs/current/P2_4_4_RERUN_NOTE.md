# P2.4.4 — reexecucao obrigatoria antes do freeze

## Diagnostico do ultimo relatorio recebido

O relatorio seed `1787683144` nao pode ser usado para congelar F2 contra esta arvore de codigo.

A arvore atual ja contem as correcoes P2.4.4 e a regressao local fecha em `335/335`, incluindo:

- check de aritmetica aceitando `144` e `cento e quarenta e quatro`;
- contrato de contribuicao distinta para `mesma pergunta ... nao repete`;
- fechamento `vou trabalhar agora` tratado como despedida, sem herdar commitment anterior.

No relatorio recebido, o checker ainda marcou `cento e quarenta e quatro` como FAIL. Isso nao corresponde ao checker presente nesta arvore (`src/campanario/e2e/scenarios.py`). Portanto a evidencia real precisa ser regenerada a partir desta copia antes de qualquer freeze.

## Gate

1. Executar `tools/windows/TESTAR_LONG_CALL.bat` nesta arvore.
2. Revisar os tres transcripts completos.
3. Se nao houver FAIL objetivo real e os WARNs restantes forem contextuais/naturalidade, registrar explicitamente `Personality/Social/Long-Call Baseline v1 = FROZEN`.
4. Somente entao mudar o gate atual para `F3 Platform Foundation / Runtime v2`.

Nao iniciar F3 antes dessa evidencia.
