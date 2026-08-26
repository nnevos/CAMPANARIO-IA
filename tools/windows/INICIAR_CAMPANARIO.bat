@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\..\.."
title Campanario IA

set "CAMPANARIO_PORT=8000"
set "CAMPANARIO_BUILD=realtime-presence-f5c4"

echo.
echo ========================================
echo          CAMPANARIO IA - START
echo ========================================
echo.

rem 0) Never silently reuse an older Campanario process on port 8000.
set "OLD_PID="
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr /R /C:":%CAMPANARIO_PORT% .*LISTENING"') do (
    if not defined OLD_PID set "OLD_PID=%%P"
)
if defined OLD_PID (
    set "OLD_IS_CAMPANARIO=NO"
    for /f "usebackq delims=" %%C in (`powershell -NoProfile -Command "$p=Get-CimInstance Win32_Process -Filter 'ProcessId=!OLD_PID!' -ErrorAction SilentlyContinue; if($p -and $p.CommandLine -match 'uvicorn' -and $p.CommandLine -match 'campanario\.main:app'){ 'YES' } else { 'NO' }"`) do set "OLD_IS_CAMPANARIO=%%C"
    if /I "!OLD_IS_CAMPANARIO!"=="YES" (
        echo [INFO] Encerrando instancia anterior do Campanario na porta %CAMPANARIO_PORT% ^(PID !OLD_PID!^)...
        taskkill /PID !OLD_PID! /F >nul 2>&1
        timeout /t 1 /nobreak >nul
    ) else (
        echo [ERRO] A porta %CAMPANARIO_PORT% ja esta ocupada pelo PID !OLD_PID!.
        echo O processo nao parece ser uma instancia do Campanario iniciada pelo launcher.
        echo Feche o processo ou libere a porta antes de iniciar.
        goto :fail
    )
)

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

rem 4) Resolve configured model.
set "CONFIGURED_MODEL="
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"CAMPANARIO_MODEL_NAME=" ".env" 2^>nul`) do set "CONFIGURED_MODEL=%%B"
if not defined CONFIGURED_MODEL for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"CAMPANARIO_OLLAMA_MODEL=" ".env" 2^>nul`) do set "CONFIGURED_MODEL=%%B"

if not defined CONFIGURED_MODEL (
    set "LOCAL_MODEL="
    for /f "skip=1 tokens=1" %%M in ('ollama list 2^>nul') do if not defined LOCAL_MODEL set "LOCAL_MODEL=%%M"
    if not defined LOCAL_MODEL (
        echo [ERRO] Nenhum modelo local foi encontrado no Ollama.
        goto :fail
    )
    set "CAMPANARIO_MODEL_NAME=!LOCAL_MODEL!"
    echo [OK] Modelo detectado automaticamente: !LOCAL_MODEL!
) else (
    ollama show "!CONFIGURED_MODEL!" >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] O modelo configurado "!CONFIGURED_MODEL!" nao esta instalado no Ollama.
        echo Use CAMPANARIO.bat ^> Trocar modelo.
        goto :fail
    )
    echo [OK] Modelo configurado: !CONFIGURED_MODEL!
)

