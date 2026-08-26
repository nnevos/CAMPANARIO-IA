@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."
title Campanario - Fabrica RenPy
set "CAMPANARIO_PORT=8000"

set "FOUND="
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr /R /C:":%CAMPANARIO_PORT% .*LISTENING"') do if not defined FOUND set "FOUND=%%P"
if not defined FOUND (
    echo [INFO] Campanario nao esta rodando. Iniciando...
    start "Campanario" "%~dp0INICIAR_CAMPANARIO.bat"
    for /l %%I in (1,1,20) do (
        timeout /t 1 /nobreak >nul
        for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr /R /C:":%CAMPANARIO_PORT% .*LISTENING"') do if not defined FOUND set "FOUND=%%P"
        if defined FOUND goto :open
    )
    echo [ERRO] Campanario nao respondeu na porta %CAMPANARIO_PORT%.
    pause
    exit /b 1
)

:open
start "" "http://127.0.0.1:%CAMPANARIO_PORT%/renpy-factory?build=renpy-quality-ui-fix"
endlocal
