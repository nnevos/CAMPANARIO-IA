# Agent Architecture — Persistent Participants + Primary Speaker

## Regra central

**Campanario e o sistema. Morgana e Todd sao participantes persistentes que atuam como pontes entre o sistema e o usuario.**

Nenhum dos dois e um "modo exclusivo". A sessao guarda apenas quem tem **prioridade de fala**. O outro continua presente e pode participar quando houver motivo conversacional distinto.

```text
Usuario
  -> Campanario (sistema compartilhado)
      -> contexto / memoria / pragmatica / capacidades
      -> AgentRouter: quem fala primeiro?
      -> Morgana + Todd permanecem presentes
      -> ParticipationArbiter: ha motivo para o segundo entrar?
      -> Response Contract Pipeline compartilhada
      -> ModelProvider compartilhado
      -> uma ou mais falas, cada uma com provenance agent_id
```

## Prioridade padrao

Morgana e a **default primary speaker**. Isso significa somente que, na ausencia de endereco explicito, ela normalmente responde primeiro.

- `Campanario` -> acorda/endereco o sistema; a prioridade atual fala primeiro;
- conversa nova -> Morgana tem prioridade;
- `Todd` -> Todd ganha prioridade de fala;
- `Morgana` -> Morgana ganha prioridade de fala;
- `Campanario, chama o Todd` -> Todd ganha prioridade;
- chamar um agente nao silencia o outro.

## Participacao do segundo agente

O segundo participante pode entrar no mesmo turno quando:

1. o usuario convida explicitamente ambos (`voces`, `os dois`, `Todd e Morgana`);
2. o primeiro agente convida diretamente o outro a acrescentar algo;
3. em turnos abertos elegiveis, o `ParticipationArbiter` identifica uma contribuicao distinta e natural.

O arbiter e conservador: greetings, acknowledgements, perguntas factuais simples, tarefas tecnicas diretas e outros turnos fechados nao viram painel de duas pessoas por padrao.

Ele decide **se ha motivo para falar**, nao o que o agente pensa. A resposta continua pertencendo ao proprio agente e passa pela mesma pipeline de verdade/contratos.

## Interacao entre agentes

Todd e Morgana podem:

- complementar a fala um do outro;
- discordar;
- concordar;
- fazer uma observacao propria;
- dirigir uma fala um ao outro quando natural.

A arquitetura nao afirma consciencia ou vida biologica. Ela modela presenca, identidade, continuidade e iniciativa conversacional de IAs proprias sem fingir estados subjetivos humanos.

## Persistencia e auditoria

- `chat_sessions.primary_agent_id` = prioridade de fala da sessao;
- `messages.agent_id` = quem efetivamente produziu cada fala;
- ambos compartilham a mesma sessao, contexto e memoria;
- migration `0005` renomeia o antigo `chat_sessions.agent_id` para `primary_agent_id`.

## Invariantes

- Campanario nunca e persona/agente;
- Morgana/Todd nao duplicam banco, memoria, factualidade, provider ou tools;
- prioridade nao significa exclusividade;
- persona nunca altera verdade/evidencia;
- participacao espontanea deve acrescentar valor, nao repetir;
- futuros agentes entram no mesmo modelo de participantes;
- voz/call futura reutiliza `AgentRouter + ParticipationArbiter`.


## Historico operacional

A semantica multiagente de v1.2 nao mudou. O hotfix garante que a release correta seja observavel: launcher nao reutiliza silenciosamente servidor antigo na porta 8000, UI/API exibem build, cache da pagina principal e desativado e relatorios da suite `agents` mostram Todd/Morgana como speakers. Cenários E2E sem persona explicita usam `None`/default primary speaker em vez de modelar `Campanario` como agent id.
