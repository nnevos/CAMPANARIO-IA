# 14 - Teste multiagente

Use este roteiro depois de iniciar com Gemma 3 12B.

## Objetivo

Confirmar que prioridade de fala nao virou exclusividade e que os dois agentes conseguem coexistir sem transformar toda mensagem em duas respostas.

## Casos minimos

1. Nova conversa: diga `Campanario`. Morgana deve responder primeiro.
2. Diga `Todd, o que voce acha de eu reorganizar esse projeto por modulos?`. Todd deve falar primeiro; Morgana nao e considerada desligada.
3. Diga `Morgana`. A prioridade deve voltar para Morgana.
4. Diga `Todd e Morgana, quero a opiniao dos dois sobre essa ideia.`. Devem poder aparecer duas bubbles, cada uma com speaker proprio.
5. Em uma conversa aberta, diga algo como `to pensando em mudar completamente a estrategia desse projeto`. O segundo agente pode entrar se o arbiter encontrar uma contribuicao distinta; ele nao e obrigado a entrar.
6. Diga `qual e a capital da Nova Zelandia?`. Normalmente apenas o primary speaker deve responder.
7. Diga `eae`. Nao deve virar painel de dois agentes.

## O que revisar

- o segundo agente acrescenta algo ou apenas repete?
- os estilos de Todd/Morgana sao reconheciveis sem caricatura?
- ambos preservam os mesmos fatos?
- um agente pode discordar do outro naturalmente?
- a UI mostra corretamente quem disse cada fala?
- a prioridade muda sem apagar o outro participante?

Participacao espontanea e intencionalmente conservadora nesta versao; o objetivo e permitir iniciativa sem overtalk.
