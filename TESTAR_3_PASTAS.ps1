param([string]$ProjectRoot = '.')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$parent = Split-Path $root -Parent
$venv = Join-Path $parent 'CAMPANARIO-PYTHON\.venv'
$python = Join-Path $venv 'Scripts\python.exe'
$database = Join-Path $parent 'CAMPANARIO-DATABASE\dados'
$zim = Join-Path $parent 'CAMPANARIO-DATABASE\zim'
Write-Host "Projeto: $root"
Write-Host "Ambiente: $python"
Write-Host "Dados: $database"
Write-Host "ZIM: $zim"
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Python externo ausente; prepare-o primeiro.' }
Push-Location $root
try {
    & $python tools/verificar_python_unificado.py --project $root --environment $venv --require-marker
    if ($LASTEXITCODE -ne 0) { throw 'Python externo nao validado.' }
    & uv pip check --python $python
    if ($LASTEXITCODE -ne 0) { throw 'Dependencias incompatíveis.' }
    # Prefer file-based Python invocation to avoid the PowerShell 5.1 quoting bug.
    & $python tools/verificar_caminhos_3pastas.py --expected-data $database --expected-zim $zim
    if ($LASTEXITCODE -ne 0) { throw 'Configuracao de dados divergente.' }
    & $python -m pytest tests/test_fase4_inc3b2_guarded_semantic.py tests/test_fase4_inc3b1_suficiencia.py tests/test_fase4_tres_pastas.py tests/test_ambiente_python_unificado.py -q
    if ($LASTEXITCODE -ne 0) { throw 'Testes dirigidos falharam.' }
    Write-Host 'OK: ambiente e dados externos com evidencia e voz verificados.'
} finally { Pop-Location }
