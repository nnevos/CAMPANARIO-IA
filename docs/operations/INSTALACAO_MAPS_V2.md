# CAMPANÁRIO MAPS V2 — Instalação de dados e serviços reais

**Checkpoint R3.16 — 23/11/2026.** O código de navegação existe, mas os dados de ruas e os serviços de roteamento **não acompanham os ZIPs**. Sem esses serviços, o Maps V2 deve exibir indisponibilidade, não calcular uma rota fictícia. O requisito de navegação real em campo permanece pendente de testes com GPS e Android.

## Arquitetura e locais

- `CAMPANARIO-IA` contém a interface Dark Matter, `navigation_v2.py`, APIs e testes; nenhuma segunda `.venv`.
- `CAMPANARIO-PYTHON` contém a única `.venv` Python 3.12.
- `CAMPANARIO-DATABASE/dados/maps` é um **local recomendado para dados OSM preparados manualmente**, não para dados privados de conversas. Instalar pacotes regionais é decisão do operador. Mapas não são distribuídos no ZIP.
- Roteador OSRM de carro local: `http://127.0.0.1:5000`.
- Roteador OSRM pedestre local (grafo próprio preparado com perfil *foot*): `http://127.0.0.1:5001`.
- Busca por endereço Nominatim autogerenciada: `http://127.0.0.1:8088`.
- Busca por categoria próxima Overpass autogerenciada: `http://127.0.0.1:12345`.
- Mapa base raster PNG em MBTiles (opcional): configurar `CAMPANARIO_MBTILES` no `.env` privado. **MBTiles não calcula rotas**.
- As URLs são de loopback e rejeitam provedores externos configurados por engano.

## Preparar o motor de carro (Windows, sem PowerShell)

1. Instalar e abrir Docker Desktop, garantindo capacidade de memória e disco adequada à região.
2. Obter legalmente um extrato regional `.osm.pbf` do OpenStreetMap (por exemplo Geofabrik) e observar as condições da licença ODbL e atribuição OSM.
3. Criar `CAMPANARIO-DATABASE/dados/maps/car` e colocar ali o extrato com nome `region.osm.pbf`.
4. Fazer backup desse diretório se já existir processamento antigo. `PREPARAR_OSRM_CARRO_V2.bat` recusa sobrescrever `region.osrm` existente.
5. Dar duplo clique em `PREPARAR_OSRM_CARRO_V2.bat`. Ele apenas executa comandos oficiais do contêiner OSRM **quando você confirma**. A imagem Docker poderá ser baixada; o processamento não é rápido nem pequeno.
6. Após o contêiner iniciar, dar duplo clique em `DIAGNOSTICAR_MAPS_V2.bat`. Porta aberta não comprova que o grafo cobre o destino: teste a rota na interface com dois pontos reais da região.

O comando automatizado cobre **somente carro**. Para caminhada é necessário preparar **outro grafo de roteamento**, compatível com pedestres e executando no endereço configurado para o perfil foot. Não tratar o grafo de carro como grafo pedestre.

### Nominatim e Overpass

São servidores independentes do OSRM. Devem receber importação regional OSM específica, usando seus procedimentos oficiais, e expor suas portas localmente. A importação pode demandar PostgreSQL, memória e armazenamento expressivos. O Maps não baixa, instala nem gerencia silenciosamente esses serviços. Sem Nominatim, a busca textual falha com mensagem clara; sem Overpass, buscas de categoria como "mercado mais próximo" ficam indisponíveis. O usuário ainda pode informar coordenadas e calcular a rota se OSRM estiver pronto.

