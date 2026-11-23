# CAMPANÁRIO — Roadmap de conclusão da arquitetura de cérebros (V9 + V9.1)

**Estado:** planejamento de integração; NÃO constitui declaração de implementação das fases pendentes.  
**Base auditada:** cópia `CAMPANARIO-IA` V9 integrada à V9.1, em 19/11/2026; incrementos P0, R1, R1.1 e R2 experimental realizados localmente na cópia IA, sem acesso ao host Windows.  
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
| Testes disponíveis | `tests/test_v9_brains.py` e regressão V8/V9.1 | Última regressão dividida documentada: **1.029 aprovados / 31 falhas preexistentes** (R2: 1.022 legados + 7 testes R2) no ambiente local; NÃO declarar 100% de sucesso |

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
- [~] **R2 incremental:** `BrainStep`/`BrainPlan` tipados com objetivo, contratos, escopos, motivo e dependências verificadas; orçamento total vem do executor R1.1. Pendentes: validação cruzada de pré-requisitos externos e política integrada em todas as ferramentas.
- [~] **R2 incremental:** seleção determinística de documento, planilha e pedido explícito misto, incluindo comandos sem `?`; classificação de ambiguidade via Ollama e esclarecimento formal ainda pendentes.
- [~] **R2 incremental:** `Conhecimento → Análise` sequenciais e read-only para consulta mista; outros seis cérebros continuam indisponíveis, sem fan-out ou múltiplos modelos adicionais. A comparação semântica não está implementada.
- [~] **R2 incremental:** IDs tipados de evidências realmente lidas são rastreados na etapa seguinte, sem transformar conteúdo em `system prompt`; resultado composto e falhas parciais explicitados. Transferência de dados analíticos entre cérebros e cache por revisão/TTL pendentes.
- [~] **R2 incremental:** plano, motivos, passos, operações, latência e resultado de consolidação na prévia e no debug factual; custos de contexto, anáforas complexas e métricas end-to-end pendentes.

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

A frase de atualização apenas documental pertencia ao patch de roadmap anterior. **R2 agora inclui código e testes locais**, descritos em `R2_PLANEJAMENTO_COLABORACAO_CEREBROS.md`; isso não homologou o Windows, o sandbox OS nem as três pastas reais.

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

**Aceitação pendente para R1 fechado:** execução Windows 3.12/EXE, sandbox OS hostil, política unificada em `/api/v1/utilities`, rede/arquivos/cancelamento auditados, R0 completo (backup/restore e contratos reais das outras duas pastas). **Esses itens devem ser resolvidos antes de liberar a R2 geral (além da colaboração somente leitura já testada) ou R6**.


## Checkpoint R2 — colaboração somente leitura (19/11/2026)

- [x] Plano tipado `BrainStep` com validação de dependências acíclicas, escopos e trace; seleção determinística de consulta mista documento + planilha.
- [x] Execução sequencial dos dois cérebros de leitura já existentes; propagação limitada a IDs de evidências observadas, sem LLM intermediário.
- [x] `CollaborationSnapshot` consolida trechos, cálculos, operações, limites e erros antes da expressão; a resposta assume explicitamente que não fez comparação semântica.
- [x] Chat e prévia da Central exibem etapas executadas/limitações. Flag desligada não ativa cérebros. Testes sintéticos registrados em `RESULTADOS_TESTES_R2.md`.
- [ ] Ainda faltam gates R0/R1 (três pastas/Windows/segurança), integração semântica cross-brain, cache versionado, seleção assistida por modelo em ambiguidade e futura colaboração com Investigação/Estratégia. **R2 não está homologada como fase completa.**

Consulte [`R2_PLANEJAMENTO_COLABORACAO_CEREBROS.md`](R2_PLANEJAMENTO_COLABORACAO_CEREBROS.md) e [`FAILSAFE_V9_CEREBROS.md`](../operations/FAILSAFE_V9_CEREBROS.md).

## Checkpoint R2.1 — dependências, proveniência e autorização opt-in (19/11/2026)

- [x] `BrainStep` valida `dependency_policy=optional|required`, contratos de entrada/saída e pré-requisitos. Dependência `required` não chama o cérebro sem evidência first-party concluída; `optional` mantém cálculos independentes e reporta a ausência da outra fonte.
- [x] `result_validation.py` rejeita trace, fonte duplicada, fonte em resultado falho, operações inválidas e divergências entre o guard first-party e os metadados de evidência; fontes de extensões não são propagadas como prova sem adaptação auditada.
- [x] Planos compostos exigem correspondência de `trace_id` e intenção antes de executar workers. Contratos legados de um cérebro mantêm compatibilidade até sua migração.
- [x] **Flag V9 ligada:** registro de capacidades exige `AuthorizationContext` explícito para ferramentas com `permissions`, sem fallback implícito a `internal_system`; `PermissionPolicy` ainda toma a decisão final.
- [ ] Unificar a autenticação/confirmação da API humana `/api/v1/utilities/invoke` com a política do runtime. O endpoint direto NÃO é coberto pela mudança acima; evitar declarar R1 encerrado.
- [ ] Homologar subprocesso, Job Objects, autorização real, `.venv` externa e Database em Windows/Python 3.12; sem esse gate não liberar ferramentas invasivas.

**R2.1 é incremento parcial sobre R2**, não fase completa nem prova de isolamento OS. Não houve mudança em Alembic, modelos, `.env` ou dados. Ver [`R21_DEPENDENCIAS_PROVENIENCIA_PERMISSOES.md`](R21_DEPENDENCIAS_PROVENIENCIA_PERMISSOES.md), [`RESULTADOS_TESTES_R21.md`](../operations/RESULTADOS_TESTES_R21.md) e [`FAILSAFE_V9_CEREBROS.md`](../operations/FAILSAFE_V9_CEREBROS.md).

### Incremento R2.2 (23/11/2026; sem liberação de gate)

Foi instalada uma ponte **parcial** da `PermissionPolicy` na API HTTP de utilidades, condicionada à flag V9, com falha fechada e testes de escrita/upload negados. Isso reduz um atalho de autorização, mas o navegador ainda não possui aprovação PF6 completa, e a operação de escrita no modo V9 permanece bloqueada por padrão. O gate prioritário continua R1; implementar autenticação de principal e confirmação vinculada a operação/scope, além de sandbox OS e homologação de host. Não avançar R5–R10 nem declarar F5 aceito. Arquitetura: IA/código, PYTHON/`.venv` externa, DATABASE/SQLite persistente; dois últimos não enviados e não alterados.

### Checkpoint R2.3 — PF6 anti-replay e validade curta (23/11/2026)

