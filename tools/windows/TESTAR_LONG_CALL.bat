@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\..\.."
title Campanario - Long Call Behavioral E2E

echo.
echo ========================================
echo  CAMPANARIO - LONG CALL BEHAVIORAL E2E
echo ========================================
echo.
echo Simula 3 calls textuais longas, 12 turnos cada.
echo Usuario + Morgana + Todd no mesmo episodio por roteiro.
echo Mede continuidade, retomada, protocolo social e latencia percebida.
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
echo [INFO] Rodando Long Call E2E. Este teste e deliberadamente demorado.
echo [INFO] 36 turnos em 3 episodios isolados; a memoria principal nao sera alterada.
echo [INFO] Latencia: TTFR, geracao por speaker, gap do segundo agente e total do turno.
echo.
uv run python -m campanario.e2e.behavioral --suite agent_long_call --no-open
set "RC=!ERRORLEVEL!"

if not "!RC!"=="2" if exist "test_reports\behavioral_e2e\latest.html" (
    start "" "test_reports\behavioral_e2e\latest.html"
    echo [OK] Relatorio Long Call aberto no navegador.
)

if "!RC!"=="2" goto :fail
if "!RC!"=="1" echo [ATENCAO] Houve FAIL objetivo; revise o transcript antes de calibrar personas.

echo.
echo Leia a conversa como uma call: continuidade, autoria, silencio, retomadas e ritmo importam tanto quanto os checks.
pause
exit /b !RC!

:fail
echo.
echo O Long Call E2E nao foi concluido.
pause
exit /b 2