Referências técnicas oficiais: [OSRM HTTP API](https://project-osrm.org/docs/v26.5.0/http), [OSRM GitHub](https://github.com/Project-OSRM/osrm-backend), [Nominatim](https://nominatim.org/release-docs/latest/admin/Installation/), [Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API/Installation), [OSM](https://www.openstreetmap.org/copyright).

## Integração no Campanário

1. Abrir Modo Patrulha ou escrever no chat "Todd, rota para o mercado mais próximo".
2. Permitir localização **apenas quando solicitado** ou informar coordenadas manuais. O desktop sem sensor não terá GPS automaticamente.
3. O resolvedor usa Overpass local para categorias e Nominatim local para nomes. Para "mais próximo", a seleção usa **distância por rota calculada pelo OSRM**, não distância em linha reta. Se os dois mais próximos não se distinguirem com margem suficiente, a UI exige seleção.
4. Uma vez calculada a rota, clicar **Iniciar**. Instruções e desvios são derivados de manobras do motor real. GPS ruim/antigo é descartado. O serviço guarda no máximo uma sessão pessoal do desktop na memória do processo; a tela pode mudar para Chat sem destruir a sessão. **Reiniciar servidor perde a sessão**.
5. Usar Pausar/Retomar/Encerrar. Encerrar remove posição e rota da memória do serviço. Não são persistidas trilhas por esse fluxo.
6. A voz do desktop usa a síntese disponível no navegador. Pode ser bloqueada ao minimizar, suspender ou fechar a aba. Não confundir isso com navegação de plano de fundo do sistema operacional.

O mapa com tiles **não solicita acesso a OpenStreetMap/CARTO por padrão**: é necessário instalar MBTiles local ou assinalar conscientemente a opção "Permitir tiles online". O roteamento e busca V2 nunca usam o serviço público de demonstração de OSRM.

## Mobile Android existente

O cliente `apps/mobile/` usa o canal HTTPS pareado já existente e o GPS nativo do próprio aparelho. A guia Maps V2 foi adicionada ao painel GPS com busca, escolha de destino, rota no servidor local do PC, manobras, detecção de desvio e TTS nativo. O desenho SVG é um **esquema da geometria real, sem base cartográfica de ruas**. A coleta é feita pelo Java `requestGpsOnce` a cada ~5 s durante o uso em primeiro plano. Ao alternar de GPS para Chat dentro do aplicativo, a sessão continua enquanto o Android mantiver o processo e o app visível.

**Não há serviço Android ForegroundService de localização em segundo plano, notificação persistente, mapa de ruas móvel instalado nem APK compilado/homologado nesta entrega.** Quando o aplicativo fica oculto, as atualizações GPS e a fala param; o usuário deve manter a tela ativa para testar. O telefone requer conexão HTTPS pareada ao PC para resolver rotas; sem PC não há roteamento offline no aparelho.

## Atualização dos dados

- Baixar extrato OSM atualizado no seu próprio processo autorizado.
- Gerar novo grafo em **diretório novo**, mantendo o grafo atual funcionando até a validação (não sobrescrever em uso).
- Parar o contêiner antigo, iniciar com novo caminho de volume e validar rotas antes de descartar o anterior.
- Atualizar Nominatim e Overpass separadamente, garantindo consistência de cobertura; dados de cada serviço não são intercambiáveis.
- Dados desatualizados podem gerar instruções incorretas. Sinalização real e regras de trânsito prevalecem.

## FAILSAFE e rollback

- GPS indisponível → exigir localização manual ou aguardar, nunca inventar origem.
- Roteador indisponível → retornar 503, manter parada de navegação e não anunciar rota.
- Geocodificador indisponível → informar ausência de índice, permitir coordenadas manuais.
- GPS incerto/obsoleto → não processar o ponto; uma única leitura fora da rota não provoca recálculo.
- Desvio confirmado → recálculo local; erro de recálculo marca OFF_ROUTE com aviso, não diz que uma rota foi obtida.
- Mudança de tela do desktop → sessão e watch continuam na aba; fechar aba/servidor ou suspender sistema interrompe.
- API local de administração permanece loopback; mobile utiliza TLS/pareamento. Sem envio de localização a provedor externo.
- Rollback: feche CAMPANÁRIO, restaure **somente** os arquivos de IA a partir do backup R3.15; preserve seus três repositórios, configurações privadas e mapas. Contêineres OSRM/Nominatim/Overpass são serviços independentes e podem ser interrompidos sem apagar os dados.


## R3.20 — localização automática e busca/rota com fallback (23/11/2026)

- Ao abrir Maps no Dark Matter, o cliente tenta `navigator.geolocation.watchPosition` automaticamente, conforme a autorização do Windows/navegador. Mantém latitude, longitude, precisão e horário somente em memória de interface; não envia localização ao servidor durante a simples observação. Sem GPS, busca por endereço permanece disponível e a origem manual continua possível.
- A tela Maps usa somente `CampanarioNavigationV2` para os botões de busca/rota, evitando que o antigo `gps-map.js` sobrescreva os handlers.
- Busca por endereço: Nominatim local primeiro; se estiver indisponível, Nominatim público em consulta explícita. Categoria próxima: Overpass local e depois público; roteamento carro: OSRM local e, se estiver indisponível, servidor público de demonstração OSRM. Caminhada: somente grafo pedestre local (não inventar rota de carro).
- O fallback está **ativado por padrão para uso pessoal** e pode ser desativado com `CAMPANARIO_MAPS_PUBLIC_FALLBACK=false`. Serviços públicos recebem a busca e, em roteamento, as coordenadas. Nominatim público tem limitação de uso, identificação do aplicativo, cache em memória e espaçamento de 1,1 s por host; não usar autocomplete nem disparar varreduras. Não há GPS fictício.
- Pendente: teste de campo em Windows/Android; conectividade e política dos provedores públicos; precisão do GPS no PC; compilação APK e navegação Android em segundo plano. Não declarar homologação de campo.
