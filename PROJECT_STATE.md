# CAMPANARIO — PROJECT STATE / HANDOFF

> **ARQUIVO CRÍTICO DE CONTINUIDADE**
>
> Leia este documento inteiro antes de modificar o projeto. Ele existe para permitir a retomada do Campanario mesmo sem acesso a qualquer conversa anterior.
>
> **Regra:** toda alteração relevante no projeto deve atualizar este arquivo no mesmo commit/entrega.

## 1. Identidade do projeto

**Campanario** é o sistema completo. Morgana e Todd serão agentes especializados sobre uma infraestrutura cognitiva compartilhada. Não são dois sistemas independentes.

Objetivo de longo prazo: assistente pessoal local-first, persistente, modular e extensível, com LLM local, memória, RAG, knowledge graph, internet controlada, ferramentas, voz, agentes e aprendizagem supervisionada/validada.

## 2. Princípios invariantes

- Local-first e funcional offline sempre que possível.
- Internet é ferramenta, não dependência fundamental.
- Monólito modular inicialmente; sem microserviços prematuros.
- Core próprio; não transformar o projeto em fork de Open WebUI, Khoj, Row-Bot etc.
- Modelo != memória != conhecimento != contexto != ferramentas != persona.
- Dependências externas ficam atrás de interfaces/adapters quando isso protege uma fronteira real.
- Persona != autoridade/permissão.
- Não tratar RAG ou armazenamento como treinamento.
- Fine-tuning somente com justificativa posterior.
- Não implementar fases futuras antecipadamente.
- Morgana e Todd podem compartilhar o mesmo LLM; não carregar dois modelos apenas para simular personas.
- Mensagens de chat NÃO são a futura memória persistente do sistema.
- Código externo só pode ser incorporado após conferência de licença e acoplamento.

## 3. Stack congelada da fundação

- Python: 3.12
- Arquitetura: monólito modular
- API: FastAPI + Uvicorn
- Dependências/ambiente: uv + pyproject.toml + uv.lock (lock será gerado ao executar `uv lock`/`uv sync`)
- Validação: Pydantic 2
- Settings: pydantic-settings
- Banco estruturado: SQLite
- ORM: SQLAlchemy 2.x
- Migrações: Alembic
- HTTP: HTTPX
- Primeiro runtime LLM: Ollama, atrás de adapter próprio
- Testes: pytest + pytest-asyncio
- Lint/format: Ruff
- Logging: biblioteca padrão Python
- Paths: pathlib + platformdirs
- IDs: UUID
- Timestamps: UTC
- Controle de versão: Git
- Licença pretendida do Campanario: Apache-2.0 (confirmar antes de publicação/distribuição)

## 4. Decisões deliberadamente NÃO congeladas

Não escolher sem benchmark/necessidade: modelo LLM definitivo, vector DB, embeddings, reranker, STT, TTS, wake word, frontend definitivo, backend de knowledge graph, framework de agentes, search provider, browser automation, MCP, modelos separados para Morgana/Todd.

## 5. Fases planejadas

0. Fundação arquitetural
1. LLM local + chat
2. Context Manager
3. Memória
4. RAG/documentos
5. Morgana e Todd
6. Internet
7. Voz
8. Tools e agentes
9. Learning + Knowledge Graph
10. Conversação contínua/dispositivos

## 6. Estado exato desta entrega

Criado:
- estrutura mínima do repositório;
- configuração tipada;
- data directory local;
- logging básico;
- FastAPI;
- endpoint `/health`;
- modelos de domínio mínimos de chat;
- contrato `ModelProvider`;
- `FakeModelProvider` para testes;
- esqueleto de `OllamaProvider` ainda sem chat implementado;
- base SQLAlchemy;
- tabelas iniciais `chat_sessions` e `messages`;
- contratos de repositories;
- ADRs iniciais;
- testes do health check e fake provider.

