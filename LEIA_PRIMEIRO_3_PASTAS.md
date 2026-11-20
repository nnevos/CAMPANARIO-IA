# ATENCAO: veja LEIA_PRIMEIRO_PYTHON_UNIFICADO.md antes de qualquer migracao.

**A preparacao do Python externo com voz agora e obrigatoria.** O fluxo antigo de criar o Python durante ATIVAR_SEPARACAO foi substituido.

# CAMPANARIO-IA | Separacao das 3 pastas (Windows)

**Objetivo:** manter lado a lado no mesmo `Documents\GitHub`:

- `CAMPANARIO-IA` — somente projeto/codigo (o projeto nao se move)
- `CAMPANARIO-PYTHON` — `.venv` reconstruida com `uv`/Python 3.12
- `CAMPANARIO-DATABASE` — `dados` (memoria, SQLite e biblioteca importada) e `zim` (enciclopedias futuras)

Este pacote foi construido sobre a **Fase 4 Inc.3B.2**. A instalacao do codigo e a ativacao dos caminhos sao duas operacoes distintas. **Pare o Campanario, o servidor local e outras instancias de uso dos bancos antes de migrar**. NAO mova nem apague pastas manualmente.

## 1. Instalar apenas os arquivos novos/alterados (ainda nao migra nada)

Na raiz `CAMPANARIO-IA`:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\CAMPANARIO_3_PASTAS_SEPARACAO_SEGURA.zip" -DestinationPath "$env:USERPROFILE\Downloads\PATCH_CAMPANARIO_3_PASTAS" -Force
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\PATCH_CAMPANARIO_3_PASTAS\APLICAR_3_PASTAS.ps1" -ProjectRoot "."
# Se todos os hashes coincidirem, e somente entao:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\PATCH_CAMPANARIO_3_PASTAS\APLICAR_3_PASTAS.ps1" -ProjectRoot "." -Apply
```

O aplicador altera apenas codigo e arquivos auxiliares, cria `BACKUP_CODIGO_ANTES_3PASTAS_*` e nunca le/substitui `.env`, SQLite, memorias ou modelos.

## 2. Verificar primeiro, depois copiar os dados e preparar Python

`uv` deve estar instalado e Python 3.12.10 disponivel. Durante a criacao do ambiente externo, `uv` pode baixar dependencias. Este passo **NAO acontece** na verificacao sem `-Apply`.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\ATIVAR_SEPARACAO.ps1" -ProjectRoot "."
# Se mostrar os tres caminhos corretos, sem erros:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\ATIVAR_SEPARACAO.ps1" -ProjectRoot "." -Apply
```

**Execute ANTES `PREPARAR_PYTHON_UNIFICADO.ps1 -Apply` e `TESTAR_PYTHON_UNIFICADO.ps1`.** Esse passo usa o diretorio original `%LOCALAPPDATA%\Campanario` (ou `CAMPANARIO_DATA_DIR` ja existente), copia o conteúdo para `..\CAMPANARIO-DATABASE\dados`, verifica SHA-256 dos arquivos comuns e usa o backup consistente do SQLite nos `.db`, `.sqlite`, `.sqlite3`. O diretorio copiado so aparece em `dados` depois de concluido. Não copia os arquivos transitórios `-wal/-shm/-journal` (o backup SQLite já considera as transacoes confirmadas).

O Python externo ja precisa estar instalado e validado por `PREPARAR_PYTHON_UNIFICADO.ps1`. O migrador NAO executa `uv sync` e **so depois** modifica as duas chaves `CAMPANARIO_DATA_DIR` e `CAMPANARIO_ZIM_DIR` no `.env`. Salva uma copia PRIVADA de `.env` em `..\CAMPANARIO-DATABASE\BACKUP_CONFIG_ANTES_SEPARACAO_*`.

**IMPORTANTE:** se `dados` ou a `.venv` externa ja existirem, a migracao para antes de escrever qualquer dado nesses locais. Nao faz mesclagem ou sobrescrita automatica. Se falhar apos copiar `dados`, a origem e o `.env` antigo permanecem disponiveis; consulte a mensagem antes de qualquer nova tentativa. Nunca aponte a configuracao para a pasta copiada incompletamente.

