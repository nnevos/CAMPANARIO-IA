@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\..\..\.."
title Campanario - Mega Teste de Personalidade

echo.
echo ========================================
echo CAMPANARIO - MEGA TESTE PERSONALIDADES
echo ========================================
echo.
if not exist ".env" copy /y ".env.example" ".env" >nul
uv run python -m campanario.e2e.behavioral --suite agent_mega --no-open
set "RC=%ERRORLEVEL%"

if not "%RC%"=="2" if exist "test_reports\behavioral_e2e\latest.html" (
  start "" "test_reports\behavioral_e2e\latest.html"
  echo [OK] Ultimo relatorio de personalidade aberto no navegador.
)
echo.
if "%RC%"=="0" (
  echo [OK] Mega suite de personalidade concluida sem FAIL automatico.
) else (
  echo [ATENCAO] A mega suite encontrou FAIL ou erro de execucao.
)
echo Use o transcript para revisar consistencia, diferenca real e ausencia de caricatura.
pause
exit /b %RC%
