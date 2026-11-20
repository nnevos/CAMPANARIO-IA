# CAMPANÁRIO — Roadmap de conclusão da arquitetura de cérebros (V9 + V9.1)

**Estado:** planejamento de integração; NÃO constitui declaração de implementação das fases pendentes.  
**Base auditada:** cópia `CAMPANARIO-IA` V9 integrada à V9.1, em 19/11/2026; incrementos P0, R1 e R1.1 realizados localmente na cópia IA, sem acesso ao host Windows.  
**Documentos vinculados:** `docs/current/ROADMAP.md`, `docs/current/V9_BRAINS_ARQUETIPOS_TALENTOS.md`, `docs/current/RELATORIO_V9_V91_INTEGRACAO.md`, `docs/operations/FAILSAFE_V9_CEREBROS.md`, `docs/operations/ETAPA1_AUDITORIA_FAILSAFES_FLUXOS_2026-11-19.md` e `docs/operations/ETAPA2_ESTABILIZACAO_FAILSAFES_2026-11-19.md`.

> **Gate de sequenciamento:** o roadmap canônico mantém a F5 (aceite físico de voz) aberta e a liberação formal da F6 bloqueada. Desenvolvimento e testes da arquitetura de cérebros podem evoluir como trilha *experimental/opt-in*, mas não promovem o projeto para F6/produção nem dispensam os gates F5. A versão V9 está desligada por padrão (`CAMPANARIO_BRAINS_V9_ENABLED=false`).

## 1. Situação real: inventário de base

| Componente | Evidência na base IA | Situação |
|---|---|---|
| Quem fala (`agents/router.py`) | `AgentRouter` existente | Preservado; não misturar com capacidades |
| Que cérebro usar (`brains/router.py`) | `CapabilityRouter` por regras explícitas; `BrainPlan` de até 3 IDs | **Parcial**: execução atual prioriza uma capacidade explícita, sem composição robusta/roteamento de ambiguidade |
| Núcleo de execução | `brains/contracts.py`, `registry.py`, `executor.py`, `isolation.py`, `network_guard.py`, `worker.py` | **Parcial**: Conhecimento/Análise em subprocesso com kill em timeout, monitoramento RSS, ambiente reduzido, orçamento total/circuit breaker R1.1 e CPU soft limit POSIX; restante não possui isolamento OS forte nem política unificada |
| Conhecimento | `brains/adapters.py` → recuperação documental existente V8 | **Funcional no escopo testado**; endurecimento de PDFs complexos, evidências e fontes ainda necessário |
| Análise | `brains/adapters.py` → CSV/XLSX e operações V8 | **Funcional no escopo testado**; sandbox rigoroso, ferramentas analíticas ampliadas e reprodutibilidade ainda necessários |
| Investigação, Programação, Estratégia, Percepção, Comunicação, Criação | `brains/registry.py` | **Indisponíveis**: catálogo sem executor; não anunciar essas capacidades como prontas |
| Expressão fundamentada | `chat/canonical_answer.py`, `chat/grounded_expression.py` | **Parcial**: validações conservadoras e fallback; ainda não há verificação semântica abrangente |
| Fichas e talentos | `brains/builds.py`, `store.py`, `agents.py` | **MVP**: oito arquétipos, seis talentos, dois ativos por turno; preconditions complexas pendentes |
| Interface e pacotes | `brains/api.py`, `brains/package.py`, `web/ferramentas.js` | **MVP local**: Central, Forja e inspeção segura; sem homologação mobile físico |
| Persistência | migração Alembic `0010_v9_brains.py` | Testada sobre SQLite temporário; instalação real de 3 pastas não verificada |
| Testes disponíveis | `tests/test_v9_brains.py` e regressão V8/V9.1 | Última regressão dividida documentada: **1.022 aprovados / 31 falhas preexistentes** (R1.1) no ambiente local; NÃO declarar 100% de sucesso |

**Inspeção R0 já implementada:** `GET /api/v1/brains/environment` e a Central de Cérebros consultam os caminhos em modo leitura mesmo com flag V9 desligada. **Não valida o Windows do usuário**. Veja [`P0_TRES_PASTAS_SEM_POWERSHELL.md`](P0_TRES_PASTAS_SEM_POWERSHELL.md) e [`P0_RELATORIO_EXECUCAO.md`](../operations/P0_RELATORIO_EXECUCAO.md).

