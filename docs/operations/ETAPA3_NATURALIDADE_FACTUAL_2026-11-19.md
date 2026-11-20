# CAMPANARIO-IA — Etapa 3: naturalidade, factualidade e pesquisa

**Data:** 19/11/2026  
**Base:** `CAMPANARIO_IA_ETAPA2_CORRIGIDO_COMPLETO.zip`  
**Contribuição analisada:** `CAMPANARIO_CORRECAO_FACTUAL.zip` (arquivos enviados pelo usuário, preparados com auxílio do Claude).  
**Ambiente executado:** Linux / Python 3.13. **Alvo do projeto:** Windows / Python >=3.12,<3.13.

## 1. Resultado e decisão de integração

A correção externa foi **integrada seletivamente**, e não sobreposta integralmente. O `service.py` e o `ollama.py` do ZIP recebido eram anteriores às proteções da Etapa 2: sobrescrevê-los apagaria a emissão de `AGENT_INTERRUPTED`, a liberação de geradores e as verificações de campos malformados. Esses arquivos permaneceram na versão da Etapa 2, recebendo apenas alterações mínimas e testadas.

Não foi introduzido um novo agente, roteador, banco, modelo de memória, fluxo alternativo ou chamada de modelo para aprovar cada fato. Todd e Morgana continuam usando a mesma base de evidências, com expressão distinta nas respostas. A saída de extração factual conserva indicação da fonte e agora diferencia correspondência exata de **possível correspondência** a um nome abreviado.

## 2. Matriz de mudanças efetivas

| ID | Arquivo | Alteração | Limite |
| --- | --- | --- | --- |
| E3-01 | `utilities/web_intent.py` | Perguntas “quem foi/era X”, “conhece X?”, “o que sabe sobre X?” e pedidos informais com nome próprio entram na verificação. Proteções para referências pessoais e sujeitos indefinidos. Corrige o verbo residual em “X é cantor?”. | Reconhecimento por gramática: não é NER universal. |
| E3-02 | `utilities/web_chat.py` | Candidatos de artigos de Wikipedia, desambiguação por nomes distintos, leitura de títulos que estendem nomes compostos, diferenciação entre categoria de abertura e menções no restante. | A busca é limitada e resultados externos podem ser incompletos ou errados. |
| E3-03 | `utilities/web_chat.py` | Evita encerrar a primeira busca ao encontrar somente uma correspondência de título estendido; busca por mais candidatos no orçamento existente. | A ausência de outro resultado **não prova exclusividade**. |
| E3-04 | `chat/knowledge.py` | Resposta de Todd/Morgana lista candidatos de modo natural, sem selecionar um no chute. Resposta curta extraída de título estendido usa explicitamente “possível correspondência” e fornece URL lida. | Fontes não garantem veracidade; confirmação de identidade pode exigir contexto do usuário. |
| E3-05 | `chat/service.py` | Propaga os candidatos somente para a resposta de ambiguidade, mantendo os wrappers de streaming/observadores da Etapa 2. | Não muda o comportamento de streaming incremental. |
| E3-06 | `model/adapters/ollama.py` | Log seguro `ollama_context_near_limit` quando `prompt_eval_count` chega a 95% da janela explicitamente configurada. Não registra conteúdo do prompt. | **Aviso de ocupação**, não prova de truncamento. |
| E3-07 | `.env.example` | Inclui comentários opcionais sobre auto pesquisa e janela de contexto. Mantém os valores originais seguros por padrão. | Não modifica `.env` real. |
| E3-08 | `tests/test_factual_quem_e.py` | Incorpora os **23 testes** fornecidos no ZIP recebido. | Simulações, sem internet real. |
| E3-09 | `tests/test_etapa3_grounding_naturalidade.py` | Acrescenta **14 testes** de privacidade, ambiguidade, possíveis correspondências, diferenças de persona, integração de chat e integridade de Ollama. | Fake utility/provider, sem Ollama físico. |

### Critérios que NÃO foram aceitos de forma automática

- **Trocar integralmente `chat/service.py`:** removeria as proteções de interrupção e `aclosing` da Etapa 2.
- **Trocar integralmente `model/adapters/ollama.py`:** restauraria o uso de `or {}` / `or ""` e aceitaria tipos de payload inválidos como valores ausentes.
- **Ativar `CAMPANARIO_WEB_AUTO_SEARCH=true` para todos:** internet automática é opção explícita do administrador, não obrigação para conversas locais.
- **Alterar `CAMPANARIO_MODEL_CONTEXT_WINDOW` para 8192 em todo hardware:** o valor adequado depende de modelo, RAM/VRAM e configuração de execução.
- **Tratar um título estendido como igualdade de identidade:** resposta de nome abreviado agora declara a correspondência como *possível*; se houver múltiplos candidatos, solicita esclarecimento.

## 3. Fluxos verificados

**Pergunta com entidade, pesquisa ativada:** entrada do usuário → `web_intent` → `ChatService.stream_turn` → `research_entity` → `web.search` → `web.read` (evidência efetivamente lida) → `ResearchResult` `grounded|ambiguous|insufficient|failed` → resposta atribuída à persona → validação e persistência → evento publicado.

**Nome abreviado:** título estendido em artigo lido, sem candidatos distintos dentro dos resultados consultados → resposta com nome completo, ressalva de possível correspondência e fonte. Se existem 2+ candidatos distintos, não resolve pela ordem do buscador; apresenta as alternativas.

