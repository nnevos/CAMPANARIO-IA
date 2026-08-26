@echo off
setlocal
cd /d "%~dp0\..\..\..\.."
echo [Campanario] PF8 Mobile Readiness - testes focados
python -m pytest -q tests/test_mobile_readiness.py tests/test_client_independent_sessions.py tests/test_permission_trust_layer.py tests/test_device_registry.py tests/test_capability_registry.py tests/test_realtime_gateway.py
endlocal
