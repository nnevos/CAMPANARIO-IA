# R1 — Execução de cérebros com contenção processual (incremento)

**Estado:** integração parcial funcional, testes locais, **não** homologação do Windows. **Data:** 19/11/2026.

## Fluxo implementado

```text
ChatService / prévia local (V9 opcional)
  → CapabilityRouter (não substitui AgentRouter)
  → autorização runtime PermissionPolicy (library:read)
  → BrainExecutor (escopos e limites)
  → subprocesso Python: brains.worker (apenas knowledge | analysis)
  → leitura Database / cálculo já existentes, sem LLM extra
  → retorno JSON tipado, limitado e validado
  → CanonicalAnswer / V9.1 / expressão / fallback
```

Os adaptadores V8 existentes fazem leitura de biblioteca, pesquisa com página e análise CSV/XLSX. O worker não aceita código, operações administrativas, caminhos fornecidos pela interface, nem objetos Python serializados via pickle. O executor encerra o subprocesso ao exceder o prazo configurado (`timeout_terminated`) ou o RSS amostrado (`memory_limit_terminated`), e recusa saída malformada/trace adulterado. O limite padrão é **8 segundos e 1024 MB RSS por consulta**, configurável no `.env` privado por `CAMPANARIO_BRAINS_V9_TIMEOUT_SECONDS` (0,5–30) e `CAMPANARIO_BRAINS_V9_MAX_MEMORY_MB` (128–4096); não há garantia de que será suficiente para XLSX enorme. Em POSIX aplica também soft/hard `RLIMIT_CPU`; no Windows monitoramento RSS e eliminação do processo são realizados pelo pai.

**Segurança e riscos:** este isolamento oferece **contenção de falhas dos dois adaptadores conhecidos, não sandbox de adversário**. O processo filho possui privilégios do usuário, pode enxergar arquivos fora do Database caso uma dependência seja comprometida, não tem firewall de processo, `chroot`/AppContainer/Job Object ou limites rígidos de I/O. **Não habilite Programação nem interprete um PDF/CSV como instruções**. `PermissionPolicy` integra a leitura de cérebros, mas `/api/v1/utilities` ainda usa uma confirmação independente, portanto S1/S2 permanecem parciais.

## Três pastas preservadas

```text
C:\Users\Steam Deck\Documents\GitHub\
  CAMPANARIO-IA\             codigo, UI, .env PRIVADO e artefatos de referencia antigos
  CAMPANARIO-PYTHON\.venv\   Python 3.12, psutil, pandas/openpyxl quando instalados
  CAMPANARIO-DATABASE\       dados\{desenvolvimento|producao}\campanario.db,
                               dados\reference\interaction_library_v2.sqlite (preferido),
                               zim\ (opcional)
```

O launcher `CAMPANARIO.vbs` dá prioridade a `Campanario.exe`; se é EXE empacotado sem Python interpretador compatível, a V9 **falha fechado** para worker de leitura (`worker_python_unavailable`). O executor não instala Python, não cria `.venv`, não edita `CAMPANARIO_DATA_DIR` nem abre/migra outro SQLite. Confira `CAMPANARIO_MEMORY_ENVIRONMENT` para evitar apontar para outro banco. Não copie a venv nem o Database dentro do IA. A Biblioteca Conversacional V2 pode continuar usando fallback de SQLite de referência legado dentro do IA até a cópia ser validada (consulte P0).

## Atualização sem terminal

1. Feche o Campanário e preserve backup do IA (incluindo `.env` pessoal) e Database separadamente.
2. Extraia **`CAMPANARIO_R1_ARQUIVOS_PARA_COPIAR.zip`** em `Downloads\R1_EXTRAIDO`.
3. Copie **o conteúdo interno** da pasta extraída sobre a raiz `CAMPANARIO-IA` pelo Explorador, mesclando pastas e substituindo só os arquivos homônimos. Compare arquivos personalizados antes de substituir.
4. Não mexa nas pastas `CAMPANARIO-PYTHON` ou `CAMPANARIO-DATABASE`, não apague a raiz IA, não sobrescreva `.env`.
5. Abra pelo launcher e consulte a Central de Cérebros; só ative `CAMPANARIO_BRAINS_V9_ENABLED=true` se a migração V9 já estiver presente e a instalação estiver homologada.

**Comandos são opcionais para manutenção/testes, não para atualização de arquivos.** O ZIP completo é referência; o overlay exige uma base IA P0 já aplicada. Se o arquivo local tiver código personalizado, não substitua cegamente.

## Testes locais e aceite

- Testes específicos: `tests/test_r1_brain_isolation.py` (autorização, protocolo, timeout que mata, consumo RSS que mata, orçamento inválido).
- Regressões relevantes: `tests/test_v9_brains.py`, `tests/test_v91_expression.py`, `tests/test_v8_knowledge.py` e `tests/test_p0_three_folders.py`.
- Ainda pendente: Python 3.12/Windows, EXE congelado e sidecar, controle de rede/diretórios/CPU/filhos via sandbox OS, integração `utilities/api` com a política, backup/restore em cópia real, memória, Ollama e mobile em hardware.

**Rollback:** desative V9 no `.env` e reinicie para voltar ao fluxo legada; se for necessário voltar ao código P0, restaure arquivos IA do seu backup com o app fechado. Não faça `alembic downgrade 0010` nem modifique automaticamente dados pessoais.


## Adendo R1.1

O próximo incremento reduz os riscos operacionais com orçamento total de execução, circuit breaker e ambiente mais restrito para os workers de leitura. Isso NÃO substitui isolamento OS. Consulte [`R11_PROTECOES_EXECUTOR_CEREBROS.md`](R11_PROTECOES_EXECUTOR_CEREBROS.md), [`FAILSAFE`](../operations/FAILSAFE_V9_CEREBROS.md) e [`testes R1.1`](../operations/RESULTADOS_TESTES_R11.md).
