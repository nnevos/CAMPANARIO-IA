# CAMPANARIO-IA — Etapa 2: estabilização dos failsafes

**Data:** 19/11/2026  
**Base:** `CAMPANARIO_IA_ETAPA1_CORRIGIDO_COMPLETO.zip`  
**Ambiente de validação local:** Python 3.13 / Linux (o alvo do projeto é Python 3.12 / Windows).  
**Limite:** não foi executado Ollama/Qwen real, GPU, WebSocket em rede instável, hardware de voz ou Android físico.

## 1. Objetivo e arquitetura preservada

Fortalecer a contenção de falhas sem introduzir outro runtime, persona, memória ou armazenamento. Morgana e Todd continuam no mesmo `ChatService` e no mesmo barramento de eventos; os clientes Web, Desktop, Android e voz seguem os contratos existentes.

As alterações são *incrementais* sobre a Etapa 1. A entrega contém 4 arquivos de código modificados, 1 arquivo de teste novo e este relatório. Não há mudança de esquema do banco, de payload das mensagens, de permissões nem de endpoints.

## 2. Correções aplicadas

| ID | Problema observável | Mudança | Arquivo |
|---|---|---|---|
| E2-01 | Um subscriber do `RuntimeEventBus` que lançasse exceção propagava a falha à chamada `publish`, podendo abortar o turno mesmo após commit. | Cada subscriber roda isolado; erros são registrados sem conteúdo da mensagem, preservando o journal e notificando os demais observadores. | `runtime/events.py` |
| E2-02 | O modelo podia falhar depois de `AGENT_RESPONSE_STARTED` sem evento terminal, deixando consumidores com um agente aparentemente ainda respondendo. | Wrapper `_guard_agent_response` publica `AGENT_INTERRUPTED` em falha/cancelamento/fechamento e relança a exceção original. | `chat/service.py` |
| E2-03 | O fechamento do streaming externo não garantia o fechamento imediato dos generators internos. | `contextlib.aclosing` encadeado em `stream_turn`, agentes primário/secundário, follow-ups e `stream_reply`. Isso permite emitir interrupção e liberar os generators ao fechar uma conexão. | `chat/service.py` |
| E2-04 | O parser Ollama tratava `message=0` e `content=0`/`[]` como campos ausentes devido a `or`, perdendo a distinção entre vazio legítimo e dado malformado. | Campos ausentes/`None` continuam vazios; valores não objeto ou conteúdo não string causam `ModelResponseError`. O marcador `done: true` continua obrigatório. | `model/adapters/ollama.py` |
| E2-05 | Após falha da geração, a UI podia permanecer no estado visual “respondendo”. | Tratamento de `AGENT_INTERRUPTED`, limpeza da bolha vazia e retorno ao estado atento. | `web/static/chat.js` |
| E2-06 | Faltava uma suíte de fault injection que reproduzisse esses casos. | 20 testes novos cobrindo observadores, timeout, indisponibilidade, payloads inválidos, commit e encerramento do stream. | `tests/test_etapa2_fault_injection.py` |

### Eventos durante a falha

**Sucesso:** `USER_TEXT → AGENT_SELECTED → AGENT_INTENT_TO_SPEAK → AGENT_RESPONSE_STARTED → AGENT_RESPONSE_CHUNK → AGENT_RESPONSE_FINISHED`.

**Falha após início:** `USER_TEXT → AGENT_SELECTED → AGENT_INTENT_TO_SPEAK → AGENT_RESPONSE_STARTED → AGENT_INTERRUPTED`. O evento de interrupção não contém texto privado nem detalhes da exceção. O erro original continua sendo tratado pelo endpoint HTTP/SSE. Falhas anteriores ao início da fala não emitem interrupção de agente.

**Regra de persistência mantida:** a mensagem do agente só é entregue como chunk depois de validada e gravada. Se a gravação falhar, o texto não é emitido nem registrado como resposta concluída; a mensagem do usuário já armazenada permanece no histórico.

**Regra de barramento:** `RuntimeEventBus` é journal process-local, não uma fila durável de entrega garantida ao navegador. Falha de subscriber não interrompe o turno; clientes desconectados podem recuperar eventos ainda retidos via replay e consultar mensagens persistidas. A reconciliação completa após expiração do journal continua uma pendência.

## 3. Testes executados

```bash
python -m compileall -q src/campanario
python -m pytest -q \
  tests/test_etapa2_fault_injection.py tests/test_etapa1_fluxos_failsafes.py \
  tests/test_memoryllm_response_contract.py tests/test_chat_service.py \
  tests/test_prompt_leak_guard.py tests/test_realtime_gateway.py \
  tests/test_api_chat.py tests/test_ollama_provider.py \
  tests/test_capability_registry.py tests/test_permission_trust_layer.py \
  tests/test_voice_call_readiness.py tests/test_voice_media_f5b.py \
  tests/test_runtime_foundation.py tests/test_runtime_telemetry.py \
  tests/test_client_independent_sessions.py tests/test_utilities_interface.py \
  tests/test_utilities_offline.py tests/test_response_pipeline.py \
  tests/test_behavior_response_guard.py
```

