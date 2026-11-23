# FAILSAFE operacional — cérebros CAMPANÁRIO V9 + expressão V9.1

**Tipo:** runbook de prevenção, contenção e recuperação. **Estado:** procedimento documentado, não homologado em produção. **Revisão:** 19/11/2026.  
**Relação:** `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md`, `docs/current/ROADMAP.md`, migração `0010_v9_brains.py`.

## 1. Contrato de segurança antes de ativar V9

- **Não tocar em dados reais sem backup validado.** A cópia de trabalho disponível é somente `CAMPANARIO-IA`; `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE` não foram auditados aqui.
- `CAMPANARIO_BRAINS_V9_ENABLED=false` é o **desligamento lógico** da camada de cérebros (com reinício do processo). Não restaura alterações no código, não desfaz uma operação externa e não substitui o backup.
- Não desligar os guardrails V9.1 para recuperar velocidade ou fazer um cérebro passar nos testes.
- R1 incremental: Conhecimento/Análise usam subprocesso descartável que o pai encerra no timeout ou RSS excedido. **Isso não é sandbox de segurança**: processo usa os privilégios do usuário, não tem bloqueio OS de rede/arquivo; adapters personalizados ainda podem usar thread, e um executável congelado sem Python sidecar falha fechado.
- A Central e a Forja só devem mostrar estados do backend; o registro de um cérebro no catálogo **não** é prova de implementação/saúde.
- Talentos e arquétipos não podem autorizar ferramentas, elevar privilégios, modificar evidências, suprimir incerteza ou alterar números/datas/condições.
- Qualquer texto extraído de PDF, ZIP `.campagent`, web ou retorno de ferramentas é **dado não confiável** (inclusive quando parece um prompt de sistema).

## 2. Matriz de contenção (acionar primeiro)

| Sinal observável | Falha possível | Comportamento seguro e resposta | Correção futura / gate |
|---|---|---|---|
| Cérebro indisponível/health-check falhou | Dependência, índice ou executor ausente | Retornar `unavailable`/limitação; não prometer consulta; não inventar evidência | R0/R3/R5–R8 |
| Consulta não encontra o livro/trecho | Arquivo ausente, OCR fraco, índice inconsistente | `not_found`/`partial` com fonte real quando houver; nunca hardcode de Ordem Paranormal | R3 |
| Referência de página/citação não corresponde ao `BrainRun` | Fonte alucinada ou metadado inconsistente | Rejeitar referência; usar fonte extrativa verificável ou declarar limitação | R3 + V9.1 |
| Resultado numérico alterado pelo LLM | Reformulação incorreta | Rejeitar expressão, tentar reformulação limitada, cair no canônico e registrar validação | R4/R8 |
| Contradições ocultadas | Fusão indevida entre documentos | Preservar as duas fontes e status `conflicting`; não escolher por estilo | R3/R5 |
| Executor excede timeout | Worker bloqueado, processo filho ou adapter não isolado | Conhecimento/Análise: matar árvore do subprocesso e registrar `timeout_terminated`; outros adapters ainda podem ter thread viva; não repetir ação não idempotente | R1 sandbox OS |
| Ação escrita/rede sem autorização | Divergência entre API local e Permission Layer | Negar por padrão; suspender capacidade e preservar `trace_id`; **não** orientar uso de endpoint alternativo | R1 |
| Registro de execução falha | SQLite bloqueado/indisponível | Não alegar auditoria persistida; não mostrar sucesso de ferramenta sem resultado verdadeiro; preservar o erro sem dados privados | R0/R1/R10 |
| Migração 0010 incompatível | Schema de banco real divergente | Não aplicar migração destrutiva; desativar flag e validar em cópia antes de restaurar banco | R0/R10 |
| `.campagent` suspeito | Zip bomb, symlink, script, traversal | Rejeitar, não importar automaticamente e não executar recursos | R9 |
| Cliente perde eventos ou voz falha | Journal local expirou/desconexão | Reconciliar por conversa persistida; nunca emitir texto não validado como concluído; conferir estado de call | R10 + F5 |
| Fichas causam drift de persona | Mudança indevida de perfil/core | Reverter build, preservar `AgentProfile` e memórias; a flag desativa os novos efeitos | R9 |

**Regra universal de falha:** segurança/permissões > integridade factual > pedido do usuário > necessidade da tarefa > talento > estilo. Um erro de ferramenta nunca se converte em sucesso textual do agente.

## 3. Passos operacionais seguros de recuperação

1. **Registrar o incidente**: data/hora, versão IA, `request_id`, `trace_id` (quando existente), `brain_id`, status, erro tipado e latência; **não copiar** mensagens privadas, `.env`, memória ou conteúdo bruto de documentos para tickets.
2. **Conter a função V9:** editar `.env` local, usar `CAMPANARIO_BRAINS_V9_ENABLED=false`, reiniciar o Campanário pelo launcher existente; verificar que o fluxo legada V9.1 responde sem novos cérebros. Isso não apaga builds/brain_runs.
3. **Revisar efeitos pendentes antes de reiniciar:** R1 encerra subprocessos de leitura, mas filhos órfãos/ações externas e adaptadores não isolados precisam inspeção; não relançar operações não idempotentes nem presumir que abortar a espera desfez efeitos.
4. **Preservar dados:** backup externo das três pastas necessárias, incluindo SQLite do Database, arquivos originais, configurações locais e voz. Não colocar credenciais ou memórias em artefatos compartilháveis.
5. **Diagnosticar em cópia:** comparar versão e hashes do código, estado da migração, logs sanitizados e resultados de testes. Nunca experimentar `downgrade` direto no banco de usuário.
6. **Retomar gradualmente:** habilitar V9 somente após teste de Conversação com flag desligada, Conhecimento sem fonte, consulta com evidência real, CSV/XLSX conhecido, Forja/Build e permissão negada. Se falhar, manter `false`.
7. **Rollback de código:** restaurar o backup do código anterior à atualização e confirmar compatibilidade de schema e flags com a versão restaurada. Reverter o pacote não reverte a migração nem os dados.
8. **Rollback de dados:** apenas depois de validação em cópia e com restauração explicitamente autorizada. Downgrade Alembic `0010→0009` **remove tabelas V9** (`agent_builds`, definições e execuções); não é um botão inocente de fail-safe.

### Exemplo de desativação lógica (Windows)

No arquivo `.env` de `C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA`, configure:

```dotenv
CAMPANARIO_BRAINS_V9_ENABLED=false
```

**Reinicie o Campanário** usando o launcher que você já utiliza; não é preciso mover ou deletar `CAMPANARIO-DATABASE`. Desativar a flag não valida o estado do SQLite e não interrompe trabalho de thread que já esteja em andamento — por isso execute os passos anteriores se houver operação ativa.

## 4. Gates obrigatórios de proteção (não implementados só por documentação)

| Gate | Teste objetivo obrigatório | Estado conhecido |
|---|---|---|
| S1 — Permissões | Leitura, escrita, rede e ação externa seguem a mesma política em `runtime/capabilities.py`, `utilities/api.py` e brains | Parcial: brain usa PermissionPolicy para `library:read`; utilidades ainda distintas |
| S2 — Timeout real | Worker travado, OOM e cancelamento não continuam após prazo; nenhum efeito externo indevido | Parcial: subprocesso read-only encerrado por timeout/RSS (testes), sem quota OS inviolável nem execução Windows comprovada |
| S3 — Evidência | Citation/page/section válida só após resultado de ferramenta com `evidence_refs`; falha honesta | Parcial: base V8/V9.1 testa casos, faltam bases reais complexas |
| S4 — Expressão factual | Números, unidades, condições, negações, contradições e referências preservados; fallback | Parcial: validador conservador V9.1 |
| S5 — Injeção/pacotes | Rejeitar prompt injection como instrução, symlink, executáveis, zip bomb, traversal | Parcial: inspeção `.campagent`, hardening completo pendente |
| S6 — Memória/identidade | Troca de build/flag não apaga experiência, memórias, perfil ou histórico | Testes temporários passaram; banco real não homologado |
| S7 — Migrações/reinstalação | Backup/restore de banco em cópia, upgrade/downgrade planejados, 3 pastas consistentes | Migração 0010 testada em SQLite temporário; PC real pendente |
| S8 — Modelo/multi-client | Ollama local e conexão móvel/voz em hardware real sem duplicar sessões ou modelos | Pendente no ambiente alvo |
| S9 — Regressão | Reexecutar suíte e comparar falhas pelo ID; zero regressões novas e pendências históricas triadas | Última evidência R2: 1.029 PASS / 31 FAIL históricos em grupos disjuntos (Linux/Python 3.13), nenhuma falha nova; Windows não homologado |

**Gate de release:** todos S1–S9 com evidência reproduzível, mais o aceite F5/F6/F7 do `ROADMAP.md` canônico. `READY` é resultado medido do executor, não configuração do catálogo.

## 5. Testes mínimos sugeridos antes de reativar

Executar no Python do ambiente do projeto (alvo declarado >=3.12,<3.13) e em uma **base de teste**, não no Database pessoal:

```powershell
$projeto = 'C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA'
$python = 'C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-PYTHON\.venv\Scripts\python.exe'
Set-Location $projeto
& $python -m pytest -q tests/test_v9_brains.py tests/test_v91_expression.py tests/test_v8_knowledge.py
& $python -m pytest -q
```

Esses comandos são **procedimento recomendado**, não evidência de que foram executados no Windows. A regressão R2 de referência foi executada em grupos disjuntos no Linux/Python 3.13 com 1.029 aprovados e 31 falhas preexistentes; as falhas precisam ser investigadas, não escondidas.

## 6. O que este documento NÃO faz

Este arquivo não altera o código, não instala sandbox, não reverte migrações, não atualiza dependências, não realiza benchmark em Windows/mobile, não habilita cérebros futuros e não recupera dados sem backup. É uma orientação verificável para execução segura das fases do roadmap.


## 7. P0 — três pastas, `.venv`, SQLite e atualização sem PowerShell (checkpoint 19/11/2026)

O mecanismo de P0 adicionou **somente** diagnóstico e barreiras no executor. Ele NÃO conclui sandbox/migração/backup/restore. Ver [`docs/current/P0_TRES_PASTAS_SEM_POWERSHELL.md`](../current/P0_TRES_PASTAS_SEM_POWERSHELL.md) e [`docs/operations/P0_RELATORIO_EXECUCAO.md`](P0_RELATORIO_EXECUCAO.md).

**Mapeamento real dos caminhos:**

- **`CAMPANARIO-IA`**: código Python, Web, agentes, cérebros, scripts e docs. `.env` é configuração PRIVADA local (não distribuída). O launcher `CAMPANARIO.vbs` prefere `Campanario.exe`, senão a venv externa, senão a antiga `.venv` no IA. ZIPs de código não contêm `.env` nem `.venv`.
- **`CAMPANARIO-PYTHON/.venv/Scripts/python.exe` e `pythonw.exe`**: ambiente compartilhado Python 3.12 com dependências/voz; não recriar ou sobrescrever ao atualizar código. Se faltar, usar `PREPARAR_PYTHON_UNIFICADO.ps1` **somente para instalação/reparo** e verificar inventário de voz/CUDA. Se o EXE empacotado tiver prioridade, revisar sua versão antes de atribuir sucesso à venv.
- **`CAMPANARIO-DATABASE/dados/{desenvolvimento|producao}/campanario.db`**: memórias, sessões, fichas e execuções SQLAlchemy/SQLite; originais importados também dependem de `data_dir`. `CAMPANARIO_DATA_DIR` define a raiz `dados`, `CAMPANARIO_MEMORY_ENVIRONMENT` separa os bancos; caminhos mal configurados podem fazer o aplicativo abrir um banco diferente, sem excluir o antigo. `CAMPANARIO-DATABASE/zim` abriga acervo opcional, referenciado por `CAMPANARIO_ZIM_DIR`.
- **Ollama**: instalado e com modelos em local administrado externamente; não distribuído, não testado pelo diagnóstico de pastas.

**Rotina de atualização sem console:** parar o aplicativo, copiar a pasta IA e o Database para backup privado, extrair `CAMPANARIO_P0_ARQUIVOS_PARA_COPIAR.zip` fora do projeto, copiar seu conteúdo relativo sobre IA pelo Explorador, substituindo apenas os homônimos. **Não apagar a pasta IA**, nem copiar a atualização sobre Database/Python. Se há código personalizado, comparar antes de substituir; este modo manual não executa hash-check/rollback automático. Reabrir `CAMPANARIO.vbs`, consultar a Central de Cérebros e seus erros; somente instalação de dependências, verificação avançada ou migração requerem comandos.

