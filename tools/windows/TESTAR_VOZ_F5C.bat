@echo off
setlocal
cd /d "%~dp0\..\.."
echo [Campanario] F5c Host Voice Integration
uv run pytest -q tests/test_host_voice_f5c.py tests/test_voice_media_f5b.py tests/test_realtime_presence_f5.py tests/test_voice_call_readiness.py
exit /b %ERRORLEVEL%
