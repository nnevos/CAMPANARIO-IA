# FAILSAFE operacional — cérebros CAMPANÁRIO V9 + expressão V9.1

**Tipo:** runbook de prevenção, contenção e recuperação. **Estado:** procedimento documentado, não homologado em produção. **Revisão:** 19/11/2026.  
**Relação:** `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md`, `docs/current/ROADMAP.md`, migração `0010_v9_brains.py`.

## 1. Contrato de segurança antes de ativar V9

- **Não tocar em dados reais sem backup validado.** A cópia de trabalho disponível é somente `CAMPANARIO-IA`; `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE` não foram auditados aqui.
- `CAMPANARIO_BRAINS_V9_ENABLED=false` é o **desligamento lógico** da camada de cérebros (com reinício do processo). Não restaura alterações no código, não desfaz uma operação externa e não substitui o backup.
- Não desligar os guardrails V9.1 para recuperar velocidade ou fazer um cérebro passar nos testes.
- O executor atual (`brains/executor.py`) usa `asyncio.wait_for(asyncio.to_thread(...))`: **timeout pode deixar a thread continuando**. Não tratar timeout como prova de interrupção física nem habilitar execução arbitrária de código com isso.
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
| Executor excede timeout | Thread pode continuar em execução | Não marcar sucesso; interromper *espera*, negar nova ação perigosa e registrar incidente; parar/reiniciar processo somente depois de avaliar efeitos pendentes | R1 sandbox real |
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
3. **Revisar efeitos pendentes antes de reiniciar:** se houve timeout ou execução externa, a thread pode continuar. Não relançar operação não idempotente; inspecionar processos/arquivos no host e exigir confirmação humana quando aplicável.
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
| S1 — Permissões | Leitura, escrita, rede e ação externa seguem a mesma política em `runtime/capabilities.py`, `utilities/api.py` e brains | Pendente: caminhos de política distintos |
| S2 — Timeout real | Worker travado, OOM e cancelamento não continuam após prazo; nenhum efeito externo indevido | Pendente: thread não sofre kill por `wait_for` |
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