**Fronteira das três pastas:** `CAMPANARIO-IA` é código e UI; `CAMPANARIO-PYTHON` contém ambiente/dependências locais; `CAMPANARIO-DATABASE` contém dados e bases pessoais. Somente o IA foi fornecido e auditado. Integrações e migrações no ambiente real requerem inspeção dos contratos e backup antes da execução. Nada nesta lista pressupõe acesso a dados pessoais, permissões ou modelos externos.

## 2. Regras arquiteturais que nunca podem regredir

1. Campanário é plataforma, não terceira personalidade. `AgentRouter` seleciona falantes; `CapabilityRouter` seleciona capacidades; não substituir um pelo outro.
2. Cérebros são compartilhados; `AgentProfile`/Bíblia de Personalidade e memórias de Morgana/Todd ficam intactos. `AgentBuild` é composição versionada, não substituição.
3. **Ordem de precedência:** segurança/permissões > integridade factual > pedido do usuário > necessidade da tarefa > talentos > estilo. Arquétipos não concedem acesso ou competência e talentos não alteram fatos.
4. Toda fonte citada deve ter operação efetivamente executada, identificador de evidência e referência rastreável; erro/não encontrado não vira certeza fabricada.
5. Fatos estruturados são compilados antes da expressão (V9.1). Falha de integridade implica nova tentativa limitada, fallback canônico ou declaração explícita de limitação, nunca vazamento de uma resposta reprovada.
6. Offline-first: um provider Ollama compartilhado quando necessário; dispositivos mobile são clientes leves, não executores de múltiplos modelos residentes.
7. Tudo que modifica dados, executa programas, acessa rede ou aciona dispositivo passa pelas mesmas políticas de autorização e auditoria, sem atalhos pela UI ou por pacote `.campagent`.
8. Rotas, telas e indicadores só mostram resultados reais: saúde do executor, operações, latência observada e evidências; nunca percentuais de precisão presumidos.
9. Migrações são aditivas, idempotentes quando cabível, com plano verificável de recuperação; nunca apagar automaticamente memórias, biblioteca, chats ou credenciais.

## 3. Sequência de implementação e critérios de aceite

Legenda: `[x]` funcionalidade observada na cópia IA; `[~]` parcial; `[ ]` não implementado ou não homologado. **Marcar `[x]` apenas com commit/arquivo, teste reproduzível e evidência de execução.**

### R0 — Baseline e validação das três pastas — P0 / BLOQUEADOR DE RELEASE

- [x] Inventariar contratos V9/V9.1 do repositório IA e registrar falhas históricas (31 na última suíte).
- [x] Criar diagnóstico de topologia das três pastas (`brains/environment.py`) e interface sem migração, leitura apenas de metadados e cabeçalho SQLite. Testar com estruturas sintéticas temporárias. **Isso não equivale a inspecionar os repositórios reais.**
- [ ] Inspecionar configurações, dependências e pontos de entrada reais em `CAMPANARIO-PYTHON`, sem copiar `.venv` para o IA.
- [ ] Inspecionar SQLite/arquivos e os scripts de backup/restore reais em `CAMPANARIO-DATABASE` **sem alterar dados de usuário**.
- [ ] Executar baseline em **Python 3.12 no Windows**, com versão Ollama, modelos, RAM, CPU e dispositivo documentados; comparar nomes/causas de falhas, não apenas totais.
- [ ] Construir matriz de contratos entre chat Web, desktop, companion mobile e voice/call, de modo que a seleção de cérebros atravesse apenas o `ChatService`/runtime compartilhado.
- [ ] Criar fixtures sintéticas e anônimas, inclusive documento fictício de Ordem Paranormal e planilha conhecida; o livro real só poderá ser testado se realmente estiver importado.

**Gate R0:** diagnóstico reproduzível + restauração de backup testada em cópia + inventário de contratos entre três pastas + baseline assinado. Não prosseguir com migração do banco real antes disso.

### R1 — Política única e isolamento de execução — P0 / FAILSAFE OBRIGATÓRIO