- [x] Núcleo de `PermissionPolicy`: token vinculado a principal, dispositivo, sessão, capacidade e escopo de operação; TTL de cinco minutos, emissão uma só vez, consumo atômico por lock e limite de pendências. Ver testes `test_r23_pf6_confirmation_hardening.py`.
- [ ] **Não é fechamento de R1**: UI de consentimento autenticado, sandbox OS, autorização em todas as rotas, execução Windows/Python 3.12 e aceites nas três pastas não foram validados. `approve()` é primitiva interna; jamais expor chamada não autenticada.
- [ ] Próximo incremento: principal humano autenticado e revisão explícita da operação + argumentos antes de permitir aprovação; testar timeout, interrupção e recuperação no Windows. Não liberar executores restantes antes de seus gates.

**Invariantes de implantação:** `CAMPANARIO-IA` só código/interface; `.venv` única em `CAMPANARIO-PYTHON/.venv`; SQLite/memórias/Biblioteca V2/documentos em `CAMPANARIO-DATABASE` (com fallback legado da Biblioteca onde documentado). Nenhuma migração automática ou alteração de dados via ZIP. FAILSAFE e relatório R2.3 são as referências de recuperação e testes.


### Checkpoint R2.4 — Aprovação local PF6 opt-in (23/11/2026)

- [x] API `/api/v1/utilities/confirmations/request` cria solicitação da `PermissionPolicy` para ferramenta WRITE conhecida; argumentos são vinculados ao escopo `operation:sha256` por JSON canônico. O token nunca é fornecido na solicitação.
- [x] API `/api/v1/utilities/confirmations/approve` exige credencial local do proprietário `CAMPANARIO_PF6_OWNER_TOKEN` forte (mínimo 32 caracteres, até 256) configurada privadamente; verifica confirmação, ferramenta, escopo, principal, reconhecimento explícito e validade antes de aprovar. Ausente = indisponível, sem autoaprovação. Segredo nunca é salvo pelo frontend nem incluído no ZIP.
- [x] Interface `ferramentas.js` revisa argumentos e exige credencial via prompt, por operação. `/invoke` aceita token PF6 fora dos argumentos; token é consumido somente na operação exata e uma vez. A confirmação legada do `UtilityService` permanece, não substitui PF6.
- [x] Regra `utilities.write` agora usa `SCOPED_CONFIRM` no runtime (somente V9); leitura e V9 desligado preservados. Upload binário/Base64 sem fluxo PF6 continuam NEGADOS em V9. Nenhuma migração, banco, `.venv` ou alteração em outros repositórios.
- [x] 36 testes direcionados aprovados e `node --check` aprovado no ambiente Linux. Suíte ampla: 530 aprovados até primeira falha de `test_g2_grounding_audit`, reproduzida no ZIP R2.3 sem alteração; suíte total NÃO aprovada.
- [ ] **R1 NÃO FECHADO:** a credencial local é prova de posse de um segredo, não identidade humana ou sessão autenticada com revalidação/revogação. Browser pode sofrer XSS; falta autenticação individual, CSRF hardening completo, proteção física da máquina, rate limiting, UI não baseada em prompt, autorização de uploads, isolamento SO/Windows Job Objects, testes reais Windows/Python 3.12 e testes dos repositórios separados. Não habilitar Programação ou expansão invasiva.

**Próxima etapa:** R2.5: revisar autenticação individual/sessões reais e UI de consentimento resistente a XSS/CSRF, revogação, limites de tentativas e ciclo de vida; em paralelo homologar Windows 3.12, baseline da suíte ampla e F5 físico. Topologia preservada: `CAMPANARIO-IA` código e interface, `CAMPANARIO-PYTHON/.venv` Python externo, `CAMPANARIO-DATABASE` SQLite/documentos/memórias persistentes externos.


### Checkpoint incremental R2.5 (23/11/2026) — Sessões PF6

**Implementado e validado em código:** `utilities/pf6_sessions.py` define sessões locais temporárias (15 min, 32 simultâneas no máximo, SHA-256 de token no servidor), bloqueio de login por cinco falhas/60 s por IP local, revogação e invalidação por alteração do segredo. `utilities/api.py` exige sessão para request/approve e para consumação de token de escrita. Confirmação continua vinculada à operação, sessão, principal e uso único. Frontend mantém token apenas em memória e oferece logout; credencial continua em `prompt` (limitação). Testes direcionados 41/41; regressão ampla 530 PASS / 1 FAIL histórico G2 e parada na primeira falha. R1 parcial.

**Não implementado:** identidade pessoal independente, contas, MFA, proteção XSS comprovada, isolamento Windows Job Objects, upload PF6, autorização global de outras rotas. Os dois executores Conhecimento/Análise permanecem únicos; seis não foram ativados. R0/R1/R2, F5 e R10 mantêm seus gates.

**Próxima ação:** R2.6 diálogo de consentimento robusto + identidade humana offline compatível com FAILSAFE, depois testes Windows e isolamento OS. Repositórios independentes: IA código; PYTHON `.venv` externa Python 3.12; DATABASE SQLite/Biblioteca V2/memórias/documentos externos. Não duplicar dados nem mover `.venv`; rollback somente arquivos IA. Ver `../operations/FAILSAFE_V9_CEREBROS.md` e `../operations/RESULTADOS_TESTES_R25.md`.


### Checkpoint R2.6 — Consentimento local e proteção da superfície Web (23/11/2026)

- [x] A tela Ferramentas substitui o `prompt` da credencial PF6 e o `confirm` da revisão exata por `<dialog>` modal com foco, opção Cancelar, checkbox explícito e apresentação dos argumentos por `textContent` (sem interpretá-los como HTML). Credencial fica apenas na memória da requisição, não no DOM após o fechamento e não em Web Storage. Permissões PF6 continuam na política central, com sessão R2.5, escopo por argumentos, expiração e uso único.
- [x] Em V9, a revisão é obrigatória antes de `/confirmations/approve`; a confirmação inicial do modo legado não substitui a autorização V9. A API `/status` informa apenas `pf6_mode` (booleano), sem divulgar segredo. Política de origem da API recusa `Sec-Fetch-Site` cross-site/same-site e origens opacas ou divergentes; a página de Ferramentas aplica CSP `script-src 'self'`, `frame-ancestors 'none'`, `object-src 'none'`, além de `no-store` e `nosniff`.
- [x] Testes direcionados R2.2–R2.6: 22 aprovados; verificação sintática JS aprovada. Regressão ampla: 530 PASS, 1 FAIL G2 histórico (já observado R2.3–R2.5), interrompida no primeiro FAIL; **não** homologada.
- [ ] R2.6 é incremento **PARCIAL**, não fecha R1: ainda não há contas/identidade humana individual, MFA, revisão completa de sinks XSS, isolamento Windows OS/Job Objects, aprovação de upload V9, validação por navegador real e Windows/Python 3.12, nem testes com repositórios externos. Não habilitar executores adicionais por causa deste incremento.
- [ ] Próximo passo R2.7: modelo de identidade offline sem substituir o segredo compartilhado de forma insegura, testes de interface real (teclado/mobile), revisão XSS completa e homologação/sandbox Windows. Repositórios independentes: `CAMPANARIO-IA` (código), `CAMPANARIO-PYTHON/.venv` (único ambiente Python externo), `CAMPANARIO-DATABASE` (SQLite/Biblioteca V2/memória/documentos persistentes); nenhum dado ou ambiente foi migrado/criado.