**Diagnóstico R0 (`GET /api/v1/brains/environment`, somente loopback):** observa pastas existentes, Python ativo, diretório de dados, configuração ZIM e lê até 16 bytes do cabeçalho SQLite. **Nunca** faz backup, `PRAGMA integrity_check`, migração, restauração, reparo, escrita ou execução de conteúdo de documentos. Estados `paths_ok`/`partial`/`blocked` descrevem apenas esses sinais; até `paths_ok` mantém `host_homologated=false`. Se `blocked`, mantenha a V9 desligada até entender o erro.

**Controle R1 incremental:** o executor agora recusa `permission_scopes` insuficientes e `BrainResult` com `brain_id`/`trace_id` incompatíveis antes de publicar evidências. Essa checagem não é a política global `PermissionPolicy`, não controla APIs externas e não mata uma thread que ultrapassa timeout. **Não habilitar o cérebro Programação nem execuções arbitrárias** sem sandbox/kill processual e permissão centralizados.

**Restauração:** (1) desligar o app; (2) voltar apenas os arquivos IA de backup; (3) manter as duas pastas externas intocadas; (4) verificar `.env` e ambiente ativo; (5) restaurar Database somente de backup testado, em operação separada e autorizada. **Nunca executar downgrade `0010→0009` automaticamente**, pois remove dados V9. A flag `false` não desfaz efeitos nem substitui restauração.

**Gates ainda pendentes para P0 completo:** acesso real aos outros repositórios, Python 3.12 no Windows, integridade e restore de cópia do banco, compatibilidade de migration `0010`, política unificada, sandbox com timeout fatal, testes Ollama/voz/mobile e comparação das falhas históricas.


### P0 — exceção importante: SQLite de referência V2 ainda no IA

A auditoria encontrou `CAMPANARIO-IA/data/interaction_library_v2.sqlite`, usado como referência comportamental **somente leitura**, distinto do SQLite de memórias em `CAMPANARIO-DATABASE/dados/<ambiente>/campanario.db`. O código P0 agora prefere uma cópia existente em `CAMPANARIO-DATABASE/dados/reference/interaction_library_v2.sqlite`, preservando fallback no IA se a cópia não existir. **Não apagamos nem migramos automaticamente** o SQLite antigo. Para concluir a separação, com aplicativo fechado e backup, copiar por Explorador para `Database/dados/reference/` e testar antes de considerar remover o legado. O diagnóstico local indica se a cópia externa foi reconhecida. Nunca tratar referência V2 como memória pessoal; nem afirmar que 100% dos SQLite foram externalizados antes desse procedimento.


## 8. Failsafe R1 — processos, políticas e três pastas (19/11/2026)

**O que efetivamente roda:** somente os cérebros instalados `knowledge` e `analysis` são executados como processos Python isolados do chat por `brains/isolation.py` → `brains/worker.py`. O executor recebe dados JSON compactos, nunca código, shell ou objetos pickle. Em `timeout_terminated` e `memory_limit_terminated` o worker é morto; não confundir monitoramento RSS por amostragem com limite rígido do kernel. Em Linux há `RLIMIT_CPU` no worker; no Windows **não há Job Object** nesta etapa. O trabalhador mantém os privilégios do processo pai e não tem política de rede; **não executar código não confiável, nem ativar Programação**.

**Se falhar em Windows:** abrir a Central de Cérebros, conferir se a aplicação está usando `CAMPANARIO-PYTHON/.venv/Scripts/python.exe` ou `pythonw.exe`. `Campanario.exe` tem precedência no launcher; se for um EXE congelado sem Python sidecar, o worker devolve `worker_python_unavailable`, e a resposta documental deve indicar limitação. Para testar a versão nova, use o launcher com a venv externa **somente se houver Python 3.12/dependências corretamente instalados**; não renomeie/apague o EXE sem backup e plano. Não instalar novos pacotes só para atualizar arquivos; `psutil` já é dependência declarada.

**Permissão central:** `composition.py` vincula a mesma `PermissionPolicy` utilizada por `runtime/capabilities.py`; `ChatService` e a prévia local criam contexto de usuário de sessão no backend; `BrainExecutor` nega contexto ausente, escopo `library:read` ausente ou política negada. O acesso HTTP local não autentica identidade de usuário, e `utilities/api.py` ainda usa seu sistema anterior de confirmação; **S1 não está encerrado**.

**Respostas sem evidência:** um erro `worker_failed`, `timeout_terminated`, `memory_limit_terminated`, `worker_python_unavailable` ou `permission_denied` não é consulta concluída. Não atribuir a documentos números ou páginas se não há `evidence_refs` de uma execução válida. Evitar repetição automática de operações com possível efeito.

**Arquivos/dados:** o ZIP R1 altera apenas `CAMPANARIO-IA` e mantém intactos `.env`, `CAMPANARIO-PYTHON/.venv`, `CAMPANARIO-DATABASE/dados/{desenvolvimento|producao}/campanario.db`, `zim` e acervo pessoal. A biblioteca V2 de referência pode continuar em fallback no IA: seguir o procedimento P0 para cópia sem apagar origem. Sem alterações de schema ou migrações nesta fase.

**Atualizar/restaurar SEM PowerShell:** fechar aplicativo e servidores, guardar backup privado de IA+Database, extrair `CAMPANARIO_R1_ARQUIVOS_PARA_COPIAR.zip` fora do projeto, copiar pastas/arquivos **dentro de** `CAMPANARIO-IA` pelo Explorador com substituição apenas de homônimos (comparar arquivos próprios). Nunca apagar a pasta IA ou substituir Database/venv. Se falhar, desativar flag e reverter os arquivos IA do backup após fechar o app. Comandos só quando uma dependência, migração ou diagnóstico opcional de manutenção exigir; o overlay de código não exige terminal.


## 9. R1.1 — orçamento, circuito de falhas e higiene do worker (19/11/2026)

**Escopo real:** `BrainExecutor.execute()` aplica um limite de tempo **único para o plano completo**, além do máximo estrutural de três cérebros; retorna `turn_budget_exhausted` sem iniciar o próximo worker se restar menos de 100 ms. A política `library:read` e o escopo do pedido permanecem obrigatórios quando fornecidos pela composição. Três falhas técnicas do mesmo cérebro em 30 segundos abrem circuito local por 20 segundos: `circuit_open` significa indisponibilidade temporária, **nunca fonte consultada**. Erro de autorização, documento ausente ou fonte contraditória NÃO abrem o circuito. O circuit breaker não é compartilhado entre processos e perde histórico no restart.

**Cancelamento e monitoramento:** o worker Python de leitura é encerrado após timeout, memória acima do limite observado e cancelamento explícito de tarefa. O `psutil` é requisito declarado do projeto; sem ele, o processo falha fechado. RSS é observado por amostragem e pode perder picos. No Windows, o kill do filho depende das APIs e do `psutil`; **Job Object/AppContainer ainda NÃO está implementado ou testado**, e processos arbitrários não devem usar esse caminho.

**Segredos e rede:** R1.1 restringe as variáveis de ambiente transmitidas ao worker, evitando tokens, proxies e `PYTHONPATH` não controlado do chat. `network_guard.py` intercepta sockets Python apenas enquanto o adaptador executa; **é proteção em nível de aplicação, não isolamento de rede pelo SO**. Bibliotecas nativas/código hostil podem contornar essa defesa. Por isso só `knowledge` e `analysis` recebem entradas JSON estruturadas de leitura; **Programação e ações externas NÃO liberadas**.

**Se aparecer `circuit_open`, `turn_budget_exhausted`, `process_monitor_unavailable`, `timeout_terminated` ou `memory_limit_terminated`:** consulte registro local de execuções, disponibilidade de Python/psutil e pastas reais na Central de Cérebros; não repetir cegamente nem atribuir páginas/documentos inexistentes. Reduzir carga/documentos, reiniciar o runtime se necessário e manter V9 desativada até isolar a causa. `worker_network_disabled` indica tentativa de rede dentro do worker de leitura; investigar dependência antes de habilitar novamente. Não remover a proteção para fazer passar uma consulta.

**Topologia e restauração:** IA (`CAMPANARIO-IA`) só contém código/interface e `.env` privado; Python (`CAMPANARIO-PYTHON/.venv`) fornece runtime; Database (`CAMPANARIO-DATABASE/dados/{desenvolvimento|producao}/campanario.db`) contém dados pessoais, com SQLite V2 de referência externo opcional em `dados/reference` e ZIM em `zim`. `CAMPANARIO_DATA_DIR`, `CAMPANARIO_MEMORY_ENVIRONMENT` e `CAMPANARIO_ZIM_DIR` determinam os caminhos; NÃO trocar ambientes involuntariamente. Para atualizar código, feche o aplicativo, faça backup privado de IA e Database, extraia **`CAMPANARIO_R11_ARQUIVOS_PARA_COPIAR.zip`** fora da raiz e copie seu conteúdo relativo para **dentro** do IA pelo Explorador, comparando personalizações. **Não usar PowerShell para substituir arquivos; não apagar pasta IA; não sobrescrever `.env`, `.venv`, Database ou modelos.** Se falhar, desligue V9, reinicie, restaure apenas o código IA do backup e trate recuperação de SQLite em procedimento separado com cópia validada.

**Gate ainda aberto:** `utilities/api.py` mantém confirmação própria; políticas de ferramentas, isolação rígida de rede/arquivos, quotas imutáveis do kernel, Python 3.12/Windows, EXE congelado, testes com Ollama real e backup/restore não foram homologados. A fase R2 só deve usar capacidades autorizadas e com evidências. Consulte [`R11_PROTECOES_EXECUTOR_CEREBROS.md`](../current/R11_PROTECOES_EXECUTOR_CEREBROS.md) e [`RESULTADOS_TESTES_R11.md`](RESULTADOS_TESTES_R11.md).


## 10. R2 — planos compostos de leitura, falha parcial e volta segura (19/11/2026)

**Implementado somente no IA:** `BrainStep`/`BrainPlan` validam limite de três etapas, dependência anterior e escopos. O roteamento misto `knowledge → analysis` só é selecionado para pedido explícito a documento **e** planilha. Ambas as operações mantêm subprocessos separados, orçamento único, permissão `library:read`, trace e seus respectivos erros. `upstream_evidence_ids` contém **somente identificadores da consulta anterior concluída**, nunca instruções, texto de documento como prompt privilegiado ou concessão de acesso.

**Nunca confundir as etapas:** o resultado da planilha é calculado pelo seu adaptador a partir de dados importados, **não** usando semanticamente o documento recuperado. `collaboration.semantic_comparison_performed=false` comunica o limite. A resposta neutra apresenta documento e planilha separadamente, com limitações. Uma única fonte encontrada não autoriza dizer que a outra foi consultada com sucesso. Ausência, erro de autorização, timeout, `worker_failed` ou evidência inconsistente são falhas honestas, não sucesso textual. A alteração do `DocumentRequest` permite instruções imperativas e delimita nomes de documentos antes de `com a planilha`, sem elevar mensagens do agente a referência de usuário.

**Se a resposta misturar números/fontes, faltar etapa ou travar:** confira na Central o plano, cada `brain_run`, `trace_id`, `status`, `operations`, `upstream_evidence_ids` e `evidence_refs`, sem copiar conteúdo confidencial para tickets. Desative `CAMPANARIO_BRAINS_V9_ENABLED=false` no `.env`, feche/reinicie o app e teste modo legado. Para rollback de código, com app parado restaure os arquivos IA anteriores do backup; **não** rebaixe Alembic 0010 nem restaure Database sem validação prévia em cópia. O registro de execuções pode persistir; a flag não elimina dados ou trabalho já realizado.

**Três pastas:** `CAMPANARIO-IA` contém código/UI/`.env`; `CAMPANARIO-PYTHON\.venv` fornece Python 3.12 e dependências do launcher; `CAMPANARIO-DATABASE\dados\{desenvolvimento|producao}\campanario.db` e documentos/ZIM ficam externos (`CAMPANARIO_DATA_DIR`, `CAMPANARIO_MEMORY_ENVIRONMENT`, `CAMPANARIO_ZIM_DIR`). O SQLite de referência V2 pode existir no IA como fallback P0 até ser copiado com backup para `Database\dados\reference`. **R2 não altera bancos, modelos, `.venv` ou caminhos locais.**

