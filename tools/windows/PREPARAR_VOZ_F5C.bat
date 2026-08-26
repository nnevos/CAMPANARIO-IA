@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\..\.."
title Campanario - Preparar Voz

echo.
echo ========================================
echo     CAMPANARIO - PREPARAR VOZ LOCAL
echo ========================================
echo.

if not exist "voice\whisper-cli.exe" (
  echo [ERRO] Nao encontrei voice\whisper-cli.exe.
  echo Copie a pasta do whisper.cpp para voice\ antes de continuar.
  echo O arquivo esperado e: %CD%\voice\whisper-cli.exe
  goto :fail
)

echo [OK] whisper-cli.exe encontrado.
set "MODELS_DIR=%CAMPANARIO_VOICE_MODELS_DIR%"
if not defined MODELS_DIR if defined LOCALAPPDATA set "MODELS_DIR=%LOCALAPPDATA%\Campanario\models"
if not defined MODELS_DIR set "MODELS_DIR=%USERPROFILE%\.campanario\models"
if not exist "!MODELS_DIR!" mkdir "!MODELS_DIR!"
set "MODEL=!MODELS_DIR!\ggml-small.bin"
if exist "!MODEL!" goto :model_ok

echo [INFO] Modelo multilingue pt-BR nao encontrado.
echo [INFO] Instalando fora do projeto em: !MODELS_DIR!
echo [INFO] Baixando ggml-small.bin oficial do projeto whisper.cpp...
where curl >nul 2>&1
if errorlevel 1 (
  echo [ERRO] curl nao esta disponivel neste Windows.
  echo Baixe manualmente ggml-small.bin do repositorio ggerganov/whisper.cpp no Hugging Face
  echo e salve em: !MODEL!
  goto :fail
)
curl.exe -L --fail --retry 3 --output "!MODEL!.part" "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
if errorlevel 1 (
  del /q "!MODEL!.part" >nul 2>&1
  echo [ERRO] Falha ao baixar o modelo.
  goto :fail
)
move /y "!MODEL!.part" "!MODEL!" >nul

:model_ok
for %%F in ("!MODEL!") do set "MODEL_SIZE=%%~zF"
if !MODEL_SIZE! LSS 100000000 (
  echo [ERRO] O modelo parece incompleto ^(!MODEL_SIZE! bytes^).
  echo Apague !MODEL! e rode este arquivo novamente.
  goto :fail
)
echo [OK] Modelo multilingue compartilhado: !MODEL!
echo [INFO] Esse arquivo fica fora do ZIP/projeto e pode ser reutilizado entre versoes.
echo.
echo [PRONTO] Agora feche qualquer Campanario aberto e rode:
echo          tools\windows\INICIAR_CAMPANARIO.bat
echo Depois, em outro CMD:
echo          tools\windows\INICIAR_VOZ_HOST_F5C.bat
echo.
pause
exit /b 0

:fail
echo.
echo Preparacao incompleta. Nada sera iniciado ate a voz estar pronta.
pause
exit /b 1
