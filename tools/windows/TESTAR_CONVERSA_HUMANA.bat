@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\..\.."
title Campanario - Conversa Humana Baseline

echo.
echo ========================================
echo  CAMPANARIO - CONVERSA HUMANA BASELINE
echo ========================================
echo.
echo Conversas cotidianas persistentes: se conhecer, historias, humor,
echo mudanca de assunto, callbacks, discordancia leve e sala compartilhada.
echo Gera tambem revisao cega Todd x Morgana.
echo.
if not exist ".env" copy /y ".env.example" ".env" >nul
where uv >nul 2>&1 || (echo [ERRO] uv nao encontrado.& pause & exit /b 2)
where ollama >nul 2>&1 || (echo [ERRO] Ollama nao encontrado.& pause & exit /b 2)
ollama list >nul 2>&1 || start "Ollama" /min ollama serve
uv sync
if errorlevel 1 exit /b 2

echo [INFO] Rodando baseline completo. Para um smoke test, use --suite agent_human_quick manualmente.
uv run python -m campanario.e2e.behavioral --suite agent_human_baseline --no-open
set "RC=!ERRORLEVEL!"
if not "!RC!"=="2" if exist "test_reports\behavioral_e2e\latest.html" start "" "test_reports\behavioral_e2e\latest.html"
if not "!RC!"=="2" if exist "test_reports\behavioral_e2e\latest.blind.md" start "" "test_reports\behavioral_e2e\latest.blind.md"
echo.
echo Leia primeiro o arquivo blind: tente identificar Todd/Morgana sem olhar o gabarito.
echo Depois revise naturalidade, continuidade, curiosidade proporcional, ausencia de palestra e callbacks.
pause
exit /b !RC!
