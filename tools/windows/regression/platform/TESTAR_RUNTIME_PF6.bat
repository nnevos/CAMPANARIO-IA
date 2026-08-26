@echo off
setlocal
cd /d "%~dp0\..\..\..\.."
python -m pytest -q tests/test_permission_trust_layer.py tests/test_capability_registry.py tests/test_device_registry.py tests/test_realtime_gateway.py
endlocal