**Atualização sem PowerShell:** feche app; backup de IA+Database; extraia `CAMPANARIO_R2_ARQUIVOS_PARA_COPIAR.zip` em Downloads, copie o **conteúdo relativo** sobre IA pelo Explorador, mesclando arquivos de código sem apagar a pasta e sem sobrescrever `.env`. A cópia manual não executa checagem automática de hash/rollback: use o manifesto, compare personalizações e retenha backups. Se `Campanario.exe` congelado ainda tiver prioridade, o launcher poderá executar versão anterior. Terminal apenas para instalar dependências, rodar diagnósticos/migrações autorizadas ou testes quando necessário.

**Gates abertos:** isolamento de rede/arquivos por SO, política comum das utilidades, homologação Windows+Python 3.12+Ollama, comparação semântica, cache de fontes, consentimento e isolamento entre sessões. A fase R2 é parcial, não liberação de Programação nem execução externa. `docs/current/R2_PLANEJAMENTO_COLABORACAO_CEREBROS.md` e `docs/operations/RESULTADOS_TESTES_R2.md` explicam testes/limites.

## 11. R2.1 — dependências obrigatórias, fontes validadas e identidade explícita

**Detectar:** `dependency_not_met` significa que a etapa seguinte exigia ao menos uma evidência real de **cada** dependência, mas uma não foi concluída; o worker dependente NÃO foi iniciado. `plan_request_mismatch` significa que `trace_id` ou `intent` do plano composto divergiu da requisição — nenhuma etapa foi executada. `invalid_brain_result` bloqueia operações/IDs/trechos inconsistentes com o resultado registrado. **Nenhum desses status comprova leitura da fonte.** Não promover dados de extensão in-process a evidência documental sem adaptador first-party revisado.

**Compatibilidade intencional:** planos de leitura documento + planilha continuam com dependência `optional`: documento ausente não cancela o cálculo independente. A resposta deve sinalizar a fonte que faltou e não concluir comparação semântica. `required` só deve ser usado quando o passo realmente depender de evidência anterior, nunca para restringir capacidades por arquétipo.

**Permissões:** com `CAMPANARIO_BRAINS_V9_ENABLED=true`, a instância de `CapabilityRegistry` composta pelo runtime exige `AuthorizationContext` explícito para ferramentas registradas com permissões; nenhuma ausência de contexto vira `internal_system`. Ao receber `PermissionDeniedError` ou `PermissionConfirmationRequired`, não tentar via outro canal nem chamar o provider; registrar o motivo sem token. Com flag desligada, compatibilidade com o registro legado é preservada.

**LACUNA CRÍTICA AINDA ABERTA:** `/api/v1/utilities/invoke`, uploads e prévia original do documento utilizam a API HTTP local e seu gate anterior, e **não** passam obrigatoriamente pelo registro de capacidades. A proteção R2.1 não unificou consentimento, autenticação de clientes pareados e confirmação central nesses endpoints. Restringir exposição à máquina local e **não liberar** Programação, rede ou ações irreversíveis até homologação R1. Não tratar `confirm:true` dentro de argumentos do modelo como aprovação de usuário.

**Recuperação:** desative a flag V9 no `.env` e reinicie, se precisar voltar ao fluxo antigo. Faça backup de IA e Database; com a aplicação parada, reponha **somente os arquivos IA** anteriores caso um contrato adicional cause regressão. Não aplicar downgrade Alembic nem restaurar o Database sem validação em cópia. Se falhas envolverem `trace_id`, envie apenas IDs/status e não os textos dos documentos/credenciais. Testes e limitações estão em `docs/operations/RESULTADOS_TESTES_R21.md`.

**Pastas e venv sem misturar dados:** `CAMPANARIO-IA` = código/UI/.env privado; `CAMPANARIO-PYTHON\.venv\Scripts\python.exe` = runtime Python 3.12 do usuário; `CAMPANARIO-DATABASE\dados\{desenvolvimento|producao}` = SQLite pessoais e originais, ZIM conforme `CAMPANARIO_ZIM_DIR`; fallback do SQLite de referência V2 ainda pode existir em IA. Configurar `CAMPANARIO_DATA_DIR` e `CAMPANARIO_MEMORY_ENVIRONMENT` sem trocar bases involuntariamente. Para instalar código R2.1, extrair o ZIP em Downloads e copiar arquivos relativos pelo Explorador (após backup), **sem PowerShell**. NÃO substituir a pasta IA inteira, `.env`, `.venv`, bancos, modelos ou ZIM. Executável `Campanario.exe` congelado pode continuar na versão anterior: validar host real.

## 8. R2.2 — Contenção de utilidades HTTP via PermissionPolicy (23/11/2026)

**Implementado e testado em Linux, não homologado Windows:** no modo experimental `CAMPANARIO_BRAINS_V9_ENABLED=true`, `POST /api/v1/utilities/invoke` passa por `PermissionPolicy.check` antes de chamar `UtilityService.run`. A API cria uma identidade local limitada (`local_browser/loopback-utilities`) **sem** usar o principal interno. Leitura precisa de `ALLOW`; escrita precisa de `ALLOW` e continua sujeita à confirmação legada em `UtilityService`. `confirm=true` no JSON NÃO aprova `PermissionPolicy`. Também há barreira para upload binário/Base64 e download de originais. Falha da política/runtime dá 503, negação/confirmação pendente dá 403. As checagens não criam arquivos nem executam operações antes da decisão.

**Limitação intencional:** `utilities.write` usa `CONFIRM` no runtime, mas a UI de utilidades ainda não dispõe de um fluxo confiável para aprovar/consumir tokens PF6. Portanto, escrita e uploads no modo V9 ficam normalmente indisponíveis. Não burlar a barreira trocando de cliente, alterando regras, injetando `confirmation_token` no payload ou usando um principal `system`. Rotas não cobertas e execução direta de `UtilityService` ainda necessitam R1; isolamento OS, rede e filhos de subprocessos seguem pendentes. `Origin`/loopback não equivale a autenticação humana.

**Recuperação segura:** pare o app, preserve código e dados privados, ajuste apenas `CAMPANARIO_BRAINS_V9_ENABLED=false` no `.env` **local**, reinicie pelo launcher existente e confirme o comportamento legado. A flag desliga a ponte experimental, mas também relaxa esta proteção HTTP: utilizar apenas em ambiente local confiável, sem publicar a API na rede. Se houver incidente, preservar auditoria e backup do Database sem experimentar migração/downgrade em produção. Para voltar o código, restaurar cópia dos arquivos IA anteriores via Explorador. Não modificar `CAMPANARIO-PYTHON/.venv` nem `CAMPANARIO-DATABASE` para instalar este patch.

**Gates:** S1 permanece parcial (somente alguns endpoints protegidos); S2–S9 e F5/F6/F7 não ganham aceite com esta alteração. O relatório executado está em `docs/operations/RESULTADOS_TESTES_R22.md`. Próximo trabalho: principal autenticado, aprovação PF6 escopada e unitária, outras superfícies de ferramentas e fault injection Windows.

## Checkpoint R2.3 — Proteção PF6 temporária e anti-replay (23/11/2026)

**Mudança restrita:** as confirmações pendentes de `PermissionPolicy` duram no máximo cinco minutos e só podem ser aprovadas uma vez. O token aprovado (armazenado apenas como hash) só autoriza uma checagem com o MESMO principal, dispositivo, sessão, permissão, capacidade e escopo; acesso concorrente é serializado. As solicitações pendentes são limitadas e novas solicitações falham fechadas quando o limite é atingido. Após reiniciar, confirmações em memória deixam de existir; refazer consentimento no fluxo autorizado. A auditoria não inclui o token bruto.

**Não criar endpoint de autoaprovação:** `PermissionPolicy.approve` permanece método interno; não comprova consentimento humano. A UI não tem autenticação humana apropriada e portanto não foi desbloqueada. `confirm=true`, Origin, loopback e credencial enviada pelo próprio navegador não são prova suficiente. O endpoint de utilidades, em V9, conserva negação de escrita/upload enquanto não houver decisão central `ALLOW` legítima. Nunca usar o principal interno `system` para contornar bloqueio.

**Recovery/rollback:** parar a aplicação; salvar backup privado independente de `CAMPANARIO-IA`, `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE` antes de mesclar arquivos IA. Se PF6 rejeitar contexto anteriormente aceito, renovar uma confirmação **por mecanismo de autenticação real**, não repetir tokens ou desativar regras arbitrariamente. Em caso de incidente, restaurar apenas arquivos IA do backup pelo Explorador, sem downgrades de SQLite, sem mover a `.venv` compartilhada externa, sem copiar dados persistentes para IA. Desativar V9 é fallback de operação legado somente em ambiente local confiável; reduz proteção e não autentica o cliente. Logs de autorização devem ser preservados sem credenciais. Em Windows/EXE antigo o patch Python pode exigir build do executável, não alteração de diretórios de dados.

**Gates ainda abertos:** autorização humana de UI, revogação/token lifecycle distribuído, isolamento OS/Job Objects e rede, E2E Windows Python 3.12/Ollama, backup/restore dos três repositórios, testes físicos F5/mobile. R1 e R10 permanecem parciais/não homologados. Ver `RESULTADOS_TESTES_R23.md`.


## Checkpoint R2.4 — Confirmação PF6 local com segredo opt-in (23/11/2026)

**Padrão seguro:** R2.4 NÃO fornece credencial, NÃO ativa V9 e NÃO concede escrita por padrão. Apenas quando o operador configura no `.env` privado `CAMPANARIO_BRAINS_V9_ENABLED=true` e `CAMPANARIO_PF6_OWNER_TOKEN` aleatório, forte (32–256 caracteres), o frontend de ferramentas pode solicitar revisão exata de operação e aprovação autenticada por segredo local. Não colocar senha no ZIP, na URL, em scripts, screenshots nem em logs. O front solicita senha sem salvá-la, mas `prompt` não é autenticação humana forte e a página deve permanecer em contexto local confiável.

**Negação e escopo:** `/confirmations/request` NÃO aprova, apenas gera solicitação vinculada aos argumentos exatos e capability. `/confirmations/approve` exige bearer separado, reconhece o consentimento, confere a operação e escopo sob lock. `/invoke` recebe token como campo independente e exige `SCOPED_CONFIRM`; sem token, token reutilizado, modificação de argumentos, segredo incorreto, expiração, política indisponível, erro de runtime => negar. Tentativas não devem alterar dados. O `confirm:true` legado não equivale a consentimento PF6. Uploads e download de informações dependem da política já existente; uploads em V9 permanecem bloqueados neste incremento. Nunca usar `system` ou liberar acesso externo para contornar.

**Riscos remanescentes:** segredo estático de máquina não prova identidade individual; sem rate limiting dedicado no endpoint de aprovação, sem revogação individual/sessões, sem garantia antimalware/XSS e sem sandbox do SO. A confirmação pela própria interface não deve ser tratada como modelo de segurança de servidor remoto. Limitar a uso offline em host confiável, não publicar em rede. Expiração e anti-replay R2.3 continuam em memória; reiniciar cancela pendências. O comportamento legado com V9 desabilitada continua com proteção menor, não usar como fallback para executar ação arriscada.

**Rollback por Explorador:** fechar o Campanário, guardar backups independentes de `CAMPANARIO-IA`, `CAMPANARIO-PYTHON`, `CAMPANARIO-DATABASE`; substituir apenas arquivos IA do backup R2.3, sem tocar `.venv` externa ou SQLite/memórias/documentos. Retirar credencial do `.env` privado caso queira desabilitar o mecanismo PF6; nunca distribuir esse arquivo. O executável Windows congelado pode requerer rebuild. Sem migrations. Ver `RESULTADOS_TESTES_R24.md`. Gates R1, R10 e F5/F6/F7 continuam abertos; **não** liberar cérebros perigosos ou ferramentas invasivas.


## Checkpoint R2.5 — Sessão PF6 do proprietário (23/11/2026)

**Default deny permanece:** sem V9 opt-in e segredo forte `CAMPANARIO_PF6_OWNER_TOKEN` no `.env` PRIVADO, o login PF6 é indisponível; não criar credenciais padrão. O segredo compartilhado **não** identifica uma pessoa individual. Qualquer origem diferente do host ou cliente não loopback é rejeitado pelo adaptador, mas isso não oferece autenticação remota nem resistência total a processos locais maliciosos.

**Sessões temporárias:** login recebe credencial por POST JSON e fornece bearer aleatório para a aba, em memória, com expiração de 15 minutos, máximo 32 sessões. O servidor armazena hash SHA-256 do token, e bloqueia por 60 s após cinco falhas por IP local, em memória e apenas no processo. Logout revoga imediatamente; reiniciar perde sessões; trocar segredo invalida sessões; não gravar tokens em logs, URL, disco, screenshots ou armazenamento do navegador. UI mantém `prompt` anterior: não alegar proteção completa contra XSS/CSRF ou roubo de credenciais por extensão/navegador comprometido.

