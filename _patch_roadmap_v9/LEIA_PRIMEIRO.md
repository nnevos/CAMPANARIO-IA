# Atualização documental — ROADMAP V9 + FAILSAFE (sem alterar código)

Este patch foi preparado para a versão `CAMPANARIO_V9_V91_IA_INTEGRADO.zip`.
Atualiza somente cinco documentos já existentes e acrescenta dois novos.
Nenhuma alteração de código, migração de banco, `.env`, voz ou memórias é executada.

## Se o ZIP estiver dentro de CAMPANARIO-IA

Feche a aplicação e abra PowerShell:

```powershell
$projeto = 'C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA'
Expand-Archive -LiteralPath "$projeto\CAMPANARIO_V9_ROADMAP_FAILSAFE_PATCH.zip" -DestinationPath "$projeto\_patch_roadmap_v9" -Force
& "$projeto\_patch_roadmap_v9\APLICAR_ROADMAP_V9.ps1" -ProjectRoot $projeto
# Se a simulação confirmar os hashes, executar:
& "$projeto\_patch_roadmap_v9\APLICAR_ROADMAP_V9.ps1" -ProjectRoot $projeto -Apply
```

O script faz **simulação por padrão**. Com `-Apply`, primeiro valida os hashes de todos
os documentos, guarda cópias em `_backups/ROADMAP_V9_...` e só depois copia os arquivos.
Em caso de personalização de um arquivo local, **recusa sobrescrevê-lo**.
Se a versão instalada for diferente, abra os arquivos `.md` do patch e integre as alterações manualmente.

### Conteúdo

- `docs/current/ROADMAP.md`: link no roadmap canônico e matriz de gates R0–R10;
- `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md`: fases, riscos, prioridades, critérios de aceite;
- `docs/operations/FAILSAFE_V9_CEREBROS.md`: resposta a incidentes e rollback seguro;
- `docs/operations/ETAPA1...` / `ETAPA2...`: referências posteriores, sem reescrever testes históricos;
- `docs/current/AGENT_PERSONALITY_ROADMAP.md`: limites das fichas e talentos;
- `README.md`: pontos de entrada.

### Observações

- Isso é **documentação planejada**, não a implementação dos seis cérebros pendentes.
- F5 (aceite de voz) continua bloqueando a liberação formal da F6.
- Flags/migração/dados existentes não são alterados.
