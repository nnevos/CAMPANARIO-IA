@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."
title Campanario - Diagnostico de latencia
where uv >nul 2>&1
if errorlevel 1 (
 echo [ERRO] Instale uv pelo site https://docs.astral.sh/uv/
 pause
 exit /b 1
)
echo Medindo Ollama local sem os prompts do Campanario...
uv run --python 3.12 python tools\diagnostics\medir_ollama.py qwen3.5:9b
pause