- [x] `BrainExecutor` utiliza subprocesso encerrável apenas para os adaptadores de Conhecimento e Análise, com `trace_id`, guard JSON, timeout fatal e monitor RSS; os adapters experimentais seguem thread por compatibilidade e **não são executores seguros para código externo**. Testes com worker travado e RSS excessivo passaram.
- [~] `PermissionPolicy` central está ligada aos cérebros pela composição canônica e valida `library:read` antes da execução. APIs de utilidades e outras entradas ainda não têm integração uniforme; acesso local não é autenticação de usuário pareado.
- [~] Isolar **as duas consultas de leitura** em processo terminável (executado e testado). **Pendente**: quotas OS rígidas de CPU/RAM/arquivo, allowlist imposta pelo sistema, bloqueio de rede, Windows Job Objects, binário empacotado e isolamento adequado para código externo.
- [~] Integrar política runtime em `brains/api.py`/ChatService/executor para leitura; **pendente**: mesma autorização efetiva em `utilities/api.py`, clientes pareados, ações e dispositivos.
- [~] **Incremento R1.1 testado:** limite total de tempo para plano de até 3 cérebros, circuit breaker volátil por cérebro (3 incidentes/30s; cooldown 20s), limpeza do subprocesso ao cancelar tarefa, `trace_id`/`request_id` no protocolo e ambiente mínimo sem tokens/proxies; falha fechada sem monitor. **Pendente:** cancelamento end-to-end em todos os canais, orçamento CPU/IO do kernel, recuperação de processos órfãos em todas as plataformas, traces distribuídos e propagação/autorização de recursos noutros serviços. Ver [`R11_PROTECOES_EXECUTOR_CEREBROS.md`](R11_PROTECOES_EXECUTOR_CEREBROS.md).
- [ ] Classificar operações em leitura, escrita, rede e ação irreversível; exigir confirmação humana para ações de risco; o cérebro nunca aprova a própria permissão.
- [~] Worker R1.1 não herda variáveis arbitrárias de ambiente; guard Python impede chamadas de rede usuais em `knowledge`/`analysis`, **mas não impõe bloqueio OS**. Continua pendente revisão de prompt injection, conteúdos e traces nos demais cérebros/APIs.
- [~] Fault injection R1/R1.1: timeout real, subprocesso travado, RSS excedido, negação, saída malformada, circuit breaker e cancelamento externo; faltam reinício durante execução, limites OS e perda de observador/evento sob Windows.

**Gate R1 — ainda NÃO cumprido:** nenhum código externo consegue escapar do sandbox; timeout interrompe a execução e não só a espera; negar permissão não executa efeito; falhas degradam com aviso e sem perda de chat. **Não liberar Programação nem ferramentas invasivas antes desse gate.**

### R2 — Planejador de capacidades e colaboração entre cérebros — P0

- [x] `CapabilityRouter` separado do `AgentRouter`, limite estrutural de três cérebros.
- [ ] Definir plano tipado com objetivo, entradas/saídas, pré-requisitos, justificativa, autorizações e orçamento por cérebro; validar dependências e proibir referências cíclicas.
- [ ] Selecionar determinísticamente pedidos explícitos (documentos, planilhas, ferramentas); usar classificação por Ollama **somente** quando a ambiguidade material justificar, com fallback para pergunta esclarecedora/fluxo legado.
- [ ] Permitir composição **sequencial e limitada** (ex.: Conhecimento → Investigação → Comunicação), sem fan-out por padrão e sem carregar múltiplos modelos desnecessariamente.
- [ ] Passar resultado de um cérebro como dado tipado não confiável para o próximo, jamais como `system prompt`; preservar lineage de evidências, erros parciais e cache por revisão de fonte/TTL.
- [ ] Instrumentar decisões do roteador, ferramentas invocadas, latência por etapa e custo de contexto observável; cenários de indireção e referência anafórica.

**Gate R2:** plano idempotente com no máximo 3 cérebros, sem loops, fonte/autorizações verificáveis, `AgentRouter` inalterado, e conversa cotidiana sem latência/model calls adicionais desnecessários.

### R3 — Conhecimento confiável e investigação documental — P0/P1

