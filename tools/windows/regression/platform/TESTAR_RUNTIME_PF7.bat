@echo off
setlocal
cd /d "%~dp0\..\..\..\.."
python -m pytest -q tests/test_client_independent_sessions.py tests/test_realtime_gateway.py tests/test_permission_trust_layer.py tests/test_capability_registry.py tests/test_device_registry.py tests/test_event_bus.py
endlocal
