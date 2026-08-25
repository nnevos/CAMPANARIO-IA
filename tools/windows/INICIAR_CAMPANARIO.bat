@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\..\.."
title Campanario IA

 echo.
 echo ========================================
 echo          CAMPANARIO IA - START
 echo ========================================
 echo.

rem 1) Check required commands.
where uv >nul 2>&1
if errorlevel 1 (
    echo [ERRO] O comando "uv" nao foi encontrado.
    echo Instale o uv e execute este arquivo novamente.
    echo https://docs.astral.sh/uv/
    goto :fail
)

where ollama >nul 2>&1
if errorlevel 1 (
    echo [ERRO] O comando "ollama" nao foi encontrado.
    echo Instale o Ollama e execute este arquivo novamente.
    echo https://ollama.com/
    goto :fail
)

rem 2) Create local config on first run. Never overwrite an existing .env.
if not exist ".env" (
    copy /y ".env.example" ".env" >nul
    echo [OK] .env criado a partir de .env.example.
)

rem 3) Make sure the Ollama service is available.
ollama list >nul 2>&1
if errorlevel 1 (
    echo [INFO] Iniciando Ollama...
    start "Ollama" /min ollama serve
    for /l %%I in (1,1,15) do (
        timeout /t 1 /nobreak >nul
        ollama list >nul 2>&1 && goto :ollama_ready
    )
    echo [ERRO] Ollama nao respondeu apos 15 segundos.
    goto :fail
)

:ollama_ready
 echo [OK] Ollama disponivel.

rem 4) If no model is configured in .env, use the first locally installed model.
set "CONFIGURED_MODEL="
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"CAMPANARIO_MODEL_NAME=" ".env" 2^>nul`) do set "CONFIGURED_MODEL=%%B"
if not defined CONFIGURED_MODEL for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"CAMPANARIO_OLLAMA_MODEL=" ".env" 2^>nul`) do set "CONFIGURED_MODEL=%%B"

if not defined CONFIGURED_MODEL (
    set "LOCAL_MODEL="
    for /f "skip=1 tokens=1" %%M in ('ollama list 2^>nul') do (
        if not defined LOCAL_MODEL set "LOCAL_MODEL=%%M"
    )
    if not defined LOCAL_MODEL (
        echo [ERRO] Nenhum modelo local foi encontrado no Ollama.
        echo Instale um modelo, por exemplo: ollama pull llama3
        goto :fail
    )
    set "CAMPANARIO_MODEL_NAME=!LOCAL_MODEL!"
    echo [OK] Modelo detectado automaticamente: !LOCAL_MODEL!
) else (
    ollama show "!CONFIGURED_MODEL!" >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] O modelo configurado "!CONFIGURED_MODEL!" nao esta instalado no Ollama.
        echo Instale com: ollama pull !CONFIGURED_MODEL!
        echo Ou use CAMPANARIO.bat ^> Trocar modelo.
        goto :fail
    )
    echo [OK] Modelo configurado: !CONFIGURED_MODEL!
)

rem 5) Sync dependencies and database schema.
echo [INFO] Verificando dependencias...
uv sync
if errorlevel 1 goto :uv_fail

echo [INFO] Aplicando migrations...
uv run alembic upgrade head
if errorlevel 1 goto :migration_fail

rem 6) Start the API. Keep this window open while Campanario is running.
echo.
echo ========================================
echo Campanario pronto para iniciar.
echo Chat:   http://127.0.0.1:8000/
echo API:    http://127.0.0.1:8000/docs
echo Health: http://127.0.0.1:8000/health
echo Para encerrar, pressione Ctrl+C.
echo ========================================
echo.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000/'"
uv run uvicorn campanario.main:app --host 127.0.0.1 --port 8000
goto :end

:uv_fail
echo [ERRO] Falha ao preparar as dependencias com uv.
goto :fail

:migration_fail
echo [ERRO] Falha ao aplicar as migrations do banco.
goto :fail

:fail
echo.
echo O Campanario nao foi iniciado.
pause
exit /b 1

:end
endlocal