- [x] Recuperação documental V8 encapsulada pelo cérebro Conhecimento.
- [ ] Auditorar PDF textual/digitalizado, DOCX, Markdown, CSV, XLSX, JSON, múltiplas colunas, notas, OCR seletivo, paginação, tabelas e estrutura do texto na base real.
- [ ] Implementar testes de regressão para busca híbrida/reranking/embedding local, identificação de página/trecho, reindexação incremental e permissões de documentos.
- [ ] Garantir `evidence_refs` somente a partir de `BrainRun` executado; deduplicar citações e distinguir fonte inexistente de ausência de trecho relevante.
- [ ] Expor comparação entre fontes, contradições, cronologias e hipóteses no cérebro **Investigação**, com fatos/hipóteses rotulados, sem inventar contexto.
- [ ] Testar a conversa de três turnos sobre **Ocultista, 20% de NEX** contra arquivo realmente importado: responder com trecho/página que existe, ou informar indisponibilidade; não hardcodar regra do livro.

**Gate R3:** consulta com prova de execução, origem e página válidas, falha honesta sem evidência, contradição preservada e testes com exemplos sintéticos mais documento real autorizado.

### R4 — Análise reprodutível de dados — P0/P1

- [x] Análise CSV/XLSX V8 com operações numéricas determinísticas e registro de ferramentas.
- [ ] Schema de colunas, formatos locais/decimais, unidades, nulos, filtros, agregações, períodos, séries temporais, comparação e gráficos com origem rastreável.
- [ ] Query SQL somente leitura ou leitura/escrita estritamente autorizada, parametrizada; sem SQL gerado por texto livre sendo executado sem validação.
- [ ] Artefatos de análise exportáveis e reutilizáveis com hash de entrada, versão da operação, parâmetros, amostragem, arredondamento e resultados verificáveis.
- [ ] Verificar limites de arquivos extensos, consumo real de RAM, concorrência, cancelamento e isolamento do R1.
- [ ] Integrar fatos calculados ao `Canonical Answer Builder`/validador V9.1: números, condições e unidades protegidos; interpretação, hipótese e recomendação separadas.

**Gate R4:** soma/estatística conhecida (CSV/XLSX) coincide com cálculo independente, nunca é recalculada pelo LLM; todas as operações são auditáveis e interrompíveis.

### R5 — Estratégia e Investigação: execução especializada — P1

- [ ] Implementar cérebro **Investigação** a partir das evidências estruturadas, com matrizes de conflito, evidência contrária, hipóteses e graus de incerteza identificados (não inventar confiança percentual).
- [ ] Implementar cérebro **Estratégia** para planos, dependências, prioridades, riscos e acompanhamento; distinguir plano sugerido de ação executada.
- [ ] Proibir que ambos inventem fontes ou executem ações; execução real de etapas exige autorização em R1 e ferramenta disponível.
- [ ] Testes com documentos contraditórios, prazos e cenários sem dados suficientes, além de validação com Morgana e Todd em estilos distintos.

**Gate R5:** registry só troca `unavailable` por `ready` após executor, health-check e suíte documentada; relatórios distinguem fato, inferência e proposta.

### R6 — Programação: ferramentas de desenvolvimento sob sandbox — P1 / DEPENDE DE R1

- [ ] Leitura segura e diffs de repositório em diretório permitido; análise estática, lint e testes com ambientes isolados, tempo/memória limitados.
- [ ] Escrita somente depois de aprovação explícita; plano, diff e rollback de arquivo antes de qualquer alteração; sem acesso a `.env`, credenciais, bancos ou código fora do workspace autorizado.
- [ ] Não usar os talentos Revisão Técnica/Artífice para contornar política; testar pacote/arquivo hostil, symlink, path traversal, prompt injection e mudanças concorrentes.

**Gate R6:** auditoria integral do que foi lido/modificado, rollback verificável, nenhuma execução fora do sandbox e bloqueio de ações não autorizadas.

### R7 — Percepção e integração de mídia — P1/P2 / DEPENDE DE F5 QUANDO FOR VOZ

- [ ] Implementar adaptadores multimodais **somente se** houver ferramentas/modelos locais compatíveis (imagem/áudio); caso contrário manter `unavailable`.
- [ ] Reaproveitar o pipeline único de call/runtime, observando consentimento, origem do dispositivo, retenção e memória de mídia.
- [ ] Verificar OCR/áudio com dados de teste, falhas de dispositivo, ausência de modelo, desconexão mobile, CPU/RAM; nunca simular percepção.
- [ ] Condicionar a homologação real de áudio aos gates F5c (STT pt-BR, reprodução, barge-in e latência percebida) do roadmap principal.

