# ADR-0038 — Personality Foundation e learning antes de voz

## Status
Aceito.

## Contexto
A Presence UI v1.3 ja representa Campanario como ambiente/call e deixa espaco para wake/STT/TTS. Entretanto Todd e Morgana ainda possuem apenas perfis iniciais e a evolucao persistente ainda nao existe.

Implementar voz agora aumentaria superficie de erro antes de estabilizar identidade, participacao e continuidade.

## Decisao

A ordem obrigatoria passa a ser:

1. Personality Foundation;
2. quick + mega personality E2E;
3. multi-agent/long-context regression;
4. Personality Baseline v1;
5. Experience/Learning Layer com proveniencia e anti-drift;
6. somente depois Presence Audio/Call Mode.

O aprendizado nao sera retraining automatico do modelo a cada conversa. Personalidade-core sera versionada e experiencia adaptativa ficara em uma camada separada.

## Consequencias

- a UI pode continuar exibindo estados futuros de voz apenas como capacidade nao conectada;
- voz nao pode ser usada para justificar pular o gate de personalidade;
- novos testes de personalidade usam familias/seed e o mesmo prompt para Todd/Morgana;
- checks automaticos nao fingem medir completamente personalidade humana; transcript permanece obrigatorio para revisao fina.