## 3. Validar usando o Python NOVO

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\TESTAR_3_PASTAS.ps1" -ProjectRoot "."

& "..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe" -m pytest tests/test_fase4_tres_pastas.py -q

& "..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe" -m pytest tests/test_fase4_inc1_biblioteca.py tests/test_fase4_inc2_ficha_neutra.py tests/test_fase4_inc2_avaliador_windows.py tests/test_fase4_inc2_avaliador_inc1_windows.py tests/test_fase4_inc3_busca_local.py tests/test_fase4_inc3b_semantic.py tests/test_fase4_inc3b_identidade_evolutiva.py tests/test_fase4_inc3b_calibracao.py tests/test_fase4_inc3b1_suficiencia.py tests/test_fase4_inc3b2_guarded_semantic.py tests/test_fase4_tres_pastas.py -q
```

Esperado: **162 testes direcionados aprovados**. Testar depois a abertura por `CAMPANARIO.vbs` e a memoria de conversas, em sua instalacao. O atalho anterior pode continuar apontando para `CAMPANARIO.vbs`: o launcher agora prefere a `.venv` externa e preserva a busca da antiga como fallback.

**NAO apague ainda a `.venv` antiga nem `%LOCALAPPDATA%\Campanario`.** Alguns componentes opcionais de voz/geracao podem ter pacotes extras nao declarados no `uv.lock`; verifique-os antes de remover qualquer coisa. O pacote nao instala ZIM nem baixa modelos Ollama.

Para usar `uv run` / `uv sync` da pasta do projeto sem recriar `.venv` local, execute primeiro `.\tools\windows\ATIVAR_AMBIENTE_CAMPANARIO.ps1` no PowerShell atual, que define `UV_PROJECT_ENVIRONMENT` corretamente.

## 4. Exportar um ZIP pequeno para compartilhar o projeto

```powershell
& "..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe" tools/exportar_campanario.py
```

O ZIP `..\CAMPANARIO_FONTE_PORTATIL.zip` inclui codigo, testes, conceitos, documentacao, `ESTADO_DO_PROJETO.md` e `RECURSOS_EXTERNOS.json`; omite `.venv`, `.env`, bancos, ZIM, logs, modelos Ollama e pesos de voz `.onnx`. O projeto completo no PC continuara com as vozes originais. O ZIP de fontes e adequado para continuar o desenvolvimento, **nao para executar o programa sozinho sem dependencias e recursos locais**. Revise qualquer arquivo do ZIP antes de compartilhar; o filtro nao e um detector universal de segredos inseridos no codigo.

## Reversao segura da configuracao

Use o caminho do `BACKUP_CONFIG_ANTES_SEPARACAO_*` exibido ao final da migracao:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\REVERTER_SEPARACAO.ps1" -ProjectRoot "." -BackupConfigDir "..\CAMPANARIO-DATABASE\BACKUP_CONFIG_ANTES_SEPARACAO_YYYYMMDD_HHMMSS_mmm"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\REVERTER_SEPARACAO.ps1" -ProjectRoot "." -BackupConfigDir "..\CAMPANARIO-DATABASE\BACKUP_CONFIG_ANTES_SEPARACAO_YYYYMMDD_HHMMSS_mmm" -Apply
```

Isso recupera o `.env` antigo, sem excluir nenhuma pasta. Para reverter tambem o **codigo** use `REVERTER_3_PASTAS.ps1` que acompanha o ZIP, apontando o backup do instalador. A reversao dos arquivos nao apaga bancos nem ambientes.

## Limites e pendencias

- O Python externo nao foi testado no seu Windows antes desta entrega.
- Os 162 testes sintéticos cobrem os caminhos, migracao, protecoes e regressao; nao substituem a revisao da memoria real no aplicativo.
- Ren'Py, quando houver `CAMPANARIO_DATA_DIR` configurado, gravara novos projetos sob `dados\renpy_factory`. Projetos Ren'Py antigos que estavam na pasta legada `AppData\Local\Campanario\Campanario\renpy_factory` devem ser revisados separadamente antes de mover.
- Modelos Ollama continuam no local administrado pelo Ollama; aqui nao se transfere Ollama.
