# Arquitetura atual — Persistent Participants v1.2

```text
Usuario / UI
    |
    v
Campanario (sistema)
    |- Chat/Context/Pragmatics
    |- Shared memory/evidence boundary
    |- AgentRouter -> prioridade de fala
    |- ParticipationArbiter -> entrada secundaria opcional
    |    |- Morgana (default primary)
    |    `- Todd
    |- Response Contract Pipeline
    |- Model Runtime (Gemma 3 12B recomendado; substituivel)
    `- SQLite persistence
```

## Separacoes obrigatorias

- sistema != agente;
- prioridade != exclusividade;
- persona != verdade;
- participant decision != conteudo da resposta;
- modelo != comportamento do Campanario;
- UI web != core (desktop futuro pode reutilizar ambos).

## Multi-speaker

Uma mensagem do usuario pode gerar uma ou duas falas. Cada fala passa pela mesma pipeline, e `messages.agent_id` registra o speaker real. O segundo agente entra apenas quando ha convite explicito ou valor conversacional distinto identificado de forma conservadora.
