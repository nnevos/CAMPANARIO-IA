# Campanário R3.20 — instalação sobre a base limpa

**Instalação recomendada:** substitua a pasta `CAMPANARIO-IA` por este projeto **completo e limpo**, não mescle com cópias antigas dentro de `docs/operations`. Faça backup antes e preserve `CAMPANARIO-PYTHON`, `CAMPANARIO-DATABASE`, `.env` e modelos de voz externos. O iniciador `CAMPANARIO.bat` continua usando a `.venv` externa; não execute PREPARAR_PC.bat se o Campanário já abre.

**Mapa:** ao abrir Patrulha/Maps e permitir localização no Windows/navegador, a posição é acompanhada automaticamente enquanto a tela estiver aberta. A busca não precisa de GPS, exceto para entender "mais próximo" sem origem manual.

**Internet e privacidade:** R3.20 consulta Nominatim/Overpass/OSRM públicos se os serviços locais não responderem. Consultas e coordenadas são enviadas a terceiros nessa situação. Adicione `CAMPANARIO_MAPS_PUBLIC_FALLBACK=false` ao `.env` e reinicie para desativar. Não há roteamento público de pedestres por substituição de perfil.

**Android:** projeto-fonte em `apps/mobile/android`; não acompanha APK compilado.

**Verificação:** use busca de endereço textual sem GPS; depois teste "mercado mais próximo" com GPS autorizado ou origem manual. Se a conexão pública falhar, consulte a mensagem real; não há rota inventada.
