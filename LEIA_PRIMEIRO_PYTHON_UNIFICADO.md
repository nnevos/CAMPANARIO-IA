# CAMPANARIO-IA — Primeiro unificar o Python, depois separar os dados

Atualizacao sobre a Fase 4 Inc.3B.2 e sobre o pacote de tres pastas, considerando os inventarios do usuario em 2026-11-19.

## Destinos escolhidos, lado a lado

```text
C:\Users\Steam Deck\Documents\GitHub\
  CAMPANARIO-IA\                 projeto e codigo (permanece no lugar)
  CAMPANARIO-PYTHON\.venv\       novo ambiente completo
  CAMPANARIO-DATABASE\dados\    dados somente depois da migracao
  CAMPANARIO-DATABASE\zim\      enciclopedias futuramente
```

**NUNCA APAGUE AS DUAS VENV ORIGINAIS ANTES DOS TESTES DE VOZ.** A antiga era `..\.venv` (81 pacotes) e a atual `CAMPANARIO-IA\.venv` (47 pacotes). Seus inventarios mostraram `piper-tts==1.8.0`, `pocket-tts==4.0.1`, `torch==2.14.1+cu130`, `torchaudio==2.11.0+cu130`, `torchvision==0.29.1+cu130`. A nova venv so e aceita se esses componentes estiverem instalados conforme as versoes registradas, com Python 3.12.10.

**O patch substitui o antigo ZIP de tres pastas:** nao e necessario instalar o ZIP antigo antes dele. Caso o codigo do ZIP antigo ja tenha sido instalado, o instalador reconhece os hashes conhecidos. Nenhuma base SQLite, `.env`, voz ONNX ou modelo Ollama entra no patch.

## 1. Instalar somente o codigo (sem alterar dados, nem as venv antigas)

Na raiz `CAMPANARIO-IA`:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\CAMPANARIO_3_PASTAS_PYTHON_UNIFICADO_SEGURO.zip" -DestinationPath "$env:USERPROFILE\Downloads\PATCH_CAMPANARIO_UNIFICADO" -Force
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\PATCH_CAMPANARIO_UNIFICADO\APLICAR_3_PASTAS.ps1" -ProjectRoot "."
# Se SEM CONFLITOS:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\PATCH_CAMPANARIO_UNIFICADO\APLICAR_3_PASTAS.ps1" -ProjectRoot "." -Apply
```

O script cria `BACKUP_CODIGO_ANTES_3PASTAS_*`. Se houver `CONFLITO`, PARE: nao sobrescreva manualmente.

## 2. Preparar o ambiente novo ANTES de migrar dados

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\PREPARAR_PYTHON_UNIFICADO.ps1" -ProjectRoot "."
# Se o destino estiver livre:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\PREPARAR_PYTHON_UNIFICADO.ps1" -ProjectRoot "." -Apply
```

A preparacao usa o `uv.lock` existente para o nucleo, desktop e testes; adiciona os componentes de voz registrados em `config/ambiente_unificado.json` com o repositorio CUDA oficial `https://download.pytorch.org/whl/cu130`. Requer `uv`, acesso a pacotes de rede durante a **instalacao**, espaco livre de varios GB e Python 3.12.10. Essa rede e exclusivamente para instalar dependencias, nao para conversas nem para consultar dados pessoais.

**Se PyTorch/CUDA nao resolver, o script para de proposito.** Nao baixa uma versao de torch diferente silenciosamente. Nao habilita dados, nao modifica `.env` e nao mexe nas venv antigas. Copie o erro para diagnostico. Se houver uma instalacao externa incompleta, pode executar novamente com `-Apply -Resume`, desde que esse destino tenha sido criado por este script; nao o apague manualmente.

O projeto conserva o `uv.lock` original; a lista de **voz opcional** fica num manifesto dedicado. Ao rodar `uv sync` futuramente, **use sempre `--inexact`**, para nao apagar esses componentes. Isso ainda nao equivale a um lock unico de todos os wheels Windows+CUDA; um lock unico so sera afirmado depois da resolucao e homologacao no seu PC.

## 3. Conferir as dependencias e regressao

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\TESTAR_PYTHON_UNIFICADO.ps1" -ProjectRoot "."
```

O teste usa o Python EXTERNO, confere as versoes e os imports, roda `uv pip check` e executa os testes direcionados, incluindo as novas protecoes. **Abrir o aplicativo e ouvir Piper e Pocket sao testes manuais complementares**; importacoes e testes sintéticos nao garantem qualidade do audio/driver. O script imprime `torch.cuda.is_available()` para orientar a verificacao GPU. XTTS/Coqui e faster-whisper NAO constaram dos inventarios e nao sao instalados por suposicao.

## 4. Migrar os bancos e ativar os caminhos, somente apos o Python passar

Pare o Campanario e qualquer servidor usando os SQLite. Quando o Python novo estiver aprovado:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\ATIVAR_SEPARACAO.ps1" -ProjectRoot "."
# Confira dados atuais, destino e ZIM. Se estiver tudo correto:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\ATIVAR_SEPARACAO.ps1" -ProjectRoot "." -Apply
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\TESTAR_3_PASTAS.ps1" -ProjectRoot "."
```

A migracao recusa uma `.venv` sem marcador de instalacao validada, e usa `uv pip check` antes da copia. **NAO executa `uv sync` durante a copia**. SQLite eh copiado por backup consistente; outros arquivos por SHA-256. O `.env` privado so muda apos copia e verificacoes; o backup da configuracao fica em `CAMPANARIO-DATABASE\BACKUP_CONFIG_ANTES_SEPARACAO_*`.

## Como exportar projeto pequeno

```powershell
& "..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe" tools/exportar_campanario.py
```

Cria `..\CAMPANARIO_FONTE_PORTATIL.zip`, sem `.venv`, bancos, ZIM, modelos pesados, `.env` ou inventarios pessoais. Revise o zip antes de compartilhar.

## Reversao e limites

`REVERTER_3_PASTAS.ps1` reverte **somente o codigo de fato modificado pelo instalador**, com hashes e backup; rode primeiro sem `-Apply`. `REVERTER_SEPARACAO.ps1` reverte o `.env` por backup, sem apagar dados ou venv.

Esta entrega nao tem como instalar as bibliotecas no Windows do usuario daqui. A disponibilidade remota das versoes CUDA e a reproducao da voz so serao confirmadas quando os comandos rodarem naquele PC. Em caso de qualquer erro, nao apague nada e nao prossiga para a migracao dos bancos.
