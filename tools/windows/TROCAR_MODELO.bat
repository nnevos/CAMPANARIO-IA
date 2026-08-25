@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\..\.."
title Campanario - Trocar modelo

echo.
echo ========================================
echo        CAMPANARIO - TROCAR MODELO
echo ========================================
echo.

where ollama >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Ollama nao encontrado.
    goto :fail
)
if not exist ".env" copy /y ".env.example" ".env" >nul

echo Modelos instalados no Ollama:
echo.
ollama list
echo.
set /p "NEW_MODEL=Digite exatamente o NAME do modelo desejado: "
if not defined NEW_MODEL goto :fail

ollama show "%NEW_MODEL%" >nul 2>&1
if errorlevel 1 (
    echo [ERRO] O modelo "%NEW_MODEL%" nao foi encontrado localmente.
    echo Use: ollama pull NOME_DO_MODELO
    goto :fail
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$p='.env'; $c=Get-Content $p -Raw; if($c -match '(?m)^CAMPANARIO_MODEL_NAME='){ $c=[regex]::Replace($c,'(?m)^CAMPANARIO_MODEL_NAME=.*$','CAMPANARIO_MODEL_NAME=%NEW_MODEL%') } else { $c += [Environment]::NewLine + 'CAMPANARIO_MODEL_NAME=%NEW_MODEL%' + [Environment]::NewLine }; Set-Content -Path $p -Value $c -Encoding ASCII"
if errorlevel 1 goto :fail

echo.
echo [OK] Modelo configurado: %NEW_MODEL%
echo Reinicie o Campanario para aplicar a troca.
echo O comportamento, memoria, pipeline e testes permanecem os mesmos.
echo.
pause
exit /b 0

:fail
echo.
echo Nenhuma alteracao foi aplicada.
pause
exit /b 1
