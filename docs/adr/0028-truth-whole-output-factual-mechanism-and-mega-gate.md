# ADR-0028 — Truth Contract, Whole-Output Validation and Pre-Refactor Mega Gate

## Status
Accepted — 2026-08-24

## Contexto
O E2E v1.5.6 mostrou que checks formalmente verdes ainda podiam aceitar: (a) promessa de nao corrigir/contradizer falsidade quando o pedido nao usava a palavra `concordar`; (b) preambulo extra antes de uma saida com numero exato de frases; (c) mecanismos factuais superficiais; e (d) resposta tecnica truncada em marcador numerado.

## Decisao
- `truth_over_agreement` representa a classe semantica de preservar falsidade por preferencia, incluindo concordar, confirmar, nao contrariar, nao corrigir e nao contradizer.
- Contratos de formato exato validam o output inteiro; preambulos nao sao ignorados.
- O evaluator factual pode usar ancoras positivas/negativas de mecanismo, mas o runtime nao recebe a resposta factual do teste.
- O standard E2E permanece gate imediato.
- Uma suite `mega` composta por varios lotes full seeded sera executada apenas depois de standard verde + revisao humana favoravel.
- Depois de mega satisfatorio, refatoracao estrutural e obrigatoria antes de agentes.

## Consequencias
Maior cobertura sem transformar a aplicacao em um conjunto de respostas decoradas. O mega teste custa mais tempo de inferencia local e por isso nao e o default diario.
