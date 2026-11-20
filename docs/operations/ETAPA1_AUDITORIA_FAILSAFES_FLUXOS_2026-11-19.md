# CAMPANARIO-IA — Etapa 1: auditoria de fluxos e failsafes

**Data:** 19/11/2026. **Escopo:** revisão estática do ZIP `CAMPANARIO_IA_ENXUTO.zip`, correções pontuais no código e testes automatizados locais. **Não é homologação do modelo real, Windows, GPU, microfone ou Android físico.**

## 1. Arquitetura preservada

Campanario continua sendo o runtime/sistema. Morgana e Todd são agentes distintos que compartilham a memória factual e usam um único `ChatService`. Nenhum serviço, banco ou persona paralelo foi criado nesta etapa.

### Mapa dos caminhos de entrada (código)

| Entrada | Implementação | Caminho até a conversa | Entrega ao cliente |
|---|---|---|---|
| Web atual | `web/static/chat.js` | `POST /api/v1/sessions/{id}/turn` → `api.submit_turn_v1` → `runtime.conversation.stream_turn()` | `RuntimeEventBus` → `/ws/v1/events` (`AGENT_RESPONSE_*`) |
| SSE legado | `api.stream_chat` | `POST /api/sessions/{id}/chat/stream` → `ChatService.stream_turn()` | SSE com `speaker_start`, `token`, `speaker_done`, `done`/`error` |
| Cliente mobile remoto | `companion/api.py` | Pareamento/TLS/permissões do dispositivo → `POST /sessions/{id}/turn` → `ChatService.stream_turn()` | HTTP com lista de mensagens; `request_id` contra reenvio ambíguo |
| Call/voz | `gateway/call.py` e `runtime/voice.py` | WebSocket autenticado → VAD/STT final → `VoiceCallCoordinator` → conversa compartilhada | Eventos e buffer de fala → TTS com `agent_id` |
| Desktop | `app/desktop.py` / `main.py` | Host local → mesmos endpoints da Web | UI nativa hospedando interface local |
| Ferramentas (via runtime) | `runtime/capabilities.py` | Validação de schema → `PermissionPolicy` → provider → timeout | Eventos `TOOL_REQUESTED`, `TOOL_STARTED`, `TOOL_RESULT` ou `TOOL_FAILED` |
| Ferramentas do navegador local | `utilities/api.py` | `POST /api/v1/utilities/invoke` → `UtilityService.run()` | Resposta síncrona; escrita exige `confirm=true` na camada de utilidades |

**Observação importante:** o endpoint de ferramentas do navegador é um caminho distinto do `CapabilityRegistry`; a confirmação booleana local não é equivalente a um token de aprovação PF6. Não houve mudança disruptiva dessa API nesta etapa.

### Fluxo conversacional real

`entrada → ChatService.stream_turn (verificações + preflight de pesquisa) → _stream_turn_impl (roteamento e persistência da mensagem do usuário) → AgentRouter → ContextManager/DialogueState/ExperienceLayer → _run_agent → provider composto → Ollama → validações de resposta e speaker → persistência da resposta → eventos para o cliente → ParticipationArbiter (opcionalmente Todd/Morgana secundário)`.

`composition.py` seleciona **dois caminhos de provider**: em modo `low_latency_mode`, `safe_provider` é usado diretamente; fora dele, aplica-se também `BehaviorResponseGuardProvider(ResponseContractPipeline)`. A configuração de `live_streaming` seleciona um guard de prompts com janela de quarentena, mas `_run_agent` utiliza `audited_stream = False` e entrega o texto final de uma vez após verificação. Esse comportamento protege contra vazamento de respostas intermediárias, porém a configuração de streaming não significa entrega incremental real; não foi alterado sem definir um contrato seguro de emissão.

## 2. Correções realizadas e justificativa

| ID | Falha encontrada | Correção aplicada | Arquivo |
|---|---|---|---|
| E1-01 | Pesquisa e planejamento web podiam começar antes de validar `session_id` ou modelo. | Fail-fast antes de efeitos externos; rechecagem na implementação permanece. | `chat/service.py` |
| E1-02 | A resposta era publicada/emitida antes da gravação no histórico. Desconexões após o primeiro token podiam deixar uma fala visível, mas ausente do banco. | A resposta validada é persistida **antes** do primeiro evento/chunk; falha na persistência não publica uma fala considerada concluída. | `chat/service.py` |
| E1-03 | Erro de gravação ou consulta da memória podia interromper toda a conversa. | Observação de memória falha sem derrubar chat; consulta falha de modo conservador e registra `memory_observation_failed` / `memory_retrieval_failed` sem texto privado em telemetria. | `chat/service.py` |
| E1-04 | Após falha da consulta, a IA poderia improvisar dados sobre lembranças pessoais. | Resposta de indisponibilidade quando a pergunta depende de memória pessoal e a consulta falha. | `chat/service.py` |
| E1-05 | Stream Ollama truncado, evento não-objeto, conteúdo malformado ou erro no JSON podia retornar como conclusão parcial/sucesso. | Exige `done: true`, valida o formato dos eventos e converte anomalias para `ModelResponseError`. | `model/adapters/ollama.py` |
| E1-06 | Alegação pessoal de intensidade/exclusividade podia ir além da evidência (ex.: “gosto” → “favorito”). | Rejeição determinística de intensificadores não licenciados, seguida de fallback à declaração real recuperada. | `chat/memory_grounding.py`, `chat/service.py` |
| E1-07 | Cache-busting do HTML não correspondia à versão `UI_VERSION = 0.8.0` para vários scripts. | Versão dos scripts no HTML alinhada ao release local. | `web/index.html` |

