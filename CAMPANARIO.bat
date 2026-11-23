@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHON=%ROOT%..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
 echo ERRO: Python externo ausente: "%PYTHON%"
 echo O Campanario usa CAMPANARIO-PYTHON como pasta irma de CAMPANARIO-IA.
 pause
 exit /b 2
)
set "PYTHONPATH=%ROOT%src;%PYTHONPATH%"
cd /d "%ROOT%"
echo CAMPANARIO - inicializando pelo Python externo existente.
"%PYTHON%" -m campanario.app.desktop
if errorlevel 1 (
 echo.
 echo Erro de inicializacao acima. Nenhum ambiente foi reinstalado.
 pause
 exit /b 1
)
exit /b 0