rem 5) Auto-wire F5c voice while keeping large Whisper models outside the project by default.
rem CAMPANARIO_VOICE_MODELS_DIR may point anywhere. Default shared cache: %%LOCALAPPDATA%%\Campanario\models.
set "VOICE_MODEL="
set "VOICE_MODELS_DIR=%CAMPANARIO_VOICE_MODELS_DIR%"
if not defined VOICE_MODELS_DIR if defined LOCALAPPDATA set "VOICE_MODELS_DIR=%LOCALAPPDATA%\Campanario\models"
rem F5 physical pt-BR is accuracy-first: prefer the largest available multilingual model.
if defined VOICE_MODELS_DIR if exist "!VOICE_MODELS_DIR!\ggml-large-v3.bin" set "VOICE_MODEL=!VOICE_MODELS_DIR!\ggml-large-v3.bin"
if defined VOICE_MODELS_DIR if not defined VOICE_MODEL if exist "!VOICE_MODELS_DIR!\ggml-large.bin" set "VOICE_MODEL=!VOICE_MODELS_DIR!\ggml-large.bin"
if defined VOICE_MODELS_DIR if not defined VOICE_MODEL if exist "!VOICE_MODELS_DIR!\ggml-big.bin" set "VOICE_MODEL=!VOICE_MODELS_DIR!\ggml-big.bin"
if defined VOICE_MODELS_DIR if not defined VOICE_MODEL if exist "!VOICE_MODELS_DIR!\ggml-medium.bin" set "VOICE_MODEL=!VOICE_MODELS_DIR!\ggml-medium.bin"
if defined VOICE_MODELS_DIR if not defined VOICE_MODEL if exist "!VOICE_MODELS_DIR!\ggml-small.bin" set "VOICE_MODEL=!VOICE_MODELS_DIR!\ggml-small.bin"
if defined VOICE_MODELS_DIR if not defined VOICE_MODEL if exist "!VOICE_MODELS_DIR!\ggml-base.bin" set "VOICE_MODEL=!VOICE_MODELS_DIR!\ggml-base.bin"
rem Legacy project-local layouts remain supported for existing checkpoints.
if not defined VOICE_MODEL if exist "models\ggml-small.bin" set "VOICE_MODEL=%CD%\models\ggml-small.bin"
if not defined VOICE_MODEL if exist "models\ggml-base.bin" set "VOICE_MODEL=%CD%\models\ggml-base.bin"
if not defined VOICE_MODEL if exist "voice\models\ggml-small.bin" set "VOICE_MODEL=%CD%\voice\models\ggml-small.bin"
if not defined VOICE_MODEL if exist "voice\models\ggml-base.bin" set "VOICE_MODEL=%CD%\voice\models\ggml-base.bin"
if not defined VOICE_MODEL if exist "voice\ggml-small.bin" set "VOICE_MODEL=%CD%\voice\ggml-small.bin"
if not defined VOICE_MODEL if exist "voice\ggml-base.bin" set "VOICE_MODEL=%CD%\voice\ggml-base.bin"
if exist "voice\whisper-cli.exe" if defined VOICE_MODEL (
    set "CAMPANARIO_VOICE_STT_BACKEND=whisper_cpp"
    set "CAMPANARIO_VOICE_TTS_BACKEND=windows_sapi"
    set "CAMPANARIO_VOICE_WHISPER_CPP_PATH=%CD%\voice\whisper-cli.exe"
    set "CAMPANARIO_VOICE_WHISPER_MODEL_PATH=!VOICE_MODEL!"
    if defined VOICE_MODELS_DIR set "CAMPANARIO_VOICE_MODELS_DIR=!VOICE_MODELS_DIR!"
    set "CAMPANARIO_VOICE_LANGUAGE=pt"
    echo [OK] Voz local F5c detectada e ligada ao Runtime ^(Whisper + Windows SAPI^).
    echo [INFO] Modelo STT externo/compartilhado: !VOICE_MODEL!
) else (
    echo [AVISO] Voz local nao configurada no Runtime.
    if not exist "voice\whisper-cli.exe" echo [AVISO] Falta: voice\whisper-cli.exe
    if not defined VOICE_MODEL echo [AVISO] Falta modelo multilingue em !VOICE_MODELS_DIR! ou em layout legado.
    echo [AVISO] Rode tools\windows\PREPARAR_VOZ_F5C.bat para instalar o modelo fora do projeto.
)

rem 6) Sync dependencies and database schema.
echo [INFO] Verificando dependencias...
uv sync --extra voice-host
if errorlevel 1 goto :uv_fail

echo [INFO] Aplicando migrations...
uv run alembic upgrade head
if errorlevel 1 goto :migration_fail

echo.
echo ========================================
echo Campanario pronto para iniciar.
echo Build:  %CAMPANARIO_BUILD%
echo Chat:   http://127.0.0.1:%CAMPANARIO_PORT%/
echo API:    http://127.0.0.1:%CAMPANARIO_PORT%/docs
echo Health: http://127.0.0.1:%CAMPANARIO_PORT%/health
echo Para encerrar, pressione Ctrl+C.
echo ========================================
echo.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:%CAMPANARIO_PORT%/?build=%CAMPANARIO_BUILD%'"
uv run uvicorn campanario.main:app --host 127.0.0.1 --port %CAMPANARIO_PORT%
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
