# CAMPANARIO V9.1 - motor de expressao fundamentada (incremento no IA)

**Escopo real:** implementacao incremental sobre a base V8 enviada em `CAMPANARIO-IA`, ainda identificada como pacote Python `0.8.0`. Nao foram disponibilizados os codigos V9 de cerebros/arquetipos/talentos nem os repositorios externos `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE`. Estes componentes externos **nao estao homologados**; `brain_ids` e os campos opcionais de perfil sao pontos de extensao, nao um roteador de cerebros implementado.

## 1. Auditoria da base antes da alteracao

- `src/campanario/chat/service.py`: `ChatService.stream_turn` recebe a pergunta; o fluxo existente seleciona agente, pesquisa fontes, compila `TurnFactSheet`, passa evidencias para `_run_agent` e publica eventos da conversa.
- `src/campanario/chat/knowledge.py`, `fact_sheet.py`, `grounded_conversation.py`, `local_library.py`, `document_intent.py`, `data_intent.py`: consultas documentais V8, comprovantes de leitura e respostas extrativas; ja existiam fluxo multi-turno de biblioteca e dados calculados.
- `src/campanario/model/`: interface `ModelProvider` e mensagens para o provedor Ollama configurado; a V9.1 **reutiliza** a integracao existente, sem exigir modelo adicional.
- `src/campanario/agents/profiles.py`, `morgana.py`, `todd.py`: perfis e Bibias de Personalidade independentes; nao substituidos.
- `src/campanario/utilities/service.py`, `utilities/document_v8.py`, `utilities/data_v8.py`: SQLite, importacao de originais e analise programatica; bancos externos permanecem intocados.
- `src/campanario/config.py`, `composition.py`, `api.py`, `web/`: configuracao, inicializacao, API e interface Dark Matter; novos controles usam estes pontos de extensao.
- Mecanismos legados de memorias, historico, referencias web e auditores continuam presentes. A V9.1 introduz uma verificacao **deterministica adicional** para expressao fundamentada, em vez de confiar apenas na autoavaliacao de outro LLM.

## 2. Pipeline operacional implementado

```
Pergunta -> Intencao V8 e tipo de resposta (modo) ->
Ferramentas documentais / dados ja existentes -> TurnFactSheet ->
CanonicalAnswer (Pydantic imutavel, uma vez por turno) ->
GroundedExpressionEngine (perfil Morgana/Todd + Ollama local) ->
validate_expression -> aceita / nova tentativa limitada / fallback extrativo ->
referencia criada por codigo -> resposta e trilha local de depuracao
```

A fonte e consultada **antes** da geracao. O mesmo objeto canonico e entregue a ambos os agentes quando participam do turno. Conteudo recuperado e tratado como dados, nao como instrucoes do agente. A resposta personalizada e mantida em memoria ate aprovada; nao se transmitam tokens factualmente nao validados ao usuario.

| Componente | Caminho | Responsabilidade |
|---|---|---|
| Conhecimento e execucao | `chat/service.py` + biblioteca/utilitarios V8 | Consultas reais e calculos; `read_count` vem do adaptador executado, nunca do texto do LLM |
| Construtor canonico | `chat/canonical_answer.py` | `AnswerMode`, `VerificationStatus`, fontes, fatos, operacoes, limites, resposta-base, integridade de IDs |
| Expressao | `chat/grounded_expression.py` | Perfil adicional, prompt com JSON factual e Ollama existente, tentativas limitadas |
| Validador | `validate_expression` no mesmo modulo | Rejeita valores alterados/inventados, condicoes ausentes, referencias artificiais, novas negacoes/causalidades, termos nao rastreados |
| Integracao | `chat/service.py`, `agents/profiles.py` | Personalidades preservadas, acao e telemetria por agente, citacoes geradas no runtime |
| Depuracao | `api.py`, `web/index.html`, `web/static/chat.js`, CSS | Botao discreto "Evidencias" com trilha real e HTTP local restrito |

### Contrato e estados

