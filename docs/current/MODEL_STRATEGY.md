# Estrategia de modelos

## Modelo recomendado atual

**`gemma3:12b`** e o baseline recomendado para esta maquina/projeto com base nos testes fornecidos ate agora.

Ele nao faz parte da identidade do Campanario. E apenas o motor recomendado atual.

## Evidencia atual

- `llama3:latest`: baseline historico com falhas recorrentes de factualidade causal, pragmatica e obediencia simultanea.
- `gemma3:12b`: standard 11/11 e 64/64 checks; mega 75 PASS / 3 FAIL informado pelo usuario.
- Qwen continua candidato valido para comparacoes futuras.

## Troca de modelo

Todos os modelos Ollama usam o mesmo adapter. Para trocar, altere `CAMPANARIO_MODEL_NAME` ou use o menu `CAMPANARIO.bat`.

Trocar o modelo nao reinicia banco, contexto, pragmatica, response pipeline, testes nem futura arquitetura de agentes.

## Regra de avaliacao

Uma troca importante de modelo exige:
1. mesma suite;
2. mesmo seed quando comparando candidatos;
3. standard;
4. mega para candidato principal;
5. leitura humana de uma amostra dos transcripts;
6. considerar latencia/RAM/VRAM alem de PASS bruto.
