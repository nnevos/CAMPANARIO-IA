# Dot-source or invoke to direct uv project operations at the external venv.
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$env:UV_PROJECT_ENVIRONMENT = Join-Path (Split-Path $ProjectRoot -Parent) 'CAMPANARIO-PYTHON\.venv'
Write-Host "UV_PROJECT_ENVIRONMENT=$env:UV_PROJECT_ENVIRONMENT"
Write-Host 'ATENCAO: use uv sync --inexact --frozen --extra desktop. Sem --inexact, o uv pode remover Piper/Pocket/CUDA.'
