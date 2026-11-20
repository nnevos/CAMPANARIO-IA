# Seguranca, compilacao e atualizacoes

## PC e rede

A API original so aceita loopback. `Host`, `Origin` e cabecalhos de proxy inesperados sao recusados. Nao exponha a porta 8000. O companion e outro listener, TLS, com API limitada e autenticacao bearer; codigos expiram em cinco minutos e so podem ser usados uma vez. Credenciais nao vao em URL. O banco guarda hash de tokens, nao tokens recuperaveis.

Pareamento nao concede automaticamente o chat. Autorizar chat permite ao aparelho usar a IA e o contexto/memoria compartilhados do PC. O pacote offline tem permissao separada por selecao de conteudo. TLS deve ser configurado com certificado valido para o endereco; o Android nao ignora erros SSL. O host aceita CAs do sistema e CAs instaladas pelo usuario conforme sua configuracao de rede. Isto nao equivale a certificate pinning.

Ative somente em rede de confianca, com firewall restrito. Nao configure port-forwarding publico. Nao ha auditoria externa de seguranca, mitigacao de todos os ataques DoS ou identidade multiusuario. Revogacao vale para acessos seguintes; nao garante interromper instantaneamente uma operacao ja iniciada.

## Dados e exclusao

No Android nativo, estado local e credenciais sao gravados em arquivo privado AES-GCM, com chave no Android Keystore. Backups automaticos desse estado sao desabilitados. Na pre-visualizacao de desenvolvimento em navegador, o fallback IndexedDB NAO e criptografado e nao persiste o token. O fluxo nativo ainda precisa ser testado em aparelho.

Apagar nota sincroniza um registro de exclusao; backups e tabelas de idempotencia podem preservar versoes anteriores. Apagar memoria no PC preserva a semantica de esquecimento existente, nao promete eliminacao forense. Apagar todos os dados do aparelho remove o armazenamento local, nao os dados do PC. Revogar aparelho nao faz remote wipe.

O ZIP de fonte nao inclui `.env`, bancos, credenciais, pesos de modelos ou historico Git. Certificados, keystores e chaves estao no `.gitignore`. Isso nao substitui verificar seus commits antes de publicar.

## Compilar Windows

Em Windows/Python 3.12:

```sh
python -m pip install -e ".[desktop]" "pyinstaller>=6,<7"
powershell -NoProfile -File packaging/build_windows.ps1
```

A receita produz uma pasta com `Campanario.exe` e seus recursos, depois um ZIP. `console=False` evita console no uso normal. WebView2 Runtime continua sendo requisito do sistema. Chroma e binarios antigos de voz sao excluidos da receita leve. Nenhum EXE foi gerado nesta entrega. O arquivo resultante nao tera assinatura Authenticode ate voce configurar e aplicar sua assinatura Windows; alertas do Windows nao devem ser tratados como motivo para desativar protecoes.

## GitHub Actions

Ha dois workflows:

- `validar.yml`: testes da fundacao como gate, testes JS e suite integral registrada. A suite integral continua visivel mesmo com falhas herdadas; seu resultado aparece em aviso e XML. Gate aprovado nao significa suite inteira verde.
- `compilar.yml`: acionamento manual; builds candidatos Windows e Android. Debug Android e padrao. Nao publica automaticamente uma release de producao.

Os workflows usam referencias major das actions e intervalos de dependencias Python. Antes de distribuicao ampla, revise e fixe actions por commit e gere lockfiles de dependencias com o ambiente de build real. Nao foi inventado um lockfile sem resolver as dependencias. As versoes de AGP/Gradle/JDK escolhidas formam uma base compativel documentada, nao uma alegacao de serem as mais recentes.

## Assinatura Android e releases

Crie uma chave release permanente pelo Android Studio ou `keytool` em uma maquina confiavel. Preserve backup seguro. Nunca comite essa chave. Configure os secrets do repositorio:

```
ANDROID_KEYSTORE_BASE64
ANDROID_KEYSTORE_PASSWORD
ANDROID_KEY_ALIAS
ANDROID_KEY_PASSWORD
```

`ANDROID_KEYSTORE_BASE64` deve conter o arquivo JKS codificado, nao o caminho. O workflow o materializa no diretorio temporario e remove ao final. Habilite `android_release` ao disparar o workflow. Sem os secrets, o build release falha explicitamente; ele nao usa uma chave temporaria fingindo ser permanente.

A identidade release e `org.campanario.mobile`; a debug e `org.campanario.mobile.dev`. Atualizacoes release precisam manter a identidade e chave. Aumente `versionCode` (atualmente 800), altere `versionName` e as versoes Python/UI em cada entrega. `ANDROID_VERSION_CODE` pode sobrepor o codigo durante builds locais.

Fluxo operacional:

1. Enviar o projeto para SEU repositorio, sem dados/segredos.
2. Executar Validar e revisar inclusive falhas da suite integral.
3. Executar Compilar, baixar os artefatos candidatos e instalar em PC/aparelho de teste.
4. Testar abertura offline, perda de rede, assinatura, atualizacao preservando dados, TLS, pareamento e revogacao.
5. Criar Release com tag estavel `vX.Y.Z`, anexar o APK release assinado e o ZIP Windows. Publicar apenas depois da verificacao.
6. Configurar `dono/repositorio` nos clientes e usar Verificar release.

O verificador consulta a ultima release publica estavel, valida formato de versao e link, e mostra uma pagina de download. Ele nao instala sozinho, nao verifica o conteudo do APK baixado pelo navegador e nao executa a branch `main`. APK e verificado pelo sistema na instalacao. Checksum SHA256 detecta mudanca de bytes, mas nao substitui assinatura ou uma origem de publicacao confiavel. Repositorio privado, autenticacao GitHub e atualizacao diferencial nao foram implementados.

## Referencias tecnicas consultadas

- pywebview: https://pywebview.flowrl.com/guide/usage.html
- pywebview/PyInstaller: https://pywebview.flowrl.com/guide/freezing.html
- Android, conteudo embarcado: https://developer.android.com/develop/ui/views/layout/webapps/load-local-content
- Assinatura Android: https://developer.android.com/studio/publish/app-signing
- Compatibilidade AGP 8.9: https://developer.android.com/build/releases/agp-8-9-0-release-notes

Essas referencias embasam escolhas de plataforma. Elas nao sao evidencia de que este projeto especifico foi compilado ou homologado nessas plataformas.
