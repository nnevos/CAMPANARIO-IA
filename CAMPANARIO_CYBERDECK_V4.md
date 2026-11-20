# Campanário — Cyberdeck UI V4

Atualização **visual e responsiva** baseada na V3 com preferências persistentes. A arquitetura de personalidade, a biblioteca, o banco de dados, os endpoints e os mecanismos de Patrulha permanecem inalterados.

## Mudanças
- Camada de estilo `src/campanario/web/static/cyberdeck.css`, carregada após `shell.css` para preservar a implementação existente.
- Hierarquia tipográfica: **Chakra Petch** em títulos e comandos; **IBM Plex Sans** em texto; **JetBrains Mono** em dados, estados e etiquetas. O CSS tenta carregar as fontes do Google Fonts quando há internet; sem internet, usa fontes de fallback do sistema. Para instalação totalmente offline, hospede legalmente as fontes localmente e altere as URLs de `@font-face`.
- Fundo central agora mostra **somente o sigilo do Campanário**, com iluminação sutil. Morgana e Todd permanecem nas mensagens e nos componentes de identificação, não como marca-d'água.
- Textura de grade discreta, superfícies técnicas, bordas, contraste, telemetria ambiental e estados de foco.
- Database com cartões de largura mais legível; sem inventar indexação documental ou alterar dados.
- Patrulha com mapa priorizado no tablet/mobile, controles maiores e layout vertical.
- Versão mobile (`apps/mobile/www/style.css`) recebeu a mesma identidade e apenas o sigilo central no fundo.
- Suporte a `prefers-reduced-motion`, safe areas, `100dvh` e campos de texto com tamanho adequado para teclado móvel.

## Observações
- As fontes externas são **opcionais** e podem gerar tráfego ao Google Fonts quando há internet. Remova os `@import` se desejar offline estrito.
- A telemetria visual é decorativa e não simula valores reais de CPU, memória ou sensores.
- Não houve execução de Ollama, Electron/Tauri ou teste em Android real neste ambiente. É necessário testar os breakpoints e as funcionalidades em execução no seu PC/celular.
- Para reverter, remova o `<link>` para `cyberdeck.css` no `index.html` e restaure `apps/mobile/www/style.css` e o trecho do sigilo central do `index.html` a partir da V3.
