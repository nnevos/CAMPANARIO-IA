# Experience / Learning

Campanario agora possui memoria experiencial compartilhada por Todd e Morgana.

## O que ele aprende automaticamente
A captura automatica e conservadora. Exemplos de alta confianca:

- `meu sistema operacional e Windows 11`;
- `eu prefiro respostas curtas`;
- `lembre que meu projeto principal e X`;
- uma resposta curta a uma pergunta realmente necessaria sobre seu contexto;
- `isso funcionou` / `isso nao funcionou` apos uma estrategia proposta.

Ele nao deve transformar toda conversa em perfil nem guardar automaticamente senhas/tokens e outros segredos.

## Curiosidade
Quando uma resposta depende de algo que o sistema nao sabe sobre voce, Todd/Morgana podem perguntar. A regra e fazer uma pergunta curta apenas se o dado realmente mudar a resposta. Se for possivel responder bem sem isso, eles devem seguir sem interrogatorio.

## Inspecao
`GET /api/v1/memory`

Inclua `?include_inactive=true` para ver memorias superseded/forgotten.

## Correcao
`PATCH /api/v1/memory/{memory_id}` com `value` e `reason` cria uma nova evidencia confirmada e preserva a anterior como superseded.

## Esquecimento
`POST /api/v1/memory/{memory_id}/forget` marca a memoria como forgotten. Na conversa, pedidos explicitos e estreitos como `esquece sobre meu editor` tambem sao reconhecidos.

## Importante
Memoria experiencial nao reescreve a Personality Core e nao e fine-tuning automatico do modelo.
