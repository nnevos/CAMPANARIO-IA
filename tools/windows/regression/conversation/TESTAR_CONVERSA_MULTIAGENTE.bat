@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\..\..\..\.."
title Campanario - Behavioral E2E Multiagente

echo.
echo ========================================
echo  CAMPANARIO - CONVERSA MULTIAGENTE E2E
echo ========================================
echo.
echo Teste integrado no mesmo episodio: usuario + Morgana + Todd.
echo Mede complemento, discordancia util, referencia cruzada e ausencia de overtalk.
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
echo [INFO] Verificando dependencias...
uv sync
if errorlevel 1 goto :fail

echo.
echo [INFO] Rodando Behavioral E2E multiagente no fluxo real do ChatService...
echo [INFO] Banco temporario isolado; nenhuma conversa principal sera alterada.
echo.
uv run python -m campanario.e2e.behavioral --suite agent_integrated --no-open
set "RC=!ERRORLEVEL!"

if not "!RC!"=="2" if exist "test_reports\behavioral_e2e\latest.html" (
    start "" "test_reports\behavioral_e2e\latest.html"
    echo [OK] Relatorio integrado aberto no navegador.
)

if "!RC!"=="2" goto :fail
if "!RC!"=="1" echo [ATENCAO] Houve FAIL objetivo; revise o transcript e os checks.

echo.
echo Leia principalmente se o segundo agente acrescentou algo e se houve conversa real entre os tres.
pause
exit /b !RC!

:fail
echo.
echo O teste multiagente nao foi concluido.
pause
exit /b 2