**Aprovação e execução:** request, approve e invoke com confirmação PF6 exigem bearer de sessão válido; pedido PF6 registra `session_id` e execução precisa da mesma sessão. Consentimento explícito dos argumentos exatos, token de operação unitário, validade da confirmação R2.3 de cinco minutos continuam obrigatórios. Logout realizado **antes** de invoke bloqueia escrita, mesmo com token PF6 aprovado; credencial compartilhada antiga enviada diretamente a `/approve` deixa de ser aceita. Uploads em modo V9 continuam bloqueados. Não conferir privilégios a cérebros, talentos, arquétipos ou personalidades.

**Recuperação:** parar app, backup privado independente das três pastas antes de mesclar; limpar sessões fechando/reiniciando servidor, ou usar logout UI. Se houver incidente, rotacionar segredo no `.env` PRIVADO e reiniciar. Reverter apenas código `CAMPANARIO-IA` com backup R2.4 pelo Explorador; NÃO restaurar SQLite, memórias ou modelos durante rollback e NÃO copiar `.venv` ou dados para IA. Atualizações por ZIP podem não modificar `Campanario.exe` congelado; possível rebuild técnico. Não promover R1/F5/R10 sem Windows 3.12, testes de isolamento OS, repositórios externos e regressão integrada.

**Evidência:** `RESULTADOS_TESTES_R25.md`: 41 testes direcionados PASS, JS sintaxe PASS; suite ampla 530 PASS / 1 FAIL G2 preexistente, interrompida no primeiro FAIL. Próximo gate R2.6: UI robusta, identidade humana individual offline, segurança XSS/CSRF e isolamento/aceite no Windows.


## Checkpoint R2.6 — UI de aprovação PF6 e mitigação Web (23/11/2026)

**Negar por padrão permanece obrigatório.** Sem V9 habilitada e credencial forte local, o modo PF6 não é autorizado. Modal de credencial e revisão é uma barreira de interação, **não prova identidade pessoal**, nem sandbox. A janela usa `textContent` para ferramenta e argumentos, checkbox de aceite exato e cancelar sem aprovação; nunca persistir segredos e tokens em DOM, logs, Storage, URLs, ZIP ou banco. Modal fechado/ESC cancela. Não afirmar resistência total a XSS, extensões maliciosas, processos locais ou CSRF apenas pela CSP/Fetch Metadata; há páginas legadas que exigem auditoria. Não relaxar `script-src` com `unsafe-inline` ou `unsafe-eval` sem revisão e testes; `style-src` ainda permite estilos inline devido à interface existente.

**Proteção HTTP:** a API de utilidades mantém loopback e Origin exato (HTTP/HTTPS) e recusa `Sec-Fetch-Site` diferente de `same-origin`/`none`. `Origin` e Fetch Metadata são sinais de navegador, não prova criptográfica de usuário; clientes não navegador ainda exigem autorização central/sessão PF6 para escrita. A CSP opera apenas na página de Ferramentas, não em todo o app. O frontend não deve contornar erros de origem, nem liberar V9 por status do cliente (`pf6_mode` é informativo). Upload V9 continua negado.

**Recovery/rollback:** fechar Campanário; efetuar backup privado e independente das três pastas. Para voltar a R2.5, repor **somente** arquivos `CAMPANARIO-IA` do backup via Explorador; reiniciar cancela sessões PF6 em memória. Não alterar a `.venv` única externa em `CAMPANARIO-PYTHON`, nem SQLite/Biblioteca V2/memórias/documentos em `CAMPANARIO-DATABASE`; não restaurar banco para rollback de UI. Se suspeitar de vazamento, rotacionar `CAMPANARIO_PF6_OWNER_TOKEN` no `.env` PRIVADO e reiniciar. Para Windows EXE congelado, atualização de fonte pode exigir rebuild. Não incluir `.env` e bancos no pacote. Não há migração.

**Verificação e gates:** 22 testes direcionados PASS e `node --check` PASS no Linux; suite ampla 530 PASS/1 FAIL G2 histórico, interrompida no primeiro erro. Sem testes no Windows 3.12, mobile real, Ollama ou repositórios externos; R1, R10 e F5 ainda abertos. Identidade individual e OS sandbox seguem pendentes. Ver `RESULTADOS_TESTES_R26.md`.


## Checkpoint R2.7 — Identificação offline PF6 (23/11/2026)

**Falha fechada:** a configuração individual é opcional e deve existir apenas no `.env` PRIVADO (`CAMPANARIO_PF6_USERS_JSON` contendo mapa de username para verificador PBKDF2-SHA256 com salt). Nunca incluir senhas, verificadores reais, tokens, `.env`, SQLite, `.venv` ou dados pessoais nos ZIPs, código, logs ou screenshots. Não distribuir senhas padrão. Com mapa individual não vazio, rejeitar login legado de proprietário e **não** fazer fallback após erro de parsing, usuário inexistente, senha incorreta ou indisponibilidade. Usuário em login não é prova de identidade do SO; fornece apenas identificação local baseada em senha; ainda não existe RBAC/ACL individual de capacidades nem MFA. Login por processo em loopback e limitação por IP local não são proteção contra processos comprometidos ou autenticação remota.

**Permissão:** emitir `principal_id=pf6-user:<nome>` somente depois da validação de verificador, não confiar em nome fornecido em pedido de aprovação/invocação. Preservar escopo exato, `session_id`, TTL, uso único, confirmação humana e centralização em `PermissionPolicy`. Alterar configuração de usuários exige reiniciar servidor para garantir recarga do `.env` e invalida sessões em memória; logout encerra sessão na aba. Nunca elevar privilégios por talento/cérebro/arquétipo; uploads V9 continuam bloqueados. Não expandir acesso de leitura ou mudança de política simplesmente porque a conta foi autenticada. A UI Dark Matter mantém `textContent` para argumentos não confiáveis; CSP/Origin/Fetch Metadata R2.6 não devem ser relaxados. XSS/CSRF **não foram auditados globalmente**.

**Rollback/recuperação:** fechar o aplicativo, efetuar backup privado independente das três pastas, restaurar exclusivamente código de `CAMPANARIO-IA` da R2.6 pelo Explorador. Preservar `CAMPANARIO-PYTHON/.venv` externa única e `CAMPANARIO-DATABASE` com SQLite/Biblioteca V2/memórias/conversas/documentos; não copiar bancos para IA, não criar .venv, não executar migrations. Retirar configuração opcional ou rotacionar senhas após incidente; tokens não persistem entre reinícios. O EXE Windows congelado pode exigir rebuild. Gate R1, R10 e F5 permanecem abertos; nenhum executor novo deve ser liberado antes da homologação. Testes: 27 PASS direcionados, node sintaxe PASS; regressão 530 PASS/1 FAIL G2 histórico. Consulte `RESULTADOS_TESTES_R27.md`.


## Checkpoint R2.8 (23/11/2026) — segurança por ferramenta e disciplina documental obrigatória

**Fail-closed individual:** se `CAMPANARIO_PF6_USERS_JSON` contiver usuários, cada operador só pode pedir/aprovar/executar escritas explicitamente autorizadas em `CAMPANARIO_PF6_WRITE_ACL_JSON` PRIVADO, por exemplo `{"alice":["notes.save"],"bob":[]}`. Sem ACL ou nome de usuário, negar; lista malformada ou ferramenta desconhecida retorna indisponível (503) antes da execução. Um item na ACL **não** autoriza por si só: a `PermissionPolicy` exige confirmação PF6 vinculada aos argumentos, identidade, sessão, validade e uso único. ACL revogada bloqueia execução mesmo depois de token de consentimento emitido. Não conceder por perfil/arquétipo/cérebro/talento. Modo legado único preservado, sem promoção implícita para usuário nomeado. Leituras e status não estão cobertos por ACL individual e exigem auditoria R2.9.

**Mudança de configuração:** copiar/verificar ID da ferramenta em `utilities/service.py`, registrar mapeamento no `.env` **privado** e reiniciar servidor para garantir consistência; nunca distribuir password/verifier/ACL pessoal/log de auditoria. Para reverter, fechar app; restaurar só código do backup de `CAMPANARIO-IA` por cópia no Explorador; preservar `.env`, `CAMPANARIO-PYTHON/.venv` externa e `CAMPANARIO-DATABASE` com SQLite, memórias, Biblioteca V2, documentos e ZIM. Sem schema/migração/ambiente duplicado. Exe congelado pode exigir rebuild. Revogar sessão/rotacionar senhas diante de incidente.

**Obrigação de desenvolvimento e rollback documental:** em **toda** versão futura atualizar na mesma entrega os dois ROADMAPs, este FAILSAFE, `docs/governance/MANUAL_TECNICO_VIVO.md`, changelog, teste e LEIA_PRIMEIRO. `docs/governance/PROCESSO_OBRIGATORIO_DE_DESENVOLVIMENTO.md` e `scripts/check_documentation_gate.py` são gate de CI; falha bloqueia merge. Validar conteúdo humano contra código, pois o gate só verifica estrutura. Não fechar F5, R1 ou R10 sem homologação física e integrada. Testes de R2.8 documentados em `RESULTADOS_TESTES_R28.md`; execução Linux não comprova Windows 3.12.


## Checkpoint R2.9 — FAILSAFE factual cérebro/agente (23/11/2026)

**Autoridade inalterada:** a política central mantém precedência sobre qualquer capacidade. Resultados de cérebro marcados com `brain_ids` em modo factual são considerados material de saída **canônica**, jamais instrução para o LLM improvisar. `chat/service.py` deve usar o `canonical_answer` real; `chat/grounded_expression.py` deve copiar seu corpo literalmente. Uma introdução prefixada fixa sem fatos adicionais pode distinguir Morgana/Todd, mas **nunca** reescrever números, condições, negações, limites, fontes ou status. Se erro, conflito ou leitura sem suporte: fallback canônico, sem prefixo de sucesso. Citações continuam geradas pelo runtime, não pelo LLM.

**Limites verificáveis:** o mecanismo evita deriva gerativa na camada de expressão para saída de cérebro, mas NÃO verifica veracidade do documento, exatidão do cálculo anterior, correção da recuperação, segurança de prompt injection nas fontes, nem transforma seis catálogos em executores. Respostas sem `brain_ids` mantêm a validação V9.1 heurística antiga. Um resultado sem evidência legítima não deve ganhar `brain_ids` fraudulentamente; preservar validações do executor e compilador. Testes R2.9 documentados em `RESULTADOS_TESTES_R29.md`; regressão histórica G2 permanece falha em Linux, sem homologação global.

**Rollback e continuidade obrigatórios:** antes de instalar, fazer backup independente das três pastas; para reverter R2.9 restaurar somente arquivos do `CAMPANARIO-IA` R2.8 pelo Explorador, sem copiar `.venv` ou bases, nem restaurar SQLite de produção. Não existem migrations. `CAMPANARIO-PYTHON` hospeda Python/`.venv` externa; `CAMPANARIO-DATABASE` hospeda SQLite, Biblioteca V2, memórias, conversas e documentos. Não incluir credenciais, `.env` ou persistência em ZIP. Cada futura modificação exige simultaneamente atualizar ROADMAP principal, ROADMAP V9, este FAILSAFE, `MANUAL_TECNICO_VIVO.md`, changelog, resultados, instruções e gate documental. **F5 voz e R1 segurança continuam abertos; foco R2.10 é vincular fatos a evidências reais antes de criar novos cérebros.**


## Checkpoint R2.10 — fail-safe de resposta e roteamento (23/11/2026)

