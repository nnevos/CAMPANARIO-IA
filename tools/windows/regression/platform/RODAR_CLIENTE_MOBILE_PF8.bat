@echo off
setlocal
cd /d "%~dp0\..\..\..\.."
echo [Campanario] Cliente mobile minimo PF8 (prova local; nao e app Android/iOS)
uv run campanario-mobile-proof %*
endlocal
