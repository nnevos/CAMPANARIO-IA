param(
    [string]$ProjectRoot = '.',
    [switch]$Apply,
    [switch]$Resume
)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath $ProjectRoot).Path
if ((Split-Path $project -Leaf) -ne 'CAMPANARIO-IA') { throw 'Projeto deve se chamar CAMPANARIO-IA; nao mover o repositorio.' }
$parent = Split-Path $project -Parent
$pythonDir = Join-Path $parent 'CAMPANARIO-PYTHON'
$newVenv = Join-Path $pythonDir '.venv'
$newPython = Join-Path $newVenv 'Scripts\python.exe'
$dbRoot = Join-Path $parent 'CAMPANARIO-DATABASE'
$newData = Join-Path $dbRoot 'dados'
$zimDir = Join-Path $dbRoot 'zim'
$oldVenv = Join-Path $project '.venv\Scripts\python.exe'
$envPath = Join-Path $project '.env'
$envContent = if (Test-Path -LiteralPath $envPath) { [IO.File]::ReadAllText($envPath) } else { '' }
$oldData = Join-Path $env:LOCALAPPDATA 'Campanario'
$envData = [Environment]::GetEnvironmentVariable('CAMPANARIO_DATA_DIR', 'Process')
if ($envContent -match '(?m)^\s*CAMPANARIO_DATA_DIR\s*=\s*(.*)\s*$') {
    $oldData = $Matches[1].Trim().Trim('"').Trim("'")
}
if ($envData) { $oldData = $envData }
if ($oldData -and -not [IO.Path]::IsPathRooted($oldData)) { throw 'CAMPANARIO_DATA_DIR atual nao e caminho absoluto. Resolva antes de migrar.' }
if (!$oldData) { throw 'Nao foi possivel localizar a pasta atual de dados.' }
Write-Host "Projeto: $project"
Write-Host "Python externo: $newVenv"
Write-Host "Dados atuais (somente leitura): $oldData"
Write-Host "Dados novos: $newData"
Write-Host "ZIM: $zimDir"
Write-Host "Antiga .venv sera mantida: $([bool](Test-Path -LiteralPath $oldVenv))"
# Never overwrite an existing destination. -Resume is an explicit recovery path.
$dataExists = Test-Path -LiteralPath $newData
if ($Resume -and -not $dataExists) { throw 'RETOMADA: destino dados nao existe; nada a retomar.' }
if (!$Resume -and $dataExists) { throw 'Pasta dados ja existe. NAO repita -Apply; verifique a copia usando -Resume antes de ativar.' }
if ($Resume -and ([IO.Path]::GetFullPath($oldData).TrimEnd('\') -ieq [IO.Path]::GetFullPath($newData).TrimEnd('\'))) {
    throw 'Configuracao ja aponta para o destino. Use TESTAR_3_PASTAS.ps1; nao reexecute a migracao.'
}
if (!(Test-Path -LiteralPath $newPython -PathType Leaf)) {
    throw 'Prepare antes a .venv externa com PREPARAR_PYTHON_UNIFICADO.ps1 -Apply. A migracao nao instala dependencias.'
}
$verifyPython = Join-Path $project 'tools\verificar_python_unificado.py'
& $newPython $verifyPython --project $project --environment $newVenv --require-marker
if ($LASTEXITCODE -ne 0) { throw 'Python externo nao validado; .env e dados nao serao modificados.' }
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (!$uvCmd) { throw 'uv necessario para conferir dependencias do novo ambiente.' }
& uv pip check --python $newPython
if ($LASTEXITCODE -ne 0) { throw 'Falha no uv pip check do ambiente externo.' }
$py = if (Test-Path -LiteralPath $oldVenv) { $oldVenv } else { $null }
if (!$py) {
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd) { $py = 'py' }
    else {
        $cmd = Get-Command python -ErrorAction SilentlyContinue
        if (!$cmd) { throw 'Python necessario para a copia segura SQLite.' }
        $py = 'python'
    }
}
if ($py -eq 'py') { $pythonArgs = @('-3.12') } else { $pythonArgs = @() }
$migration = Join-Path $project 'tools\migrar_biblioteca_3pastas.py'
if (!(Test-Path -LiteralPath $migration)) { throw 'Instale primeiro o patch de codigo APLICAR_3_PASTAS.ps1.' }
Write-Host 'Plano de migracao/retomada (origem intocada):'
$verifyCopy = Join-Path $project 'tools\verificar_copia_3pastas.py'
if (!(Test-Path -LiteralPath $verifyCopy -PathType Leaf)) { throw 'Instale primeiro a correcao de retomada segura.' }
if ($Resume) {
    Write-Host 'RETOMADA: comparando os dados existentes com a origem, sem regravar arquivos.'
    & $newPython $verifyCopy --source $oldData --destination $newData
    if ($LASTEXITCODE -ne 0) { throw 'RETOMADA BLOQUEADA: copia existente diverge da origem. Nenhuma configuracao foi alterada.' }
} else {
    & $newPython $migration --source $oldData --destination $newData
    if ($LASTEXITCODE -ne 0) { throw 'Plano de migracao rejeitado.' }
}
if (!$Apply) {
    if ($Resume) { Write-Host 'SOMENTE VERIFICACAO. Se a copia estiver integra, use -Resume -Apply para ativar os caminhos SEM recopia.' }
    else { Write-Host 'SOMENTE VERIFICACAO. Use -Apply para copiar os dados e ativar os caminhos.' }
    exit 0
}
if (!$Resume) {
    & $newPython $migration --source $oldData --destination $newData --apply
    if ($LASTEXITCODE -ne 0) { throw 'Copia falhou. A origem e .env nao foram alterados.' }
}
if (!(Test-Path -LiteralPath $newData -PathType Container)) { throw 'Copia nao publicada.' }
# Even on the first application, verify the published content before changing .env.
# On resume this duplicates the earlier dry-run check, intentionally detecting changes in between.
& $newPython $verifyCopy --source $oldData --destination $newData
if ($LASTEXITCODE -ne 0) { throw 'Verificacao da copia falhou. .env nao sera alterado.' }
# The external Python was prepared separately. Do not synchronize packages here, to preserve voice engines.
New-Item -ItemType Directory -Path $zimDir -Force | Out-Null
$backupDir = Join-Path $dbRoot ('BACKUP_CONFIG_ANTES_SEPARACAO_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $backupDir | Out-Null
if (Test-Path -LiteralPath $envPath) { Copy-Item -LiteralPath $envPath -Destination (Join-Path $backupDir '.env') }
# No other .env keys are altered. Single path key per setting.
$lines = @(($envContent -split '\r?\n') | Where-Object { $_ -notmatch '^\s*CAMPANARIO_(DATA_DIR|ZIM_DIR)\s*=' })
$newContent = ($lines -join "`r`n").TrimEnd("`r", "`n") + "`r`n" +
    'CAMPANARIO_DATA_DIR="' + $newData + '"' + "`r`n" +
    'CAMPANARIO_ZIM_DIR="' + $zimDir + '"' + "`r`n"
$tempEnv = $envPath + '.separacao.tmp'
try {
    [IO.File]::WriteAllText($tempEnv, $newContent, (New-Object System.Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $tempEnv -Destination $envPath -Force
    Push-Location $project
    try {
        # Avoid python -c / nested quotes on Windows PowerShell 5.1.
        $pathVerifier = Join-Path $project 'tools\verificar_caminhos_3pastas.py'
        & $newPython $pathVerifier --expected-data $newData --expected-zim $zimDir
        if ($LASTEXITCODE -ne 0) { throw 'A verificacao de caminhos falhou.' }
    } finally { Pop-Location }
} catch {
    if (Test-Path -LiteralPath (Join-Path $backupDir '.env')) {
        Copy-Item -LiteralPath (Join-Path $backupDir '.env') -Destination $envPath -Force
    } else {
        Remove-Item -LiteralPath $envPath -ErrorAction SilentlyContinue
    }
    throw
} finally {
    Remove-Item -LiteralPath $tempEnv -ErrorAction SilentlyContinue
}
Write-Host 'CONCLUIDO: 3 pastas ativas. Dados existentes verificados; origem e antigas .venv mantidas.'
Write-Host "Backup de configuracao (.env privado): $backupDir"
Write-Host "Para executar pytest: & '$newPython' -m pytest ..."
Write-Host 'Depois de validar o aplicativo e os testes, voce pode avaliar a remocao manual da .venv antiga.'
