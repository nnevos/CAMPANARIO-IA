@echo off
setlocal
cd /d "%~dp0\..\.."
python -m pytest -q tests/test_realtime_presence_f5.py tests/test_voice_call_readiness.py tests/test_mobile_readiness.py tests/test_client_independent_sessions.py
endlocal
