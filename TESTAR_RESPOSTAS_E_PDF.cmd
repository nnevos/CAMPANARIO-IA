@echo off
setlocal
set "PROJECT=%~dp0"
set "PYTHON=%PROJECT%..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo ERRO: Python externo nao encontrado em "%PYTHON%".
  echo O projeto deve estar ao lado de CAMPANARIO-PYTHON.
  pause
  exit /b 1
)
pushd "%PROJECT%"
"%PYTHON%" -m pytest -q tests\test_resposta_conversacional_com_evidencia.py tests\test_upload_pdf_grande_stream.py
set "STATUS=%ERRORLEVEL%"
popd
echo.
if "%STATUS%"=="0" (echo OK: testes novos de respostas e PDF passaram.) else (echo FALHOU: confira a mensagem acima.)
pause
exit /b %STATUS%