Veja `CHANGELOG_R26.md`, `LEIA_PRIMEIRO_R26.md`, `docs/operations/RESULTADOS_TESTES_R26.md` e `docs/operations/FAILSAFE_V9_CEREBROS.md`.


## Checkpoint R2.7 — Identidades PF6 individuais opcionais (23/11/2026)

**Incremento implementado (R1 ainda PARCIAL):** `utilities/pf6_identities.py` permite configurar voluntariamente operadores locais nomeados (`CAMPANARIO_PF6_USERS_JSON`) com verificadores PBKDF2-HMAC-SHA256 (600.000 iterações, salt individual de 16 bytes). Identificadores validados (3–32 caracteres ASCII definidos) e credenciais de no mínimo 16 caracteres para novos verificadores. Sem novo banco ou conta padrão; verificadores permanecem no `.env` privado, não em ZIP, IA ou Database. O login de Ferramentas aceita nome de usuário e senha, continua com sessões de 15 minutos, lockout de cinco tentativas/60 segundos por cliente e revogação em memória. Ao configurar contas individuais, a senha antiga `CAMPANARIO_PF6_OWNER_TOKEN` **não** permite login ou bypass no modo individual; no modo antigo sem contas configuradas, o proprietário continua compatível.

**PF6 e auditoria:** `principal_id=pf6-user:<nome>` percorre solicitação, aprovação e invocação e é gravado nas trilhas de política existentes. O token PF6 ainda é escopado à operação exata, sessão e principal, one-shot/TTL de cinco minutos. Alteração do conjunto de verificadores invalida sessões individuais existentes; configuração não vazia malformada é erro fechado 503 e nunca aceita segredo proprietário como fallback. A interface Dark Matter passou a mostrar campo opcional de usuário, mantendo segredo e bearer em memória temporária, nunca em LocalStorage.

**Validação observada (Linux):** 27/27 testes direcionados PASS; `node --check` PASS; regressão geral `pytest -q -x`: 530 PASS / 1 FAIL no G2 (`test_false_claim_never_streamed_or_saved`), mesma falha pré-existente R2.3–R2.6; suíte não aprovada. Integração real com navegador, Windows 3.12, mobile, Ollama e repositórios externos não testada. Revisão de XSS/CSRF limitada à superfície Ferramentas, sem alegar auditoria global. Sem sandbox Windows/Job Objects, MFA, ACL individual por capacidade, identidade por OS ou autenticação de clientes remotos; falhas não devem liberar os outros seis executores nem F6/F7.

**Próximo desenvolvimento sugerido R2.8:** revisão de permissões/ACL por usuário, sessão e rota para todo o sistema; auditoria da UI e E2Es reais Windows/mobile, sandbox SO e resolução da falha G2. **Três pastas intactas:** `CAMPANARIO-IA` contém código e interface, `CAMPANARIO-PYTHON` contém Python e `.venv` externa compartilhada, `CAMPANARIO-DATABASE` mantém SQLite, Biblioteca V2, memórias, conversas e documentos persistentes. Sem migrations nem duplicação de dados. A instalação e rollback são feitos por mesclagem/restauração apenas da pasta IA no Explorador de Arquivos, com backups privados independentes antes de qualquer alteração. Ver FAILSAFE e `RESULTADOS_TESTES_R27.md`.


## R2.8 (23/11/2026) — checkpoint experimental, R1 aberto

ACL de ferramentas de escrita PF6 por usuário offline, deny-only, sem permissões implícitas (`utilities/pf6_acl.py` + checagens em `utilities/api.py`). Configuração privada `CAMPANARIO_PF6_WRITE_ACL_JSON`; configurada em `.env` individual, nunca incluída no ZIP. Confirmações PF6 continuam vinculadas a escopo exato, sessão e principal. Contas individuais sem ACL têm escrita negada; modo de proprietário legado não muda. **Gate da documentação** agora exige sincronizar `ROADMAP.md`, este roadmap, `FAILSAFE_V9_CEREBROS.md` e `docs/governance/MANUAL_TECNICO_VIVO.md` a cada nova versão, com changelog/relatório/instruções e revisão de código. A automação checa presença/versão, não verdade semântica. Testes PF6 direcionados 28 PASS; F5 físico/R1 sandbox/R10 seguem pendentes. Próxima etapa R2.9: XSS/CSRF/endpoints e homologação, mantendo a topologia IA, Python `.venv` externa e Database independente.


## Checkpoint R2.9 — precedência factual sobre expressão (23/11/2026)

- [x] `GroundedExpressionEngine.express` detecta `CanonicalAnswer.brain_ids` em modo factual e evita uma paráfrase livre pelo LLM; o conteúdo do compilador canônico é copiado literalmente, com abertura de estilo **fixa e não factual** para Morgana ou Todd quando existe leitura/evidência válida. Falta/conflito/erro permanece literalmente como compilado.
- [x] `ChatService` dá precedência ao `canonical.canonical_answer` de um cérebro sobre fontes auxiliares; testes em `tests/test_r29_brain_factual_boundary.py`. É uma restrição da saída **dos cérebros implementados** e não desliga o modelo para conversa comum.
- [ ] Não afirmar que o LLM passa a ser verificador semântico, nem que o texto da fonte é verdade externa; proveniência é rastreabilidade de leitura. Seis cérebros seguem sem executor. Cross-source reasoning, avaliações de factualidade real e adversariais maiores faltam.
- [ ] Auditoria de endpoints, XSS/CSRF global, sandbox Windows e aceite integrado seguem abertos em R1. Voz fica fora do foco deste incremento, mas F5 não foi concluída.

**Próximo passo R2.10:** verificar seleção e vinculação de evidências/afirmações e sinais de contradição em Conhecimento e Análise antes de avançar para Investigação/Estratégia. Os três repositórios continuam independentes: código em `CAMPANARIO-IA`, `.venv` única em `CAMPANARIO-PYTHON`, dados persistentes em `CAMPANARIO-DATABASE`. Gate documental obrigatório em todos os próximos incrementos.


