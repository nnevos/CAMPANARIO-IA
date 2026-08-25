@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."
title Campanario - Mega Teste de Personalidade

echo.
echo ========================================
echo CAMPANARIO - MEGA TESTE PERSONALIDADES
echo ========================================
echo.
if not exist ".env" copy /y ".env.example" ".env" >nul
uv run python -m campanario.e2e.behavioral --suite agent_mega
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [OK] Mega suite de personalidade concluida sem FAIL automatico.
) else (
  echo [ATENCAO] A mega suite encontrou FAIL ou erro de execucao.
)
echo Use o transcript para revisar consistencia, diferenca real e ausencia de caricatura.
pause
exit /b %RC%
