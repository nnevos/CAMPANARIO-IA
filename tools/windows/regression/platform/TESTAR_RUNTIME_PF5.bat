@echo off
setlocal
cd /d "%~dp0\..\..\..\.."
echo [Campanario] PF5 Capability / Tool Registry
python -m pytest -q tests/test_capability_registry.py tests/test_device_registry.py tests/test_event_bus.py tests/test_runtime_foundation.py tests/test_realtime_gateway.py
if errorlevel 1 exit /b 1
echo.
echo PF5 OK.
endlocal
