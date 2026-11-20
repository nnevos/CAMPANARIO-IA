# CAMPANÁRIO V7 — Dark Matter (interface completa)

## Escopo
Camada visual global aplicada sobre a V6.1, preservando endpoints, código de mapas, conversação, agentes, preferências persistentes, banco de diálogos, ferramentas e permissões.

## Modificações
- `src/campanario/web/static/dark-matter-v7.css`: tokens de cores preto-carvão, painéis foscos, bordas neutras, sem degradês ou glow artificial; cores de agentes discretas; contraste e estados de foco.
- `src/campanario/web/index.html`: carrega a folha V7 depois das camadas anteriores e ajusta `theme-color`.
- Todas as páginas que usam o shell (Início, Database, Patrulha, Configurações) recebem a nova linguagem.
- O mapa mantém o seletor e o comportamento da V6.1: estilo escuro alternativo sem chave; CARTO original com chave, se configurada.
- Tipografia mantida: Chakra Petch, IBM Plex Sans, JetBrains Mono (fontes remotas com fallback local).
- Mobile: superfícies uniformes, foco acessível, controles com alvos mínimos e respeito à área segura.

## Observações
- Não foram adicionados dados fictícios nem alterados os mecanismos de personalidade.
- A verificação estática não substitui teste visual no aplicativo Windows e em Android.
- Os gradientes e sombras internos de widgets de terceiros podem requerer ajustes adicionais se houver componentes não cobertos pela camada de estilo.
