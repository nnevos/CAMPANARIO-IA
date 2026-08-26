@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\..\..\.."
title Campanario - Teste PF1 Runtime

echo.
echo ========================================
echo       TESTE PF1 RUNTIME FOUNDATION
echo ========================================
echo.

where uv >nul 2>&1
if errorlevel 1 (
  echo [ERRO] uv nao encontrado.
  exit /b 1
)

uv run pytest -q tests/test_runtime_foundation.py tests/test_runtime_hosting.py tests/test_api_chat.py tests/test_health.py
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" echo [OK] PF1 runtime boundary/lifecycle verde.
if not "%RC%"=="0" echo [ERRO] PF1 apresentou falhas.
exit /b %RC%
