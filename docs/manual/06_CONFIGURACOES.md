# 06 - Configuracoes e modelos

Configuracoes locais ficam em `.env`; o arquivo nao deve ser versionado/distribuido.

## Principais variaveis

- `CAMPANARIO_MODEL_PROVIDER=ollama`
- `CAMPANARIO_MODEL_NAME=gemma3:12b` (recomendado atual)
- `CAMPANARIO_MODEL_BASE_URL=http://127.0.0.1:11434`
- `CAMPANARIO_MODEL_TIMEOUT_SECONDS=120`
- `CAMPANARIO_MODEL_TEMPERATURE=0.35`
- `CAMPANARIO_CONTEXT_MAX_MESSAGES=20`
- `CAMPANARIO_CONTEXT_SUMMARY_MAX_CHARS=4000`

Aliases `CAMPANARIO_OLLAMA_*` antigos existem apenas por compatibilidade.

## Trocar modelo

Execute `CAMPANARIO.bat` -> **Trocar modelo**. O launcher lista os modelos instalados no Ollama e atualiza `.env`.

Trocar Llama/Gemma/Qwen nao altera banco, contexto, response pipeline ou futura memoria/agentes. Depois de uma troca importante, rode o standard E2E.
