# Execução local P0 — relatório verificável

**Data:** 2026-11-19 • **Base:** código IA V9+V9.1, com atualização documental R0–R10 aplicada.

## Alterações operacionais executadas

- Encontrado SQLite de referência V2 legado no IA. A consulta read-only foi alterada para preferir cópia em `Database/dados/reference` se existente; fallback original mantido, sem migrar nada. Teste sintético executado.
- Auditoria estática das três pastas pelo código do launcher, `config.py`, `storage/database.py`, `README.md` e manuais de migração. **Nenhum acesso ao Windows ou aos dois repositórios externos**.
- `src/campanario/brains/environment.py`: preflight apenas leitura, sem criação/migração de arquivos, com relatório separado por caminho e gatilho explícito para pendências.
- `GET /api/v1/brains/environment`: diagnóstico local independentemente da flag V9; tela Central de Cérebros apresenta estado real e ressalvas. Não confundir com um health-check do Ollama.
- Executor: checagem de `permission_scopes` contra `BrainDefinition` **antes** da chamada, e rejeição de `BrainResult` com `brain_id`/`trace_id` inconsistente ou operação ausente ao declarar `completed`. Isso é defesa parcial; não substitui `PermissionPolicy` central nem sandbox.
- Testes P0 criados: layouts temporários, read-only, faltas, cabeçalho SQLite inválido, permissão negada, rastreio adulterado e API local. Nenhum banco pessoal usado.
- Empacotamento para cópia pelo Explorador, sem atualização via PowerShell. Sem mudanças de migration, `.env`, personalidades, memórias ou Database.

## Estado dos gates

| Marco | Evidência nesta cópia | Estado |
|---|---|---|
| R0 — código IA/contratos | inspeção + testes | parcial |
| R0 — 3 pastas reais | não fornecidas | pendente |
| R0 — backup/restore do Database real | não acessível; não executado | pendente |
| R0 — Windows/Python3.12/Ollama/voz | não acessível; não executado | pendente |
| R1 — impedir escopo declarado ausente | executor e teste sintético | implementado/testado |
| R1 — provenance de resultado `BrainResult` | executor e teste sintético | implementado/testado |
| R1 — PermissionPolicy unificada nas APIs | não implementado neste incremento | pendente |
| R1 — sandbox de processo/kill real no timeout | não implementado neste incremento | pendente |
| R2–R10 | requisitos descritos no roadmap | não homologados |

**Não declarar P0 encerrado:** o laboratório não contém `CAMPANARIO-PYTHON` nem `CAMPANARIO-DATABASE` do usuário. A verificação de caminhos é necessária, mas não demonstra integridade ou restauração do SQLite real, nem isola execução de código perigoso. A falha herdada da suíte deve ser comparada por identidade com o baseline antes do release.

## Repetição local (para mantenedores, não para atualização de arquivos)

Com Python/dependências instalados, na pasta IA: `python -m pytest -q tests/test_p0_three_folders.py tests/test_v9_brains.py tests/test_v91_expression.py`. Rodar a suíte completa separadamente, sem misturar dados reais nos testes.

Resultados detalhados e ambiente ficam no `RESULTADOS_TESTES_P0.txt` incluído no pacote de entrega. A execução em Linux/Python 3.13 **não** homologa runtime Windows/Python 3.12.

## Resultado final de validação local

A suíte completa (`python -m pytest -q`) registrou **1.011 aprovados, 31 falhas e 18 warnings**. As 31 falhas correspondem exatamente às identidades de teste do baseline V9+V9.1 (sem novas regressões identificadas). A suíte direcionada incluindo Biblioteca Conversacional V2 passou em **53 testes**. Ver [`RESULTADOS_TESTES_P0.md`](RESULTADOS_TESTES_P0.md). Esses resultados foram obtidos em Linux/Python 3.13 e não são homologação Windows.
