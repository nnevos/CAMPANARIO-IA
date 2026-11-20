> **Atualização P0 posterior (recomendada):** para atualizar apenas o código IA numa instalação V9+V9.1, prefira [cópia pelo Explorador sem PowerShell](P0_TRES_PASTAS_SEM_POWERSHELL.md). Os comandos de patch abaixo são históricos e não precisam ser repetidos a cada atualização.

# CAMPANÁRIO V9 + V9.1 — Cérebros, fichas de agentes e expressão fundamentada

## Escopo e compatibilidade

Este incremento **V9 integrado sobre a V9.1** foi aplicado exclusivamente ao repositório `CAMPANARIO-IA` previamente fornecido. Mantém o `AgentRouter` de prioridade de fala, `AgentProfile`, a personalidade de Morgana/Todd, a Biblioteca Conversacional V2, as memórias, a recuperação documental V8 e o mecanismo canônico de evidências V9.1. Não substitui os repositórios `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE`, que não foram disponibilizados. A versão de pacote em `pyproject.toml` permanece 0.8.0 para não alterar contratos externos.

### Fluxo implementado

```text
Mensagem recebida → AgentRouter existente (quem fala)
                 → detecção de intenção / CapabilityRouter V9 (que capacidade é necessária)
                 → política e escopo de ferramenta
                 → BrainExecutor V9 (execução real, trace_id, status, duração)
                    ├─ KnowledgeBrain → recuperação documental V8, fontes/evidence_refs
                    └─ AnalysisBrain  → análise CSV/XLSX V8, operações numéricas reais
                 → consolidação factual e TurnFactSheet V9.1
                 → expressão de Morgana/Todd + ficha AgentBuild + talentos orientativos
                 → validação de integridade V9.1 / fallback quando necessário
                 → resposta e histórico existentes
```

O **Campanário é o orquestrador**, e não uma terceira personalidade. Cérebros compartilham as ferramentas já existentes e **não exigem** outro LLM residente. A seleção explícita por fonte/documento e planilha é determinística; perguntas abertas continuam no fluxo conversacional legado. Não há roteamento especulativo para cérebros indisponíveis. Um `BrainPlan` permite no máximo três cérebros distintos, mas o MVP executa um cérebro por intenção explícita; não foram implementadas chamadas paralelas arbitrárias nem seleção de cérebros por outro LLM.

### Contratos e módulos

- `brains/contracts.py`: `Brain` (Protocol), `BrainDefinition`, `BrainRequest`, `BrainResult`, `EvidenceRef`, `ResourceBudget`, `BrainStatus`. Solicitações são estruturas tipadas, com `request_id`, `trace_id`, orçamento e escopo de permissões; resultados descrevem operações reais e evidências, não alegações geradas pelo modelo.
- `brains/router.py`: `CapabilityRouter` e `BrainPlan` separados de `agents/router.py`. Escolha explícita de Conhecimento/Análise ou nenhuma ferramenta para conversa normal.
- `brains/registry.py` e `brains/adapters.py`: registro, checagem de saúde e adaptadores para o código de leitura e análise preexistente. O registro sinaliza honestamente indisponibilidade.
- `brains/executor.py`: execução com `asyncio.wait_for`, rastreamento de latência e registro de execução via `BuildStore`. **Limitação:** timeout encerra a espera, mas não mata uma thread Python em execução; isolamento duro de CPU/RAM/processo é pendência.
- `brains/builds.py`, `brains/store.py`, `brains/models.py`: fichas tipadas Pydantic, validação de arquétipos e talentos, revisões otimistas, tabelas adicionais e execuções observadas.
- `brains/api.py`: operações locais para consulta do registro, manutenção das fichas, prévia e inspeção/exportação de pacotes.
- `brains/package.py`: `.campagent` declarativo, com `manifest.json`, formato `campagent/1`, verificações SHA-256, limites de tamanho, rejeição de symlinks, scripts, arquivos executáveis e travessia de diretórios. **A importação apenas inspeciona**; o usuário deve salvar a ficha explicitamente.
- `chat/service.py` e `chat/grounded_expression.py`: integração das fontes executadas, evidências canônicas e diretivas de expressão **não autoritativas**. Sem permissão ou fonte real, uma ficha não pode criar evidências.