O `CanonicalAnswer` e validado com Pydantic (`extra=forbid`, modelos congelados) e inclui UUID do turno, pergunta, intencao, modo, fontes, fatos com `fact_id`/`source_ids`/valores/condicoes, `ToolExecution`, limitacoes, contradicoes, ausencias e resposta factual independente da personalidade. IDs duplicados ou sem fonte sao rejeitados.

- `verified`: reservado neste incremento a resultado **computado** respaldado por ferramenta com leitura registrada; nao prova a veracidade de todos os dados de origem.
- `partially_verified`: trecho de documento efetivamente lido; corresponde a uma **afirmacao da fonte**, nao a prova externa da afirmacao.
- `unverified`: sem verificacao factual.
- `not_found`: consulta sem trecho/evidencia confiavel.
- `conflicting`: resultados ambiguos ou fontes divergentes; sem escolher arbitrariamente.
- `tool_error`: consulta indisponivel/falha.

O modo `conversational` preserva o fluxo livre preexistente. `grounded` tenta a expressao controlada em consultas documentais e calculos. `hybrid` e selecionado por intencao de analise/interpretacao ou pedido explicito; neste incremento segue a mesma politica conservadora de expressao, **nao implementa uma classificacao semantica completa de fatos, hipoteses e recomendacoes**. Os modos podem ser pedidos por texto (por exemplo, "modo fundamentado").

### Integridade e falhas

1. O modelo pode trocar vocabulos neutros, tom e ordem, mas o validador rejeita mudancas de tokens numericos, qualificadores literais (como "somente apos"), novas referencias, negacoes e causalidade detectaveis.
2. Fontes, IDs e paginas provem dos metadados reais da consulta, anexados pelo sistema; o LLM **nao** escreve citacoes.
3. A verificacao e conservadora e pode rejeitar parafrases legitimas. Usa igualdade e heuristicas lexicais; **nao comprova equivalencia semantica geral**. Inversoes sutis podem nao ser detectadas. Rejeicao usa resposta extrativa, jamais resposta inventada.
4. Tentativas configuradas `0..2`; indisponibilidade do Ollama ou reprovacao repetida acionam fallback. Uma fonte ausente nao autoriza resposta com atribuicao falsa.
5. Valores monetarios em `data.sum` sao calculados com `Decimal` (dados invalidos/ausentes impedem soma). A ferramenta de analise V8 continua sujeita a suas outras limitacoes.

## 3. Arquivos, configuracao e interface

Acrescente ao `.env` existente **somente se desejar alterar os padroes**:

```dotenv
CAMPANARIO_GROUNDED_EXPRESSION_ENABLED=true
CAMPANARIO_GROUNDED_EXPRESSION_RETRIES=1
```

Zero tentativas extras significa uma chamada de expressao; `1` permite uma reformulacao adicional. O limite de duas novas tentativas e aplicado na configuracao. A funcionalidade usa o provedor/modelo Ollama ja configurado, sem servidor novo.

No chat Dark Matter, o botao "Evidencias" e o indicador consultam `GET /api/v1/sessions/{session_id}/grounding-debug` **somente a partir do host local** (requisicao remota recebe HTTP 403). A trilha tem `mode`, `status`, `intent`, `brains_activated` (vazio se nao houver roteador real), `tools_executed`, fontes, resposta canonica, resultado da validacao, tentativas e latencia. Trata-se de **eventos e saidas observaveis**, nao de raciocinio privado. A depuracao e limitada a 100 sessoes e dura apenas enquanto o processo existe. A UI utiliza `textContent` para apresentar os dados sem interpretar HTML das fontes.

**Privacidade:** embora local, a trilha pode conter trechos documentais e rascunhos rejeitados; nao exponha essa rota publicamente. Mobile remoto nao recebe esse endpoint.

## 4. Instalacao em Windows (tres pastas)

Pastas existentes:

```text
C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA
C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-PYTHON
C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-DATABASE
```

