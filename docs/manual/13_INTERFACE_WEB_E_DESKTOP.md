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

## Identidade visual dos agentes

A interface principal usa uma base monocromática (preto, branco e cinzas) para reduzir ruído visual. As cores de identidade ficam reservadas aos agentes: **Morgana usa amarelo** e **Todd usa vermelho**.

As falas dos agentes exibem um retrato quadrado imediatamente antes do conteúdo. O mesmo retrato aparece em miniatura na faixa de presença. Essas imagens são elementos de identidade visual da UI e não alteram roteamento, personalidade, memória ou prioridade de fala.

## Núcleo de presença animado

A Presence UI mantém a estética de ambiente escuro com profundidade, superfícies translúcidas e um núcleo circular central. O núcleo respira/pulsa de forma contínua para indicar presença sem simular voz. Em repouso ele é neutro; quando um agente entra em fala, a luz do núcleo herda a identidade visual desse agente: **âmbar/dourado para Morgana** e **vermelho para Todd**. A animação respeita `prefers-reduced-motion`.

