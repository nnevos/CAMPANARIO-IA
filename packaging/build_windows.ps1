$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($env:OS -ne 'Windows_NT') { throw 'Build desktop exige Windows.' }
python -m PyInstaller --clean --noconfirm packaging/desktop.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller falhou.' }
Copy-Item .env.example dist/Campanario/.env.example
Copy-Item LEIA-ME-V08.md dist/Campanario/LEIA-ME-V08.md
New-Item -ItemType Directory -Force dist/Campanario/docs | Out-Null
Copy-Item -Recurse docs/current dist/Campanario/docs/current
Compress-Archive -Force -Path dist/Campanario -DestinationPath dist/Campanario-Windows-0.8.0.zip
Get-FileHash -Algorithm SHA256 dist/Campanario-Windows-0.8.0.zip | Format-List
