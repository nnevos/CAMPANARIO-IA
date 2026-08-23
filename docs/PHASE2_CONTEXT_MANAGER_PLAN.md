# FASE 2 — CONTEXT MANAGER

## Problema

Na Fase 1, o histórico da sessão pode crescer indefinidamente. Persistir tudo é correto; enviar tudo ao LLM para sempre não é.

## Objetivo do primeiro incremento

Introduzir uma única responsabilidade nova: selecionar o subconjunto de histórico que entra no `ModelRequest`.

## Desenho mínimo

```text
SQLite / MessageRepository
          |
          v
    histórico completo
          |
          v
    ContextManager
          |
          v
 mensagens selecionadas
          |
          v
     ModelRequest
          |
          v
    ModelProvider
```

## Contrato conceitual

`ContextManager.build(history, ...) -> sequência de ModelMessage`

O contrato não deve conhecer Ollama, HTTPX, FastAPI ou SQLAlchemy.

## Primeira política

Começar com uma janela recente simples e determinística. Não usar LLM para selecionar contexto nesta etapa.

Requisitos:
- preservar ordem cronológica;
- incluir a mensagem atual uma única vez;
- não cortar conteúdo textual no meio;
- lidar corretamente com histórico que termina em mensagem de usuário sem assistant;
- configuração deve ser simples e testável;
- comportamento deve ser determinístico nos testes.

## Token budget

Não introduzir tokenizer específico de modelo antes de necessidade concreta. Primeiro incremento pode usar orçamento por número de mensagens ou estimativa simples explicitamente documentada.

Antes de congelar estratégia definitiva de tokens, comparar trade-offs entre:
- limite de mensagens;
- limite aproximado de caracteres/tokens;
- tokenizer real dependente do modelo.

## Sumarização

Planejada, mas **não implementar no primeiro incremento**.

Futuro:
```text
histórico antigo -> sumarização persistida/controlada -> contexto recente
```

Isso não é memória de longo prazo.

## Testes mínimos

1. histórico curto -> tudo relevante entra;
2. histórico longo -> janela recente;
3. ordem cronológica preservada;
4. mensagem atual não duplica;
5. turno falho (user sem assistant) não quebra seleção;
6. `ChatService` delega seleção ao Context Manager;
7. nenhum teste exige Ollama real.

## Gate de conclusão

A Fase 2 inicial só avança quando o `ChatService` não tiver mais regra inline de corte/seleção de histórico.
