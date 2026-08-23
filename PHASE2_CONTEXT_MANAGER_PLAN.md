# FASE 2 — PLANO INICIAL DO CONTEXT MANAGER

## Objetivo

Evitar que todo o histórico da sessão seja enviado indefinidamente ao LLM.

## Primeiro incremento proposto

- Criar contrato `ContextManager`.
- Criar implementação inicial `RecentMessagesContextManager`.
- Configuração inicial por quantidade/orçamento simples.
- Receber histórico completo e devolver `ModelMessage[]`.
- Garantir ordem cronológica.
- Preservar pares de conversa quando possível.
- Ignorar artefatos inválidos já bloqueados na borda.
- Não implementar sumarização ainda.

## Testes mínimos

1. conversa curta -> todo histórico entra;
2. conversa longa -> somente janela recente entra;
3. ordem cronológica preservada;
4. mensagem do usuário sem resposta posterior não quebra contexto;
5. system messages futuras podem ser acomodadas sem reescrever tudo;
6. `ChatService` passa a depender de `ContextManager`, não de regra inline.

## Critério de conclusão do incremento

`ChatService` não decide diretamente quantas mensagens antigas enviar.
Essa responsabilidade pertence ao Context Manager.
