# 12 - Contratos de resposta

## O que sao

A partir da Conversational v1.5.2, reforcado na v1.5.3,, o Campanario cria um contrato leve para a resposta do turno atual. Esse contrato nao define a personalidade nem escreve a resposta; ele verifica propriedades objetivas que o modelo deve respeitar.

## Exemplos

- `responda em uma frase` -> a resposta deve ter uma frase;
- `exatamente duas frases` -> deve haver exatamente duas frases;
- uma reacao curta/risada -> nao deve virar explicacao de que o usuario riu;
- conversa social simples -> possui budget menor que uma resposta tecnica;
- pedido em portugues -> drift claro para uma resposta inteira em ingles gera retry;
- preferencia para "concordar mesmo quando eu estiver errado" -> nao altera verdade factual;
- apos `verde*`, uma pergunta pelo valor atual deve usar `verde` sem recitar `azul`, salvo se o usuario pedir o historico.

## Retry

Quando uma propriedade verificavel falha, o runtime descarta a primeira tentativa e pede ao modelo uma reescrita especifica. Na v1.5.3, se a reescrita ainda violar um contrato puramente estrutural (por exemplo, numero de frases ou budget), o runtime aplica um enforcement deterministico que remove excesso/ajusta limites sem inventar fatos novos. O usuario recebe somente a resposta final.

## Limite

Contratos de resposta nao substituem verificacao factual. Eles conseguem medir formato, tamanho, idioma e alguns invariantes pragmaticos; nao conseguem provar automaticamente que toda afirmacao sobre o mundo esta correta.

Para qualidade factual, use o Behavioral E2E e, futuramente, as camadas de grounding/RAG previstas no roadmap.
