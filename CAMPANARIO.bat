@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Campanario

:menu
cls
echo.
echo ========================================
echo              CAMPANARIO
echo ========================================
echo.
echo  [1] Iniciar Campanario
echo  [2] Iniciar voz ^(F5c.1^)
echo  [3] Diagnosticar voz
echo  [4] Parear este PC para voz
echo  [5] Testar F5 voz/realtime
echo  [6] Long Call Behavioral E2E
echo  [7] Abrir ultimo relatorio
echo  [8] Trocar modelo
echo  [9] Comparar modelos
echo [10] Abrir manual
echo [11] Runtime headless ^(desenvolvimento^)
echo [12] Sair
echo.
set /p "OP=Escolha uma opcao: "

if "%OP%"=="1" call "tools\windows\INICIAR_CAMPANARIO.bat"
if "%OP%"=="2" call "tools\windows\INICIAR_VOZ_HOST_F5C.bat"
if "%OP%"=="3" call "tools\windows\DIAGNOSTICO_VOZ_F5C.bat"
if "%OP%"=="4" call "tools\windows\PAREAR_VOZ_HOST_F5C.bat"
if "%OP%"=="5" call "tools\windows\TESTAR_VOZ_F5C.bat"
if "%OP%"=="6" call "tools\windows\TESTAR_LONG_CALL.bat"
if "%OP%"=="7" call "tools\windows\CONSULTAR_ULTIMO_TESTE.bat"
if "%OP%"=="8" call "tools\windows\TROCAR_MODELO.bat"
if "%OP%"=="9" call "tools\windows\COMPARAR_MODELOS.bat"
if "%OP%"=="10" call "tools\windows\ABRIR_MANUAL.bat"
if "%OP%"=="11" call "tools\windows\INICIAR_RUNTIME_HEADLESS.bat"
if "%OP%"=="12" exit /b 0
if not "%OP%"=="1" if not "%OP%"=="2" if not "%OP%"=="3" if not "%OP%"=="4" if not "%OP%"=="5" if not "%OP%"=="6" if not "%OP%"=="7" if not "%OP%"=="8" if not "%OP%"=="9" if not "%OP%"=="10" if not "%OP%"=="11" if not "%OP%"=="12" (
  echo.
  echo Opcao invalida.
  timeout /t 1 /nobreak >nul
)
goto :menu
