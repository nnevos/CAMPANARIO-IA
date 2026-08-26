@echo off
setlocal
cd /d "%~dp0\..\..\..\.."
echo.
echo Campanario - PF3 Realtime/API Gateway
echo ======================================
echo Testando API v1, WebSocket, replay/reconexao e compatibilidade legado...
echo.
uv run pytest -q tests/test_realtime_gateway.py tests/test_api_chat.py tests/test_event_bus.py tests/test_runtime_foundation.py tests/test_runtime_hosting.py tests/test_health.py
set EXIT_CODE=%ERRORLEVEL%
echo.
if %EXIT_CODE%==0 (
  echo PF3 OK.
) else (
  echo PF3 FALHOU. Codigo %EXIT_CODE%.
)
exit /b %EXIT_CODE%
