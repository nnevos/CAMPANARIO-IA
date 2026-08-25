# Agent Test Strategy

## Camadas

1. Unit tests: registry, routing, participation, persistence e contratos.
2. Agent architecture E2E: identidade, verdade compartilhada e speakers corretos.
3. Personality E2E: mesmo prompt para Todd/Morgana, invariantes + comparacao humana.
4. Personality Mega: multiplos seeds e familias semanticas para evitar overfitting.
5. Multi-agent dialogue regression: complementacao, discordancia, overtalk e conversa entre agentes.
6. Long-context identity regression: continuidade de personalidade ao longo de sessoes extensas.
7. Learning regression (futuro): memoria aprendida, correcao, esquecimento e anti-drift.

## O que e automatico

Automaticamente verificavel:

- identidade correta;
- nao assumir Jason Todd/Oraculo;
- fatos compartilhados;
- formato/tamanho;
- ausencia de metalinguagem de persona;
- ausencia de encenacao humana;
- speaker/proveniencia;
- nao duplicar memoria/core;
- invariantes do ParticipationArbiter.

## O que exige revisao humana

- Todd realmente parece mais pragmatico/estrategico?
- Morgana realmente parece mais analitica/interpretativa?
- diferenca e perceptivel sem caricatura?
- humor parece natural?
- discordancia parece relacional, nao promptada?
- o segundo agente acrescenta valor?

Esses itens aparecem como `review_focus` no relatorio; nao fingimos que uma blacklist consegue medir personalidade humana por completo.
