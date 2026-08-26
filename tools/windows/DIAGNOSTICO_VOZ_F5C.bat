@echo off
setlocal
cd /d "%~dp0\..\.."
echo [Campanario] F5c - diagnostico de voz do host
uv run --extra voice-host campanario-host-voice --diagnose
echo.
echo Dispositivos de audio detectados:
uv run --extra voice-host campanario-host-voice --list-audio-devices
pause
