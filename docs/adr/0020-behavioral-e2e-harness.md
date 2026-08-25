# ADR-0020 — Behavioral E2E Harness no Ollama real

## Contexto

A validacao da fundacao conversacional vinha exigindo que o usuario copiasse manualmente roteiros longos para o chat e depois devolvesse o transcript. Os testes unitarios/deterministicos validam o codigo, mas nao provam o comportamento do modelo local dentro da pipeline real. Ao mesmo tempo, usar o proprio LLM como juiz principal mostrou-se pouco confiavel: autoanalises anteriores ignoraram erros reais e inventaram problemas inexistentes.

## Decisao

Adicionar um harness E2E local e isolado, executado no computador do usuario contra o Ollama realmente configurado.

Fluxo:

`cenarios semanticamente variados -> ChatService real -> Pragmatics/Behavior/Context -> PromptLeakGuard -> Ollama -> checks deterministicos + transcript -> relatorio HTML/JSON/Markdown`

O harness:
- usa SQLite temporario e nao toca o banco principal;
- nao exige API web em execucao;
- usa a mesma configuracao/modelo/temperatura do Campanario;
- varia formulacoes por seed para reduzir overfitting a um roteiro fixo;
- mede propriedades objetivas sem declarar sozinho que uma conversa e natural;
- preserva transcript local para revisao humana;
- nao usa corpus privado nem o modelo como juiz principal.

## Consequencias

- O gate v1.5 deixa de depender de copiar dezenas de mensagens manualmente.
- `TESTAR_COMPORTAMENTO.bat` passa a ser o caminho padrao de validacao no Windows/Ollama.
- `CONSULTAR_ULTIMO_TESTE.bat` reabre o ultimo relatorio.
- `test_reports/` e dado local de teste, fica fora de versionamento/release.
- Revisao humana continua obrigatoria para naturalidade, timing, humor e personalidade.
- Falhas encontradas pelo harness sao evidencia para o proximo incremento, mas nao autorizam hardcode de respostas especificas.