**Gate R7:** dados multimodais com proveniência, consentimento e recursos medidos em hardware alvo; nenhum segundo pipeline cognitivo.

### R8 — Comunicação e Criação — P1/P2

- [ ] Implementar cérebro **Comunicação** para estrutura, tradução e adaptação do texto, reutilizando a V9.1; ele não é outro agente, não executa busca fictícia e não substitui o motor de verificação factual.
- [ ] Implementar cérebro **Criação** para escrita e ideação; manter fronteira explícita entre ficção, opinião, exemplo ilustrativo e afirmação factual sobre fontes reais.
- [ ] Manter Ollama/provider compartilhado, contratos de entrada/saída tipados, orçamento de tokens e fallback quando a capacidade não estiver disponível.
- [ ] Testar mesma ficha factual em Morgana/Todd, integridade de números/datas/negações, tradução sem alterar condições e criatividade sem citação falsa.

**Gate R8:** duas apresentações distintas de fatos invariantes; sem referências fabricadas, sem LLM extra para perguntas triviais e sem vazamento de texto reprovado.

### R9 — Arquétipos, talentos, Forja e pacotes — P1/P2

- [x] Oito arquétipos declarativos, seis talentos, `AgentBuild` e persistência `0010` no IA; Forja MVP e inspeção `.campagent`.
- [ ] Criar avaliador declarativo verificável para `preconditions`, prioridades e conflitos de talentos; máximo 2 ativos/turno, com motivos observáveis e sem alteração de permissões/fatos.
- [ ] Prévia comparativa da mesma evidência em builds diferentes, sem gravar memória por acidente; revisão otimista, histórico de versões e rollback seguro de configuração.
- [ ] Testar ciclo de exportar/inspecionar/aplicar **com consentimento**, integridade/checksums, limites de zip e prevenção de ZIP bomb, symlink, scripts e path traversal; pacote nunca contém memória, credenciais, documento pessoal nem permissão efetiva por padrão.
- [ ] Validar a Forja e Central em tela pequena, teclado/leitor de tela e sessões multi-client independentes; rastros medidos, sem números decorativos.

**Gate R9:** troca de build não afeta memórias/conversas, talento nunca altera evidência, pacote hostil é rejeitado e Forja reflete exclusivamente estado real.

### R10 — Operação confiável, performance e release — P0 PARA PRODUÇÃO / P2 PARA POLIMENTO

- [ ] Consolidar telemetria: `request_id`, `trace_id`, cérebro, operação, sucesso/falha, tempo, tamanho do contexto, evidências, cache hit, interrupções; dados sensíveis fora dos logs.
- [ ] Definir SLIs e metas **antes de medir**: percentis p50/p95 de latência por modo, uso de RAM/CPU, taxa de timeout, falhas de ferramenta, cobertura de citações, sucesso de rollback e taxa de erro por cenário; não publicar precisão inventada.
- [ ] Realizar regressão total no Python 3.12 suportado; registrar os testes que historicamente falham (31 na última execução) e resolver ou justificar individualmente antes de chamar o release de homologado.
- [ ] Executar E2E em Windows com Ollama local e três pastas; testar desligar flag sem corrupção, migração `0010` com cópia do banco, export/import seguro, mobile em rede e quedas de conexão.
- [ ] Exercitar o runbook `docs/operations/FAILSAFE_V9_CEREBROS.md` com fault injection, backup e restauração em cópia de dados, sem apagar instalações existentes.
- [ ] Acompanhar gatilhos F5/F6/F7 do roadmap canônico; realizar aceite físico de voz e mobile antes de declarar Campanário pronto para uso cotidiano.

**Gate R10 / definição de pronto:** todos os oito cérebros têm executor/health-check/testes verificáveis; sistema sem regressão nova, isolamento e permissionamento testados, evidências válidas, Ollama/Windows/mobile homologados, restauração demonstrada, documentação e métricas reais. O gate de produção depende também de F5/F6/F7, não apenas deste documento.

## 4. Ordenação recomendada e entregáveis por incremento

