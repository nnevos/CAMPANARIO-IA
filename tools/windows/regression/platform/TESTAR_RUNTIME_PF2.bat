@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\..\..\.."
title Campanario - Teste PF2 Event Bus

echo.
echo ========================================
echo          TESTE PF2 EVENT BUS
echo ========================================
echo.

where uv >nul 2>&1
if errorlevel 1 (
  echo [ERRO] uv nao encontrado.
  exit /b 1
)

uv run pytest -q tests/test_event_bus.py tests/test_runtime_foundation.py tests/test_runtime_hosting.py tests/test_chat_service.py tests/test_api_chat.py tests/test_health.py
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" echo [OK] PF2 contratos, ordem, provenance e replay verdes.
if not "%RC%"=="0" echo [ERRO] PF2 apresentou falhas.
exit /b %RC%