1. **Fatos nao vem do agente:** para resposta V9 individual com `brain_ids`, uma afirmacao de documento precisa ser trecho literal de um `SourceRecord.excerpt` vinculado. Se nao for, status `not_found`, sem promover porcentagem ou identidade citada falsamente. Assercao literal de um documento NAO significa verdade externa; o executor deve manter IDs, guard e leituras first-party validados. Nao dar permissao pela personalidade.
2. **Nao inventar consultas:** com web automatico desativado e sem consulta real, nao criar um `ResearchResult` falso com status `disabled`, nao afirmar que pesquisou ou que a ferramenta falhou. Perguntas claramente subjetivas podem ir para conversa normal, sem acionar pesquisa/biblioteca/ZIM. Ainda e proibido inventar biografias, resultados atualizados e memorias pessoais quando nao ha fonte; pedidos factuais concretos permanecem fechados.
3. **Limites:** roteador linguistico cobre somente formatos testados; nao e classificador universal. Correspondencia de substrings nao equivale a implicacao semantica, avaliacao de contradicoes ou veracidade de noticias. Respostas LLM em conversa geral nao sao totalmente auditadas. Testar cenarios falsos positivos e falsos negativos antes de ampliar as isencoes.
4. **Regressao/rollback:** 76 PASS direcionados; regressao geral parou apos 530 PASS na falha historica G2 de auditoria pessoal (nao reparada). Sem homologacao Windows, mobile, Ollama ou dados persistentes externos. Havendo erro, fechar app, restaurar backup do IA R2.9 por copia do Explorador; preservar `.env` privado, `CAMPANARIO-PYTHON/.venv`, `CAMPANARIO-DATABASE` e seus SQLite e memorias. Sem migrations. Para retorno legado V9, mudar flag somente com verificacao e backup; isso nao reverte alteracoes em dados.
5. **Governanca:** atualizar ROADMAP principal, ROADMAP V9, este FAILSAFE, Manual Tecnico Vivo, changelog, resultados e instrucoes na mesma versao; validar gate documental. R1 sandbox e F5 permanecem abertos; nao promover F6 ou os seis cerebros ausentes.


## Checkpoint R2.11 — FAILSAFE de memoria pessoal e pertinencia da evidencia (23/11/2026)

1. **Antes de emitir texto ou armazenar:** se a pergunta for sobre memoria pessoal e houver afirmacoes explicitas do usuario recuperadas, executar auditoria estruturada (resposta + pergunta + citacoes originais) e rejeitar respostas sem citacao valida ou com intensidade/exclusividade inventadas. A auditoria do LLM nao concede autoridade: o verificador deterministico `unlicensed_personal_strength` tem veto final. Uma unica reparacao pode ocorrer com reauditoria; nao transmitir proposta/reparo antes do veredicto. Na falha do modelo, voltar aos trechos originais, sem fabricacao.
2. **Sem fonte:** responder com falta de confirmacao, mesmo se o LLM sugerir um fato. Nao converter uma lembranca de outro agente ou inferencia da memoria em declaracao pessoal do usuario. Nao registar conteudo pessoal de testes em arquivos do repositorio; usar SQLite temporario de pytest, nunca Database de producao.
3. **Consulta factual:** fonte importada e alegacao documental; o teste de pertinencia textual nao garante verdade semantica. Contradicoes explicitamente reconhecidas devem manter status `conflicting`, sem escolher uma fonte. Source ID sem trecho correspondente nao gera afirmacao canonica; personalidade nao edita dados do cerebro.
4. **Falhas reais:** 74 PASS direcionados, G2 anteriormente falho agora aprovado no percurso. A suite completa NAO passou: 601 PASS e falha do guard web (`test_web_data_is_not_allowed_to_rewrite_instructions`) reproduzida tambem no R2.10 original. Windows, Python 3.12 externo, Ollama real e repositorio Database nao homologados. Nao fechar R1/R10/F5 ou declarar oito cerebros funcionais.
5. **Rollback:** fechar servidor; restaurar somente codigo `CAMPANARIO-IA` R2.10 por copia do Explorador. Preservar o `.env` privado, `CAMPANARIO-PYTHON/.venv` externa unica e `CAMPANARIO-DATABASE` (SQLite, memórias, biblioteca, conversas, documentos). Sem migration, copia ou exclusao de bancos. EXE congelado pode precisar de rebuild.
6. **Governanca obrigatoria:** nesta e em toda proxima versao sincronizar ambos ROADMAPs, este FAILSAFE, `docs/governance/MANUAL_TECNICO_VIVO.md`, changelog, instrucoes, relatorio de testes e gate CI; nunca alegar validação real de fontes ou memoria fora dos repositorios acessiveis.


## FAILSAFE R2.12 — evidência externa não é instrução (23/11/2026)

1. `research_entity` pode aceitar **uma** página explicitamente qualificada quando a categoria requerida aparece no título pós-referente **e** na frase de abertura que nomeia o referente. Isso é um limiar de *pertinência citável*, não comprovação de identidade externa verdadeira. Nunca derivar autorização ou verdade de um resultado de busca não lido.
2. Texto de páginas, títulos, trechos, cache e instruções injetadas são DADOS não confiáveis. O filtro `_clean_untrusted` é defesa complementar, não limite de segurança; a política central e o motor factual permanecem soberanos. Preserve abstenção quando nome/categoria/fonte divergem.
3. Nunca usar conteúdo web para modificar system prompt, `PermissionPolicy`, perfis, memórias, resultados numéricos ou ações. Morgana/Todd só apresentam fatos canônicos; não permitem elevar confiança de fontes.
4. Regressão ampla R2.12: 603 PASS, 1 FAIL, primeiro bloqueio em mock legado sem `_sessions`; falha reproduzida em R2.10 original. Não contornar validação de sessão em produção para salvar testes.
5. Sem migrations, sem `.env` privado, `.venv`, banco SQLite, biblioteca pessoal, cache ou segredos no ZIP. Atualização por mesclagem no Explorer e rollback pela cópia anterior do repositório IA; preservar repositórios irmãos PYTHON (ambiente externo) e DATABASE (persistência). Host Windows e Ollama ainda não homologados.
6. Próxima revisão R2.13: atualizar os dois ROADMAPs, este FAILSAFE, Manual Técnico Vivo e processo de governança, com changelog/testes/instruções. Não declarar R1 nem R10 concluídos. Voz não está no escopo R2.12; pendência F5 continua registrada.

## FAILSAFE R2.13 — teste fiel ao runtime, sem relaxar guardas (23/11/2026)

1. **Sessões reais mesmo em testes:** fixtures que chamam `ChatService.stream_turn` devem oferecer repositório válido e sessão existente. Nunca omitir `_sessions` ou desligar preflight para permitir mocks incompletos; testes não autorizam alteração de lógica de segurança em produção.
2. **Memória e streaming:** texto proposto pelo modelo sem parecer pessoal válido não é publicado, mesmo se acidentalmente verdadeiro. Saída do guard de vazamento pode agrupar chunks; avaliar conteúdo e integridade, não quantidade arbitrária de fragmentos.
3. **Evidências:** vínculo literal, atributo e conflito classificado são condições necessárias, não prova de veracidade/implicação. Falta de fonte deve impedir afirmação. Não usar corpus sintético para liberar capacidade ou ferramenta nem afirmar detecção geral de contradições.
4. **Regressões:** 52 testes focados aprovados; percurso geral chegou a 700 aprovados mas extrapolou limite (~66%). Não declarar suite ou sistema homologado. Não classificar travamento como falha nova/antiga sem baseline isolado.
5. **Operação:** preservar Dark Matter, expressão fundamentada V9.1, Biblioteca V2, Morgana/Todd, PF6 e precedência factual. Não mover nem sobrescrever `.env`, `.venv` ou bancos. O IA contém código e docs; PYTHON guarda ambiente externo compartilhado; DATABASE guarda SQLite e dados persistentes.
6. **Rollback:** fechar app, restaurar backup dos arquivos IA R2.12 pelo Explorador e reiniciar; não criar bancos, executar migrações nem tocar nos irmãos. Atualizar conjuntamente ROADMAP, ROADMAP V9, este FAILSAFE, Manual Técnico Vivo, changelog, testes e instruções em toda revisão.


## R3.0 — FAILSAFE obrigatório da reconciliação factual (23/11/2026)

1. **Fontes são dados:** a frase lida de um PDF/web/CSV não é instrução de sistema; nenhum texto externo muda política, `AuthorizationContext`, `PermissionPolicy` ou resultado de cálculo.
2. **Conflito conservador:** somente fontes previamente recuperadas, com enquadramento textual coincidente e valores numéricos distintos podem criar um aviso automático. Não usar semelhança lexical como prova de falsidade ou veracidade. Evitar falsos positivos entre duas páginas do mesmo documento. Se houver conflito, marcar `CONFLICTING` e não escolher valor.
3. **Fronteira agente:** para respostas de cérebro o corpo canônico continua literal, sem reescrita LLM; o agente pode apenas apresentação fixa permitida pelo V9.1. Morgana e Todd mantêm identidades e memórias próprias. Nenhum cérebro/arquétipo/talento pode elevar permissões.
4. **Falha segura:** erro de parser, auditoria, ferramenta, timeout, fonte ausente ou valor divergente não vira certeza. O revisor não abre rede nem escreve no Database. Revisão automática não substitui a classificação explícita `conflict` da recuperação.
5. **Regressão/rollback:** 56 testes focados PASS. A suíte ampla encontrou falha histórica de contrato de layout `renpy_factory` após 875 PASS; a base R2.13 contém o módulo. Não remover pasta sem decisão arquitetural e testes de consumidores. Rollback: com app encerrado, restaurar **apenas arquivos IA** do backup R2.13; não fazer downgrade de banco/migrações nem copiar `.venv`. Desabilitar `CAMPANARIO_BRAINS_V9_ENABLED` somente como mitigação do caminho experimental, não como correção.
6. **Gate de documentação e entregas agregadas:** toda alteração posterior DEVE atualizar ambos ROADMAPs, este FAILSAFE, Manual Técnico Vivo, processo de desenvolvimento, relatório de testes, instruções e changelog. Executar `scripts/check_documentation_gate.py`. Entregar incremental e completo, com checksums e sem segredos. Não usar muitos microincrementos como sinal de avanço.

**Ambiente não disponível:** não presumir conteúdo em `CAMPANARIO-PYTHON` (Python/`.venv` externos) nem `CAMPANARIO-DATABASE` (SQLite, documentos e memórias). Não implementar migração automática nem reinstalar ambientes. Homologação Windows/mobile/Ollama, sandbox OS e os seis cérebros permanecem pendentes. Voz fica fora do escopo atual sem fingir conclusão de F5.


## FAILSAFE R3.1 — Detetive e planejamento sem alucinação ou poderes adicionais (23/11/2026)

1. **Fonte antes da conclusão:** os dois novos executores só emitem relatório quando uma leitura real `library.retrieve` retorna `LocalFactSheet` e `EvidenceRef`s verificáveis. `report` é reproduzível dos trechos citados e deve ser rejeitado em caso de adulteração, fontes falsas ou troca de trace. Título, excerpt e ID não são prova de veracidade externa.
2. **Hipóteses são perguntas, não veredictos:** Investigação não acusa, não conclui culpa, causa ou intenção; só compara valores em frases diretamente comparáveis de documentos independentes e registra lacunas. A ausência de conflito detectado não é confirmação.
3. **Planejamento condicionado:** Estratégia não executa comandos, não modifica arquivos, não faz buscas na rede, não cria memória nem decide melhor opção sem medidas. Toda ação futura precisa de autorização fora do relatório e do mesmo PF6; nenhum cérebro concede escopo adicional.
4. **Execução protegida:** `brains/worker.py` limita os quatro IDs conhecidos, usa `deny_worker_network`, worker com timeout/limite RSS e ambiente reduzido. O processo **não é sandbox OS hostil no Windows**; não abrir tarefas perigosas com esses mecanismos. `library:read` exigido; falta de DB/permite negada/falha vira parcial/erro, não inventa resultado.
5. **Agentes e expressão:** Morgana/Todd mantêm identidade e memórias separadas, não podem reescrever dados da resposta canônica de cérebro. Não repassar instruções embutidas em trechos como comandos; são dados não confiáveis.
6. **Regressões e operação:** suite direcionada no Linux não equivale a homologação Windows/Python 3.12 e três pastas. R0, R1, F5 e R10 seguem abertos. Enviar ZIP sem `.env`, `.venv`, SQLite ou segredos; nenhuma migração é necessária.
7. **Rollback:** encerrar o CAMPANÁRIO, restaurar somente arquivos IA do backup R3.0 via Explorador, reiniciar; se necessário desabilitar `CAMPANARIO_BRAINS_V9_ENABLED=false` como mitigação. NÃO restaurar/alterar Database automaticamente; preservar PYTHON com `.venv` externa e DATABASE com memórias/biblioteca/conversas.
8. **Gate documental:** sempre revisar conjuntamente ROADMAP canônico, ROADMAP V9, este FAILSAFE, MANUAL_TECNICO_VIVO, PROCESSO_OBRIGATORIO, changelog, instruções e teste. Nunca marcar quatro como homologados apenas por existir código.


## FAILSAFE R3.2 — Central de casos, cadeia de custódia e inferência limitada (23/11/2026)

