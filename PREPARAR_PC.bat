@echo off
setlocal
cd /d "%~dp0"
title Preparacao segura - Campanario
where uv >nul 2>&1
if errorlevel 1 (
  echo Instale Python 3.12 e uv para preparar o ambiente.
  pause
  exit /b 1
)
REM Do not run an exact uv sync here: it would remove voice components installed externally.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0PREPARAR_PYTHON_UNIFICADO.ps1" -ProjectRoot "%~dp0" -Apply
if errorlevel 1 goto fail
if not exist .env copy .env.example .env >nul
if exist "%~dp0tools\windows\CRIAR_ATALHO.ps1" (
  powershell.exe -NoProfile -File "%~dp0tools\windows\CRIAR_ATALHO.ps1"
  if errorlevel 1 goto fail
)
echo Ambiente unificado validado. Para migrar os dados execute ATIVAR_SEPARACAO.ps1 separadamente.
pause
exit /b 0
:fail
echo Preparacao incompleta. .env, .venv antigas e bancos originais estao preservados.
echo Se a instalacao nova estiver incompleta, consulte as mensagens antes de usar -Resume.
pause
exit /b 1
