@echo off
setlocal
cd /d "%~dp0\..\..\..\.."
echo Campanario - F3 Platform Foundation closure
python -m pytest -q tests/test_runtime_telemetry.py tests/test_platform_foundation_closure.py tests/test_realtime_gateway.py tests/test_mobile_readiness.py tests/test_voice_call_readiness.py
if errorlevel 1 exit /b 1
echo F3 closure PASS.
endlocal
