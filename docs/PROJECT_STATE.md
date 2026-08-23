# CAMPANARIO — PROJECT STATE / HANDOFF

> ARQUIVO CRÍTICO DE CONTINUIDADE
>
> Leia este documento inteiro antes de modificar o projeto. Ele permite retomar o Campanario mesmo sem acesso ao histórico do chat.
>
> Regra: toda alteração relevante deve atualizar este arquivo no mesmo incremento/entrega.

## 1. Identidade do projeto

Campanario é o sistema completo. Morgana e Todd serão agentes especializados sobre uma infraestrutura cognitiva compartilhada.

Objetivo de longo prazo: assistente pessoal local-first, persistente, modular e extensível, com LLM local, memória, RAG, knowledge graph, internet controlada, ferramentas, voz, agentes e aprendizagem supervisionada/validada.

## 2. Princípios invariantes

- Local-first e funcional offline sempre que possível.
- Internet é ferramenta, não dependência fundamental.
- Monólito modular inicialmente.
- Core próprio.
- Modelo != memória != conhecimento != contexto != ferramentas != persona.
- Dependências externas atrás de interfaces/adapters quando isso protege uma fronteira real.
- Persona != autoridade/permissão.
- Mensagens de chat não são a futura memória cognitiva.
- Não implementar fases futuras antecipadamente.
- Código externo só entra após análise de licença e acoplamento.

## 3. Stack congelada da fundação

- Python 3.12
- FastAPI + Uvicorn
- uv + pyproject.toml + uv.lock
- Pydantic 2 + pydantic-settings
- SQLite
- SQLAlchemy 2.x
- Alembic
- HTTPX
- Ollama atrás de `ModelProvider`
- pytest + pytest-asyncio
- Ruff
- stdlib logging
- pathlib + platformdirs
- UUID
- timestamps UTC
- Git

## 4. Estado real validado em 2026-08-23

Ambiente:
- Windows
- Python 3.12.10
- Ollama 0.32.15
- modelo provisório: `llama3:latest` (4.7 GB)

Validações concluídas:
- `uv run pytest`: 5/5 testes passaram.
- FastAPI iniciou corretamente.
- `/health` retornou `ok`.
- sessão criada via `POST /api/sessions`.
- chat via `POST /api/sessions/{session_id}/chat/stream` funcionou.
- streaming SSE foi recebido token a token.
- caminho real validado: Campanario -> ModelProvider -> OllamaProvider -> Ollama -> llama3.
- mensagem do usuário persistida.
- resposta do assistente persistida com `model = llama3:latest`.
- histórico recuperado via `GET /api/sessions/{session_id}/messages`.
- servidor Uvicorn foi encerrado e iniciado novamente.
- após reinício, a mesma sessão e as mesmas mensagens continuaram disponíveis.
- persistência SQLite após reinício está validada.

Sessão usada no teste:
`8f8ac41d-4beb-4048-887d-d002c748b7f4`

Resposta persistida no teste:
`Olá! Eu recebi sua mensagem e estou pronto para comunicar!`

Observação:
- existe um `StarletteDeprecationWarning` relacionado ao TestClient/httpx. Não bloqueia a Fase 1 e não deve motivar upgrade isolado apenas para silenciar o warning.

## 5. Status da Fase 1

O circuito funcional principal da Fase 1 está VALIDADO:
- sessão;
- chat local;
- streaming;
- Ollama real;
- persistência SQLite;
- recuperação após reinício;
- testes sem dependência de GPU/Ollama.

A Fase 1 ainda precisa de um pequeno endurecimento de bordas antes de ser formalmente encerrada.

## 6. Próximo incremento técnico

**Fase 1 — Hardening mínimo**

Adicionar/testar:
1. sessão inexistente deve retornar erro previsível (idealmente 404);
2. Ollama indisponível deve retornar erro controlado, sem stack trace bruto ao cliente;
3. request vazio/inválido deve ser rejeitado de forma clara;
4. resposta interrompida/parcial deve ter política explícita de persistência;
5. timeout HTTP do Ollama deve ser configurável;
6. logs devem registrar erro operacional sem gravar conteúdo sensível desnecessário;
7. suíte de testes deve continuar funcionando sem Ollama/GPU.

Depois disso:
**encerrar formalmente Fase 1 e iniciar Fase 2 — Context Manager.**

## 7. O que ainda NÃO foi implementado

- Context Manager inteligente.
- sumarização/seleção de contexto.
- memória cognitiva persistente.
- RAG.
- Morgana/Todd.
- internet.
- voz.
- tools/agentes.
- knowledge graph.
- UI própria.

## 8. Protocolo de recuperação

Em uma nova conversa:
1. enviar o projeto completo;
2. pedir para ler `PROJECT_STATE.md` primeiro;
3. ler `docs/ARCHITECTURE.md`, `docs/ROADMAP.md` e ADRs;
4. comparar documentação com código real;
5. não avançar de fase se o gate atual não estiver concluído;
6. se a tarefa tocar conceito de longo prazo, pedir o documento Campanario v2.0;
7. se tocar código open source externo, pedir os snapshots/repositórios correspondentes;
8. ao concluir qualquer incremento, atualizar este arquivo novamente.

## 9. Hardware alvo

- Ryzen 5 8600G
- RTX 5060 Ti 16 GB
- Windows

Prioridade futura de GPU:
LLM > STT quando necessário > embeddings/reranker somente se justificar.
