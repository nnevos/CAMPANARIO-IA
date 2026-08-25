# FASE 2 — CONTEXT MANAGER

## Problema

Persistir todo o histórico é correto; enviar todo o histórico ao LLM indefinidamente não. A janela recente resolveu o crescimento do prompt, mas o teste manual mostrou perda de continuidade: ao sair da janela, fatos antigos deixaram de estar disponíveis e o modelo inventou uma lembrança.

## Incremento 1 — janela recente — concluído

`RecentMessagesContextManager` mantém uma janela determinística por quantidade de mensagens concluídas, default 20, preservando ordem cronológica e evitando começar por `assistant` órfão quando o corte atravessa um turno.

## Incremento 2 — sumarização persistida — implementado em 2026-08-24

Fluxo atual:

```text
historico completo no SQLite
        |
        +--> trecho antigo --> resumo incremental persistido
        |
        +--> janela recente -------------------------+
                                                     v
                                    system summary + recent messages
                                                     |
                                                     v
                                              ModelRequest
```

Regras:
- o histórico original nunca é substituído pelo resumo;
- o resumo vive em `context_summaries`, separado de `messages`;
- cada resumo registra `through_message_id`, evitando resumir novamente o mesmo prefixo;
- quando novas mensagens saem da janela, o resumo anterior + apenas o novo trecho antigo são enviados ao modelo de sumarização;
- o resumo é limitado por `CAMPANARIO_CONTEXT_SUMMARY_MAX_CHARS` (default 4000);
- o prompt de sumarização exige preservar fatos, nomes, preferências, decisões e referências úteis, sem invenção;
- o contexto final contém o resumo como mensagem `system` seguido da janela recente;
- se a sumarização falhar por erro do provider, o chat continua usando apenas a janela recente;
- isso continua sendo gerenciamento de contexto, não memória cognitiva.

## Contrato

`ContextManager.build(history)` agora é assíncrono porque a política de sumarização pode chamar o `ModelProvider`.

## Persistência

Migration `0002` cria `context_summaries`:
- `session_id` (PK/FK);
- `content`;
- `through_message_id` (FK);
- `updated_at`.

## Validação automatizada

Coberto:
1. janela curta e longa;
2. ordem cronológica;
3. `assistant` órfão no corte;
4. `user` sem resposta;
5. mensagens não concluídas;
6. delegação do `ChatService`;
7. criação e persistência do resumo;
8. reutilização do resumo sem resumir o mesmo prefixo;
9. atualização incremental quando a janela avança;
10. fallback para janela recente quando o provider falha;
11. round-trip do repositório de resumo.

Suíte após Incremento 2: **18/18 testes**.

## Incremento 3 — resumo estruturado/source-aware — implementado em 2026-08-24

Após o teste manual revelar contaminação por texto do assistant, o resumo deixou de ser texto livre e passou a usar JSON estruturado v1 dentro de `context_summaries.content`.

Campos atuais: `first_user_message`, `user_facts`, `user_preferences`, `user_plans`, `user_constraints`, `conversation_topics` e `assistant_context`. Mensagens do usuário são a fonte primária para fatos pessoais/planos; a extração autoritativa não recebe texto do assistant. `assistant_context` é resumido em uma chamada separada e é explicitamente não autoritativo. Resumos legados em texto livre são reconstruídos a partir do histórico original. JSON inválido não é persistido e mantém o fallback para a janela recente.

ADR: `docs/adr/0007-source-aware-context-summary.md`.

Validação automatizada: **21/21 testes**.

## Gate final — APROVADO em 2026-08-24

Validação real no Windows/Ollama confirmou preservação exata de `CODIGO-TESTE-4821`, `capivara`, `verde`, `Marte` e `astronomia/história/programação`, inclusive após reinício. Sugestões do assistant deixaram de contaminar os fatos do usuário. A Fase 2 está encerrada.

O próximo trabalho não altera o mecanismo de memória/contexto: é uma fundação comportamental transversal, registrada em ADR-0008, para melhorar naturalidade e reduzir invenções antes de agentes completos. Memória cognitiva/RAG e Morgana/Todd independentes continuam fora deste gate.

## Evidência manual que motivou o Incremento 3
O teste longo/reinício confirmou persistência parcial, mas revelou contaminação/distorção de fatos no resumo (especialmente os assuntos dos três livros) e uma resposta falsa de que o contexto havia sido perdido após reinício. O Incremento 3 foi implementado exatamente para tratar essa evidência; agora falta validá-lo no ambiente real. A referência em `docs/reference/dialogue_examples/` continua apenas como material de comportamento/testes e não está ativa no runtime.