## Checkpoint R2.10 — auditoria literal fonte→afirmacao (23/11/2026)

Conhecimento e Analise continuam os unicos dois cerebros com executor. `chat/canonical_answer.py` rejeita `source_assertion` de resultado V9 de cerebro quando o texto nao consta literalmente de nenhum `SourceRecord.excerpt` referenciado pela afirmacao. O gate funciona antes do Motor V9.1; ao falhar rebaixa para `not_found`. Esta e uma prova de correspondencia textual, NAO de veracidade do conteudo, inferencia nem verificacao de relevancia semantica. Saidas `computed` seguem o adaptador de Analise; contradicoes continuam explicitadas no status ja existente. `chat/evidence_gate.py` e `chat/service.py` separam solicitacoes subjetivas das consultas factuais, preservando o modo conversacional quando cabivel.

**Real:** 76 PASS direcionados; suite geral 530 PASS ate falha historica G2; Windows/Ollama/Database nao testados. **Proximo R2.11:** cobertura de perguntas por evidencia, confronto conservador de fontes, benchmark, G2. R1 isolamento, F5 voz e seis novos executores permanecem pendentes. Três repositorios separados: IA=codigo, PYTHON=.venv unica externa, DATABASE=dados SQLite persistentes. Processo obrigatorio: revisar ambos ROADMAPs, FAILSAFE, Manual Tecnico Vivo e relatorio em cada entrega.


## Checkpoint R2.11 — evidencia vinculada, auditoria G2 e restricoes de inferencia (23/11/2026)

**Implementado em IA:** integracao do auditor pessoal existente (`chat/memory_grounding.py`) ao runtime (`chat/service.py`), antes da publicacao ou persistencia. Modelo fornece parecer estruturado com citacoes, mas o veto deterministico sobre novas intensidades/exclusividade continua independente do parecer. Ausencia de memorias confiaveis implica resposta desconhecida. Novo teste `tests/test_r211_evidence_audit.py` cobre relevancia lexical, conflito entre dois documentos, percentual alterado com source_id valido e citações invalidas. As implementacoes previas de `evidence_gate.py` e `canonical_answer.py` foram **testadas, nao reescritas**. Isso nao prova implicacao semantica ou veracidade externa.

**Validacao:** 74 PASS direcionados, compilacao Python PASS. Regressoes `pytest -q -x`: 601 PASS e 1 FAIL do guard web; a mesma falha reproduzida no ZIP R2.10 original. G2 passou nos direcionados e no percurso amplo. Teste legado HTML ajustado sem mudanca visual. Nao homologado com `.venv` Windows ou Database externo; Ollama e mobile nao testados. F5 segue pendente e fora do escopo atual; R1, R10 e as seis capacidades ainda nao executaveis permanecem pendentes. **R2.12 sugerida:** benchmark factual e tratamento da falha preexistente na selecao de evidencia web sem reduzir resistencia a instrucoes em paginas. Obrigatorio atualizar 2 ROADMAPs, FAILSAFE e Manual Vivo a cada alteracao; IA/PYTHON/DATABASE continuam independentes.


### Checkpoint R2.12 — benchmark de fonte externa, sem novos executores (23/11/2026)

- [x] Na recuperação web `research_entity`, uma página qualificada por categoria e cujo **título e abertura** identificam literalmente o mesmo referente pode sustentar identificação citada. Snippet de busca não é prova; o corpo precisa ter sido lido; categorias inconsistentes são recusadas. Instruções maliciosas no conteúdo permanecem dados de menor confiança e são filtradas da nota de apresentação.
- [x] Matriz determinística `tests/test_r212_factual_benchmark.py` (16 cenários, PASS), mais bateria focal factual (64 PASS). Avalia seleção, abstenção e foco literal, não verdade universal nem coerência semântica.
- [ ] Suíte ampla parou após 603 PASS em falha de mock de sessão do legado web, reproduzida no baseline R2.10. Não enfraquecer `ChatService` para permitir sessões inexistentes.
- [ ] R2.13: adequar fixtures legadas à autenticação/sessões atuais, corpus anonimizado ampliado, validação de contradições e evidência com dados reais, integração Ollama/Windows/Python externo. R1 segue parcial. Apenas Conhecimento e Análise executam; seis outros cérebros catalogados ainda não possuem executor.

Governança obrigatória: atualizar sempre os dois ROADMAPs, FAILSAFE e Manual Vivo, além de testes, changelog, instruções e relatório. Separação IA (código) / PYTHON (`.venv` externa) / DATABASE (SQLite e memória persistente) mantida.

## Checkpoint R2.13 — infraestrutura de regressão factual (23/11/2026)

- [x] Atualização de fixtures de sessão legadas para respeitar `ChatService.stream_turn` sem alterar segurança em produção; testes de auditoria pessoal e proteção de streaming readequados aos contratos vigentes.
- [x] Novo corpus sintético offline de 27 cenários verificando pertinência literal, divergência **já classificada** por retriever, ausência de fonte e adulteração de valores com IDs válidos. 52 testes focados PASS. Os cinco cenários de conflito confirmam propagação de status, **não** detecção automática de conflito pelo cérebro.
- [ ] A regressão ampla ficou **inconclusiva** após 700 PASS (timeout, ~66%). Nenhuma homologação Ollama/Windows/Database ou validação estatística de veracidade. R1 isolamento e seis cérebros não executáveis permanecem pendentes.
- [ ] R2.14: identificar e isolar travamento na suíte geral, expandir testes de entailment/contradição sem alegar que fontes são verdade; validar comportamento no host Windows.

Não liberar Investigação, Estratégia ou outros executores pelo resultado de testes sintéticos; política central e separação cérebro factual → agente expressivo continuam obrigatórias. Os três repositórios IA/PYTHON/DATABASE permanecem independentes.


## Marco R3.0 — fatos antes da personalidade e critérios para os seis cérebros (23/11/2026)

**Auditoria de executores:** `BrainRegistry.local()` continua instalando apenas `KnowledgeBrain` e `AnalysisBrain`. Os seis demais são declarações de catálogo indisponíveis. Este marco NÃO representa entrega dos oito executores.

**Novo contrato transversal implementado:** `reconcile_numeric_evidence()` faz revisão **lexical conservadora** sobre documentos independentes que o runtime realmente leu. Se fontes distintas usarem a mesma frase com um valor numérico diferente, o `build_canonical()` de cérebro mantém status `CONFLICTING`, registra fontes e não escolhe um valor. A revisão não valida verdade de nenhuma fonte, não detecta toda contradição semântica, não autoriza ferramentas e não substitui `PermissionPolicy` nem o isolamento. Números calculados pelo cérebro de Análise não são tratados como citações documentais.

