@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."
title Campanario Runtime Headless - PF1b

echo.
echo ========================================
echo       CAMPANARIO RUNTIME - HEADLESS
echo ========================================
echo.
echo Este host prova o runtime sem Web/FastAPI.
echo Nao execute junto com a Web esperando compartilhamento entre processos;
echo isso so sera suportado depois do Realtime Gateway.
echo.

where uv >nul 2>&1
if errorlevel 1 (
  echo [ERRO] uv nao encontrado.
  exit /b 1
)

uv run alembic upgrade head
if errorlevel 1 exit /b 1

uv run campanario-runtime
endlocal
