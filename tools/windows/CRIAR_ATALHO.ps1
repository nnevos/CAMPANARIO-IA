$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Campanario.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:WINDIR "System32\wscript.exe"
$shortcut.Arguments = '"' + (Join-Path $root "CAMPANARIO.vbs") + '"'
$shortcut.WorkingDirectory = $root
$shortcut.Description = "Campanario - ambiente de inteligencia pessoal"
$icon = Join-Path $root "packaging\campanario.ico"
if (Test-Path $icon) { $shortcut.IconLocation = $icon }
$shortcut.Save()
