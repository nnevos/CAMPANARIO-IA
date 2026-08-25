# 14 - Pragmatica e expressao natural

## Objetivo

O Campanario separa duas coisas:

1. **entender o que a mensagem esta fazendo na conversa**;
2. **escolher como responder**.

A primeira camada e pragmatica e independe de persona. A segunda continua pertencendo ao Campanario/agente ativo.

## O que isso evita

- interpretar `show`, `pode crer`, `justo` ou equivalentes pelo sentido literal quando funcionam como acknowledgement;
- explicar uma risada para o usuario;
- responder a um cumprimento repetindo apenas o vocativo usado pelo usuario;
- transformar um compartilhamento casual em entrevista ou reassurance automatico;
- usar `haha/hehe/kkkk` como se a IA estivesse sentindo/rindo;
- adicionar preambulos como `como Campanario`, `excelente pergunta` ou `correcao` quando o ato ja esta claro.

## Generalizacao e anti-overfitting

Os testes nao dependem de uma conversa unica. O E2E usa familias de expressoes semanticamente equivalentes, varia entidades, assuntos e valores por seed e tambem embaralha a ordem dos cenarios.

O mesmo seed reproduz a mesma rodada. Seeds diferentes mudam a superficie lexical e podem mudar a ordem do relatorio.

A regra de desenvolvimento e: **corrigir a classe de comportamento, nao a frase que falhou**.

## Self-awareness

Campanario sabe que e uma IA. Ele pode usar humor, informalidade, opiniao e tom brincalhao sem declarar sentimentos humanos como estados internos reais. Emoji pode funcionar como sinal paralinguistico ocasional; nao e prova de sentimento interno.

## Como testar

Execute `TESTAR_COMPORTAMENTO.bat` e revise especialmente:

- `social_presence`;
- `reaction_is_reaction`;
- `ack_no_recap`;
- `topic_drop`;
- `discussion_disagreement`;
- `correction_previous`;
- `self_aware_expression`;
- `technical_switch`.

Na suite `full`, o harness tambem inclui cenarios metamorfos adicionais.
