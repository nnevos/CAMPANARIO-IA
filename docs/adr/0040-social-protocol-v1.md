# ADR 0040 — Social Protocol v1 para conversa multiagente

## Contexto

O Behavioral E2E integrado real (Gemma 3 12B, seed `1787664681`) teve 3 PASS / 1 WARN / 0 FAIL, com 51 PASS / 2 WARN / 0 FAIL. A conversa mostrou boa complementaridade e silêncio seletivo, mas revelou duas falhas de etiqueta do sistema: (1) menção ao nome do outro agente dentro de um endereçamento direto era interpretada como convite de grupo; (2) uma resposta podia simular labels como `Campanario:` / `Morgana:` dentro da própria bubble.

## Decisão

Adicionar um protocolo social compartilhado, separado de Personality Core, aplicado a Todd e Morgana na composição de contexto.

O protocolo estabelece que participantes devem:
- escutar antes de entrar;
- não repetir/parafrasear contribuição suficiente apenas para marcar presença;
- acrescentar função nova quando entram;
- aceitar silêncio como comportamento válido;
- distinguir referência ao outro de convite ao outro;
- corrigir ideias sem disputa de status;
- não iniciar loops autônomos entre agentes;
- emitir somente a própria fala, sem simular speakers.

O `ParticipationArbiter` passa a tratar `Morgana, pegue o ponto do Todd...` como endereçamento exclusivo a Morgana, e equivalente para Todd. Convites explícitos de grupo (`Todd e Morgana`, `os dois`, `vocês dois`, etc.) continuam permitindo ambos.

## Consequências

- Personality Core permanece independente e não é alterado por etiqueta social.
- Speaker boundaries continuam propriedade do sistema, não do modelo.
- O Behavioral E2E integrado passa de 4 cenários / 7 turnos para 6 cenários / 10 turnos, cobrindo referência sem convite e correção social.
- Simulação de labels de speaker vira violação automática no E2E integrado.
