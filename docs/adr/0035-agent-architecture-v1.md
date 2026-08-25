# ADR-0035 - Agent Architecture v1

## Status
Aceito.

## Contexto
A foundation organizada passou regressao standard com `gemma3:12b` em 11/11 cenarios e 64/64 checks. O gate pre-agentes foi concluido. O conceito do sistema exige que agentes sejam personas/ponte, nao inteligencias paralelas.

## Decisao
Criar `campanario.agents` com `AgentProfile`, `AgentRegistry` e composicao de persona sobre o contexto compartilhado.

A selecao e persistida por sessao (`chat_sessions.agent_id`) e cada resposta assistant registra o agente que a produziu (`messages.agent_id`). A migration 0003 adiciona somente esses metadados; nenhum banco ou memoria paralela e criado.

O perfil `campanario` e no-op para preservar exatamente a foundation congelada. Todd e Morgana acrescentam apenas identidade, perspectiva e tendencias de expressao ao system context existente.

## Consequencias
- trocar persona nao reinicia contexto nem memoria;
- Response Contract Pipeline, pragmatica, proveniencia e provider permanecem compartilhados;
- novos agentes podem ser adicionados via perfil/registry;
- futura interacao entre agentes deve reutilizar o mesmo core e nao criar loops/modelos independentes sem novo ADR.
