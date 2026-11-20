# CAMPANARIO V9.1 - patch seguro (IA)

**Instale apenas sobre o CAMPANARIO-IA V8 anterior.** Esta entrega nao substitui os repositorios `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE` e nao integra uma V9 com cerebros que nao foi fornecida.

1. Feche Campanario. Copie a pasta Database e o `.env` para um backup proprio.
2. Extraia este ZIP **fora** da pasta `CAMPANARIO-IA`. Exemplo `C:\Temp\CAMPANARIO_V91_PATCH`.
3. PowerShell, simule primeiro:

```powershell
$projeto = 'C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA'
$patch = 'C:\Temp\CAMPANARIO_V91_PATCH'
& "$patch\tools\windows\APLICAR_V91_SEGURA.ps1" -ProjectRoot $projeto -PatchRoot $patch
```

4. Se nenhuma divergencia for acusada, aplique com backup automatico dos arquivos substituidos:

```powershell
& "$patch\tools\windows\APLICAR_V91_SEGURA.ps1" -ProjectRoot $projeto -PatchRoot $patch -Apply
```

**Protecoes:** valida todos os SHA-256 do patch, confere hash V8 original de cada arquivo preexistente, recusa arquivos alterados localmente, cria backup em pasta irma e nao toca em `.env`, bancos, personalidades externas, instalacao Python ou modelos de voz. O comando sem `-Apply` e apenas simulacao. Script ainda nao foi executado em Windows real neste ambiente.

Consulte `docs/current/V91_EXPRESSAO_FUNDAMENTADA.md` para arquitetura, testes e limitacoes. Os arquivos `RESULTADOS_TESTES_V91.txt` e `DEMONSTRACAO_V91_EXECUTADA.json` registram resultados reais com **documentos ficticios de teste**.
