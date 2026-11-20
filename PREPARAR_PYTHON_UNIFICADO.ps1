param(
    [string]$ProjectRoot = '.',
    [switch]$Apply,
    [switch]$Resume
)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath $ProjectRoot).Path
if ((Split-Path $project -Leaf) -ne 'CAMPANARIO-IA') { throw 'Execute na raiz CAMPANARIO-IA.' }
$parent = Split-Path $project -Parent
$targetRoot = Join-Path $parent 'CAMPANARIO-PYTHON'
$targetVenv = Join-Path $targetRoot '.venv'
$targetPython = Join-Path $targetVenv 'Scripts\python.exe'
$profilePath = Join-Path $project 'config\ambiente_unificado.json'
$verify = Join-Path $project 'tools\verificar_python_unificado.py'
$marker = Join-Path $targetRoot 'AMBIENTE_VALIDADO.json'
if (!(Test-Path -LiteralPath $profilePath -PathType Leaf) -or !(Test-Path -LiteralPath $verify -PathType Leaf)) {
    throw 'Instale primeiro o patch de separacao/unificacao.'
}
$profile = Get-Content -LiteralPath $profilePath -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host '=== CAMPANARIO: preparar AMBIENTE UNIFICADO (sem tocar bancos/.env) ==='
Write-Host "Projeto atual: $project"
Write-Host "Destino Python: $targetVenv"
Write-Host "Ambiente antigo preservado: $(Test-Path -LiteralPath (Join-Path $parent '.venv'))"
Write-Host "Ambiente atual preservado: $(Test-Path -LiteralPath (Join-Path $project '.venv'))"
Write-Host "Voz antiga solicitada: $($profile.runtime_requirements -join '; ')"
Write-Host "PyTorch index: $($profile.indexes.pytorch_cuda)"
if (Test-Path -LiteralPath $marker) {
    if (!(Test-Path -LiteralPath $targetPython -PathType Leaf)) { throw 'Marcador existe mas Python externo esta ausente; nao sobrescrever.' }
    & $targetPython $verify --project $project --environment $targetVenv --require-marker
    if ($LASTEXITCODE -ne 0) { throw 'Ambiente com marcador invalido. Pare e investigue antes de tentar instalar.' }
    Write-Host 'OK: ambiente externo ja validado. Nao sera reinstalado.'
    exit 0
}
if (Test-Path -LiteralPath $targetVenv) {
    if (!$Resume) { throw 'Destino Python ja existe sem marcador validado. Use -Resume somente para retomar instalacao incompleta deste patch.' }
    Write-Host 'RETOMADA autorizada: destino existente nao sera apagado.'
} elseif ($Resume) {
    throw '-Resume foi solicitado, mas ambiente de destino nao existe.'
}
if (!$Apply) {
    Write-Host 'SOMENTE VERIFICACAO: nenhuma instalacao foi executada.'
    Write-Host 'Use -Apply para recriar com uv o nucleo, desktop, testes, Piper, Pocket e as versoes CUDA registradas.'
    Write-Host 'IMPORTANTE: precisa de internet para obter os pacotes; pode baixar varios GB.'
    exit 0
}
$uv = Get-Command uv -ErrorAction SilentlyContinue
if (!$uv) { throw 'uv nao encontrado; o .env continua inalterado.' }
$previousUV = [Environment]::GetEnvironmentVariable('UV_PROJECT_ENVIRONMENT', 'Process')
$env:UV_PROJECT_ENVIRONMENT = $targetVenv
Push-Location $project
try {
    Write-Host 'ETAPA 1/4: instalar nucleo/desktop/testes do uv.lock no Python externo.'
    & uv sync --project $project --extra desktop --frozen --inexact --python 3.12.10
    if ($LASTEXITCODE -ne 0) { throw 'Falha no uv sync; dados e venvs antigos permanecem intactos.' }
    if (!(Test-Path -LiteralPath $targetPython -PathType Leaf)) { throw 'uv nao criou o Python de destino.' }
    $installArgs = @('pip', 'install', '--python', $targetPython, '--index', [string]$profile.indexes.pytorch_cuda, '--default-index', [string]$profile.indexes.primary)
    $installArgs += @($profile.runtime_requirements | ForEach-Object { [string]$_ })
    Write-Host 'ETAPA 2/4: resolver motor de voz e CUDA antes de baixar os pesos.'
    & uv @installArgs --dry-run
    if ($LASTEXITCODE -ne 0) { throw 'Versoes de voz/CUDA nao resolvidas. Nao substitua pins automaticamente; informe o erro.' }
    Write-Host 'ETAPA 3/4: instalar motores de voz na nova .venv (sem alterar as antigas).'
    & uv @installArgs
    if ($LASTEXITCODE -ne 0) { throw 'Instalacao da voz falhou. O ambiente externo fica incompleto; .env e dados originais intactos.' }
    Write-Host 'ETAPA 4/4: conferir consistencia, nomes e codigo atual.'
    & uv pip check --python $targetPython
    if ($LASTEXITCODE -ne 0) { throw 'Conflito de dependencias: nao validar nem ativar a nova .venv.' }
    & $targetPython $verify --project $project --environment $targetVenv --mark
    if ($LASTEXITCODE -ne 0) { throw 'Verificacao final falhou. Nenhum caminho foi ativado.' }
    Write-Host 'SUCESSO: ambiente externo preparado. Proxima etapa: TESTAR_PYTHON_UNIFICADO.ps1.'
    Write-Host 'ATENCAO: ainda nao alteramos a pasta de dados nem o .env.'
} finally {
    Pop-Location
    if ($null -eq $previousUV) { Remove-Item Env:\UV_PROJECT_ENVIRONMENT -ErrorAction SilentlyContinue }
    else { $env:UV_PROJECT_ENVIRONMENT = $previousUV }
}
