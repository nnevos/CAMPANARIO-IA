@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\..\.."
title Campanario - Comparar modelos

echo.
echo ========================================
echo       CAMPANARIO - MODEL BAKEOFF
echo ========================================
echo.
where uv >nul 2>&1 || (echo [ERRO] uv nao encontrado.& goto :fail)
where ollama >nul 2>&1 || (echo [ERRO] Ollama nao encontrado.& goto :fail)
echo Modelos instalados:
ollama list
echo.
set /p "MODELS=Digite os NAMEs separados por espaco (ex: llama3:latest qwen3:8b gemma3:4b): "
if not defined MODELS goto :fail
set /p "SEED=Seed para comparacao [424242]: "
if not defined SEED set "SEED=424242"
echo.
echo [INFO] Todos os modelos receberao a MESMA suite e o MESMO seed.
uv sync
if errorlevel 1 goto :fail
uv run python -m campanario.e2e.model_bakeoff --seed !SEED! --suite standard !MODELS!
if errorlevel 2 goto :fail
echo.
echo [OK] Comparacao salva em test_reports\model_bakeoff\comparison.md
start "" "test_reports\model_bakeoff\comparison.md"
pause
exit /b 0
:fail
echo.
echo A comparacao nao foi concluida.
pause
exit /b 1
