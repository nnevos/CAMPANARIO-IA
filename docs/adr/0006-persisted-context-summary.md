# ADR-0006 — Sumarização de contexto persistida e incremental

**Status:** Aceito em 2026-08-24.

A validação manual de sessão longa mostrou que a janela recente impede crescimento indefinido do prompt, mas também faz fatos antigos desaparecerem do contexto e pode induzir o modelo a inventar lembranças.

Decisão:
- manter o histórico original de mensagens intacto;
- persistir um resumo separado por sessão em `context_summaries`;
- registrar até qual `message_id` o resumo cobre;
- atualizar o resumo somente com mensagens antigas ainda não cobertas;
- enviar ao modelo `system summary + janela recente`;
- se a atualização do resumo falhar, continuar com a janela recente em vez de derrubar o chat.

O resumo é mecanismo de gerenciamento de contexto, não memória cognitiva/episódica/semântica e não autoriza RAG, embeddings ou knowledge graph.
