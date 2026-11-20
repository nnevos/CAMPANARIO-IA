param([string]$Projeto = (Get-Location).Path)
$ErrorActionPreference = 'Continue'
try { $Raiz = (Resolve-Path -LiteralPath $Projeto -ErrorAction Stop).Path } catch {
    Write-Host 'ERRO: abra o PowerShell na pasta do projeto ou informe -Projeto com o caminho.'
    exit 1
}
Write-Host '=== DIAGNOSTICO CAMPANARIO (somente leitura) ==='
Write-Host "Pasta informada: $Raiz"
Write-Host ''
Write-Host '[1] Servidor que realmente ocupa a porta 8000:'
try {
    $conexoes = @(Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction Stop)
    if ($conexoes.Count -eq 0) { Write-Host 'NENHUM processo ouvindo na porta 8000.' }
    foreach ($conexao in $conexoes) {
        $idProcesso = [int]$conexao.OwningProcess
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $idProcesso" -ErrorAction SilentlyContinue
        if ($proc) { Write-Host ("PID={0}; Executavel={1}; Linha={2}" -f $idProcesso,$proc.ExecutablePath,$proc.CommandLine) }
        else { Write-Host "PID=$idProcesso; detalhes indisponiveis" }
    }
} catch { Write-Host ("Nao foi possivel consultar a porta: " + $_.Exception.Message) }
Write-Host ''
Write-Host '[2] Configuracao de pesquisa no projeto informado:'
$envPath = Join-Path $Raiz '.env'
if (Test-Path -LiteralPath $envPath) {
    Write-Host "Arquivo .env encontrado: $envPath"
    $linhas = @(Select-String -LiteralPath $envPath -Pattern '^\s*CAMPANARIO_WEB_AUTO_SEARCH\s*=' -ErrorAction SilentlyContinue)
    if ($linhas.Count -eq 0) { Write-Host 'Sem CAMPANARIO_WEB_AUTO_SEARCH no .env.' }
    else { foreach ($linha in $linhas) { Write-Host ("Linha {0}: {1}" -f $linha.LineNumber,$linha.Line.Trim()) } }
} else { Write-Host 'ARQUIVO .env NAO EXISTE nesta pasta.' }
foreach ($escopo in @('Process','User','Machine')) {
    $valor = [Environment]::GetEnvironmentVariable('CAMPANARIO_WEB_AUTO_SEARCH',$escopo)
    if ($null -eq $valor) { $valor = '<nao definida>' }
    Write-Host "Variavel de ambiente ($escopo): $valor"
}
Write-Host ''
Write-Host '[3] Python da .venv e configuracao efetiva:'
$python = Join-Path (Split-Path $Raiz -Parent) 'CAMPANARIO-PYTHON\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = Join-Path $Raiz '.venv\Scripts\python.exe' }
if (Test-Path -LiteralPath $python) {
    Push-Location $Raiz
    try {
        $codigo = 'from campanario.config import get_settings; import campanario.config as c; s=get_settings(); print("CONFIG_PY:",c.__file__); print("WEB_AUTO_SEARCH:",s.web_auto_search); print("ARQUIVO_LOG:",s.database_path.parent / "logs" / "desktop.log"); import importlib.util; print("PIPER_INSTALADO:",importlib.util.find_spec("piper") is not None)'
        & $python -c $codigo 2>&1 | ForEach-Object { Write-Host $_ }
    } finally { Pop-Location }
} else { Write-Host 'Nao encontrei .venv\Scripts\python.exe na pasta informada.' }
Write-Host ''
Write-Host '[4] Motor de voz que o backend em 127.0.0.1:8000 esta usando:'
try {
    $vozes = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/voice/voices' -Method Get -TimeoutSec 8 -ErrorAction Stop
    Write-Host "Piper instalado no SERVIDOR: $($vozes.piper_installed)"
    foreach ($agente in @('morgana','todd')) {
        $v = $vozes.agents.$agente
        if ($v) {
            Write-Host "$agente - motor=$($v.engine); modelo=$($v.model_path)"
            $modelo = [string]$v.model_path
            Write-Host "  ONNX existe: $(Test-Path -LiteralPath $modelo -PathType Leaf)"
            Write-Host "  JSON existe: $(Test-Path -LiteralPath ($modelo + '.json') -PathType Leaf)"
        }
    }
} catch { Write-Host ("Falha ao consultar API de voz: " + $_.Exception.Message) }
Write-Host ''
Write-Host '[5] Ultimos erros do desktop.log:'
$logCandidates = @()
if ($env:LOCALAPPDATA) {
    $logCandidates += (Join-Path $env:LOCALAPPDATA 'Campanario\desenvolvimento\logs\desktop.log')
    $logCandidates += (Join-Path $env:LOCALAPPDATA 'Campanario\producao\logs\desktop.log')
}
$foundLog = $false
foreach ($log in $logCandidates) {
    if (Test-Path -LiteralPath $log -PathType Leaf) {
        $foundLog = $true
        Write-Host "Log: $log"
        $tail = @(Get-Content -LiteralPath $log -Tail 90 -ErrorAction SilentlyContinue)
        $matches = @($tail | Select-String -Pattern 'Falha TTS|piper|Traceback|Error|Exception|knowledge_decision|knowledge_retrieval|knowledge_search')
        if ($matches.Count -gt 0) { $matches | Select-Object -Last 16 | ForEach-Object { Write-Host $_.Line } }
        else { Write-Host 'Nenhum erro correspondente nas ultimas 90 linhas.' }
    }
}
if (-not $foundLog) { Write-Host 'Log nao encontrado nos caminhos padrao; veja o caminho ARQUIVO_LOG acima.' }
Write-Host ''
Write-Host '=== FIM. NENHUMA CONFIGURACAO FOI ALTERADA. ==='