**Nota:** E1-06 é um failsafe *parcial*: não valida todas as inferências possíveis (profissão, residência, conclusão de planos etc.). Não se deve apresentar o sistema como totalmente protegido contra falsas alegações pessoais com base apenas nessa verificação.

## 3. Evidências de teste

Comandos executados na cópia extraída, em Python **3.13** (o projeto declara alvo **3.12** em `pyproject.toml`):

```bash
python -m compileall -q src/campanario
python -m pytest -q tests/test_etapa1_fluxos_failsafes.py tests/test_memoryllm_response_contract.py tests/test_chat_service.py tests/test_prompt_leak_guard.py tests/test_realtime_gateway.py tests/test_api_chat.py tests/test_ollama_provider.py
python -m pytest -q tests/test_capability_registry.py tests/test_permission_trust_layer.py tests/test_voice_call_readiness.py tests/test_voice_media_f5b.py tests/test_runtime_foundation.py tests/test_runtime_telemetry.py tests/test_client_independent_sessions.py tests/test_utilities_interface.py tests/test_utilities_offline.py tests/test_response_pipeline.py tests/test_behavior_response_guard.py
```

Resultados: **68 + 71 = 139 testes aprovados** nos blocos direcionados e de integração; compilação Python aprovada.

Um teste exploratório separado de compatibilidade mais antiga (`test_neptune_mode.py`, `test_g2_grounding_audit.py`, `test_g2_semantic_evidence_regression.py`) registrou **13 falhas e 10 aprovações**. Não foram escondidas ou reclassificadas como sucesso. Elas evidenciam conflitos de contrato entre a retirada do auditor de memória por segundo modelo e os testes legados que ainda o exigem; há também um teste que espera chunks incrementais quando o chat atual entrega a resposta já validada em um chunk. As falsas inferências além de intensidade/exclusividade **continuam pendentes**. Uma execução inicial da suíte inteira foi interrompida por limite de tempo e não é evidência de aprovação geral.

## 4. Matriz de failsafes e lacunas de cobertura

| Proteção | Situação após etapa | Limitação |
|---|---|---|
| Sessão e modelo válidos antes do preflight | Corrigido/testado | Não foi feita auditoria de concorrência entre exclusão de sessão e execução do turno |
| Ollama indisponível / timeout / stream inválido | Adaptador com erros tipados; stream inválido testado | Falta teste com Ollama real e rede oscilante no host Windows |
| Prompt leak | Guard existente, testes direcionados aprovados | Bufferização intencional impede streaming de baixo atraso efetivo |
| Identidade de quem falou | Contratos e reparo existentes | Modelos reais e todos os modos de diálogo não homologados |
| Persistência antes da entrega da fala | Corrigido/testado | Falha ao publicar evento após commit ainda merece reconciliação de cliente |
| Memória indisponível | Degradação conservadora corrigida/testada | Sem avaliação de falhas físicas do SQLite/Chroma e retomada |
| Memória pessoal / extrapolação | Restrição de intensificadores corrigida/testada | Auditoria geral de inferências segue aberta |
| Tool permissions | `PermissionPolicy` existente, testes aprovados | Caminho browser-local de utilidades não utiliza o mesmo mecanismo PF6 |
| Interface Web e SSE legado | Apontam para o mesmo `ChatService` | Interfaces de transporte ainda são múltiplas |
| Dispositivo mobile / TLS / call | Contratos inspecionados, testes de integração aprovados | Pareamento real em rede, STT/TTS e barge-in físico não homologados |

## 5. Backlog recomendado para Etapa 2 (não alterado aqui)

1. **P0 — Grounding pessoal:** definir contrato único para verificação de inferências (naturalidade vs. segundo modelo vs. latência) e reconciliar os testes G2 antigos com o modo enxuto. Testar implicações, negações, planos e graus de certeza sem alucinar.
2. **P0 — Streaming:** resolver explicitamente o conflito entre baixa latência e validação antes de exibição; nenhum trecho não validado deve chegar ao WebSocket/TTS.
3. **P1 — Ferramentas:** avaliar unificação das aprovações de escrita entre `utilities/api.py` (UI local) e `CapabilityRegistry/PermissionPolicy` (runtime); preservar compatibilidade.
4. **P1 — Estado cliente/servidor:** testar reconciliação quando o banco confirma a resposta mas há falha do EventBus ou da conexão WebSocket; consumidores podem recarregar histórico persistido.
5. **P1 — Confiabilidade:** aplicar fault injection no ambiente declarado (Python 3.12, Windows, Ollama/Qwen, SQLite/Chroma, voz) e medir latência, timeout, retomada e integridade transacional.

## 6. Critério para seguir a produção

A Etapa 1 entrega código corrigido, novos testes e mapa dos caminhos de execução. **Não fecha a homologação integral do projeto.** Não há mudança de identidade da Morgana/Todd, novo runtime, novo banco nem alteração no formato das mensagens. Para implantar no PC principal, manter um backup do banco de dados e executar os testes e a validação de runtime/voz do próprio ambiente antes de substituir a versão em uso.
