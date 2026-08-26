@echo off
setlocal
cd /d "%~dp0\..\..\..\.."
echo [Campanario] PF4 Device Registry - contratos, persistencia, reconnect e provenance
uv run pytest -q tests/test_device_registry.py tests/test_event_bus.py tests/test_realtime_gateway.py tests/test_runtime_foundation.py
pause
