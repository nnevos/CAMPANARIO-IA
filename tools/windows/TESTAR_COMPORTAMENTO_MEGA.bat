@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\..\.."
title Campanario - MEGA Teste Comportamental E2E

echo.
echo ========================================
echo   CAMPANARIO - MEGA TESTE COMPORTAMENTAL
echo ========================================
echo.

where uv >nul 2>&1
if errorlevel 1 (
    echo [ERRO] uv nao encontrado.
    goto :fail
)
where ollama >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Ollama nao encontrado.
    goto :fail
)

if not exist ".env" copy /y ".env.example" ".env" >nul

ollama list >nul 2>&1
if errorlevel 1 (
    echo [INFO] Iniciando Ollama...
    start "Ollama" /min ollama serve
    for /l %%I in (1,1,15) do (
        timeout /t 1 /nobreak >nul
        ollama list >nul 2>&1 && goto :ollama_ready
    )
    echo [ERRO] Ollama nao respondeu.
    goto :fail
)

:ollama_ready
set "CONFIGURED_MODEL="
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"CAMPANARIO_MODEL_NAME=" ".env" 2^>nul`) do set "CONFIGURED_MODEL=%%B"
if not defined CONFIGURED_MODEL for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"CAMPANARIO_OLLAMA_MODEL=" ".env" 2^>nul`) do set "CONFIGURED_MODEL=%%B"
if not defined CONFIGURED_MODEL (
    set "LOCAL_MODEL="
    for /f "skip=1 tokens=1" %%M in ('ollama list 2^>nul') do if not defined LOCAL_MODEL set "LOCAL_MODEL=%%M"
    if not defined LOCAL_MODEL (
        echo [ERRO] Nenhum modelo local instalado.
        goto :fail
    )
    set "CAMPANARIO_MODEL_NAME=!LOCAL_MODEL!"
    echo [OK] Modelo detectado: !LOCAL_MODEL!
) else (
    echo [OK] Modelo configurado: !CONFIGURED_MODEL!
)

echo [INFO] Verificando dependencias...
uv sync
if errorlevel 1 goto :fail

echo.
echo [INFO] Rodando bateria MEGA contra o Ollama real...
echo [INFO] O banco principal NAO sera usado; os testes usam banco temporario isolado.
echo.
uv run python -m campanario.e2e.behavioral --suite mega --no-open
set "TEST_EXIT=!ERRORLEVEL!"

if exist "test_reports\behavioral_e2e\latest.html" (
    start "" "test_reports\behavioral_e2e\latest.html"
    echo.
    echo [OK] Relatorio aberto no navegador.
    echo Para abrir novamente depois, execute CONSULTAR_ULTIMO_TESTE.bat
)

if "!TEST_EXIT!"=="2" goto :fail
if "!TEST_EXIT!"=="1" (
    echo.
    echo [ATENCAO] O harness encontrou pelo menos uma falha objetiva.
    echo Consulte o relatorio para ver o transcript e os checks.
)

echo.
pause
exit /b !TEST_EXIT!

:fail
echo.
echo O teste nao foi concluido.
pause
exit /b 2
