# Resultados verificáveis — R1.1, contenção operacional de cérebros

**Ambiente:** Linux, Python 3.13.5. **Base:** cópia do código IA R1, sem SQLite pessoal, Ollama, Windows, Database externo ou alterações na `.venv`. Data do checkpoint: 19/11/2026 (janela desta conversa).

| Execução | Aprovados | Falhas | Observações |
|---|---:|---:|---|
| Direcionada: R1.1, R1, V9, V9.1, V8 e P0 | 58 | 0 | 6 testes novos da R1.1 |
| Regressão grupo A (33 arquivos) | 461 | 0 | Execução terminada |
| Regressão grupo B (34 arquivos) | 228 | 21 | Falhas históricas |
| Regressão grupo C1 (8 arquivos) | 29 | 1 | Falha histórica |
| Regressão grupo C2 (9 arquivos) | 83 | 1 | Falha histórica |
| Regressão grupo C3 (8 arquivos) | 135 | 1 | Falha histórica |
| Regressão grupo C4 (9 arquivos) | 86 | 7 | Falhas históricas |
| **Total da regressão (disjunta)** | **1.022** | **31** | **0 identidades de falha novas** contra R1 |

A regressão não foi uma única execução: o grupo C original ficou bloqueado e foi subdividido em quatro execuções para obter resultado completo. Foram comparados identificadores dos 31 testes com falha, e os conjuntos são iguais à R1. A regressão tem seis testes a mais que a base R1 e 31 falhas preexistentes. Os 58 testes direcionados sobrepõem a suíte; **não somar** 58 a 1.022.

**Novos testes específicos (6):** orçamento total do plano, abertura/recuperação de circuit breaker, negação de permissão não aciona breaker, higiene de ambiente de subprocesso, bloqueio de conexões Python no worker e encerramento sob cancelamento externo.

**Validado com fixtures reais locais:** os testes legados exercitam documento importado, evidência de consulta, cálculo de planilha, migração em SQLite temporário, autorização, timeout e RSS. **Não validado:** rede/arquivo como sandbox do SO, Job Objects Windows, integridade de instalação externa, segurança contra código hostil, recuperações físicas de banco, Ollama real e PC/mobile.

**Verificação sintática:** módulos Python alterados compilados por `compileall`. `ruff` não estava instalado nesse ambiente; não foi afirmada lintagem com ruff. Nenhuma dependência ou migração foi acrescentada.
