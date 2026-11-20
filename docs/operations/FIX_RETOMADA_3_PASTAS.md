# Incidente Windows — retomada segura da separação

- Base: CAMPANARIO-IA após ambiente Python unificado e correção de chamada de agentes, em 2026-11-19.
- Ocorrência observada: `tools/migrar_biblioteca_3pastas.py --apply` concluiu e publicou 1.022 arquivos (583.970.337 bytes). O comando `python -c` no PowerShell 5.1 perdeu as aspas internas e lançou `SyntaxError` após a publicação.
- O script antigo tinha restauração de `.env` em `catch`, mas sua primeira proteção recusa novo `-Apply` quando `dados` já existe.
- Correção: `-Resume`, que não usa `migrate(..., apply=True)` e exige comparação somente leitura da árvore de origem e destino, hash SHA256 dos arquivos comuns, `PRAGMA quick_check` e hash do dump lógico dos SQLite. Indisponibilidade, arquivos alterados e duplicação bloqueiam antes de alterar `.env`.
- Confirmação dos caminhos: programa Python em arquivo próprio, em vez de `python -c`, tanto na ativação quanto em `TESTAR_3_PASTAS.ps1`.
- Uma segunda checagem ocorre no momento do `-Resume -Apply` para evitar mudança entre verificação inicial e ativação. Backup do `.env` e restauração na falha mantidos.
- Nenhum ZIM, banco pessoal, `.env`, modelo ou ambiente virtual faz parte do pacote. A origem de dados continua intocada.
- Limite: comparação do conteúdo lógico pode consumir tempo proporcional ao tamanho dos SQLite e bloqueia se dados mudaram após a cópia. Sem mesclagem automática.