**Aceite R3.0 observado:** 56 testes dirigidos PASS (Linux/Python 3.13); regressão `pytest -q -x` 875 PASS e uma falha de layout legado de `renpy_factory`, pasta presente no ZIP R2.13; suíte integral não homologada. Sem Ollama/Windows/Database. Registros: `docs/operations/RESULTADOS_TESTES_R30.md`.

**Planejamento agregado a seguir:** (1) validar guardas, corpus, isolamento e desempenho dos dois executores existentes no Windows real; (2) definir contratos read-only de Investigação/Estratégia **com evidência e permissões sem atalhos**; (3) implementar com testes da cadeia cérebro → CanonicalAnswer → expressão do agente sem fatos novos; (4) após gate OS, expandir Programação; (5) Percepção, Comunicação, Criação e integração R10. R1/R0 e F5 não foram formalmente fechados.

**Separação invariável:** `CAMPANARIO-IA` = código; `CAMPANARIO-PYTHON` = `.venv` externa única; `CAMPANARIO-DATABASE` = dados persistentes. Atualizar sempre os dois roadmaps, FAILSAFE, Manual Técnico Vivo, changelog, relatório e rollback.


## Marco R3.1 — R5 parcial: executores concretos de Investigação e Estratégia (23/11/2026)

**Mudança demonstrável:** `brains/investigation.py` implementa `InvestigationBrain` e `StrategyBrain`. Ambos usam leitura real via `chat/document_intent.search_document` (SQLite `mode=ro`, `PRAGMA query_only=ON`), produzem `BrainResult` com fontes efetivamente recuperadas e relatório determinístico. `registry.py`, `worker.py`, `isolation.py`, `executor.py`, `result_validation.py`, `router.py`, `collaboration.py`, `brains/api.py` e `chat/service.py` fazem a integração de autorização, subprocesso interrompível, roteamento explícito, validação e apresentação canônica.

**Escopo exato de R5:** [x] executor local read-only dos dois cérebros; [x] status operacional e referências rastreáveis; [x] relatório de lacunas e divergência numérica conservadora; [x] plano condicional com critérios de parada; [x] caminho da prévia e colaboração com `CanonicalAnswer`; [ ] auditoria semântica, inferência causal e hipóteses inferidas com avaliação externa; [ ] planejamento multiobjetivo, simulação, ranking baseado em dados e ferramentas autorizadas; [ ] aceite real Windows + Database externo. **R5 é PARCIAL, não homologada**; R1 sandbox ainda aberto.

Os quatro restantes (`programming`, `perception`, `communication`, `creation`) continuam indisponíveis, sem declarar executor pelo catálogo. Quatro cérebros **com executor no código** não significa quatro cérebros totalmente homologados. Nenhum cérebro, talento ou agente recebe permissões novas, pode alterar resultados de cálculo ou inventar fontes. O modelo/persona não reformula o relatório como fato novo: V9.1 recebe resposta canônica.

**Próximo marco:** estrutura de investigação baseada em relações e cronologia extraídas com verificadores, plano de opções com métricas verificadas e testes de abstenção; homologação do sandbox/Windows quando disponível. Voz F5 sem implementação nesta etapa; trilha formal de F6 continua dependente do gate existente.

**Fronteira:** IA/código, PYTHON/`.venv` externa, DATABASE/SQLite e dados pessoais, sem migrações. Processo de documentação/checkpoint R3.1 obrigatório.

**Complemento R3.1 verificado:** os relatórios agora contam trechos/origens efetivamente recuperados, e Investigação lista datas dd/mm/aaaa literais válidas sem associá-las automaticamente a eventos. Estratégia bloqueia escolha por valores numéricos comparáveis em conflito. Bateria final 74 PASS; regressão anterior 881 PASS/1 FAIL legado e reexecução após ajuste final interrompida antes de completar.


## R3.2 — Espaço de casos auxiliar aos cérebros R5 (23/11/2026)

- [x] Workspace independente de conversa com originais preservados, SHA-256, cronologia declarada, intervalos aritméticos e hipóteses sem veredito, em `brains/casework.py`.
- [x] CLI local para operador via launcher BAT Windows e `.venv` externa; nenhum cérebro/arquétipo/talento recebeu novas permissões.
- [ ] Integração automática do workspace com `BrainExecutor`, `CanonicalAnswer`, APIs de casos autenticadas e Campanário Field **ainda não realizada**. R3.1 continua com quatro executores reais (`knowledge`, `analysis`, `investigation`, `strategy`), quatro pendentes.
- [ ] R1 e R10 continuam não homologados. Casos guardados somente em `CAMPANARIO-DATABASE/dados/cases`, não na árvore IA, e sem SQLite adicional. Referir FAILSAFE R3.2, Manual Vivo R3.2 e testes.

## R3.3 — Casos dentro da interface principal (23/11/2026)

- [x] `CaseWorkspace` R3.2 recebeu adaptador HTTP local nativo em `brains/casework_api.py`, montado no FastAPI principal, com sessão PF6 e identidade do operador verificadas a cada requisição. Todos os dados continuam em `CAMPANARIO-DATABASE/dados/cases`; ambiente Python continua externo.
- [x] `Database > Casos` no Dark Matter: originais, SHA-256, propostas estruturadas, cronologia, hipóteses concorrentes e dossiês sem sair do Campanário. Operações de escrita só com confirmação explícita PF6, scope do conteúdo e ACL adicional para identidades individuais.
- [ ] Ainda **não há** ancoragem automática de caso no `BrainExecutor`, nem chat case-aware de Morgana/Todd; os executores R3.1 (Conhecimento, Análise, Investigação e Estratégia) permanecem independentes da nova UI de casos. Não chamar de oito cérebros operacionais: os outros quatro executores ainda estão pendentes.
- [ ] Validação Windows/mobile e hermeticidade de processos do R1 continuam abertas. O acesso à API é apenas loopback; nenhum endpoint Field de casos foi liberado.

**Próximo gate:** consultas case-aware de leitura com contexto de evidências explicitamente selecionadas, autorização por sessão/identidade e canonicidade factual preservada; testes offline e homologação Windows antes de qualquer promoção de gate.


## Marco R3.4 — Consulta de caso com fronteira factual (23/11/2026)

