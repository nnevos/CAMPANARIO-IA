# Model Bakeoff e refatoracao pre-agentes

## Por que existe
O Campanario separa comportamento de modelo. Antes de adicionar agentes, compare motores locais sem alterar a pipeline.

## Como comparar
1. Instale os modelos no Ollama (`ollama pull ...`).
2. Execute `COMPARAR_MODELOS.bat`.
3. Informe os NAMEs exatamente como aparecem em `ollama list`.
4. Use o mesmo seed.
5. Repita com pelo menos 3 seeds.
6. Abra `test_reports/model_bakeoff/comparison.md` e os relatórios individuais.

## Critérios
Naturalidade, factualidade, obediencia, latencia e recursos. PASS bruto nao basta.

## Regra
Nao altere prompts/regexes entre candidatos. Se fizer isso, a comparacao deixa de ser valida.