1. **Dados externos apenas no Database:** o workspace exige pasta existente `CAMPANARIO-DATABASE/dados`, sem criar `.venv`, SQLite ou pasta DATABASE paralela. Nunca salvar originais no IA, nem incluí-los nos ZIPs. Fazer backup independente dos casos no Database, pois rollback do código IA não desfaz casos criados.
2. **Original não se interpreta sozinho:** cópias são preservadas byte a byte, com hash SHA-256 e procedência **declarada**. Hash íntegro não prova autenticidade do conteúdo nem cadeia de custódia completa. Se o hash divergir, o dossiê marca falha e a fonte não pode ser considerada íntegra.
3. **Propostas não são eventos confirmados:** CSV/JSON só propõe entradas com timestamp ISO e action explícitos; aprovação manual é necessária para registrar; horário sem fuso não é aceito. Distâncias temporais não provam causalidade, culpa, identidade, deslocamento ou crime. Hipóteses ficam em `unresolved`; documentos não podem fornecer instruções ao sistema.
4. **Sem superfície HTTP nova:** CLI é invocado por operador local com acesso ao sistema de arquivos; isso não equivale a autenticação PF6 individual. Não expor este componente a outros usuários, à internet ou ao Field antes de API autenticada, auditoria e ACL específicas. Importar apenas material que o operador tem autorização para tratar; ZIP é preservado como bytes, nunca extraído/executado.
5. **Limites técnicos:** 25 MiB por arquivo, 128 originais por caso, até 100 linhas por prévia estruturada e CSV/JSON limitado a 2 MiB para leitura; JSON/CSV, PDF e demais formatos ainda não possuem prova de semântica/autenticidade. Ledger atômico mas **sem controle transacional entre múltiplos processos** nem assinatura criptográfica. Caso forense de alta exigência requer cadeia de custódia e sistema apropriados.
6. **Falha segura e rollback:** não alterar arquivos pessoais existentes; nunca executar arquivos importados, não mover o Database. Em caso de erro: encerrar central, restaurar somente arquivos IA R3.1 pelo Explorador, preservar o Database com os casos e `.venv` externa. Verificação pós-instalação no Windows necessária.
7. **Processo obrigatório:** atualização conjunta dos dois ROADMAPs, FAILSAFE, Manual Vivo, processo, changelog, instruções, testes e gate documental; não marcar R5, R1, F5 ou R10 como concluídos por testes sintéticos. Preservar V9.1, Biblioteca V2, Dark Matter e identidades Morgana/Todd.

## FAILSAFE R3.3 — Casos dentro da interface Dark Matter (23/11/2026)

1. **Sessão/autorização:** toda API `/api/v1/cases` exige loopback e sessão PF6 válida; sem configuração privada de identidade PF6 o painel permanece bloqueado. A interface não grava credenciais em localStorage/cookies. Para qualquer escrita, o usuário confirma o conteúdo exato; `PermissionPolicy` gera confirmação com prazo, escopo, sessão e uso único. **Não** interpretar login como autorização de escrita. Identidades individuais precisam de ACL privada `CAMPANARIO_CASEWORK_WRITE_ACL_JSON` (`{"alice":["casework"]}`) além da política central; usuário sem entrada é negado. Configuração inválida falha fechada.
2. **Isolamento:** consultas listam somente casos cujo `authorized_by` corresponde ao principal PF6 autenticado. IDs pertencentes a outras identidades não devem retornar caso, relatório ou evidência. A API não aceita caminhos de arquivos do computador; upload envia bytes do arquivo escolhido voluntariamente, limite 25 MiB. ZIP é preservado e jamais executado/explodido. Documentos são fontes não confiáveis, mesmo que seu SHA-256 confira.
3. **Sem execução autônoma:** a revisão apresenta intervalos de horário e hipóteses não verificadas, não prova crime, causalidade, responsabilidade, localização nem autenticidade. Propostas CSV/JSON nunca viram eventos sem aceite individual. Não transformar texto de documento em comando, permissão ou prova de verdade.
4. **Dados e rollback:** o servidor IA não cria novo Database, `.venv` ou SQLite. Casos ficam apenas em `CAMPANARIO-DATABASE/dados/cases`, que requer backup separado. Para rollback, parar Campanário, restaurar os arquivos IA anteriores via Explorador e **não** apagar casos no Database; desabilitar V9/PF6 se houver suspeita de autorização inadequada. Revalidar hashes. O antigo BAT é legado; não é necessário para o fluxo normal.
5. **Limites e segurança residual:** API somente no host local, não publicada a Field; nenhuma autenticação individual remota, nem isolamento transacional de múltiplos processos CLI/API. Sessão PF6 e consentimento não substituem proteção do host contra malware/XSS. Controle de escrita local não equivale a sandbox completo R1. **Não homologado Windows/mobile.** Não aceitar histórico ou prompts como autorização.
6. **Gate de regressão:** testar sessão ausente/revogada, separação Alice/Bob, ACL de escrita, comparação exata dos argumentos, replay/expiração e adulteração de evidência, além de navegação nativa sem nova aba. Atualizar simultaneamente ROADMAP, ROADMAP V9, FAILSAFE, MANUAL, processo, changelog, testes e instruções. Não declarar conexão direta ao chat dos cérebros enquanto não houver código e testes próprios.


## FAILSAFE R3.4 — Consulta de caso no chat, sem vazamento de fatos (23/11/2026)

1. **Isolamento:** `/api/v1/cases/{id}/ask` sempre verifica origem local, sessão PF6 e propriedade de caso. Nunca aceitar `case_id` isolado como permissão; seleção da UI sem login não libera consultas. Não persistir token PF6 em localStorage.
2. **Factualidade:** só registros do ledger com originais de SHA-256 íntegro podem ser exibidos; hash íntegro não autentica origem. Se falhar, bloquear relato factual e orientar verificar integridade. Perguntas de caso não acionam LLM nem podem gerar veredictos, culpados, causas, localizações ou autorização. Morgana/Todd apenas apresentam trechos iguais com introduções fixas.
3. **Sem efeitos colaterais:** consulta não escreve ledger, conversa, memória ou SQLite; o chat principal apresenta a resposta transitória sem salvar no histórico comum. Eventos/hipóteses novos continuam exigindo consentimento PF6 da API R3.3.
4. **Limites:** cinco classes de intenção lexical; perguntas não reconhecidas retornam resumo controlado. Nenhuma interpretação PDF/XLSX/OCR, inferência semântica ou execução conjunta dos quatro cérebros; não dizer que a investigação foi resolvida.
5. **Rollback:** restaurar apenas IA R3.3 com app fechado via Explorador, mantendo DATABASE (dados privados/casos) e PYTHON (.venv externa) intactos; revogar sessão comprometida e conferir hashes.
6. **Gate:** atualizar ambos ROADMAPs, FAILSAFE, Manual Técnico Vivo, Processo, changelog, relatório e instruções. Testar ausência de sessão, troca de identidade, adulteração, classificação de perguntas, abstenção e UI. Não declarar homologação Windows/mobile sem teste real.


## R3.4 — Fail-safe do modo pessoal local (sem PF6 obrigatório)

1. Somente **loopback**: respeitar `LocalOnlyBoundary`, verificação `require_local`, origem/Fetch Metadata. Nunca habilitar modo sem credencial em acesso remoto/Field/reverse proxy. O usuário único no próprio PC pode operar Casos sem `CAMPANARIO_BRAINS_V9_ENABLED` e sem configurar PF6.
2. **Integridade antes de conclusão:** SHA-256 dos originais, IDs de evidências e status `reported_only`/`limited`; datas e relatos não são causalidade. Acesso direto local não aumenta factualidade.
3. **Escritas intencionais:** a interface solicita confirmação simples. Como a API local não exige token PF6, essa confirmação de UX não substitui controle de acesso. Não transmitir a interface em rede hostil; não confiar em arquivos de origem desconhecida. Não permitir caminhos de arquivo do navegador ou arquivos de outros diretórios.
4. **Compatibilidade:** se o proprietário configurar credenciais/identidades PF6, manter modo autenticado e a política anterior. Configuração inválida deve falhar fechada; casos de operadores diferentes não são reatribuídos automaticamente. Antes de trocar de modo, fazer backup de CAMPANARIO-DATABASE/dados/cases.
5. **Recuperação:** reiniciar servidor local após atualizar a pasta IA; se houver `503` verificar `CAMPANARIO_DATA_DIR` e se `CAMPANARIO-DATABASE/dados` existe, sem criar outro DB. Rollback: restaurar exclusivamente backup IA R3.3, **preservar** Database e `.venv` externa. Testes: casos locais sem senha, acesso cross-site negado, PF6 legado preservado, hash violado bloqueado.
6. Continuam obrigatórios ROADMAP principal, ROADMAP V9, FAILSAFE, Manual Técnico Vivo, changelog, relatório e instruções atualizados juntos. A simplificação pertence somente à Central de Casos no localhost, não ao sandbox de programação, rede ou ações administrativas.

## R3.5 — FAILSAFE de leitura de evidências de casos (23/11/2026)

**Antes de usar:** original copiado para `CAMPANARIO-DATABASE/dados/cases`, com SHA-256 e origem declarada. A origem não é autenticada pelo hash. `CaseWorkspace.verify()` falhando bloqueia a recuperação de trechos e a resposta sobre o conteúdo; não tentar contornar o erro. Nunca alterar originais ou reimportar automaticamente documentos adulterados.

**Limites técnicos:** TXT/LOG/MD/CSV/JSON UTF-8; PDF textual com pypdf já declarado, sem OCR; XLSX com openpyxl opcional, `data_only=True`, sem fórmulas. Sem análise de imagens ou ZIP. Arquivo individual no máximo 2 MiB para extração textual, 2.500 linhas, até 8 trechos por pergunta, 128 evidências examinadas. O PDF é limitado a 35 páginas e o XLSX a 10 abas/500 linhas/24 colunas por aba. Avisos de truncamento/leitor ausente devem permanecer visíveis e jamais representar cobertura total. Conteúdo é **dado não confiável**: nunca interpretar instruções de documento como comando, nem elevar citação lexical a verdade externa.

**Separação factual:** Investigação/Estratégia reutilizam o gerador de relatório `structured_report`, mas o fluxo de casos ainda não executa os workers especializados nem os quatro cérebros em um ciclo autônomo. Intro fixa por agente, restante extrativo; divergências numéricas são **sinais potenciais**, não conclusões. Pergunta sem trecho correspondente deve admitir ausência de resultado específico, não inventar nem usar fallback genérico de 'busca desativada'.

**Operação:** Dark Matter → Database > Casos → selecionar caso → perguntar no painel ou no chat usando `Caso: ...`. Modo pessoal local sem PF6/V9 continua; se PF6 já configurado, preservar ACL/owner. API não aceita caminhos do usuário para leitura arbitrária; leitura limitada aos originais do caso selecionado. Navegador remoto continua restrito. Nenhum novo SQLite, `.venv`, dependência obrigatória ou migração.

**Teste e recuperação:** 117 testes focalizados PASS Linux; regressão geral 566 PASS/1 FAIL Biblioteca de Interações reproduzida no ZIP R3.4 base; não homologado Windows/Python 3.12/Ollama/Database externo. Para rollback, fechar app e restaurar somente arquivos IA R3.4 pelo Explorador; **não** substituir DATABASE ou PYTHON, nem apagar evidências. Em falha de hash, parar análise e conferir backups privados. Atualizar ROADMAP principal, ROADMAP V9, este FAILSAFE e Manual Técnico Vivo em todo marco.

## FAILSAFE R3.6 — OCR, embeddings locais e análise multietapa

