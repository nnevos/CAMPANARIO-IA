@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%~dp0..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe"
if not exist "%PY%" (
 echo ERRO: Python externo nao encontrado: "%PY%"
 goto :END
)
"%PY%" "tools\verificar_cellbit_offline.py"
:END
pause
endlocal
