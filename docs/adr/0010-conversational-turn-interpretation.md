# ADR-0010 — Interpretacao conversacional leve antes de personas completas

## Status

Aceito em 2026-08-24.

## Contexto

O Behavior v2.1 melhorou factualidade simples, coerencia sim/nao e obediencia a formato, mas o teste
manual mostrou que `oi` e `beleza?` ainda eram tratados como atendimento, perguntas simples continuavam
verbosas e a autoanalise preenchia categorias genericas em vez de inspecionar a conversa de verdade.

Continuar acrescentando regras globais ao system prompt aumentaria acoplamento e tenderia a deixar a
conversa artificial. O conceito do Campanario estabelece conversa casual e companhia como casos de uso
de primeira classe.

## Decisao

Adicionar `ConversationTurnInterpreter`, deterministico e sem chamada extra ao LLM, dentro da camada
comportamental. Ele classifica o turno atual apenas para orientar estilo e profundidade:

- `social`;
- `factual_simple`;
- `technical`;
- `discussion`;
- `creative`;
- `audit`;
- `general`.

A classificacao nao decide fatos, memoria, seguranca, ferramentas nem agente. Ela injeta uma dica curta
no system context do turno. Para `audit`, a camada tambem inclui um trace observavel das respostas
recentes (tamanho, pergunta final e trecho), ajudando o modelo a auditar comportamento concreto.

## Consequencias

- Conversa casual pode permanecer curta sem depender de uma longa lista de excecoes no prompt.
- Pedidos tecnicos podem receber mais estrutura sem contaminar papo social.
- Autoanalise ganha evidencia observavel sem criar uma segunda chamada ao modelo.
- O interpretador e reversivel e pode ser substituido por um classificador melhor no futuro.
- Todd/Morgana continuam inativos; um roteador de agentes futuro pode consumir sinais semelhantes sem
  acoplar a identidade do Campanario a este classificador.
- Classificacao heuristica pode errar; por isso ela deve ser tratada como dica de estilo, nunca como
  autoridade semantica/factual.
