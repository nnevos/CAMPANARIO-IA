#Requires -Version 5.1
<#
Campanario V8 - installer for the IA repository ONLY.
Dry run by default. Never writes to DATA/PYTHON repositories or .env.
All incoming source file hashes must match manifest-v8.json.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [string]$PatchRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$project = [System.IO.Path]::GetFullPath($ProjectRoot).TrimEnd([char[]]@([char]92,[char]47))
$patch = [System.IO.Path]::GetFullPath($PatchRoot).TrimEnd([char[]]@([char]92,[char]47))
$manifestPath = Join-Path $patch 'manifest-v8.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw 'Manifesto ausente na raiz do patch V8.'
}
if (-not (Test-Path -LiteralPath (Join-Path $project 'pyproject.toml') -PathType Leaf)) {
    throw 'A pasta indicada não parece ser CAMPANARIO-IA (pyproject.toml ausente).'
}
if ((Split-Path $project -Leaf) -ne 'CAMPANARIO-IA') {
    throw 'ProjectRoot deve apontar para a pasta CAMPANARIO-IA.'
}
if ($project -eq $patch) { throw 'Extraia o patch FORA de CAMPANARIO-IA.' }
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.version -ne '8.0.1' -or -not $manifest.files) { throw 'Manifesto V8 desconhecido.' }
$sourceFiles = @()
foreach ($item in $manifest.files) {
    $relative = [string]$item.path
    if (($relative -notmatch '^[A-Za-z0-9_./-]+$') -or
        $relative.StartsWith('/') -or $relative.Contains('..') -or
        $relative -match '(^|/)(\.env|\.git|\.venv|vozes|data)(/|$)') {
        throw "Caminho não permitido no manifesto: $relative"
    }
    $relNative = $relative.Replace('/', [string][System.IO.Path]::DirectorySeparatorChar)
    $source = Join-Path $patch $relNative
    $destination = Join-Path $project $relNative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Arquivo do patch ausente: $relative"
    }
    $calculated = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($calculated -ne ([string]$item.sha256).ToLowerInvariant()) {
        throw "Hash divergente no patch: $relative"
    }
    $sourceFiles += [pscustomobject]@{ Relative = $relative; Source = $source; Destination = $destination }
}
Write-Host ("Manifesto íntegro: {0} arquivos / somente CAMPANARIO-IA" -f $sourceFiles.Count)
foreach ($file in $sourceFiles) {
    Write-Host ("{0}: {1}" -f $(if (Test-Path -LiteralPath $file.Destination) {'ATUALIZAR'} else {'ADICIONAR'}), $file.Relative)
}
$githubRoot = Split-Path $project -Parent
foreach ($sibling in @('CAMPANARIO-PYTHON','CAMPANARIO-DATABASE')) {
    if (-not (Test-Path -LiteralPath (Join-Path $githubRoot $sibling) -PathType Container)) {
        Write-Warning "Pasta irmã $sibling não localizada; não será criada nem modificada."
    }
}
if (-not $Apply) {
    Write-Host 'SIMULAÇÃO: nenhum arquivo foi escrito. Use -Apply para aplicar com backup.'
    exit 0
}
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$backup = Join-Path $githubRoot ('CAMPANARIO-IA_BACKUP_ANTES_V8_' + $stamp)
New-Item -ItemType Directory -Path $backup -ErrorAction Stop | Out-Null
$replaced = @()
try {
    # Prepare complete backup before altering any original source.
    foreach ($file in $sourceFiles) {
        if (Test-Path -LiteralPath $file.Destination -PathType Leaf) {
            $oldBackup = Join-Path $backup ($file.Relative.Replace('/', [string][System.IO.Path]::DirectorySeparatorChar))
            New-Item -ItemType Directory -Path (Split-Path $oldBackup -Parent) -Force | Out-Null
            Copy-Item -LiteralPath $file.Destination -Destination $oldBackup -ErrorAction Stop
        }
    }
    foreach ($file in $sourceFiles) {
        $existed = Test-Path -LiteralPath $file.Destination -PathType Leaf
        $replaced += [pscustomobject]@{ File = $file; Existed = $existed }
        New-Item -ItemType Directory -Path (Split-Path $file.Destination -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $file.Source -Destination $file.Destination -Force -ErrorAction Stop
    }
} catch {
    Write-Warning "Cópia interrompida. Tentando restaurar apenas os arquivos alterados: $_"
    foreach ($entry in $replaced) {
        if ($entry.Existed) {
            $oldBackup = Join-Path $backup ($entry.File.Relative.Replace('/', [string][System.IO.Path]::DirectorySeparatorChar))
            if (Test-Path -LiteralPath $oldBackup) {
                Copy-Item -LiteralPath $oldBackup -Destination $entry.File.Destination -Force
            }
        } elseif (Test-Path -LiteralPath $entry.File.Destination) {
            Remove-Item -LiteralPath $entry.File.Destination -Force
        }
    }
    throw
}
Write-Host "V8 aplicada somente no código IA. Backup anterior: $backup"
Write-Host 'Nenhuma pasta DATABASE/PYTHON, .env, .git, SQLite ou voz foi alterada.'
Write-Host 'Próximos passos: instalar dependências extras e testar conforme docs/current/V8_MOTOR_CONHECIMENTO.md.'