- [x] `casework_dialogue.py` oferece cinco intenções de leitura determinística e retorna IDs de fontes armazenadas e hashes verificados; a API `/api/v1/cases/{id}/ask` usa sessão PF6 e escopo de proprietário.
- [x] Central e chat principal compartilham a seleção do caso na mesma aba, sem enviar evidências a um modelo nem alterar conteúdo factual por persona.
- [ ] Este caminho **ainda não chama** diretamente os quatro executores `knowledge`, `analysis`, `investigation`, `strategy` sobre originais do cofre. Os quatro executores R3.1 continuam existentes, mas o módulo de casos apresenta sua própria síntese read-only, sem alegar execução cerebral adicional.
- [ ] R1 sandbox, R5 inferência semântica e R10 Windows/Database seguem parciais; os quatro cérebros restantes não têm executor. Próximo: transformar fontes selecionadas do cofre em resultados `BrainResult` verificáveis, preservando escopos PF6, sem inferir fatos.
- Três repositórios preservados: IA, PYTHON (venv externa), DATABASE (persistência).


### R3.4 — Separação entre Central de Casos pessoal e ativação dos cérebros

`casework_api.py` é um serviço de casos da plataforma e **não** depende de `brains_v9_enabled`. Quando não existe configuração de identidade PF6, clientes verdadeiramente locais usam `loopback-utilities` e consultam/criam casos sem login; conversas sobre casos usam o material de `CaseWorkspace` e a resposta determinística sem LLM. Ao configurar PF6 voluntariamente, volta a exigir o fluxo autenticado e política central de aprovação. Não confundir esse acesso ao caso com executor Investigação/Strategy em subprocesso ou concluir R1 por isso. Sem conexão remota, sem banco duplicado, sem alterar os quatro executores.

## Checkpoint R3.5 — fontes do cofre acessíveis na investigação conversacional (23/11/2026)

- [x] Fluxo caso selecionado → validação de owner pela API R3.4 → SHA-256 por arquivo → extração textual com limites → seleção lexical → citação `[E...]` e linha → relatório determinístico de Investigação ou Estratégia → abertura fixa Morgana/Todd. Nenhuma chamada ao LLM para gerar as afirmações deste caminho.
- [x] Reutilização do componente puro `structured_report` do executor R3.1 sobre `EvidenceRef` construídas **somente** de originais verificados. **Não é execução do `BrainExecutor`/worker** neste fluxo e não representa análise semântica profunda. Conhecimento e Análise continuam executores separados; não declarar colaboração total dos quatro nesta API.
- [x] Limite estrito de leitura, ausência de interpretação de imagem/ZIP, fórmulas de planilha não executadas, falha de integridade bloqueia respostas; números divergentes sinalizados apenas em frases estritamente comparáveis. 117 testes focalizados PASS.
- [ ] Ainda faltam revisão humana de inferências, análise temporal e semântica avançada, exportação de localização estável em PDF, integração Field, sandbox Windows e homologação Ollama/Database. Oito cérebros catalogados, quatro com executores. Voz fora do foco.
- **Repos separados:** IA=código; PYTHON=.venv externa; DATABASE=casos, memórias e bases persistentes, sem migração.

## Checkpoint R3.6 — colaboração fundamentada de casos

Os quatro executores existentes permanecem Conhecimento, Análise, Investigação e Estratégia. R3.6 acrescenta uma **orquestração read-only** sobre evidências de caso, não quatro novos workers nem investigação causal automática. O compilador de resposta canônica e a personalidade não podem conceder fatos ou autoridade a resultados de OCR/embedding. OCR lê texto visível, recuperação semântica seleciona passagens, hipóteses continuam não verificadas. Todos os resultados são condicionados a integridade SHA-256 e a limites; indisponibilidade de Ollama/Tesseract permite fallback lexical, nunca invenção. R1 sandbox Windows, homologação integrada R10 e os outros quatro cérebros permanecem pendentes. Três repositórios separados: IA código, PYTHON `.venv` externa e DATABASE persistente; sem dependências obrigatórias novas nem migração. Próxima etapa: visão revisável, relações tipadas e avaliações reais.

Percepção visual provisória **não** significa cérebro de Percepção R7 homologado: R3.6 só propõe observações não verificadas via Ollama local opt-in e não altera o estado dos oito executores (4 ativos/4 pendentes).


## Marco R3.7 — ciclo investigativo limitado e documentos DOCX/HTML (23/11/2026)

- [x] `brains/case_investigation_pipeline.py` evoluiu de uma passagem para até **três consultas sucessivas**: pergunta inicial e até duas verificações registradas pelo operador nas hipóteses. Cada rodada é somente leitura, verifica SHA-256 e registra quantidade de citações novas e motivo de parada; saída limitada a 16 citações deduplicadas. Não executa buscas novas na internet, ações de sistema ou decisões sem autorização.
- [x] Se somente uma consulta secundária tiver trechos, a pergunta principal permanece **sem evidência suficiente**; hipóteses mantêm `unverified`. A resposta canônica de Morgana/Todd preserva os trechos, sem reescrita generativa.
- [x] `casework_sources.py` agora extrai texto de DOCX (XML Word com limites para ZIP, sem macros nem relações externas) e HTML/HTM (somente texto visível, sem executar scripts); `casework.py` e o seletor Dark Matter aceitam essas extensões. PDF digitalizado, OCR, embeddings Ollama e imagem continuam opcionais, sujeitos às limitações R3.6. DOCX/HTML não equivalem a compreensão universal de formatos ou verdade semântica.
- [x] 108 testes direcionados aprovados em Linux/Python 3.13 (incluindo 8 novos testes R3.7). Suíte ampla parou após 566 PASS/1 FAIL em Biblioteca de Interações, já presente na base R3.6/R3.5; não homologada.
- [ ] Investigador universal e compreensão semântica universal **não são atingíveis como garantias gerais**: faltam leitura fiel de documentos complexos, planejamento causal com revisão humana, avaliação em corpus real, OCR/Ollama reais no host Windows, segurança de arquivos não confiáveis e autorização de ações. O ciclo R3.7 é investigação iterativa documental limitada.
- [ ] Outros quatro cérebros especializados permanecem sem executor e R1/R10 continuam abertos. Voz F5 continua fora do foco solicitado, sem ser declarada concluída.

**Próximo marco maior:** avaliar fidelidade e cobertura documental com conjunto de casos reproduzível (incluindo contradições semânticas), permitir revisão humana das hipóteses e conectar decisões justificadas a novas perguntas sem promover palpites a fatos. IA mantém só código, PYTHON mantém uma única `.venv` externa, DATABASE mantém casos/SQLite/memórias; rollback apenas substituindo arquivos IA via Explorador do Windows.


## Marco R3.8 — matriz de relações e fila adaptativa (23/11/2026)