**Resultado direcionado e de integração: 159 aprovados, 0 falhas.** Desses, 20 foram adicionados nesta etapa. A compilação do Python passou. Também foram executados isoladamente os casos de pesquisa sem fonte e bloqueio de ferramentas não autorizadas, com sucesso.

### Suíte geral — resultado honesto

Foram coletados **648 testes**; a execução completa com `--maxfail=20` foi interrompida após **393 aprovações e 20 falhas**. A mesma execução, na **base da Etapa 1**, apresentou **373 aprovações e as mesmas 20 falhas**, identificadas pelo mesmo ID de teste. Os 20 testes da Etapa 2 explicam a diferença de aprovações. Esse recorte **não indica novas regressões**, mas também **não permite homologar os 648 testes**.

As falhas já existentes nesse recorte abrangem auditoria semântica G2 de afirmações pessoais, indexação vetorial semântica, versões antigas de contratos de pesquisa, expectativas de streaming incremental e arquivos de documentação histórica ausentes do ZIP enxuto. Em um bloco exploratório separado de Web, memória e mobile, foram encontrados **49 aprovados e 3 falhas**, exatamente os mesmos 3 casos que falham na Etapa 1 (mocks/assinaturas do módulo de pesquisa web). Não foram alterados contratos antigos para forçar aprovação.

**Limitação de ambiente:** o container executou Python 3.13; o `pyproject.toml` exige `>=3.12,<3.13`. A passagem dos testes locais não substitui validação no host-alvo.

## 4. Backlog aberto após a Etapa 2

1. **P0 — Afirmações pessoais G2:** várias inferências sem fonte continuam possíveis quando o modelo afirma graduação, residência, exclusividade ou profissão a partir de planos e preferências; a verificação determinística da Etapa 1 é parcial. Definir verificador semântico com latência controlada, preservando naturalidade e separando testes legados.
2. **P0 — Streaming incremental seguro:** o chat atual retém a resposta até a validação. Isso é seguro, mas não garante vários chunks de baixa latência. Não habilitar emissão antecipada sem auditoria parcial e mecanismo de rollback verificável.
3. **P1 — Reconciliação dos clientes:** desenvolver ressincronização por histórico persistido quando o journal em memória expirar, quando uma publicação for perdida ou quando o navegador desconectar.
4. **P1 — Web research:** rever compatibilidade de mocks/testes com `skip_wikipedia`, a seleção de fontes por categoria e os testes históricos de recuperação; não promover snippets a fatos.
5. **P1 — Unificação de ferramentas:** `utilities/api.py` e `CapabilityRegistry/PermissionPolicy` possuem caminhos de aprovação distintos. A unificação ainda não foi realizada.
6. **P1 — Homologação real:** testar Python 3.12 / Windows / Ollama/Qwen / SQLite/Chroma / WebSocket instável / TTS e STT. Medir latência, encerramento, persistência e recuperação.

## 5. Instalação e rollback

1. Desligar o Campanario e fazer backup do projeto e da pasta de dados, incluindo SQLite, configurações e memória.
2. Se **a Etapa 1 já estiver instalada**, aplicar somente `CAMPANARIO_ETAPA2_ARQUIVOS_CORRIGIDOS.zip` por cima da pasta que contém `CAMPANARIO-IA`.
3. Se **a Etapa 1 ainda não estiver instalada**, usar o `CAMPANARIO_IA_ETAPA2_CORRIGIDO_COMPLETO.zip`, derivado do ZIP completo corrigido da Etapa 1.
4. No ambiente Python 3.12 do projeto, executar os comandos de teste acima e validar chat Web e voz reais antes de implantar.
5. Para rollback, restaurar o backup do código feito antes da Etapa 2; **nenhuma migração de dados é necessária**.

### Arquivos modificados nesta etapa

- `src/campanario/runtime/events.py`
- `src/campanario/chat/service.py`
- `src/campanario/model/adapters/ollama.py`
- `src/campanario/web/static/chat.js`

### Arquivos adicionados

- `tests/test_etapa2_fault_injection.py`
- `docs/operations/ETAPA2_ESTABILIZACAO_FAILSAFES_2026-11-19.md`

**Conclusão:** as falhas de observers, interrupção após início, fechamento encadeado e parser malformado foram corrigidas e testadas em ambiente simulado. A arquitetura foi preservada; a homologação completa e os riscos de grounding semântico/streaming incremental permanecem explicitamente abertos.
