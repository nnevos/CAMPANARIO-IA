@echo off
setlocal
cd /d "%~dp0apps\mobile\android"
where gradle >nul 2>&1
if errorlevel 1 (
 echo Gradle nao encontrado. Abra apps\mobile\android no Android Studio,
 echo instale Android SDK 35 e use Build ^> Build APK(s).
 echo Nao existe APK pre-compilado neste pacote.
 pause
 exit /b 2
)
gradle --no-daemon assembleDebug
if errorlevel 1 (
 echo Build falhou. Verifique Android SDK 35, JDK 17, Gradle 8.11.1 e logs.
 pause
 exit /b 1
)
echo APK debug: apps\mobile\android\app\build\outputs\apk\debug\app-debug.apk
pause