**Falha/sem permissão de pesquisa:** o modelo não recebe permissão para inventar uma pesquisa ou biografia; retorna resposta de incerteza. O modo `web_auto_search=false` continua padrão e `/pesquisar` pode ser usado explicitamente.

**Proteções da Etapa 2:** `AGENT_INTERRUPTED`, rejeição de JSON truncado/malformado, fechamento de geradores e persistência antes de emissão de texto seguem intactos.

## 4. Evidência dos testes

```text
python -m compileall -q src/campanario                     PASSOU
python -m pytest -q [23 módulos direcionados]              201 passed, 0 failed
python -m pytest -q tests/test_etapa3_grounding_naturalidade.py   14 passed
python -m pytest -q tests/test_factual_quem_e.py            23 passed
python -m pytest -q --maxfail=20                          431 passed, 20 failed
```

O comparativo histórico foi feito na mesma base da Etapa 2 com `--maxfail=20`: **393 passaram / 20 falharam**. Na Etapa 3, 37 novos testes explicam 37 aprovações adicionais, e um teste histórico de recuperação de entidade anteriormente falho passou: `test_entity_web_requires_readable_relevant_sources`. Dos **primeiros 20 testes falhos** da Etapa 2, os primeiros **19 reaparecem**; a última vaga é ocupada pelo próximo teste histórico de organização do projeto porque a execução para no limite de 20 falhas. **Não foi detectada regressão nova nesse recorte**, sem alegar validação da suíte integral.

Uma execução exploratória sem encerrar nas primeiras 20 falhas ultrapassou o tempo máximo do ambiente (andamento até cerca de 84% da coleta). Não se considera a suíte completa homologada. Além disso, lint com `ruff` não pôde ser executado porque `ruff` não está instalado neste ambiente.

Entre as pendências históricas persistentes estão os contratos antigos G2 de auditoria semântica de memórias pessoais, mocks de pesquisa web e compatibilidade de stubs, testes históricos de streaming incremental e arquivos históricos ausentes no ZIP enxuto. Nenhum teste ou contrato existente foi alterado para esconder essas falhas.

### Como reproduzir o conjunto direcionado

```bash
python -m pytest -q \
  tests/test_etapa3_grounding_naturalidade.py tests/test_factual_quem_e.py \
  tests/test_etapa2_fault_injection.py tests/test_etapa1_fluxos_failsafes.py \
  tests/test_memoryllm_response_contract.py tests/test_chat_service.py \
  tests/test_prompt_leak_guard.py tests/test_realtime_gateway.py \
  tests/test_api_chat.py tests/test_ollama_provider.py \
  tests/test_capability_registry.py tests/test_permission_trust_layer.py \
  tests/test_voice_call_readiness.py tests/test_voice_media_f5b.py \
  tests/test_runtime_foundation.py tests/test_runtime_telemetry.py \
  tests/test_client_independent_sessions.py tests/test_utilities_interface.py \
  tests/test_utilities_offline.py tests/test_response_pipeline.py \
  tests/test_behavior_response_guard.py tests/test_personality_application.py \
  tests/test_compact_persona_grounding.py
```

## 5. Instalação e rollback

1. Encerrar o Campanario e fazer **backup do projeto, bancos, memórias e `.env`**.
2. Se a **Etapa 2 já estiver instalada**, usar o ZIP **incremental** da Etapa 3. Extrair na pasta **que contém** a pasta `CAMPANARIO-IA`.
3. Se a Etapa 2 ainda não estiver instalada, usar o ZIP **completo** da Etapa 3, que acumula as correções das Etapas 1–3.
4. Não sobrescrever `.env` pessoal nem importar arquivos Python do ZIP do Claude por cima do projeto atualizado; a integração já está incluída nos pacotes.
5. No Python 3.12 do host, executar os testes acima. Para testar pesquisa automática, definir **conscientemente** `CAMPANARIO_WEB_AUTO_SEARCH=true` no `.env`; testar também `false`, pesquisa explícita, bloqueio de buscadores e nomes ambíguos.
6. Aumentar `CAMPANARIO_MODEL_CONTEXT_WINDOW` para 8192 **apenas se** modelo/hardware tolerarem, com medição de latência e RAM/VRAM. A configuração padrão permanece 4096.
7. Para rollback, restaurar o backup anterior. **Nenhuma migração de dados foi introduzida nesta etapa.**

## 6. Pendências antes de homologação plena

- **P0:** G2 de inferências pessoais além de qualificadores simples (“planejo” versus “concluí”; residência e profissão). Não introduzir mais uma segunda chamada de modelo em todos os turnos sem projeto específico e latência medida.
- **P1:** testes reais no Windows/Python 3.12, Ollama/Qwen, provedor de busca configurado, páginas indisponíveis/alteradas e fontes contraditórias.
- **P1:** validar latência e qualidade subjetiva de Todd/Morgana com conversas humanas reais; testes automatizados de fraseado não medem naturalidade integral.
- **P1:** streaming incremental seguro, reconciliação de clientes desconectados e atualização dos testes históricos sem afrouxar contratos.

**Conclusão:** a Etapa 3 integra a contribuição factual mantendo os failsafes da Etapa 2, adiciona incerteza explícita para nomes abreviados e preserva personalidades separadas. Não comprova conhecimento factual universal, funcionamento real dos buscadores nem homologação do runtime completo.
