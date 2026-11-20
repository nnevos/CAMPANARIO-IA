@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%~dp0..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe"
if not exist "%PY%" (
 echo ERRO: Python unificado ausente em "%PY%"
 goto :END
)
"%PY%" "tools\verificar_wikipedia_offline.py"
:END
pause
endlocal
