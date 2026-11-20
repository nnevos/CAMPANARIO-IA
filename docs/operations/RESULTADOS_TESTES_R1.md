# Campanário — evidências de testes do incremento R1

**Checkpoint local:** 19/11/2026; repositório IA P0 em Linux, **Python 3.13.5** (fora do alvo Windows/Python 3.12). Nenhum acesso à instalação particular das pastas `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE`, nem ao Ollama real do usuário. Todos os arquivos/importações são sintéticos em diretórios temporários.

## Execuções observadas

| Conjunto | Aprovados | Falhas | Observação |
|---|---:|---:|---|
| R1 + V9/V9.1/V8 + P0 direcionados | 52 | 0 | `test_r1_brain_isolation.py`, `test_v9_brains.py`, `test_p0_three_folders.py`, `test_v91_expression.py`, `test_v8_knowledge.py` |
| Regressão 1/3 (33 arquivos de teste) | 461 | 0 | Grupo A: `test_agents.py` até `test_fase4_inc3b_diagnostico_scores.py` |
| Regressão 2/3 (33 arquivos) | 221 | 21 | Grupo B: `test_fase4_inc3b_identidade_evolutiva.py` até `test_project_layout.py` |
| Regressão 3/3 (34 arquivos) | 334 | 10 | Grupo C: `test_prompt_leak_guard.py` até `test_wikipedia_zim_offline.py` |
| **Total regressão disjunta** | **1.016** | **31** | **Zero novas identidades de falha em comparação ao baseline P0 (1.011 PASS/31 FAIL)** |

**Nota de metodologia:** a suíte de 1.047 casos em um único comando excedeu o limite do ambiente em duas tentativas. Os mesmos 100 arquivos foram então testados em três grupos de conjuntos disjuntos; suas contagens somam 1.047. A segunda execução do grupo C terminou em **334 PASS/10 FAIL**. Não descrever este resultado como uma execução única e contínua.

## Segurança e fault injection verificadas

- Deny antes da execução quando `PermissionPolicy` não permite ou não há contexto de autorização.
- Worker Conhecimento/Análise lê documento/planilha efetivamente importado e devolve objeto canônico reconstruído de JSON (sem `pickle`).
- Timeout sintético em processo travado por 30 segundos: retornou `timeout_terminated` e o PID não ficou em execução.
- Alocação sintética acima de 128 MiB: terminou com `memory_limit_terminated`.
- Payload malformado: resposta recusada; não produziram evidências falsas.
- Limites de memória fora do intervalo permitido são rejeitados ao construir orçamento.
- Controle V9 desligado, personalidade, memória e seleção de falantes permanecem cobertos por regressões da base.

## Não testado / não afirmado

- Sandbox OS com lista de pastas/autorização de rede, Windows Job Objects e quotas imutáveis; consumo RSS é monitorado por polling.
- Ação de código externo, Programação, escrita/rede de `utilities/api.py` sob a mesma política; permanecem fora do escopo.
- `Campanario.exe` congelado e execução dos workers com o Python 3.12 da venv externa no Windows.
- Desempenho de XLSX real extenso, Ollama mobile/voz, migração/backup/restore nos dados do usuário.
- Correção das 31 falhas históricas, ainda abertas.

## Repetição opcional para desenvolvedores (não necessária para copiar atualização)

```text
python -m pytest -q tests/test_r1_brain_isolation.py tests/test_v9_brains.py tests/test_p0_three_folders.py tests/test_v91_expression.py tests/test_v8_knowledge.py
```

Para comparar regressões, registrar **nomes completos das falhas**, não apenas contagem. Testar com SQLite temporário e `.venv` apropriada, nunca no Database pessoal.
