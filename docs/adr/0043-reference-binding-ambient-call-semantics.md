# ADR 0043 — Reference Binding e Ambient Call Semantics

## Contexto

O Long Call seed `1787678674` chegou a 0 FAILs, mas follow-ups elipticos ainda podiam perder o referente mesmo com historico e Conversation Focus Stack. A call social tambem mostrou uma interpretacao errada: exigir nome/wake a cada turno ou palavra especial para permitir pensamento em voz alta.

## Decisao

Manter o Focus Stack deterministico e adicionar uma camada estreita de binding pragmatico dentro do briefing temporario:

- `mesma pergunta` -> pergunta anterior do usuario;
- `resposta/ponto dele/dela` -> fala imediatamente anterior relevante;
- `aterrissa isso` -> ideia da fala imediatamente anterior;
- `sequencia curta` -> problema imediatamente anterior;
- `so o essencial` -> questao imediatamente anterior;
- `qual coisa cortar/preservar` -> escolhas recentes definidas pelo usuario;
- `primeira ideia` -> abertura da call + escolhas/restricoes do usuario;
- `resume a decisao` -> conclusao da troca anterior, sem metalinguagem.

Quando o usuario declara que uma arquitetura apenas incomoda mas nao esta quebrando, o contexto registra somente essa incerteza e proibe inventar subsistemas concretos.

No Social Protocol, call ambiente significa que nomes sao opcionais para enderecamento explicito. Em pensamento em voz alta sem pergunta/pedido/risco, silencio e comportamento preferivel; nao existe palavra magica para `nao responder`.

## Consequencias

- nenhuma segunda inferencia;
- nenhuma memoria persistente nova;
- nenhuma alteracao no Personality Core;
- melhora de continuidade depende de fatos do usuario, nao de resumo criativo do assistant;
- Long Call E2E passa a testar funcao pragmatica, nao apenas tema/speaker.