| Lote | Prioridade | Dependência | Entrega mínima verificável | Libera |
|---|---|---|---|---|
| L0 | P0 | Base V9/V9.1 | Baseline Windows/Python 3.12, contratos das 3 pastas, backups | Implementação segura |
| L1 | P0 | L0 | R1: executor isolado, política unificada, fault injection | Programação e ferramentas restritas |
| L2 | P0 | L1 | R2: planos tipados, composição limitada e traces | Colaboração entre cérebros |
| L3 | P0 | L2 | R3/R4: fontes e análises confiáveis, testes de evidência/valor | Conhecimento + Análise robustos |
| L4 | P1 | L3 | R5: Investigação e Estratégia realmente executáveis | Quatro cérebros operacionais |
| L5 | P1 | L1 + L4 | R6: Programação em sandbox | Cinco cérebros operacionais |
| L6 | P1/P2 | L3 + F5 quando áudio | R7: Percepção, consentimento e mídia verificável | Seis cérebros operacionais |
| L7 | P1/P2 | L2 + L3 | R8: Comunicação e Criação sobre V9.1 | Oito cérebros operacionais |
| L8 | P1/P2 | L2–L7 | R9: talentos/Forja/pacotes com controles completos | Personalização segura |
| L9 | P0 release | Todos + gates F5/F6/F7 | R10: regressão, métricas, restauração e aceite real | Homologação integrada |

Os lotes podem avançar parcialmente em paralelo **apenas quando não contornarem pré-requisitos de segurança**. Não usar contagem de cérebros no registry como indicador de conclusão.

## 5. Matriz mínima de testes de aceite

| ID | Caso | Condição de sucesso |
|---|---|---|
| V9-01 | `AgentRouter` × `CapabilityRouter` | Escolha de falante independe dos cérebros |
| V9-02 | Ordem Paranormal 20% NEX | Página/trecho de documento realmente importado **ou** limitação honesta; nunca regra fixa |
| V9-03 | Contradição entre fontes | Mostrar as duas evidências, sem escolher arbitrariamente |
| V9-04 | Resultado CSV/XLSX | Valor calculado programaticamente, com input/parâmetros/saída auditáveis |
| V9-05 | Expressão Morgana/Todd | Mesmo fato, número, condição, certeza e fonte em estilos diferentes |
| V9-06 | Talento/arquétipo/pacote | Sem privilégio adicional, alteração de resultado ou acesso a memórias |
| V9-07 | Ferramenta negada | Nenhum efeito externo ocorre e há motivo auditado |
| V9-08 | Timeout / OOM / crash | Executor isolado termina, chat continua e não há sucesso falso |
| V9-09 | Falha de evidência/validador | Fallback canônico ou indisponibilidade; nenhuma resposta reprovada exibida |
| V9-10 | Flag desligada | Mesmo fluxo V9.1 anterior, sem custo dos novos cérebros |
| V9-11 | SQLite / migração / backup | Conversas e memórias preservadas, rollback de código e restauração testados |
| V9-12 | `.campagent` hostil | Rejeitar path traversal, symlink, script, bomba zip, checksum inválido |
| V9-13 | Web/desktop/mobile/call | Estado e sessão coerentes; CPU/RAM/latência medidos no hardware real |
| V9-14 | Novos seis cérebros | Cada brain só marca `ready` com executor, testes de contrato e health-check reais |

A atualização deste **roadmap é apenas documental**. Nenhum executor adicional, isolamento novo, migração adicional ou teste de integração em ambiente real foi instalado por esta alteração.

## 6. Recuperação e decisão de rollback

Consultar o runbook `docs/operations/FAILSAFE_V9_CEREBROS.md`. Em caso de incidente no novo roteamento, desativar `CAMPANARIO_BRAINS_V9_ENABLED=false`, reiniciar controladamente e preservar banco/trace e evidências de falha. **Não** fazer `alembic downgrade 0010` automaticamente: as tabelas V9 contêm builds e histórico operacional e seriam perdidas no downgrade. Se houver corrupção/incompatibilidade, restaurar backup **em cópia** e só depois decidir o procedimento de produção.


## Checkpoint P0 — 19/11/2026 (implementação parcial, não gate fechado)

