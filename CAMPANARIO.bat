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
echo  [2] Abrir manual
echo  [3] Trocar modelo
echo  [4] Teste comportamental standard
echo  [5] Mega teste comportamental
echo  [6] Comparar modelos
echo  [7] Testar arquitetura de agentes
echo  [8] Testar personalidades Todd/Morgana
echo  [9] Mega teste de personalidades
echo [10] Abrir ultimo relatorio
echo [11] Sair
echo.
set /p "OP=Escolha uma opcao: "

if "%OP%"=="1" goto :start_app
if "%OP%"=="2" goto :manual
if "%OP%"=="3" goto :model
if "%OP%"=="4" goto :standard
if "%OP%"=="5" goto :mega
if "%OP%"=="6" goto :bakeoff
if "%OP%"=="7" goto :agents
if "%OP%"=="8" goto :personality
if "%OP%"=="9" goto :personality_mega
if "%OP%"=="10" goto :report
if "%OP%"=="11" exit /b 0

echo.
echo Opcao invalida.
timeout /t 1 /nobreak >nul
goto :menu

:start_app
call "tools\windows\INICIAR_CAMPANARIO.bat"
goto :menu
:manual
call "tools\windows\ABRIR_MANUAL.bat"
goto :menu
:model
call "tools\windows\TROCAR_MODELO.bat"
goto :menu
:standard
call "tools\windows\TESTAR_COMPORTAMENTO.bat"
goto :menu
:mega
call "tools\windows\TESTAR_COMPORTAMENTO_MEGA.bat"
goto :menu
:bakeoff
call "tools\windows\COMPARAR_MODELOS.bat"
goto :menu
:agents
call "tools\windows\TESTAR_AGENTES.bat"
goto :menu
:personality
call "tools\windows\TESTAR_PERSONALIDADES.bat"
goto :menu
:personality_mega
call "tools\windows\TESTAR_PERSONALIDADES_MEGA.bat"
goto :menu
:report
call "tools\windows\CONSULTAR_ULTIMO_TESTE.bat"
goto :menu
