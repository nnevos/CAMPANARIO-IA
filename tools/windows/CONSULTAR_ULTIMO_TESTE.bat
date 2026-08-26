@echo off
setlocal
cd /d "%~dp0\..\.."
if not exist "test_reports\behavioral_e2e\latest.html" (
    echo Nenhum relatorio comportamental encontrado.
    echo Execute uma suite de teste primeiro (por exemplo TESTAR_LONG_CALL.bat).
    pause
    exit /b 1
)
start "" "test_reports\behavioral_e2e\latest.html"
exit /b 0