- [x] Diagnóstico de três pastas/venv/SQLite integrado à Central de Cérebros; endpoint local funciona com `CAMPANARIO_BRAINS_V9_ENABLED=false`. Somente leitura; não cria nem move pastas.
- [x] Defesa no executor contra escopo ausente e `BrainResult` incompatível com ID de cérebro/rastro; testes específicos.
- [x] Entrega de atualização por cópia de arquivos no Explorador, sem PowerShell para modificar código; documentação de backup, `.env` privado, venv externa e SQLite em pasta irmã.
- [ ] Acesso e validação reais a `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE` do host, Python 3.12/Windows/Ollama, backup/restore e migration em cópia.
- [ ] Política de autorização unificada e sandbox com kill real; sem esse item **R1 permanece bloqueado**.

**Pasta e persistência (contrato explícito):** `CAMPANARIO-IA` contém código, UI e `.env` privado. A `.venv` executável fica em `CAMPANARIO-PYTHON/.venv/Scripts` (Python 3.12); launcher tenta `Campanario.exe` primeiro, venv externa depois, e venv legada por último. `CAMPANARIO-DATABASE/dados/{desenvolvimento|producao}/campanario.db` guarda SQLite conforme `CAMPANARIO_DATA_DIR` e `CAMPANARIO_MEMORY_ENVIRONMENT`; `CAMPANARIO-DATABASE/zim` guarda ZIM opcional. Não instalar `.venv` ou banco dentro de ZIPs de atualização de código. O controle manual por Explorador e os limites do diagnóstico estão no manual P0.


### Pendência identificada no P0 — Biblioteca Conversacional V2

- [x] Identificado SQLite estático legado `CAMPANARIO-IA/data/interaction_library_v2.sqlite`, usado por `agents/interaction_library.py` como exemplos comportamentais de leitura, **não** banco de memória pessoal.
- [x] Implementada preferência por `CAMPANARIO-DATABASE/dados/reference/interaction_library_v2.sqlite` quando já existe, mantendo fallback legado; diagnóstico aponta qual caso está em uso.
- [ ] Copiar e validar a biblioteca V2 real na pasta separada do usuário (sem exclusão automática e sem alterar dados pessoais). O R0 só poderá marcar isolamento total de bancos após essa validação.


### Checkpoint R1 incremental — subprocesso e política (19/11/2026)

**Código implementado:** `brains/isolation.py`, `brains/worker.py`, `brains/executor.py`, `brains/contracts.py`, `chat/service.py`, `brains/api.py`, `composition.py`. Protocolo JSON em processo isolado; apenas `knowledge` e `analysis` são aceitos; a exceção/saída inválida não gera evidência. O processo é encerrado ao exceder timeout (não apenas `asyncio.wait_for` sobre thread) ou RSS amostrado. Em POSIX há limite soft de CPU; no Windows CPU/RSS dependem do watchdog do pai, portanto **não garante contenção hostil**. O processo roda com permissões de SO do usuário e pode acessar filesystem/rede se biblioteca comprometida: **não é sandbox seguro para executar código arbitrário**. `sys.frozen` falha com `worker_python_unavailable` se não houver intérprete sidecar; o launcher que prioriza EXE precisa homologação.

**Segurança:** a `PermissionPolicy` do runtime checa `library:read` para chat e prévia; o executor nega se não receber contexto. Os outros caminhos de utilidades e o `PermissionPolicy` de ações externas ainda precisam ser unificados. Criação de agentes, talentos e arquivos não elevam escopos.

**Três pastas:** não mover a `.venv` de `CAMPANARIO-PYTHON`; worker usa `sys.executable` (Python 3.12 esperado). Não embutir venv em ZIP nem alterar arquivos em `CAMPANARIO-DATABASE/dados`; a escolha do SQLite vem do `CAMPANARIO_DATA_DIR` e `CAMPANARIO_MEMORY_ENVIRONMENT` já configurados. O SQLite da Biblioteca Conversacional V2 permanece com fallback legado documentado. Nunca executar migrations como parte de sobreposição de arquivos.

**Aceitação pendente para R1 fechado:** execução Windows 3.12/EXE, sandbox OS hostil, política unificada em `/api/v1/utilities`, rede/arquivos/cancelamento auditados, R0 completo (backup/restore e contratos reais das outras duas pastas). **O próximo lote de desenvolvimento deve atacar esses itens antes de R2/R6**.