- [x] `case_reasoning.py` mantém a fronteira entre **ligação documental** (identidade do ID, citação literal, sobreposição lexical) e **inferência causal** (não implementada). Referências favoráveis/contrárias refletem cadastramento humano, não probabilidade de uma hipótese.
- [x] As verificações subsequentes de Investigação são priorizadas conforme termos da pergunta e hipóteses com posições cadastradas conflitantes, preservando limite de 3 rodadas, IDs e hashes, e sem execução autônoma.
- [x] Os resultados chegam à UI de casos e chat de Morgana/Todd pela resposta determinística canônica. Nenhum cérebro recebeu autoridade, ferramentas de escrita ou acesso remoto novos.
- [ ] Seguimento: benchmark semântico, avaliação quantitativa de hipóteses sob premissas verificadas, revisão humana e homologação real. Conhecimento/Análise/Investigação/Estratégia possuem executores; outros 4 continuam pendentes.
- **Testes:** 91 dirigidos PASS; regressão ampla 566 PASS, 1 FAIL histórico em Biblioteca de Interações; Linux/Python 3.13, sem Windows/Ollama real.
- **Repos:** IA código, PYTHON `.venv` compartilhada externa, DATABASE dados persistentes; nenhum novo SQLite, ambiente ou migração.

## R3.9 — contrato de proposição textual para Investigação/Estratégia

- [x] `case_claims.review_claims()` recebe apenas citações previamente conferidas pelo `CaseWorkspace`, devolve etiquetas linguísticas de escopo limitado e possíveis oposições textuais entre arquivos distintos. A chave textual requer mesmo sujeito/predicado/complemento, não apenas sobreposição de palavras.
- [x] `investigate_case()` inclui `claim_review`, e o chat de Casos exibe a classificação como **afirmação da fonte, não verdade verificada**. Morgana e Todd não parafraseiam o trecho factual com LLM.
- [ ] A classificação não é inferência semântica geral nem conclusão investigativa: sem co-referência, temporalidade refinada, tradução, probabilidades de verdade ou prova causal. Quatro cérebros continuam com executores; Programação, Percepção, Comunicação e Criação pendentes.
- [ ] R1 sandbox, homologação Windows/Ollama/Database, R10 e gate F5 permanecem abertos. Próxima etapa: adjudicação revisável de afirmações contraditórias com corpus anotado e teste de fonte independente.
- Não alterar a separação CAMPANARIO-IA, CAMPANARIO-PYTHON/.venv externa e CAMPANARIO-DATABASE.



## Checkpoint R3.10 — sugestões semânticas auditáveis

- [x] `case_semantic_review.py` acrescenta anotações literais e relações possíveis por modelo Ollama local, **desligado por padrão**. Resultados são `unverified_model_annotation` / `unverified_model_suggestion`, não um novo cérebro executor nem verdade semântica certificada.
- [x] Fonte obrigatória: citações do Caso conferidas com SHA-256, ID, linha e trecho; o modelo não fornece afirmações independentes nem altera o compilador factual canônico. Morgana/Todd continuam apenas apresentadores.
- [ ] Ainda não são compreensão universal, extração estruturada exaustiva, auditoria humana persistente ou homologação de modelos no Windows. Programação, Percepção, Comunicação e Criação sem executores; segurança OS e R10 abertos.
- [ ] Próxima prioridade: corpus anotado de contradição/paráfrase, avaliação por classe e revisão auditável de relações, com critérios de falha e degradação.
- CAMPANARIO-IA, CAMPANARIO-PYTHON/.venv externa e CAMPANARIO-DATABASE permanecem independentes; nenhum dado privado distribuído e nenhuma migração.


## R3.11 — pré-homologação de interpretação (23/11/2026)

- [x] Inventário local condicional de OCR, ZIM, embeddings e modelo semântico em loopback; não liga V9 ou permissões automaticamente.
- [x] Benchmark artificial de 18 relações com classes separadas e opção de avaliação real via Ollama instalado.
- [ ] **Próxima fase** somente após relatório de precisão/recall real, validação de fontes e inspeção humana de erros; quatro cérebros existentes, quatro não implementados.
- CAMPANARIO-IA, CAMPANARIO-PYTHON/.venv externa e CAMPANARIO-DATABASE continuam independentes.


## R3.12 — homologação factual como gate de evolução dos oito cérebros

Implementado avaliador de aceitação **no IA** (`scripts/homologate_factual.py`) com 34 pares sintéticos e duas rodadas em Ollama local; relatórios opcionais apenas no CAMPANARIO-DATABASE externo. Não houve homologação no Windows/Database nem avaliação de fontes reais neste ambiente. `PASS` técnico não prova compreensão geral, confiabilidade de OCR nem ausência de alucinação; avanço para os outros quatro executores requer teste real com material revisado por humanos, revisão de erros e contratos específicos. Conhecimento, Análise, Investigação e Estratégia mantêm os executores existentes. Não ligar Programação ou qualquer execução privilegiada por resultado de benchmark. CAMPANARIO-PYTHON mantém .venv externa única.


## R3.13 — compatibilidade do upload do chat com modo pessoal local

O upload de arquivo pelo próprio chat não deve ser bloqueado pela política central de V9 quando a instalação for pessoal local e **não houver PF6 configurado**. Exceção restrita aos endpoints de upload; `utilities.invoke`, permissões dos cérebros e identidades configuradas continuam protegidas. Nenhum novo cérebro é habilitado nesta correção; homologação factual R3.12 permanece pendente.


## Checkpoint R3.14 — modo pessoal local por padrão

A configuração `CAMPANARIO_LOCAL_PERSONAL_MODE` é `true` por padrão. O chat e utilidades locais e a Central de Casos dispensam login PF6 e autorização por operação, independentemente de credenciais PF6 antigas no `.env`, sem apagar credenciais nem bancos. A lógica de autenticação anterior permanece disponível com `false` para recuperação futura. O isolamento dos originais, validação de citações, proteção contra sobrescrita e acesso somente loopback **não são permissões que o usuário precisa gerenciar** e permanecem. Foi implementado upload de evidência em fluxo, com teto operacional 1 GiB e 4096 evidências/caso; não é capacidade ilimitada nem homologação Windows. O Catálogo V9 de oito cérebros mantém quatro executores; os demais seguem pendentes.


## Checkpoint R3.15 — biblioteca realmente acessível e respostas ligadas ao documento

**Falha real reportada:** clipe do chat fazia apenas staging de arquivos, mas não invocava `library.import`; portanto, um arquivo presente em `CAMPANARIO-DATABASE/dados/.../utilidades/arquivos/` podia não existir em `documents` nem em `document_sections`, impossibilitando `search_document`. A UI não tornava essa distinção visível. Uma continuação com `qual` sem interrogação era classificada como conversa genérica, fazendo o modelo responder sem a fonte desejada.

