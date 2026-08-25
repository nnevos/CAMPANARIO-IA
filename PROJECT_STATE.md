# PROJECT STATE — Foundation organizada / pre-agentes

## Status

A fundacao conversacional foi congelada apos o bakeoff de modelos e reorganizada para a fase de agentes. O codigo e a evidencia final do estado real.

## Modelo recomendado

`gemma3:12b` e o baseline recomendado atual. Evidencia fornecida: standard 11/11 cenarios e 64/64 checks; mega 75 PASS / 3 FAIL. A arquitetura permanece model-portable.

## Estrutura canonica

- `campanario.chat`: contexto, pragmatica, turns, provenance, prompts e ChatService.
- `campanario.response`: contratos, validacao, reparo e prompt safety.
- `campanario.model`: protocolo/runtime/adapters.
- `campanario.storage`: persistencia.
- `campanario.e2e`: suites e comparacao de modelos.
- `campanario.composition`: composition root.
- `tools/windows`: operacao Windows.
- `docs/current`: estado/arquitetura/roadmap atuais.
- `docs/history`: evolucao historica; nao e documentacao operacional.

## Mudancas de cleanup

- `campanario.llm` removido apos migracao dos imports canonicos.
- `chat/behavior.py` quebrado em modulos menores.
- scripts `.bat` individuais removidos da raiz e acessados por `CAMPANARIO.bat`.
- documentos versionados antigos arquivados.
- `.env`, `.venv`, caches e relatorios nao pertencem ao pacote distribuido.

## Bloqueado ate regressao final

Todd/Morgana ativos, RAG, web, tools, voz e memoria cognitiva.

## Gate atual unico

1. manter suite offline verde;
2. rodar standard E2E com `gemma3:12b` na estrutura organizada;
3. se nao houver regressao arquitetural, congelar este checkpoint;
4. iniciar **Agent Architecture v1** (Todd/Morgana), sem novo tuning da foundation por frase isolada.
