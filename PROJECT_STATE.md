# CAMPANARIO — PROJECT STATE / HANDOFF

> **ARQUIVO CRÍTICO DE CONTINUIDADE.** Leia antes de alterar o projeto e atualize após cada incremento relevante.

## 1. Estado atual

**Fase 1 — CONCLUÍDA em 2026-08-23.**

Próxima fase autorizada: **Fase 2 — Context Manager**.

Stack congelada da fundação:
- Python 3.12;
- monólito modular;
- FastAPI + Uvicorn;
- uv + `pyproject.toml`;
- Pydantic 2 + pydantic-settings;
- SQLite;
- SQLAlchemy 2.x;
- Alembic;
- HTTPX restrito ao adapter Ollama;
- pytest + pytest-asyncio;
- Ruff;
- UUID e timestamps UTC.

## 2. Hardware/ambiente validado

- Windows.
- Python 3.12.10.
- Ollama 0.32.15.
- Modelo provisório de desenvolvimento: `llama3:latest` (4.7 GB).
- Hardware alvo do projeto: Ryzen 5 8600G + RTX 5060 Ti 16 GB.

O modelo `llama3:latest` **não está congelado como modelo definitivo**. Foi usado apenas para validar infraestrutura.

## 3. Fase 1 — evidências concluídas

Automação:
- pacote deste checkpoint executa **8/8 testes** com sucesso;
- a suíte normal não depende de GPU nem Ollama real.

Validação manual no Windows:
- `/health` funcionando;
- criar/listar sessões funcionando;
- chat real via `ChatService -> ModelProvider -> OllamaProvider -> Ollama`;
- streaming SSE token a token funcionando;
- pergunta e resposta persistidas no SQLite;
- histórico permanece após reiniciar Uvicorn;
- UUID de sessão inexistente retorna `404 {"detail":"Session not found"}`;
- JSON malformado retorna 422;
- `message=""` retorna 422;
- `message="   "` retorna 422 após correção de whitespace;
- entrada whitespace rejeitada após a correção não é persistida;
- Ollama indisponível retorna SSE `model_unavailable` sem derrubar Campanario;
- em falha do modelo, a mensagem do usuário é preservada e nenhuma resposta `assistant` falsa/incompleta é persistida;
- após religar Ollama, o mesmo fluxo volta a responder normalmente;
- teste final respondeu em streaming `Campanario OK.`.

Sessões/IDs de teste são evidência de desenvolvimento e não fazem parte da arquitetura.

## 4. Política de falha congelada na Fase 1

- Mensagem válida recebida do usuário é um evento real e é persistida.
- Falha do modelo não apaga essa mensagem.
- Se a geração não conclui, não persistir uma resposta `assistant` incompleta.
- Erro é comunicado pelo stream.
- Erros do fornecedor são traduzidos na fronteira `ModelProvider`:
  - `ModelUnavailableError`;
  - `ModelTimeoutError`;
  - `ModelResponseError`.
- Camadas superiores não devem conhecer exceções HTTPX/Ollama.
- Não criar ainda tabela `turns`/`generation_attempts`; só reconsiderar com evidência futura.

## 5. Configuração relevante

`CAMPANARIO_OLLAMA_TIMEOUT_SECONDS=120`

O timeout do provider é configurável sem alterar código.

## 6. Dívidas/observações conhecidas

- Warning atual dos testes: `StarletteDeprecationWarning` do `TestClient`/httpx. Não bloqueia o projeto e não deve causar upgrade isolado sem análise coordenada.
- No banco local de desenvolvimento podem existir artefatos manuais antigos, como mensagens `"string"` do corpo padrão do Swagger e uma mensagem whitespace criada antes da correção.
- O SQLite de execução fica fora do repo pelo `platformdirs`; backup de código não equivale a backup dos dados.

## 7. Próximo trabalho autorizado — Fase 2

### Objetivo

Separar **histórico persistido** de **contexto enviado ao modelo**.

Princípio:

`mensagens no banco != contexto do prompt`

### Primeiro incremento

1. criar contrato próprio `ContextManager`;
2. criar implementação inicial de janela recente (`RecentMessagesContextManager` ou nome equivalente);
3. receber histórico completo e devolver mensagens do modelo em ordem cronológica;
4. limitar contexto por orçamento simples/configurável;
5. preservar coerência de turnos quando possível;
6. definir comportamento para mensagem de usuário sem resposta posterior;
7. integrar ao `ChatService`;
8. observabilidade simples do tamanho/quantidade selecionada;
9. testes unitários;
10. **não implementar sumarização ainda**.

### Fora do escopo da Fase 2 inicial

- memória cognitiva;
- memória episódica/semântica;
- RAG;
- embeddings/vector DB;
- Morgana/Todd;
- internet;
- voz;
- tools/agentes;
- knowledge graph;
- UI própria.

## 8. Regra de retomada em outra conversa

1. Ler `RECOVER_FIRST.md` e este arquivo.
2. Conferir código e testes antes de aceitar documentação como verdade.
3. Rodar `uv run pytest` se o ambiente permitir.
4. Considerar Fase 1 encerrada salvo bug real reproduzível.
5. Continuar apenas a Fase 2.
6. Se decisão envolver visão de longo prazo, ler `docs/reference/Projeto_Campanario_v2.0_Documento_de_Conceito.docx`.
7. Se tarefa depender de código open source externo, solicitar o snapshot exato listado em `docs/REFERENCE_MANIFEST.md`.
8. Atualizar handoff após o trabalho.
