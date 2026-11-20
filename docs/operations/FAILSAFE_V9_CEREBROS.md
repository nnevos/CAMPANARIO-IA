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
| S9 — Regressão | Reexecutar suíte e comparar falhas pelo ID; zero regressões novas e pendências históricas triadas | Última evidência: 1.004 PASS / 31 FAIL (já presentes na base V9.1) |

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

Esses comandos são **procedimento recomendado**, não evidência de que foram executados no Windows. A suíte completa de referência foi executada no ambiente Linux/Python 3.13 com 1.004 aprovados e 31 falhas preexistentes; as falhas precisam ser investigadas, não escondidas.

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