1. Feche Campanario. Faca backup **independente** do Database e do `.env`; mantenha os modelos de voz e o Python externo.
2. Extraia `CAMPANARIO_V91_PATCH.zip` fora de `CAMPANARIO-IA`, por exemplo `C:\Temp\CAMPANARIO_V91_PATCH`. O patch pressupoe o codigo **V8 entregue anteriormente**, sem edicoes locais divergentes; o instalador verifica SHA-256 esperado e **aborta** se detectar base inesperada.
3. Em PowerShell, execute uma simulacao e revise a lista:

```powershell
$projeto = 'C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA'
$patch = 'C:\Temp\CAMPANARIO_V91_PATCH'
& "$patch\tools\windows\APLICAR_V91_SEGURA.ps1" -ProjectRoot $projeto -PatchRoot $patch
& "$patch\tools\windows\APLICAR_V91_SEGURA.ps1" -ProjectRoot $projeto -PatchRoot $patch -Apply
```

4. O aplicador cria backup dos arquivos substituidos em uma pasta **irma** `CAMPANARIO-IA_BACKUP_ANTES_V91_*`, antes da primeira copia, e nao escreve nas outras duas pastas, `.env`, bancos SQLite ou modelos. Se `-Apply` recusar por divergencia, nao force; compare a personalizacao com a V8 e integre manualmente.
5. Reinicie o servidor, force recarregamento da pagina no navegador e execute:

```powershell
& '..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe' -m pytest tests/test_v91_expression.py tests/test_v8_knowledge.py tests/test_resposta_conversacional_com_evidencia.py -q
& '.\TESTAR_3_PASTAS.ps1' -ProjectRoot '.'
```

Este incremento **nao exige nova migracao SQL**: reutiliza o esquema V8. Nao reinstale nem elimine o Database. Para reverter, feche o aplicativo e restaure apenas o codigo guardado no backup.

## 5. Demonstracoes e resultados

Os testes automatizados em `tests/test_v91_expression.py` usam provedor com respostas deliberadamente erradas para verificar fallback e **biblioteca SQLite realmente importada** para a conversa de Ordem Paranormal. O documento criado e `Ordem Paranormal Exemplo.md` e contem uma regra **ficticia de teste**, "Marca Exemplo Q7"; nao foi verificado nenhum livro real nem pagina oficial de RPG. A resposta correta e extrativa, com fonte realmente recuperada, e rejeita a "Marca Errada" do provedor simulado. O teste de CSV calcula `100.10 + 200.20 = 300.30` e rejeita valores ausentes.

Suite completa deste ambiente (Linux, Python 3.13): **989 passaram, 31 falharam**. Base V8 antes desta alteracao: **974 passaram, 32 falharam**. As 31 falhas atuais ja apareciam no conjunto de falhas da base V8 (nenhuma nova). Suite direcionada: **32 passaram, 0 falharam**. O executor real de Ollama, Windows PowerShell, dispositivos moveis, instalacao externa e cerebros V9 **nao foram homologados**.

## 6. Pendencias para considerar V9.1 concluida integralmente

- Integracao efetiva ao roteador de **cerebros V9** (nao enviado) e suas politicas de talentos; neste incremento `brain_ids` fica vazio e `archetypes`/`talents` sao opcionais, sem ativar ferramentas.
- Verificacao semantica robusta de sinonimos, relacoes causais e negacoes complexas; atual politica deterministica pode gerar falsos negativos e nao e prova formal de ausencia de alucinacao.
- Segmentacao estruturada completa de fatos, interpretacoes, hipoteses e recomendacoes para modo hibrido; somente classificacao de modo e protecao do fato computado foram integradas.
- Cache persistente de representacoes canonicas e invalidacao por hash/versao; no momento ha reutilizacao do mesmo resultado durante **um turno**, nao cache de varias sessoes.
- Metricas comparativas de latencia e fidelidade com **Ollama real**, teste com **documento real** de Ordem Paranormal e testes no Windows/mobile.
- Integracao/homologacao com os codigos atuais de `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE`, nao fornecidos.

**Regra de operacao:** respostas de fontes nao sao fatos garantidos; sao afirmacoes rastreadas. O mecanismo protege os resultados recuperados contra alteracao na expressao, com as limitacoes acima.
