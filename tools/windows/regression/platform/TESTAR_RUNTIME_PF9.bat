@echo off
setlocal
cd /d "%~dp0\..\..\..\.."
echo [Campanario] PF9 Voice / Call Readiness
uv run pytest -q tests/test_voice_call_readiness.py tests/test_realtime_gateway.py tests/test_client_independent_sessions.py tests/test_mobile_readiness.py
exit /b %ERRORLEVEL%