Ainda NÃO criado:
- endpoint de chat;
- ChatService completo;
- repositories SQLite concretos;
- migrations Alembic geradas/configuradas;
- streaming SSE;
- chamada real ao Ollama;
- UI;
- memória/RAG/agentes/voz/internet.

## 7. Próximo incremento recomendado

**Incremento 2 — Persistência + primeiro circuito de chat.**

Ordem:
1. inicializar/configurar Alembic;
2. criar migration inicial para `chat_sessions` e `messages`;
3. implementar repositories SQLAlchemy;
4. implementar `ChatService`;
5. implementar `OllamaProvider` via HTTPX;
6. criar endpoint de criação/listagem de sessão;
7. criar endpoint de chat streaming SSE;
8. persistir mensagem do usuário e resposta concluída;
9. testes unitários usando `FakeModelProvider`;
10. teste de integração Ollama opcional, nunca obrigatório para suíte normal.

Critério de sucesso:
- criar sessão;
- enviar "Olá";
- receber resposta local em streaming;
- persistir pergunta/resposta;
- reiniciar Campanario;
- recuperar histórico;
- testes unitários funcionarem sem Ollama/GPU.

## 8. Arquivos de referência que podem ser necessários no futuro

Se uma nova conversa precisar reconstruir contexto, pedir ao usuário, quando disponíveis:
1. documento **Projeto Campanario v2.0 — Documento de Conceito**;
2. este `PROJECT_STATE.md`;
3. `docs/ARCHITECTURE.md`;
4. `docs/ROADMAP.md`;
5. `docs/adr/`;
6. `pyproject.toml`;
7. árvore atual do repositório;
8. arquivos diretamente relacionados à tarefa atual;
9. erros/logs relevantes, se houver.

Para reutilização open source, pedir especificamente os snapshots/repositórios relevantes antes de copiar/adaptar código. Referências já consideradas: Row-Bot/Thoth, JARVIS, LocalMind, Khoj, Open WebUI e MemoryWebAssistant. AnythingLLM foi excluído da análise anterior.

## 9. Política de atualização deste handoff

Após QUALQUER incremento relevante:
- atualizar `Estado exato desta entrega`;
- registrar o que foi concluído;
- registrar decisões novas e motivo;
- atualizar `Próximo incremento`;
- registrar problemas/bugs conhecidos;
- registrar migrations/schema relevantes;
- registrar dependências adicionadas/removidas;
- registrar arquivos de referência necessários;
- nunca apagar decisões antigas silenciosamente: se mudarem, registrar substituição em ADR.

## 10. Protocolo para uma IA sem memória da conversa

Ao receber este projeto em uma conversa nova:

1. Leia `PROJECT_STATE.md`.
2. Leia `docs/ARCHITECTURE.md` e `docs/ROADMAP.md`.
3. Leia ADRs relevantes.
4. Inspecione `pyproject.toml` e a árvore real.
5. Compare este handoff com o código; **o código é evidência do estado real**, e divergências devem ser apontadas.
6. Não implemente fase futura só porque ela aparece no roadmap.
7. Antes de mudar arquitetura congelada, explique trade-off e crie/substitua ADR.
8. Se faltar o documento conceitual e a tarefa tocar requisitos de longo prazo/personas/memória, solicite-o.
9. Se a tarefa tocar código open source externo, solicite o snapshot/repositório/licença pertinente.
10. Ao terminar, atualize este arquivo.

## 11. Questões abertas

- Confirmar formalmente Apache-2.0 antes de publicar/distribuir.
- Escolher modelo Ollama inicial por benchmark no hardware alvo, não por suposição.
- Definir política de mensagens parcialmente geradas/canceladas antes de streaming avançado.
- Frontend permanece fora do escopo atual.

## 12. Hardware alvo conhecido

- Windows
- Ryzen 5 8600G
- RTX 5060 Ti 16 GB

Prioridade futura de GPU: LLM > STT quando necessário > embeddings/reranker somente se justificar. CPU deve ser fallback quando aplicável.
