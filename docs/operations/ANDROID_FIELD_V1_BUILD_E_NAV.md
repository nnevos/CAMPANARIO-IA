# Campanario Field V1 (R3.17) — Compilação e navegação Android nativa

## Escopo comprovável

O pacote inclui o **projeto Android**, não um APK: neste ambiente Linux estão ausentes Android SDK, Gradle e acesso à rede para instalá-los. Nenhum APK foi gerado, assinado, instalado ou testado em dispositivo real. A base R3.16 já possuía um host Android Java com interface HTML local embarcada; este marco **não converteu toda a interface em Jetpack Compose**. Acrescentou uma **Activity de navegação nativa Android**, um **ForegroundService `location`** com notificação e TTS Android, cliente HTTPS versionado que usa o pareamento já existente, e traçado nativo da geometria OSRM sem inventar mapa de ruas. A conversa, Notas e Biblioteca continuam na interface embarcada existente.

## Como compilar no Windows, sem PowerShell

1. Instale Android Studio recente, JDK 17 e **Android SDK Platform 35** pelo SDK Manager do Android Studio.
2. No Android Studio, escolha **Open** e selecione `CAMPANARIO-IA/apps/mobile/android`. Sincronize o projeto com Gradle (a versão AGP declarada é 8.9.2 e requer Gradle compatível; configure Gradle 8.11.1). A primeira sincronização requer acesso ao repositório de plugins e bibliotecas Android, sem incorporar serviços remotos em runtime.
3. Use **Build > Build APK(s)**. Um APK de desenvolvimento de fato compilado aparecerá em `apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk`, apenas **se o build tiver sucesso**. A assinatura debug é local e temporária; atualização sobre pacote de assinatura diferente poderá exigir reinstalação. Para builds por comando, `COMPILAR_FIELD_ANDROID.bat` tenta usar Gradle instalado no PATH; não existe wrapper distribuído nesta versão.
4. No telefone, instale o APK por fluxo Android autorizado. Abra o Field, conecte-se ao servidor HTTPS pareado com certificado confiável para o Android, e vá em **GPS > Abrir navegação Android nativa**.
5. Autorize localização e, caso solicitado, notificações. Pesquise destino, escolha candidato quando houver ambiguidade, calcule rota (OSRM instalado no PC), e toque em **Iniciar GPS**. A notificação persistente permite retornar à tela nativa e encerrar o serviço. Voltar ao chat **não encerra** o serviço nativo.
6. Teste primeiro parado ou como passageiro. O mapa atual é **um esquema da geometria real**, sem basemap de ruas, não deve ser usado como navegação viária única.

## Requisitos do Campanario Server

- Reutiliza `/api/companion/v1/maps/v2/{resolve,route,status,fix,recalculate,command/...}` já implementadas na R3.16.
- HTTPS com certificado confiável no telefone e dispositivo já pareado, sem exposição direta de Ollama ou SQLite.
- OSRM carro e opcional caminhada, Nominatim e Overpass locais com dados OSM instalados no PC. Sem esses serviços, o aplicativo **não inventa rotas nem locais**.
- Nenhuma coordenada é gravada permanentemente pelo novo serviço; o GPS é enviado ao PC pareado durante sessão de navegação. Não oferece roteamento offline independente no Android.

## Arquitetura e limites

- `CompanionMapsClient.java`: rota HTTPS autenticada, operação allowlisted, sem redirecionamentos, timeout e limite do payload/resposta. Credencial obtida do `SecureStore` Android Keystore já existente, nunca embutida no APK.
- `NativeNavigationActivity.java`: seleção por busca OSM, escolhas ambíguas, solicitação de rota OSRM, start/pause/stop, visualização da rota e acesso ao chat. Só inicia guia após GPS recente.
- `NavigationForegroundService.java`: serviço de localização visível com notificação e TTS pt-BR, ciclo de atualização de GPS, solicitação de recálculo, e retorno ao mapa/chat. O Android pode encerrar o serviço por restrições de bateria, GPS ou recursos; **não há promessa de execução ilimitada**.
- `RouteGeometryView.java`: desenha apenas pontos reais retornados por OSRM. Não substitui MapLibre ou tiles MBTiles.
- Reutiliza o aplicativo já pareado; não implementa ainda UI inteiramente Compose, Room, QR de pareamento, OTA assinado e instalação nativa, controle remoto WireGuard, central operacional completa, serviços offline no Android, nem APK release assinado.

## Critérios de teste em aparelho (a executar)

1. Instalação do APK debug real em dispositivo Android 8.0+ (API 26+) e autorização de notificações/localização.
2. Sem internet/PC, o aplicativo abre e exibe notas e conteúdo previamente sincronizados; sem rota online, não anuncia manobras.
3. HTTPS pareado alcança o servidor na rede local ou túnel privado; certificado validado pelo Android.
4. Com OSRM/Overpass/Nominatim instalados e dados OSM da região, busca estabelecimento próximo, detecta ambiguidade, oferece escolha, calcula rota e inicia serviço nativo.
5. Alternar para chat, apagar a tela e reabrir o Maps; testar notificação, economia de energia, TTS e atualizações GPS com tempo real.
6. Simular perda do servidor, desvio e chegada em trajeto seguro; avaliar recuperação, atualização de rota e encerramento.
7. Testar assinatura e atualização do APK com mesma chave antes de distribuir OTA; **OTA privado não está implementado**.

Não declare esses cenários homologados sem evidência de teste em hardware.

## Rollback

Fechar Field, interromper a navegação pela notificação e restaurar o código R3.16 por cópia em CAMPANARIO-IA. A atualização não altera os dois repositórios irmãos nem os bancos persistentes do PC. Dados locais do app instalado permanecem vinculados ao package ID e assinatura da build; faça backup dos dados de campo antes de reinstalar o app.

**Atalho SOS:** o botão no cabeçalho do Field abre o discador nativo Android (ACTION_DIAL), sem iniciar chamadas nem declarar atendimento. Disponível offline quando há aplicativo instalado; não substitui assistência de emergência.
