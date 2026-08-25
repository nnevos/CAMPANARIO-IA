# 09 - Solucao de problemas

## Ollama/modelo

- rode `ollama list`;
- confirme que o modelo definido em `.env` existe;
- baseline recomendado atual: `gemma3:12b`.

## Chat nao abre

Confirme o console do servidor e teste `http://127.0.0.1:8000/health`.

## `model_response_error`

Pode indicar falha do provider ou protecao de resposta. Preserve logs tecnicos, mas nao copie dados privados desnecessarios.

## Comportamento parece regressar

Rode o standard pelo `CAMPANARIO.bat`. Nao altere prompt baseado em uma frase isolada; determine se a falha vem de modelo, contexto, response contract, evaluator ou conhecimento faltante.

## Prompt interno apareceu

Pare a conversa e trate como incidente. O prompt leak guard existe para impedir exposicao de instrucoes internas.
