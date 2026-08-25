@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."
title Campanario - Personalidades Todd e Morgana

echo.
echo ========================================
echo  CAMPANARIO - PERSONALIDADE DOS AGENTES
echo ========================================
echo.
if not exist ".env" copy /y ".env.example" ".env" >nul
uv run python -m campanario.e2e.behavioral --suite agent_personality
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [OK] Suite de personalidade concluida sem FAIL automatico.
) else (
  echo [ATENCAO] A suite encontrou FAIL ou erro de execucao.
)
echo Compare Todd e Morgana no mesmo seed. O gate automatico cobre invariantes; estilo fino exige revisao humana.
pause
exit /b %RC%
