# Auditoria somente leitura. Compare os arquivos instalados com a Etapa 3.
param([string]$ProjectRoot = ".")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path $ProjectRoot).Path
$expected = @(
    @{ File = "src/campanario/utilities/web_intent.py"; Sha256 = "1747C469878CFF578EA850B63F8C8B880643E62A8EC1698FFC07AA1B3361B302" }
    @{ File = "src/campanario/utilities/web_chat.py"; Sha256 = "25ACE36598F68694B76C4A1C484076B48D56E30BBADDB467486E228AD0D48993" }
    @{ File = "src/campanario/chat/knowledge.py"; Sha256 = "D02CD58721B198B8049CB96F128D5923E851D628D77C70F49054C14A42BDA57B" }
    @{ File = "src/campanario/chat/service.py"; Sha256 = "C431839DEA57EC01FE4945C40AA7DE403BE0E5BF2A3057AD39DDDC37952F75F5" }
    @{ File = "src/campanario/model/adapters/ollama.py"; Sha256 = "CB9BB6EF39E848C6C067622F92B01AD4B0A6BC77EB2C2B96006E954264947AE6" }
    @{ File = ".env.example"; Sha256 = "5FEDEBEB606A75B4A5C4DC34B4888813E7B41DDDB585D88649E6A337DD69EED1" }
)
Write-Host "Comparacao de arquivos com o pacote Etapa 3 (somente leitura)"
$diff = 0
foreach ($item in $expected) {
    $localPath = Join-Path $root $item.File
    if (-not (Test-Path -LiteralPath $localPath -PathType Leaf)) {
        Write-Host ("AUSENTE: " + $item.File)
        $diff++
        continue
    }
    $observed = (Get-FileHash -LiteralPath $localPath -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($observed -eq $item.Sha256) {
        Write-Host ("IGUAL:   " + $item.File)
    } else {
        Write-Host ("DIFERE:  " + $item.File)
        Write-Host ("          Atual: " + $observed)
        Write-Host ("          Etapa3: " + $item.Sha256)
        $diff++
    }
}
Write-Host ("Arquivos diferentes/ausentes: " + $diff + " de " + $expected.Count)
Write-Host "Nenhum arquivo foi alterado."
