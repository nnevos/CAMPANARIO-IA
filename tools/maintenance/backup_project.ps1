param(
    [string]$Destination = "$HOME\Documents\CampanarioBackups"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupRoot = Join-Path $Destination "Campanario-$Timestamp"
$CodeTarget = Join-Path $BackupRoot "project"
$DataTarget = Join-Path $BackupRoot "app-data"

New-Item -ItemType Directory -Force -Path $CodeTarget | Out-Null
New-Item -ItemType Directory -Force -Path $DataTarget | Out-Null

Write-Host "Backing up project from $ProjectRoot"

# Copy project while excluding transient/secrets-heavy folders/files.
robocopy $ProjectRoot $CodeTarget /E /XD ".venv" ".git" "__pycache__" ".pytest_cache" ".ruff_cache" /XF ".env" "*.pyc" | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy project failed with code $LASTEXITCODE" }

$AppData = Join-Path $env:LOCALAPPDATA "Campanario"
if (Test-Path $AppData) {
    Write-Host "Backing up Campanario app data from $AppData"
    robocopy $AppData $DataTarget /E | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy app data failed with code $LASTEXITCODE" }
} else {
    Write-Warning "Campanario app-data directory not found at $AppData"
}

$ZipPath = "$BackupRoot.zip"
Compress-Archive -Path "$BackupRoot\*" -DestinationPath $ZipPath -Force
Remove-Item -Recurse -Force $BackupRoot

Write-Host "Backup created: $ZipPath"
Write-Host "Note: .env was intentionally excluded. Keep secrets/configuration separately and securely."
