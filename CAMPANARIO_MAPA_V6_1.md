# Campanário V6.1 — correção do mapa

A CARTO passou a exigir chave de API em setembro de 2026. A V6 solicitava tiles Dark Matter sem chave, gerando a marca d’água API KEY REQUIRED.

## Funcionamento
- **Padrão sem configuração:** OpenStreetMap raster com filtro escuro aplicado somente ao mapa, sem chave. É uma aproximação visual, **não** o estilo oficial CARTO Dark Matter.
- **CARTO Dark Matter original:** solicite sua chave em https://carto.com/basemaps/apikey/ e cole no campo da Patrulha, clicando em Aplicar chave. A chave é salva apenas no armazenamento local do navegador/aplicativo e enviada ao servidor CARTO na URL de cada tile.
- **Offline:** MBTiles PNG já instalado mantém seu próprio estilo e não recebe filtro nem requer chave.
- Marcadores, trilhas, rotas e navegação permanecem no canvas e não recebem o filtro de cores.
- A atribuição CARTO só aparece quando seu serviço está selecionado.

## Limitações
A disponibilidade dos tiles depende da internet e das políticas dos provedores. O modo sem chave usa OpenStreetMap e não é cartografia Dark Matter oficial. Não houve teste ponta a ponta em Windows/Android com rede real neste ambiente.
