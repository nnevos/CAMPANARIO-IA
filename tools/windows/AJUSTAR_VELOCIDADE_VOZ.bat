@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul

echo ========================================
echo Campanario - Velocidade da voz ^(SAPI^)
echo ========================================
echo.
echo Escolha um preset para Todd e Morgana:
echo   1 - Calma       ^(Todd 1 / Morgana 0^)
echo   2 - Natural     ^(Todd 3 / Morgana 2^)
echo   3 - Rapida      ^(Todd 5 / Morgana 4^)
echo   4 - Muito rapida^(Todd 7 / Morgana 6^)
echo   5 - Turbo       ^(Todd 9 / Morgana 8^)
echo.
set /p SPEED=Opcao [1-5]: 

if "%SPEED%"=="1" set "TODD_RATE=1"& set "MORGANA_RATE=0"& goto :apply
if "%SPEED%"=="2" set "TODD_RATE=3"& set "MORGANA_RATE=2"& goto :apply
if "%SPEED%"=="3" set "TODD_RATE=5"& set "MORGANA_RATE=4"& goto :apply
if "%SPEED%"=="4" set "TODD_RATE=7"& set "MORGANA_RATE=6"& goto :apply
if "%SPEED%"=="5" set "TODD_RATE=9"& set "MORGANA_RATE=8"& goto :apply

echo [ERRO] Opcao invalida.
exit /b 1

:apply
setx CAMPANARIO_VOICE_TODD_RATE "%TODD_RATE%" >nul
if errorlevel 1 goto :fail
setx CAMPANARIO_VOICE_MORGANA_RATE "%MORGANA_RATE%" >nul
if errorlevel 1 goto :fail

echo.
echo [OK] Velocidade salva para as proximas execucoes:
echo      Todd    = %TODD_RATE%
echo      Morgana = %MORGANA_RATE%
echo.
echo Feche qualquer Campanario que esteja rodando e inicie novamente.
echo Para ajuste manual, use valores de -10 a +10 nas variaveis:
echo   CAMPANARIO_VOICE_TODD_RATE
echo   CAMPANARIO_VOICE_MORGANA_RATE
exit /b 0

:fail
echo [ERRO] Nao foi possivel salvar a configuracao com SETX.
exit /b 1