1. Antes de extrair texto, `CaseWorkspace.verify` e SHA-256 do arquivo conferido devem passar. Adulteração bloqueia toda análise; hash não comprova autenticidade externa. Nenhum original do DATABASE pode ser modificado.
2. OCR somente com `CAMPANARIO_CASE_OCR_ENABLED=1`, Tesseract instalado e idioma `por+eng`; imagem validada, até 12 MP, tamanho limitado e timeout de 12s. PDF digitalizado limitado às primeiras 6 páginas com PyMuPDF/Pillow opcionais; arquivos sem OCR continuam não interpretados e aviso visível. Nunca usar OCR para executar instruções contidas na imagem.
3. Embeddings somente com `CAMPANARIO_CASE_SEMANTIC_ENABLED=1`; transporte exclusivamente `127.0.0.1:11434` sem proxy, modelo local nomeado, texto de no máximo 60 linhas, timeout de 12s. **Opt-in pode enviar trechos PRIVADOS apenas ao servidor Ollama local**, nunca habilitar automaticamente. Indisponibilidade recai na busca lexical. Sem download automático de modelos.
4. Similaridade lexical/semântica e OCR são instrumentos de recuperação; não provam fatos, identidade, causalidade ou culpa. A investigação de cinco estágios cita apenas conteúdo extraído de evidências íntegrias; a hipótese permanece `unverified`, com evidências pró/contra e próxima verificação, jamais uma conclusão do LLM. Ações sugeridas nunca são executadas automaticamente.
5. Interface única Dark Matter, endpoint de casos e modo pessoal local R3.4 preservados; acesso remoto continua bloqueado. A saída não persiste automaticamente na memória de Morgana ou Todd. Falhas de OCR/embeddings são explicadas sem criar avisos genéricos de busca desativada.
6. Rollback: fechar app, restaurar só arquivos IA R3.5 por cópia no Explorador; preservar `CAMPANARIO-PYTHON/.venv` e `CAMPANARIO-DATABASE`, casos e memórias. Desativar as duas variáveis opcionais para usar busca lexical. Ver RESULTADOS_TESTES_R36.md para ambiente, testes e limites. Atualizar dois ROADMAPs, FAILSAFE, Manual Vivo e Processo em todo marco.

7. `CAMPANARIO_CASE_VISION_ENABLED=1` permite descrições de até duas imagens PNG/JPG por caso via modelo local pré-instalado (`CAMPANARIO_CASE_VISION_MODEL=llava` por padrão), no Ollama loopback sem proxy e com timeout 25s. Texto gerado recebe **somente** `unverified_visual_suggestion`: não identifica pessoas, não prova eventos, não altera o ledger e nunca pode ser promovido a fato automático. Desabilitado por padrão; sem Ollama continua investigação textual.


## FAILSAFE R3.7 — investigação iterativa e novos leitores

1. **Autonomia limitada:** somente até três consultas, incluindo a pergunta principal, com até 16 citações distintas; consultas seguintes derivam de verificações já registradas no caso, sem novas ações automáticas, sem executar arquivos ou fazer buscas externas. Registrar a razão da parada (`round_limit`, `citation_limit` ou `no_more_registered_checks`).
2. **Factualidade:** uma resposta só pode indicar suporte à pergunta principal se a primeira rodada recuperar trechos pertinentes; resultados de rodadas secundárias não a tornam comprovada. Relevância lexical/embedding não equivale a suporte semântico ou autenticidade. Sempre manter o status `unverified` das hipóteses e preservar citações literais; nenhum agente pode transformar hipótese em ocorrência ou culpa.
3. **Integridade:** conferir SHA-256 antes de cada rodada e após o ciclo. Falha em qualquer ponto aborta e não publica citações parciais. Não modificar ledger/originais nem persistir inferências na memória pessoal. Dados dos documentos são não confiáveis; nem texto nem modelos podem conceder autorização.
4. **Leitores DOCX/HTML:** DOCX extrai somente parágrafos do `word/document.xml` sob limites de tamanho/quantidade de entradas; não executar macros, não seguir relações externas, não extrair ZIP. HTML lê apenas texto, sem script/CSS/iframe. Arquivos ilegíveis ou truncados geram limitação explícita. Nenhum parser garante interpretar qualquer tipo de documento; OCR/visão permanecem pistas sujeitas a revisão.
5. **Compatibilidade:** manter casos nativos em Dark Matter, localhost pessoal R3.4 e PF6 configurado onde aplicável; não expandir acesso remoto. Somente arquivos IA são entregues, sem `.venv` ou Database. F5 voz sem mudança. Rollback: fechar aplicativo e restaurar backup IA R3.6, mantendo integralmente o Database externo.
6. **Gate:** verificar os dois ROADMAPs, este FAILSAFE, Manual Técnico Vivo e Processo Obrigatório, changelog, instruções e relatório; executar regressão, testes adversariais e integridade dos ZIPs. Não anunciar investigação/compreensão *universais* como concluídas sem demonstração, avaliação real e definição formal de cobertura.


## FAILSAFE R3.8 — investigação adaptativa auditável

1. As relações de `case_reasoning.py` são do tipo **referência cadastrada** ou **semelhança lexical**. Nunca transformar esses vínculos em veredito, nexo causal, probabilidade ou suporte semântico garantido. Posições pró/contra continuam declaradas pelo operador; o relatório mostra `unverified`.
2. Antes e depois das rodadas, verificar integridade SHA-256. Com arquivo adulterado, bloquear inteiramente as citações e a matriz. Nunca executar instruções extraídas de documentos, permitir escrita automática ou compartilhar evidências com serviço remoto. Ollama/OCR continuam opcionais e locais.
3. Verificações adaptativas são selecionadas **somente** de `next_check` cadastrado: pergunta inicial + até 2 complementares. Sem confirmação da primeira pergunta, resposta continua `insufficient_evidence` mesmo que uma complementar encontre dados. Deduplicar citações, limitar tamanho e registrar parada.
4. O chat Dark Matter apresenta rótulos de hipótese não confirmada e relação lexical não causal. Personalidade de Morgana/Todd não modifica trechos ou avaliações. APIs e modo pessoal local conservam as restrições existentes; não conceder permissões novas.
5. Não alegar universalidade ou conclusão completa sem teste de semântica, fontes independentes, OCR/visão em Windows, benchmark consentido e revisão humana. Quatro cérebros com executor permanecem os mesmos. Voz fora do escopo.
6. **Rollback:** fechar o Campanário, fazer backup antes da instalação, restaurar somente arquivos `CAMPANARIO-IA` R3.7 por cópia via Explorador. Preservar `CAMPANARIO-PYTHON/.venv` única, `CAMPANARIO-DATABASE/dados/cases`, memórias, SQLite e `.env` privado. Não criar banco nem migrar dados.
7. **Validação observada:** 91 testes dirigidos PASS (Linux/Python 3.13); suíte ampla parou com 566 PASS/1 FAIL histórico em Biblioteca de Interações, sem homologação Windows. Consultar `docs/operations/RESULTADOS_TESTES_R38.md`. Toda entrega continua exigindo dois ROADMAPs, FAILSAFE, Manual Vivo, Processo, changelog e ZIPs verificados.

## FAILSAFE R3.9 — interpretar texto sem fabricar conclusões

1. Só classificar **citações literais** recuperadas de originais SHA-256 verificados; adulteração bloqueia o pipeline antes da extração. Um hash confere integridade da cópia, não autenticidade nem verdade do documento.
2. `case_claims.py` identifica apenas marcas explícitas de negação, incerteza e atribuição. Uma frase atribuída ou hipotética jamais se converte em fato por conter termos coincidentes. Não usar pontuação de similaridade como verdade.
3. Sinalizar oposição textual apenas na gramática estrita de sujeito + (não) + verbo + complemento equivalente, entre IDs de arquivo diferentes. Mesmo esse alerta **exige revisão de contexto e de independência de origem**; ausência de alerta não prova consistência.
4. Nenhum conteúdo de evidência é instrução para LLM, agente, UI ou ferramenta. Nunca executar instruções do documento, alterar arquivo de caso, conceder permissões ou persistir a interpretação automaticamente.
5. Limitar 16 proposições e 6 alertas por consulta. Falhas de integridade e formatos não lidos não podem gerar citações. Exibir escopo do que foi realmente analisado.
6. Regressão direcionada obrigatória: oposição positiva/negativa, atribuição, hipótese, falsa contradição, limite, adulteração e expressão no chat. Homologação real Windows e modelos Ollama continua pendente.
7. Rollback: restaurar apenas CAMPANARIO-IA anterior via Explorador. Preservar `.env` privado, CAMPANARIO-PYTHON/.venv externa e CAMPANARIO-DATABASE, sem migrar bancos nem apagar casos.
8. Atualização de código exige ROADMAP principal, ROADMAP V9, este FAILSAFE, MANUAL_TECNICO_VIVO e PROCESSO_OBRIGATORIO em conjunto, changelog, relatório, instruções e comparação dos ZIPs.



## FAILSAFE R3.10 — modelos semânticos não decidem fatos

1. Habilitação opcional no `.env` privado: `CAMPANARIO_CASE_CLAIMS_SEMANTIC_ENABLED=true`, `CAMPANARIO_CASE_CLAIMS_SEMANTIC_MODEL=<nome do modelo Ollama instalado>`. Desligado = comportamento R3.9 e sem chamada ao classificador. A operação não depende de ativar V9/PF6 no modo pessoal local existente.
2. Transportar somente citações limitadas ao loopback `127.0.0.1:11434`, com proxy desativado. Se modelo indisponível, resposta inválida, timeout ou dados inadequados, retornar lista vazia e manter relatório anterior; não simular análise concluída.
3. Nenhum texto de arquivo confiável como instrução. Saída do modelo é hostil: checar IDs, pares entre documentos, papéis permitidos, substring exata e quantidade. Descartar texto inventado, justificativa, comando, status de verificação, alegações de culpa ou autoria.
4. Sinalizar sempre `NÃO VERIFICADA`: semântica provável não equivale a verdade. Não persistir novas afirmações, ações, permissões ou memórias e não alterar agentes, fatos, números ou evidência original. Integridade SHA-256 falha = bloquear revisão antes do modelo.
5. Sem promessa de compreender qualquer formato ou contexto; OCR/visão e embeddings são opcionais e não se tornam validação de verdade. Revisar documentos reais e casos adversariais antes de alegar precisão.
6. Regressão obrigatória: ausência de Ollama, JSON inválido, prompt injection, texto fabricado, usuário só, documentos diferentes, adulteração e resposta de Morgana/Todd. A suíte geral só é aprovada se terminar sem falhas; não extrapolar testes direcionados.
7. Rollback: fechar Campanário, restaurar apenas CAMPANARIO-IA anterior via Explorador e manter `.env` privado, CAMPANARIO-PYTHON/.venv compartilhada e CAMPANARIO-DATABASE com SQLite/originais/memórias. Nenhum banco ou migração criado.
8. Atualizar atomicamente ROADMAP principal/V9, FAILSAFE, Manual Técnico Vivo, Processo, changelog, instruções e relatório em toda nova versão, e verificar ZIP incremental/completo.


## FAILSAFE R3.11 — ativação baseada em evidência, não indiscriminada

1. Não gerar, publicar nem sobrescrever `.env` privado do usuário sem backup; `--apply` só atua em `.env` regular existente e cria `.env.backup_R311_*` antes de alterações. Exige reiniciar app.
2. Ativar apenas opções de análise local cujo runtime/modelo ou pré-requisitos são encontrados: OCR (Tesseract + bibliotecas), embeddings e modelo de chat/visão (Ollama loopback), ZIM explícito. Ausência = recurso desativado; não simular teste concluído.
3. Detecção de nome de modelo **não comprova qualidade**; OCR de PDF digitalizado requer backend extra. Nunca ligar automaticamente web, ações de escrita, permissões PF6, V9 experimental ou execução autônoma.
4. Testes sintéticos validam o avaliador, não a acurácia do LLM. Taxa real de falso positivo, limites OCR/visão e testes Windows são bloqueadores para declarar o gate de interpretação concluído.
5. Modelo e fontes são não confiáveis: saída continua provisória e citada; não promover hipótese a fato, modificar evidências, memórias ou agentes.
6. Persistência em CAMPANARIO-DATABASE, `.venv` única em CAMPANARIO-PYTHON e código em CAMPANARIO-IA; nenhum SQLite/env duplicado no ZIP. Rollback por restauração de backup `.env` e dos arquivos IA anteriores.
7. Atualização obrigatória conjunta ROADMAP (2), FAILSAFE, Manual Vivo, Processo, changelog, teste, instrução e ZIPs com hashes.


## FAILSAFE R3.12 — homologação factual e falsos conflitos

- **Sem Ollama real:** retornar `INCONCLUSIVE` (código 3), não criar resultado fictício, não marcar a versão homologada. Modelo indisponível, JSON fora do contrato e predição incompleta bloqueiam a avaliação.
- **Métrica insuficiente ou falso conflito:** `BLOCKED` (código 2). Não usar as sugestões semânticas como fatos nem desativar a fronteira V9.1 para obter nota maior. Duas rodadas são obrigatórias; rótulos inválidos são rejeitados.
- **PASS no corpus:** código 0 indica APENAS gate técnico com 34 pares sintéticos. Não é aprovação de Windows, OCR, fontes reais, causalidade, investigação autônoma, memória dos agentes nem prontidão dos outros quatro cérebros. Exigir avaliação humana independente e regressão antes de liberar marcos.
- **Relatórios:** nunca incluir dados privados em ZIP nem criar DB no IA. O modo `--output-dir` só grava JSON de métricas dentro do CAMPANARIO-DATABASE irmão já existente. Se gravar falhar, conservar saída do terminal e registrar incidente, sem afirmar auditoria persistida.
- **Rollback:** restaurar exclusivamente arquivos IA do ZIP anterior e opcionalmente remover o avaliador; sem migração, alteração de .env, alteração da .venv externa ou de evidências. CAMPANARIO-PYTHON e CAMPANARIO-DATABASE são independentes. Não desligar segurança para fazê-lo funcionar.


