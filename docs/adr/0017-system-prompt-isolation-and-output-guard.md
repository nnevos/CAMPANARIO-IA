# ADR-0017 — System prompt isolation and output guard

## Contexto

Na validacao manual da Conversational v1.4, uma mensagem social simples (`salve`) fez o modelo local ecoar/reformular instrucoes internas do Campanario. O request continha mais de uma mensagem com role `system`, incluindo um boundary de turno inserido imediatamente antes do usuario.

Templates de chat locais podem interpretar multiplos blocos `system` de forma diferente. O comportamento observado e classificado como P0 porque instrucoes internas nao devem chegar a saida visivel.

## Decisao

1. `BehaviorContextManager` deve produzir exatamente um bloco `system`, sempre na primeira posicao do request.
2. O turn boundary, modo atual, semantica de continuacao e contexto persistido sao compostos nesse unico bloco lider.
3. Nao inserir mensagens `system` entre mensagens `user`/`assistant`.
4. Todo provider usado no runtime e envolvido por `PromptLeakGuardProvider`.
5. O guard mantem uma janela de seguranca no stream e bloqueia a resposta se detectar marcadores estruturais internos do Campanario, inclusive quando o marcador cruza chunks.
6. Em caso de deteccao, falhar explicitamente e nao persistir a resposta do assistant.

## Consequencias

- reduz compatibilidade ambigua com chat templates locais;
- preserva isolamento de modo sem role `system` intermediaria;
- adiciona defesa em profundidade contra prompt leakage;
- respostas curtas podem sofrer pequeno buffering inicial para permitir a verificacao do stream;
- Pragmatic Input Understanding permanece desconectado do runtime ate o gate comportamental ser retomado.
