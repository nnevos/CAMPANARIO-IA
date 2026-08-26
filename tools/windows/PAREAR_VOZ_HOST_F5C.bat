@echo off
setlocal
cd /d "%~dp0\..\.."
echo [Campanario] F5c - parear este PC como dispositivo de voz
uv run --extra voice-host campanario-host-voice --pair
pause
