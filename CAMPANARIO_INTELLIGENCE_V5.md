# CAMPANÁRIO — Intelligence UI V5

## Objetivo
Evolução visual da V4 para um painel de inteligência com inspiração nas três referências fornecidas, mantendo o núcleo, os agentes, a Biblioteca Conversacional V2 e as preferências persistentes V3.

## Implementado
- Nova folha `src/campanario/web/static/intelligence-v5.css`, aplicada depois do tema V4; HUD ciano operacional, tipografia Chakra Petch / IBM Plex Sans / JetBrains Mono (com fallback local), bordas técnicas e contraste.
- Núcleo Campanário como único sigilo ambiental. Morgana e Todd permanecem em componentes de participação e mensagens, com estados visuais existentes.
- `intelligence-v5.js` liga a etiqueta do HUD ao estado e à página realmente reportados pela interface; não inventa telemetria.
- Database com histórico em lista compacta e datas legíveis pt-BR, sem alterar o formato armazenado no servidor.
- Patrulha com mapa dominante, painel de controle lateral rolável no desktop, mapa em primeiro lugar no mobile e retículas decorativas que não capturam eventos do mapa.
- Breakpoints 1000 / 700 / 390 px, campos legíveis, botões tocáveis e respeito a movimento reduzido.

## Limites
Não há feeds de inteligência, radar, satélite, clima, telemetria de sistema, GPS ou mapas novos simulados. A fonte de mapa permanece a já integrada. A disponibilidade de fontes Google depende da conexão; há fallback. Não foram alteradas permissões, endpoints, banco de memória ou modelos. Teste visual final em Windows/Android e Ollama deve ser feito na instalação real.

## Verificação
`node --check` nos JS alterados; integridade ZIP validada. Não há validação end-to-end de hardware neste ambiente.
