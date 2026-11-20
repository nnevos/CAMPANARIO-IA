param([string]$ProjectRoot='.', [Parameter(Mandatory=$true)][string]$BackupConfigDir, [switch]$Apply)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath $ProjectRoot).Path
$backup = (Resolve-Path -LiteralPath $BackupConfigDir).Path
$parent = Split-Path $project -Parent
$expected = Join-Path $parent 'CAMPANARIO-DATABASE'
if (-not $backup.StartsWith($expected + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Backup deve estar na pasta CAMPANARIO-DATABASE.' }
$old = Join-Path $backup '.env'
if (!(Test-Path -LiteralPath $old)) { throw 'Backup de .env nao encontrado. Nao alterar a configuracao.' }
Write-Host "Restaurar configuracao de: $old"
if (!$Apply) { Write-Host 'SOMENTE VERIFICACAO. Use -Apply para restaurar .env.'; exit 0 }
$current = Join-Path $project '.env'
if (Test-Path -LiteralPath $current) { Copy-Item -LiteralPath $current -Destination (Join-Path $backup '.env.antes_reversao') -Force }
Copy-Item -LiteralPath $old -Destination $current -Force
Write-Host 'REVERTIDO apenas o .env. Dados novos e antigos preservados. Utilize Python antigo ate validar.'
