@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."
title Campanario - Memoria Semantica

echo.
echo ========================================
echo        MEMORIA SEMANTICA - G2
echo ========================================
echo.
echo Modelo recomendado: embeddinggemma ^(aprox. 622 MB^)
echo Uso: vetores locais para recuperar memorias do SQLite.
echo Nenhuma conversa sera enviada para nuvem por esta ferramenta.
echo.
where ollama >nul 2>&1
if errorlevel 1 (
 echo [ERRO] Ollama nao encontrado no PATH.
 goto :fim
)
ollama show embeddinggemma >nul 2>&1
if errorlevel 1 (
 echo Baixando embeddinggemma para o Ollama local...
 ollama pull embeddinggemma
 if errorlevel 1 goto :falha
) else (
 echo [OK] embeddinggemma instalado.
)
where uv >nul 2>&1
if errorlevel 1 (
 echo [ATENCAO] uv nao encontrado. Teste manualmente mais tarde.
 goto :fim
)
echo.
echo Executando diagnostico com 4 memorias sinteticas...
uv run python tools\maintenance\DIAGNOSTICAR_BUSCA_SEMANTICA.py
if errorlevel 1 goto :falha
echo [OK] Diagnostico finalizado.
goto :fim
:falha
echo [ATENCAO] Nao foi possivel validar a busca semantica.
echo Confira Ollama, configuracao de modelo e logs.
:fim
echo.
pause
endlocal