### Catálogo de cérebros

| Cérebro | Status neste incremento | Escopo |
|---|---|---|
| Conhecimento | Implementado; saúde depende da biblioteca local | Recuperação textual/híbrida preexistente, evidências reais |
| Análise | Implementado; saúde depende da biblioteca local | CSV/XLSX com operações determinísticas preexistentes |
| Investigação | Indisponível | Planejado; nenhum executor instalado |
| Programação | Indisponível | Planejado; nenhum executor instalado |
| Estratégia | Indisponível | Planejado; nenhum executor instalado |
| Percepção | Indisponível | Planejado; nenhum executor instalado |
| Comunicação | Indisponível | Planejado; nenhum executor instalado |
| Criação | Indisponível | Planejado; nenhum executor instalado |

Não existe indicação falsa de precisão, competência ou disponibilidade: o endpoint `/catalog` apresenta somente as capacidades realmente instaladas.

### Forja, arquétipos e talentos

`AgentBuild` é um complemento **por composição** do `AgentProfile`, sem copiar a Bíblia de Personalidade e sem tocar em memórias privadas. Admite `mode=free` ou `mode=archetype` com um principal e um secundário opcional. O catálogo disponibiliza **Investigador, Executor, Oráculo, Artífice, Estrategista, Guardião, Explorador e Arauto**. O arquétipo secundário nunca bloqueia cérebros nem concede permissões.

Os talentos declarativos são **Olhar Investigativo, Leitura Profunda, Plano de Ação, Revisão Técnica, Sentinela e Tradução Clara**. Cada definição tem `id`, `trigger`, `preconditions`, `effect`, `priority`, `conflicts` e `version`; até **dois** são ativados por turno, somente quando os gatilhos batem. Nenhum talento altera números, fontes, autorização, resultados de ferramentas ou condições factuais.

**Precedência:** segurança/permissões > integridade factual > pedido do usuário > necessidade da tarefa > talento > estilo. Os parâmetros de afinidade 0–5 são *preferências*, nunca pontuações medidas de precisão. Fichas podem ser atualizadas preservando histórico e memórias. Agentes novos compartilham o mesmo provider/modelo local; não criam modelos residentes extras.

### HTTP e interface real (loopback)

O router é protegido pela dependência existente `require_local` e pela flag de ativação:

| Rota | Finalidade |
|---|---|
| `GET /api/v1/brains/catalog` | Capacidade, saúde e catálogos declarativos |
| `GET /api/v1/brains/runs` | Execuções observadas e latências medidas |
| `GET /api/v1/brains/builds/{agent_id}` | Ficha persistida |
| `PUT /api/v1/brains/builds/{agent_id}` | Salvar ficha com revisão otimista |
| `POST /api/v1/brains/agents` | Criar agente de configuração neutra |
| `POST /api/v1/brains/preview` | Prévia com recuperação/cálculo real |
| `GET /api/v1/brains/builds/{agent_id}/export` | Exportar `.campagent` declarativo |
| `POST /api/v1/brains/package/inspect` | Validar pacote, **sem** aplicar automaticamente |

A seção **Central de Cérebros** e a **Forja de Agentes** estão integradas à página de ferramentas Dark Matter, com CSS responsivo e indicadores preenchidos a partir de status e rastros do backend. A interface não apresenta raciocínio privado nem métricas inventadas. *Não houve teste em navegador mobile físico neste ambiente.*

### Persistência e rollback

`src/campanario/migrations/versions/0010_v9_brains.py` é uma migração Alembic aditiva baseada em `0009`. Cria `agent_builds`, `archetype_definitions`, `talent_definitions`, `agent_talents`, `brain_registry` e `brain_runs` e índices de rastreamento. Insere fichas iniciais **livres**, sem mudar perfis nem memorizações de Morgana e Todd. O teste automatizado criou um SQLite temporário com conversa, aplicou upgrade `0009`→`0010`, voltou `0010`→`0009` e confirmou preservação da conversa. Esse teste não substitui backup do Database real.

**Configuração:** no `.env` de sua instalação, adicionar

```dotenv
CAMPANARIO_BRAINS_V9_ENABLED=true
```

