@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\..\..\.."
title Campanario - Personalidades Todd e Morgana

echo.
echo ========================================
echo  CAMPANARIO - PERSONALIDADE DOS AGENTES
echo ========================================
echo.
echo Bateria: 8 eixos x Todd/Morgana = 16 cenarios.
echo O relatorio final mostra BATE/REVISAR por eixo antes do transcript.
echo.
if not exist ".env" copy /y ".env.example" ".env" >nul
uv run python -m campanario.e2e.behavioral --suite agent_personality --no-open
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [OK] Suite de personalidade concluida sem FAIL automatico.
) else (
  echo [ATENCAO] A suite encontrou FAIL ou erro de execucao.
)

if not "%RC%"=="2" if exist "test_reports\behavioral_e2e\latest.html" (
  start "" "test_reports\behavioral_e2e\latest.html"
  echo [OK] Ultimo relatorio de personalidade aberto no navegador.
)

echo Leia a Analise conceitual BATE/REVISAR e depois compare os transcripts pareados.
pause
exit /b %RC%
