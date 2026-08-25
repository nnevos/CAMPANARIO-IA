@echo off
setlocal
cd /d "%~dp0\..\.."
if not exist "docs\manual\README.md" (
    echo Manual nao encontrado em docs\manual\README.md
    pause
    exit /b 1
)
start "" notepad "docs\manual\README.md"
exit /b 0