A variável fica desativada (`false`) por padrão. **Com a flag desligada, o chat mantém o fluxo V9.1 anterior** — isso foi testado. Para desativar em caso de problema, volte a `false` e reinicie, sem apagar nada. Não faça downgrade SQL sem um backup completo: o downgrade `0010` remove **somente** as tabelas V9, o que também remove fichas e registros V9 criados depois da migração; não remove memórias/conversas antigas. O startup e a migração devem ocorrer no Database usado pelo IA, conforme sua configuração existente. **Não há necessidade de migrar as outras duas pastas sem verificar seus contratos reais.**

### Atualização sobre a instalação de três pastas

1. Feche o Campanário. Faça cópia externa de `CAMPANARIO-DATABASE`, `.env` e, idealmente, das três pastas.
2. Extraia o **patch incremental V9 integrada** fora de `CAMPANARIO-IA`, por exemplo `C:\Temp\CAMPANARIO_V9_INTEGRADA_PATCH`.
3. Execute a simulação (não modifica arquivos):

```powershell
$projeto = 'C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA'
$patch = 'C:\Temp\CAMPANARIO_V9_INTEGRADA_PATCH'
& "$patch\tools\windows\APLICAR_V9_INTEGRADA_SEGURA.ps1" -ProjectRoot $projeto -PatchRoot $patch
```

4. Confira hashes/caminhos. Se estiver sobre a **V9.1 original** sem personalizações, execute com `-Apply` para backup automático do código alterado:

```powershell
& "$patch\tools\windows\APLICAR_V9_INTEGRADA_SEGURA.ps1" -ProjectRoot $projeto -PatchRoot $patch -Apply
```

5. Garanta que suas dependências Python existentes estejam instaladas e migre pelo fluxo Alembic/boot já configurado no projeto. Para ambiente de desenvolvimento, consulte `alembic.ini`, `pyproject.toml` e `docs/current/V91_EXPRESSAO_FUNDAMENTADA.md`.
6. Ative `CAMPANARIO_BRAINS_V9_ENABLED=true`, reinicie o backend local, verifique `GET /api/v1/brains/catalog`, use a Central/Forja e faça uma consulta documental real. Para voltar à V9.1, desligue a flag.

O patch **recusa** arquivos existentes que não tenham SHA-256 idêntico à V9.1 distribuída na atualização anterior; exige conciliação manual para alterações locais. Ele não toca `.env`, arquivos de usuário, `CAMPANARIO-PYTHON`, `CAMPANARIO-DATABASE`, vozes ou arquivos SQLite. A versão completa do IA deve ser usada apenas com conferência e backup, não para sobrescrever instalação personalizável indiscriminadamente.

### Verificação local

```bash
python -m pytest -q tests/test_v9_brains.py tests/test_v91_expression.py tests/test_v8_knowledge.py
python -m pytest -q
python -m compileall -q src/campanario
node --check src/campanario/web/ferramentas.js
PYTHONPATH=src python tools/demo_v9_integrada.py
```

A execução aqui foi em Linux/Python 3.13 com ambiente de dependências já disponível; o projeto declara oficialmente **Python >=3.12,<3.13** para instalação. Não foi possível testar Ollama real, o PDF original de Ordem Paranormal, o dispositivo móvel físico, o PowerShell Windows ou os dois repositórios irmãos. A demonstração trabalha apenas com **documentos e números fictícios**, explicitamente identificados. Resultados e limitações adicionais: `docs/current/RELATORIO_V9_V91_INTEGRACAO.md`.

### Pendências explicitamente não implementadas

- Executor real dos seis cérebros futuros e planejamento colaborativo especializado ou roteamento por LLM em ambiguidade;
- Sandbox de processo isolado com limites rígidos de CPU/RAM; timeout atual limita espera, não interrompe processo ativo;
- Métricas longitudinalmente validadas de precisão factual (não inferir precisão dos testes unitários);
- Validação semântica universal das mudanças de significado no texto do LLM (a V9.1 preserva validação conservadora e fallback);
- Homologação em Windows/mobile, Ollama em produção, integração das pastas Python/Database não fornecidas.

## Princípio de projeto

**O cérebro executa; o arquétipo orienta; o talento condiciona procedimento; a personalidade expressa; a política autoriza; a evidência fundamenta.**
