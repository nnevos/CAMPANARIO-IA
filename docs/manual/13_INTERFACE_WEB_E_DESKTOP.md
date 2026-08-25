# 13 - Interface web e futuro desktop

## Hoje

O Campanario roda como servico local e a interface e aberta no navegador em `http://127.0.0.1:8000/`.

Isso e uma arquitetura valida para a maior parte do projeto: chat, agentes, memoria, RAG, configuracoes, arquivos, testes, modelos e dashboards podem continuar no frontend web.

## Por que nao fazer um programa desktop inteiro agora

Transformar tudo em UI nativa cedo adicionaria complexidade sem melhorar o nucleo da inteligencia. O backend FastAPI ja cria uma fronteira limpa entre interface e sistema.

## Quando desktop nativo passa a valer a pena

Principalmente para:
- wake word sempre ativo;
- hotkeys globais;
- tray icon/startup com Windows;
- audio em background;
- overlays/notificacoes;
- integracao profunda com automacao do sistema.

A recomendacao e envolver a UI web existente em uma shell desktop leve quando essas funcoes entrarem. O core do Campanario nao deve ser reescrito.
