param(
    [Parameter(Mandatory=$true)][string]$ProjectRoot,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath $ProjectRoot).Path
if (-not (Test-Path -LiteralPath (Join-Path $project 'src/campanario/brains/router.py'))) {
    throw 'Projeto V9 integrado nao detectado. Nao aplique este patch em V8 ou V9.1 sem cerebros.'
}
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.format -ne 1 -or $manifest.scope -ne 'documentation_only') { throw 'Manifesto de patch nao reconhecido.' }
$allowed = @(
    'README.md',
    'docs/current/ROADMAP.md',
    'docs/current/AGENT_PERSONALITY_ROADMAP.md',
    'docs/operations/ETAPA1_AUDITORIA_FAILSAFES_FLUXOS_2026-11-19.md',
    'docs/operations/ETAPA2_ESTABILIZACAO_FAILSAFES_2026-11-19.md',
    'docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md',
    'docs/operations/FAILSAFE_V9_CEREBROS.md'
)
$entries = @($manifest.files)
if ($entries.Count -ne $allowed.Count) { throw 'Quantidade inesperada de arquivos no manifesto.' }
$pending = @()
foreach ($rel in $allowed) {
    $matches = @($entries | Where-Object { $_.path -ceq $rel })
    if ($matches.Count -ne 1) { throw "Arquivo ausente ou duplicado no manifesto: $rel" }
    $item = $matches[0]
    $source = Join-Path $PSScriptRoot $rel
    $target = Join-Path $project $rel
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Arquivo ausente no patch: $rel" }
    $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sourceHash -cne $item.new_sha256.ToLowerInvariant()) { throw "Arquivo do patch foi modificado: $rel" }
    if (Test-Path -LiteralPath $target) {
        $localHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($localHash -ceq $item.new_sha256.ToLowerInvariant()) {
            Write-Host "JA ATUALIZADO: $rel"
            continue
        }
        if ([string]::IsNullOrWhiteSpace($item.baseline_sha256) -or $localHash -cne $item.baseline_sha256.ToLowerInvariant()) {
            throw "CONFLITO: $rel possui alteracoes locais; faca conciliacao manual. Nada foi sobrescrito."
        }
    } elseif (-not [string]::IsNullOrWhiteSpace($item.baseline_sha256)) {
        throw "CONFLITO: arquivo esperado da base nao existe: $rel"
    }
    $pending += $rel
    Write-Host "PRONTO PARA ATUALIZAR: $rel"
}
if (-not $Apply) {
    Write-Host "Simulacao concluida: $($pending.Count) arquivo(s) pendente(s). Use -Apply para aplicar com backup."
    exit 0
}
if ($pending.Count -eq 0) { Write-Host 'Nenhum arquivo pendente. Nada alterado.'; exit 0 }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = Join-Path $project "_backups/ROADMAP_V9_$stamp"
foreach ($rel in $pending) {
    $target = Join-Path $project $rel
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        $save = Join-Path $backup $rel
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $save) | Out-Null
        Copy-Item -LiteralPath $target -Destination $save
    }
}
foreach ($rel in $pending) {
    $target = Join-Path $project $rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $rel) -Destination $target
    Write-Host "ATUALIZADO: $rel"
}
Write-Host "Concluido (somente documentacao). Backups dos arquivos anteriores: $backup"
