# ADR 0044 — Dialogue State Compiler

## Status

Aceito para P2.4; aguardando revalidacao real Long Call.

## Contexto

P2.3b–P2.3e adicionaram Working Conversation State, Focus Stack e bindings pragmaticos. Esses mecanismos melhoraram a continuidade, mas o modelo ainda recebia um conjunto relativamente grande de instrucoes e precisava reconstruir a funcao do turno durante a propria geracao. Seeds diferentes mostraram falhas intermitentes em `mesma pergunta`, `aterrissa isso`, `sequencia curta`, `resume a decisao`, retornos de topico e escolhas de produto.

## Decisao

Criar `src/campanario/chat/dialogue_state.py` com `DialogueState` e `DialogueStateCompiler`.

Antes de cada chamada de agente, `ChatService` compila deterministicamente o historico em um estado curto contendo objeto raiz, assunto ativo, pedido resolvido, referente imediato, escolhas do usuario, troca anterior relevante, assuntos suspensos, assumptions proibidas e sinais de fechamento/ack.

O compilador:

- nao chama outro modelo;
- nao e memoria persistente;
- nao altera Personality Core;
- nao promove tangentes do assistant a fatos do usuario;
- reutiliza o Focus Stack apenas como estrutura interna de topicos;
- torna follow-ups elipticos em pedidos explicitos antes da geracao;
- preserva o objeto do usuario contra auto-referencia indevida ao Campanario.

`working_conversation_note()` permanece apenas como compatibilidade/testes legados; o runtime passa a usar `DialogueStateCompiler`.

## Consequencias

Positivas:

- estado testavel diretamente sem depender da resposta do LLM;
- menos prompt patchwork;
- base reutilizavel futuramente por Web, Call, Mobile e Platform Runtime;
- melhor separacao entre interpretar a conversa e responder.

Custos:

- heuristicas deterministicas ainda precisam evoluir com atos discursivos novos;
- o compilador nao substitui memoria/Experience Layer;
- a revalidacao com Gemma continua obrigatoria.
