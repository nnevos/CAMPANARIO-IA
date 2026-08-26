@echo off
setlocal
cd /d "%~dp0\..\.."
echo [Campanario] F5c - Host Voice
uv run campanario-host-voice
if errorlevel 1 echo [Campanario] Host Voice terminou com erro. Rode tools\windows\PREPARAR_VOZ_F5C.bat e reinicie o Campanario.
pause
