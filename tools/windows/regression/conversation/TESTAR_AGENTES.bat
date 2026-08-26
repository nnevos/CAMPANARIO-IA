@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\..\..\.."
title Campanario - Teste de Agentes

echo.
echo ========================================
echo    CAMPANARIO - TESTE DE ARQUITETURA DE AGENTES
echo ========================================
echo.

if not exist ".env" copy /y ".env.example" ".env" >nul

uv run python -m campanario.e2e.behavioral --suite agents
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
    echo [OK] Suite de agentes concluida sem FAIL automatico.
) else (
    echo [ATENCAO] A suite de agentes encontrou FAIL ou erro de execucao.
)
echo O relatorio agora identifica Morgana/Todd em vez de rotular tudo como Campanario.
echo Revise o relatorio humano antes de ajustar as personas.
pause
exit /b %RC%