**Correção integrada na UI:** chat passa `index=true` em `upload-stream`; o endpoint preserva o arquivo no workspace, importa por `UtilityService` no mesmo DATABASE externo e retorna `indexed`, `indexed_sections`, `index_state`, `document_id` ou `index_error` sem fingir êxito. Importação é feita em thread durante a requisição, nunca em background silencioso. PDF sem texto/OCR ausente e JSON inválido são marcados como não pesquisáveis. Arquivos antigos enviados somente ao staging: em Ferramentas → Arquivos, usar **Indexar**; documentos com erros: Ferramentas → Biblioteca → **Reindexar**. O original continua imutável, com SHA-256 validado antes da reindexação.

**Gerenciamento:** o Explorador e a Biblioteca têm paginação (100 itens/página e total real), nomes, estados, visualização do texto extraído, exclusão e renomeação. A Biblioteca tem `library.rename` (metadados apenas, preservando extensão/arquivo) e `library.reindex` (reextração do original validado e substituição transacional da indexação). Arquivos na pasta autorizada oferecem Indexar/Renomear/Mover/Lixeira. O conteúdo original preservado não é editado diretamente; nova versão deve ser importada conscientemente. Chat permanece na interface Dark Matter, sem nova aba/aplicativo de investigação.

**Intenção documental:** `document_request` reconhece “arquivo relacionado a ordem paranormal” e remove o sufixo “e me diga...” do nome sugerido. Perguntas de acompanhamento com “qual/quais/quem...” sem `?` mantêm a referência explícita recente ao documento; falta de citação continua exigindo abstenção factual. Nenhum nome de criatura da franquia foi codificado como resposta. Trecho recuperado mostra **o que a fonte diz**, não valida cânone externo.

**Verificação:** 90 testes direcionados PASS, incluindo regressões V8, PF6 pessoal, cérebros, casos e semântica; regressão geral: 33 PASS, 1 falha preexistente em `uv.lock` ausente. Compilação e JavaScript verificados. Não houve acesso ao acervo privado do operador nem homologação com Windows/Ollama reais. **Rollback:** fechar o Campanário, restaurar a cópia R3.14 do código e reiniciar; preservar o DATABASE. Metadados criados nesta versão são compatíveis com schema V8; cópia privada de segurança recomendada antes de reindexar ou excluir.


## Checkpoint R3.16 — Maps V2 como serviço factual compartilhado

- Maps é **infraestrutura geográfica determinística**, não um novo executor dos oito cérebros; OSRM fornece geometria, duração estimada e manobras. Morgana/Todd podem solicitar navegação pelo chat existente, sem gerar coordenadas fictícias ou distâncias no LLM.
- APIs desktop permanecem loopback; APIs mobile usam TLS e token pareado por dispositivo. Nenhum cérebro recebe capacidade irrestrita de navegar, rastrear continuamente ou executar automações.
- Servidores OSRM/Nominatim/Overpass e OSM locais não são distribuídos; validação física, TTS Android/desktop e serviço Android em segundo plano pendentes. Quatro executores existentes continuam sem alteração.
- Preservar factualidade V9.1, F5 aberto, personalidades e memórias Todd/Morgana separadas; os três repositórios permanecem irmãos.


## Checkpoint R3.17 — Field ligado aos serviços, não aos fatos do LLM

O Android reutiliza APIs Maps V2 e identidade de dispositivo já pareada, sem criar executores novos, sem expandir capacidades dos quatro cérebros existentes e sem alterar contrato V9.1 de Morgana/Todd. A voz de navegação usa manobras OSRM e não geração livre. Código nativo de guia entregue, **APK/OTA/Room e validação de GPS real pendentes**. Plataforma Field ainda híbrida; os quatro cérebros remanescentes continuam pendentes.

## Checkpoint R3.19 — pacote de trabalho enxuto e busca geográfica corrigida

O código foi reduzido aos módulos necessários ao runtime, testes, contrato Android e guias técnicos atuais. Documentação histórica foi removida **apenas do pacote distribuído**, não dos backups existentes no computador do usuário. A busca textual de endereço funciona sem GPS; buscas por proximidade continuam exigindo origem real/manual. GPS impreciso pode orientar a busca com ressalvas; navegação curva a curva requer fix recente de qualidade. Gradle/SDK Android e OSRM local não foram homologados nesta entrega.


## R3.20 — localização automática e busca/rota com fallback (23/11/2026)

- Ao abrir Maps no Dark Matter, o cliente tenta `navigator.geolocation.watchPosition` automaticamente, conforme a autorização do Windows/navegador. Mantém latitude, longitude, precisão e horário somente em memória de interface; não envia localização ao servidor durante a simples observação. Sem GPS, busca por endereço permanece disponível e a origem manual continua possível.
- A tela Maps usa somente `CampanarioNavigationV2` para os botões de busca/rota, evitando que o antigo `gps-map.js` sobrescreva os handlers.
- Busca por endereço: Nominatim local primeiro; se estiver indisponível, Nominatim público em consulta explícita. Categoria próxima: Overpass local e depois público; roteamento carro: OSRM local e, se estiver indisponível, servidor público de demonstração OSRM. Caminhada: somente grafo pedestre local (não inventar rota de carro).
- O fallback está **ativado por padrão para uso pessoal** e pode ser desativado com `CAMPANARIO_MAPS_PUBLIC_FALLBACK=false`. Serviços públicos recebem a busca e, em roteamento, as coordenadas. Nominatim público tem limitação de uso, identificação do aplicativo, cache em memória e espaçamento de 1,1 s por host; não usar autocomplete nem disparar varreduras. Não há GPS fictício.
- Pendente: teste de campo em Windows/Android; conectividade e política dos provedores públicos; precisão do GPS no PC; compilação APK e navegação Android em segundo plano. Não declarar homologação de campo.


## Checkpoint R3.21 — Field GitHub Pages (23/11/2026)
- Frontend PWA público estático, isolado em `pages/`, com GPS do navegador, mapa OSM e consulta de rotas públicas; não contém dados privados.
- Servidor Python/Ollama/Database continuam exclusivamente no PC; acesso opcional via listener Companion HTTPS autenticado e CORS para origem Pages explicitamente configurada.
- Compatibilidade e limitações: consulta cartográfica pública sujeita a quota, rota de carro somente, GPS em primeiro plano, sem APK nem homologação em campo; tela e notas offline, sem roteamento offline.
- Implantação reversível: excluir publicação Pages / desabilitar `CAMPANARIO_FIELD_PAGES_ORIGIN`; sem migração de dados e sem alterações nos três repositórios externos.
- Testes da alteração e pendências descritos em `docs/operations/RESULTADOS_TESTES_R321.md`. Não declarar homologado o acesso real a PC ou geolocalização do usuário.