## FAILSAFE R3.13 — anexos no chat sem falha de política central

- **Falha:** "Permissão não concedida pela política central" ao enviar arquivo pelo clipe do chat em V9, mesmo no modo pessoal local sem PF6.
- **Causa:** `/api/v1/utilities/upload-stream` exigia confirmação V9 para toda gravação, diferentemente do modo pessoal da Central de Casos.
- **Correção restrita:** exceção somente para upload local sem PF6 configurado; acesso entre origens, remoto, nomes inválidos, formatos bloqueados, limites de bytes e sobrescrita continuam negados. Quando houver PF6 individual ou token owner configurado, manter a checagem V9 original; configuração de identidades inválida falha fechada.
- **Não conceder:** `utilities.invoke`, escrita em casos, controle dos cérebros, privilégios remotos nem importação automática do arquivo.
- **Rollback:** restaurar a cópia R3.12 dos arquivos IA; jamais reverter dados privados por cima de alterações recentes.
- **Verificação:** testes `test_r313_local_chat_upload.py`, `test_upload_pdf_grande_stream.py`, `test_r22_utilities_permission_bridge.py` e suites correlatas; homologação Windows continua pendente.


## Adendo R3.14 — simplicidade local e recuperação

**Novo padrão intencional:** `CAMPANARIO_LOCAL_PERSONAL_MODE=true` (também se ausente do `.env`). A Central de Casos e as utilidades locais não exigem PF6 nem autorização por chamada. Credenciais PF6 antigas não são apagadas; `false` restaura o controle anterior após reiniciar. Atenção: retornar ao modo protegido pode ocultar casos criados no modo pessoal até uma migração autorizada; não editar `case.json` manualmente. Casos anteriores mantêm `authorized_by` original.

**Controles preservados sem interação do usuário:** servidor somente local, origem igual, caminhos confinados ao workspace externo, arquivos originais com hash, proibição de sobrescrita, extensão e nomes válidos, limites operacionais de recursos e limites de confiança factual. Uploads são transmitidos em fluxo; limites por arquivo de 1 GiB continuam evitando esgotamento acidental do disco. O usuário pediu retirada de limites de uso, não alteração de evidências nem acesso externo.

**Rollback:** fechar o Campanário, restaurar backup do código R3.13 e reiniciar. Não restaurar o DATABASE nem apagar a `.venv`. Casos escritos com tamanho acima de 25 MiB continuarão armazenados no DATABASE e poderão deixar de ser importáveis novamente na versão antiga.


## Checkpoint R3.15 — biblioteca realmente acessível e respostas ligadas ao documento

**Falha real reportada:** clipe do chat fazia apenas staging de arquivos, mas não invocava `library.import`; portanto, um arquivo presente em `CAMPANARIO-DATABASE/dados/.../utilidades/arquivos/` podia não existir em `documents` nem em `document_sections`, impossibilitando `search_document`. A UI não tornava essa distinção visível. Uma continuação com `qual` sem interrogação era classificada como conversa genérica, fazendo o modelo responder sem a fonte desejada.

**Correção integrada na UI:** chat passa `index=true` em `upload-stream`; o endpoint preserva o arquivo no workspace, importa por `UtilityService` no mesmo DATABASE externo e retorna `indexed`, `indexed_sections`, `index_state`, `document_id` ou `index_error` sem fingir êxito. Importação é feita em thread durante a requisição, nunca em background silencioso. PDF sem texto/OCR ausente e JSON inválido são marcados como não pesquisáveis. Arquivos antigos enviados somente ao staging: em Ferramentas → Arquivos, usar **Indexar**; documentos com erros: Ferramentas → Biblioteca → **Reindexar**. O original continua imutável, com SHA-256 validado antes da reindexação.

**Gerenciamento:** o Explorador e a Biblioteca têm paginação (100 itens/página e total real), nomes, estados, visualização do texto extraído, exclusão e renomeação. A Biblioteca tem `library.rename` (metadados apenas, preservando extensão/arquivo) e `library.reindex` (reextração do original validado e substituição transacional da indexação). Arquivos na pasta autorizada oferecem Indexar/Renomear/Mover/Lixeira. O conteúdo original preservado não é editado diretamente; nova versão deve ser importada conscientemente. Chat permanece na interface Dark Matter, sem nova aba/aplicativo de investigação.

**Intenção documental:** `document_request` reconhece “arquivo relacionado a ordem paranormal” e remove o sufixo “e me diga...” do nome sugerido. Perguntas de acompanhamento com “qual/quais/quem...” sem `?` mantêm a referência explícita recente ao documento; falta de citação continua exigindo abstenção factual. Nenhum nome de criatura da franquia foi codificado como resposta. Trecho recuperado mostra **o que a fonte diz**, não valida cânone externo.

**Verificação:** 90 testes direcionados PASS, incluindo regressões V8, PF6 pessoal, cérebros, casos e semântica; regressão geral: 33 PASS, 1 falha preexistente em `uv.lock` ausente. Compilação e JavaScript verificados. Não houve acesso ao acervo privado do operador nem homologação com Windows/Ollama reais. **Rollback:** fechar o Campanário, restaurar a cópia R3.14 do código e reiniciar; preservar o DATABASE. Metadados criados nesta versão são compatíveis com schema V8; cópia privada de segurança recomendada antes de reindexar ou excluir.


## FAILSAFE R3.16 — navegação orientada por serviços geográficos reais

- Não há localização presumida como fix GPS: geolocalização deve vir do dispositivo com timestamp/precisão; amostras obsoletas, imprecisas, repetidas ou inválidas são rejeitadas. Coordenadas manuais precisam ser rotuladas como tal.
- Nominatim/Overpass/OSRM somente em loopback, configuráveis pelo `.env` privado. Serviço indisponível ou grafo sem cobertura → erro visível; **nunca** substituí-los por LLM, OSRM demo ou dados inventados. MBTiles raster não oferece roteamento.
- Vários destinos parecidos → seleção explícita. "Mais próximo" por categoria → comparar distância de rota real OSRM; uma diferença insuficiente leva a esclarecimento.
- Desvio por GPS exige **três** leituras com precisão suficiente fora da geometria; recálculo tem cooldown e preserva destino, não anuncia sucesso sem resposta real. Se falhar, estado OFF_ROUTE e aviso; usuário deve seguir sinalização e parar em local seguro.
- Voz é subordinada a manobras reais; navegador/Android podem suspender áudio. Desktop sessão em memória da aba e servidor, não persiste após reiniciar. Android mantém apenas sessão em primeiro plano; **não** existe serviço de foreground nativo homologado.
- Provedores de tiles externos não são consultados sem opt-in da interface. GPS mobile percorre canal pareado HTTPS, não API local administrativa. Stop apaga rota e posição em RAM do serviço; nenhum histórico GPS é salvo no módulo Maps V2.
- Dados OSM locais são obtidos e processados conscientemente; `PREPARAR_OSRM_CARRO_V2.bat` bloqueia sobrescrita do grafo. Fazer backup do grafo antes de atualizar; rollback R3.15 apenas nos arquivos IA.
- Aceite físico pendente: não usar Maps V2 como navegador crítico até ensaios práticos com mapas reais, trechos diversos, aparelho Android e alertas audíveis.


## Checkpoint R3.17 — FAILSAFE Field / navegação

Sem dispositivo pareado HTTPS e grafos OSRM/índices OSM locais: não iniciar rota e exibir falha. GPS sem permissão, impreciso ou obsoleto: negar início/atualização; o serviço Android funciona somente após comando explícito do usuário com notificação. Sem rota o LLM não fabrica distâncias ou instruções. Falha de conexão: publicar erro, não anunciar novo recálculo concluído. O usuário pode encerrar pela tela ou pela notificação. Alternar para chat não cancela o serviço; fechar/reiniciar o Android pode interrompê-lo conforme políticas do SO. O código Java ainda **não passou por compilação Android nem ensaio em aparelho**, não é software homologado para navegação crítica. Backup do IA R3.16 e rollback de código; não tocar DATABASE ou PYTHON, sem `.env`, tokens ou chaves em pacote. OTA automática e navegação Android independente offline NÃO estão implementadas.

## FAILSAFE R3.19 — substituição de pasta e GPS

**Troca segura:** renomear a pasta CAMPANARIO-IA atual (backup), extrair nova pasta lado a lado e copiar exclusivamente `.env` original para a nova raiz. Nunca sobrepor ZIP limpo na pasta antiga, pois arquivos históricos e cópias defeituosas permaneceriam. Preservar `CAMPANARIO-PYTHON`, `.venv` irmã, `CAMPANARIO-DATABASE`, chaves e vozes locais. Se houver falha, restaurar pasta original sem tocar bancos. `uv.lock` confiável do ZIP de origem acompanha pacote enxuto.

**GPS:** busca de destino por nome/endereço não deve exigir sensor. Origem manual é válida para calcular rota, nunca para simular guia ao vivo. Coordenadas de GPS aproximado são contexto não certificado; para "mais próximo" sem origem, exigir definição de origem. Navegação ao vivo continua exigindo posição recente e confiável. Não afirmar rota real sem retorno de roteador OSM, nem Android homologado sem APK/build/aparelho.


## R3.20 — localização automática e busca/rota com fallback (23/11/2026)

- Ao abrir Maps no Dark Matter, o cliente tenta `navigator.geolocation.watchPosition` automaticamente, conforme a autorização do Windows/navegador. Mantém latitude, longitude, precisão e horário somente em memória de interface; não envia localização ao servidor durante a simples observação. Sem GPS, busca por endereço permanece disponível e a origem manual continua possível.
- A tela Maps usa somente `CampanarioNavigationV2` para os botões de busca/rota, evitando que o antigo `gps-map.js` sobrescreva os handlers.
- Busca por endereço: Nominatim local primeiro; se estiver indisponível, Nominatim público em consulta explícita. Categoria próxima: Overpass local e depois público; roteamento carro: OSRM local e, se estiver indisponível, servidor público de demonstração OSRM. Caminhada: somente grafo pedestre local (não inventar rota de carro).
- O fallback está **ativado por padrão para uso pessoal** e pode ser desativado com `CAMPANARIO_MAPS_PUBLIC_FALLBACK=false`. Serviços públicos recebem a busca e, em roteamento, as coordenadas. Nominatim público tem limitação de uso, identificação do aplicativo, cache em memória e espaçamento de 1,1 s por host; não usar autocomplete nem disparar varreduras. Não há GPS fictício.
- Pendente: teste de campo em Windows/Android; conectividade e política dos provedores públicos; precisão do GPS no PC; compilação APK e navegação Android em segundo plano. Não declarar homologação de campo.

**Rollback operacional:** restaurar o ZIP limpo R3.19 para reverter a camada Maps, sem modificar CAMPANARIO-PYTHON ou CAMPANARIO-DATABASE. Para ficar offline sem reinstalar: `CAMPANARIO_MAPS_PUBLIC_FALLBACK=false` no `.env` e reiniciar. Se acesso a GPS for negado, manter busca textual/origem manual; nunca burlar permissão do sistema operacional.


## Checkpoint R3.21 — Field GitHub Pages (23/11/2026)
- Frontend PWA público estático, isolado em `pages/`, com GPS do navegador, mapa OSM e consulta de rotas públicas; não contém dados privados.
- Servidor Python/Ollama/Database continuam exclusivamente no PC; acesso opcional via listener Companion HTTPS autenticado e CORS para origem Pages explicitamente configurada.
- Compatibilidade e limitações: consulta cartográfica pública sujeita a quota, rota de carro somente, GPS em primeiro plano, sem APK nem homologação em campo; tela e notas offline, sem roteamento offline.
- Implantação reversível: excluir publicação Pages / desabilitar `CAMPANARIO_FIELD_PAGES_ORIGIN`; sem migração de dados e sem alterações nos três repositórios externos.
- Testes da alteração e pendências descritos em `docs/operations/RESULTADOS_TESTES_R321.md`. Não declarar homologado o acesso real a PC ou geolocalização do usuário.
