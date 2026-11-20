param([string]$ProjectRoot = '.', [switch]$SmokeOnly)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath $ProjectRoot).Path
if ((Split-Path $project -Leaf) -ne 'CAMPANARIO-IA') { throw 'Raiz deve ser CAMPANARIO-IA.' }
$target = Join-Path (Split-Path $project -Parent) 'CAMPANARIO-PYTHON\.venv'
$python = Join-Path $target 'Scripts\python.exe'
$verify = Join-Path $project 'tools\verificar_python_unificado.py'
if (!(Test-Path -LiteralPath $python)) { throw 'Ambiente externo inexistente. Rode PREPARAR_PYTHON_UNIFICADO.ps1 -Apply.' }
Push-Location $project
try {
    & $python $verify --project $project --environment $target --require-marker
    if ($LASTEXITCODE -ne 0) { throw 'Manifesto Python nao validado.' }
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (!$uv) { throw 'uv nao encontrado para executar uv pip check.' }
    & uv pip check --python $python
    if ($LASTEXITCODE -ne 0) { throw 'Conflito de dependencias do Python externo.' }
    # On Windows PowerShell 5.1, passing nested quotes through python -c can remove them.
    # Execute a .py file instead: no shell quoting ambiguity, no package installation.
    $voiceSmoke = Join-Path $project 'tools\testar_imports_voz_unificado.py'
    if (!(Test-Path -LiteralPath $voiceSmoke -PathType Leaf)) { throw 'Teste de voz ausente: tools/testar_imports_voz_unificado.py.' }
    & $python $voiceSmoke
    if ($LASTEXITCODE -ne 0) { throw 'Importacao de voz falhou; nao remover as venv antigas.' }
    if (!$SmokeOnly) {
        $tests = @('tests/test_fase4_inc1_biblioteca.py', 'tests/test_fase4_inc2_ficha_neutra.py', 'tests/test_fase4_inc2_avaliador_windows.py', 'tests/test_fase4_inc2_avaliador_inc1_windows.py', 'tests/test_fase4_inc3_busca_local.py', 'tests/test_fase4_inc3b_semantic.py', 'tests/test_fase4_inc3b_identidade_evolutiva.py', 'tests/test_fase4_inc3b_calibracao.py', 'tests/test_fase4_inc3b1_suficiencia.py', 'tests/test_fase4_inc3b2_guarded_semantic.py', 'tests/test_fase4_tres_pastas.py', 'tests/test_ambiente_python_unificado.py', 'tests/test_python_unificado_smoke_voz.py')
        & $python -m pytest @tests -q
        if ($LASTEXITCODE -ne 0) { throw 'Regressao falhou. Nao ativar pastas/dados.' }
    }
    Write-Host 'OK: verificacoes concluidas. Ainda teste audio real de Morgana/Todd antes de remover ambientes antigos.'
} finally { Pop-Location }
