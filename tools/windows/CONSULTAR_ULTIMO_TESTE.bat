@echo off
setlocal
cd /d "%~dp0\..\.."
if not exist "test_reports\behavioral_e2e\latest.html" (
    echo Nenhum relatorio comportamental encontrado.
    echo Execute TESTAR_COMPORTAMENTO.bat primeiro.
    pause
    exit /b 1
)
start "" "test_reports\behavioral_e2e\latest.html"
exit /b 0
