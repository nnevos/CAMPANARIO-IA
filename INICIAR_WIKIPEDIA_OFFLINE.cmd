@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
rem Fase 5 / Kiwix: passe um ZIM real ao kiwix-serve, nunca a pasta.
rem Se houver varios wikipedia_pt*.zim, use o nome de arquivo mais recente
rem em ordem descendente, como faz o leitor de ZIM do Campanario.
set "BASE=%~dp0..\CAMPANARIO-DATABASE"
set "ZIMDIR=%BASE%\zim"
set "TOOLSDIR=%BASE%\kiwix"
set "KIWIX="
set "ZIMFILE="

if not exist "%ZIMDIR%\" (
  echo ERRO: Pasta de ZIMs nao encontrada:
  echo   "%ZIMDIR%"
  goto :END
)

rem Localizar apenas arquivos .zim na raiz da pasta ZIM.
for /f "delims=" %%F in ('dir /b /a-d /o-n "%ZIMDIR%\wikipedia_pt*.zim" 2^>nul') do if not defined ZIMFILE set "ZIMFILE=%ZIMDIR%\%%F"
if not defined ZIMFILE (
  echo ERRO: Nao foi encontrado nenhum arquivo wikipedia_pt*.zim em:
  echo   "%ZIMDIR%"
  echo Coloque um arquivo ZIM completo nessa pasta, sem descompacta-lo.
  goto :END
)
if not exist "%ZIMFILE%" (
  echo ERRO: Arquivo ZIM selecionado nao existe:
  echo   "%ZIMFILE%"
  goto :END
)

if exist "%TOOLSDIR%\" (
  for /r "%TOOLSDIR%" %%F in (kiwix-serve.exe) do if not defined KIWIX set "KIWIX=%%~fF"
)
if not defined KIWIX (
  echo ERRO: kiwix-serve.exe nao encontrado em:
  echo   "%TOOLSDIR%"
  echo Extraia o pacote kiwix-tools nessa pasta, mantendo as DLLs.
  goto :END
)

echo Wikipedia offline: http://127.0.0.1:8181
echo Arquivo ZIM selecionado:
echo   "%ZIMFILE%"
echo Mantenha esta janela aberta enquanto usar o Campanario.
rem Executar na pasta do executavel para preservar a localizacao de DLLs.
for %%F in ("%KIWIX%") do pushd "%%~dpF"
"%KIWIX%" --address=127.0.0.1 --port=8181 --blockexternal "%ZIMFILE%"
set "RET=%ERRORLEVEL%"
popd
echo Kiwix terminou, codigo %RET%.
if not "%RET%"=="0" (
  echo Se o erro citar o arquivo .zim, confira se o download terminou
  echo e se o arquivo nao foi corrompido.
)
:END
pause
endlocal
