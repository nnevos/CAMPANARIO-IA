# 12 - Agentes: Morgana e Todd

## Como pensar neles

Campanario e o sistema. Morgana e Todd sao IAs-persona que permanecem presentes no mesmo espaco de conversa e usam a mesma inteligencia, contexto, memoria e capacidades.

**Morgana tem prioridade padrao de fala.** Isso nao significa que Todd esteja desligado.

## Chamadas

- `Campanario` -> chama o sistema; quem tem prioridade responde primeiro.
- `Morgana` -> Morgana passa a ter prioridade.
- `Todd` -> Todd passa a ter prioridade.
- `Campanario, chama o Todd` -> Todd passa a ter prioridade.
- `Todd e Morgana, o que voces acham?` -> ambos podem responder no mesmo turno.

Os botoes Morgana/Todd no topo da interface mudam **prioridade de fala**, nao presenca.

## Participacao espontanea

Em conversas abertas, o segundo agente pode entrar se tiver algo realmente distinto para acrescentar. O Campanario usa um arbitro conservador para evitar que toda mensagem gere duas respostas.

Ele tende a nao convocar o segundo agente em cumprimentos, acknowledgements, perguntas factuais simples ou tarefas diretas. Convites explicitos aos dois sempre permitem participacao conjunta.

## Interacao entre eles

Os agentes podem complementar, discordar, concordar e falar um com o outro. Isso continua dentro das mesmas regras de factualidade, memoria e autonomia do usuario.

## O que continua compartilhado

- historico e contexto;
- memoria do Campanario;
- modelo ativo;
- factualidade/evidencia;
- Response Contract Pipeline;
- futuras tools/RAG/web.

Nao existe um banco ou "cerebro" independente por agente.
