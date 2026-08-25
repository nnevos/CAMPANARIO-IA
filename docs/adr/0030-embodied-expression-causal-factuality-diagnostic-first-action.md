# ADR-0030 - Embodied Expression Guard + Causal Factuality + Diagnostic First Action

## Status
Aceito - Conversational v1.5.9.

## Contexto
A revisao humana da v1.5.8 encontrou tres classes que ainda escapavam aos checks: encenacao corporal da IA (`*riso silencioso*` e equivalentes), respostas factuais com conceito geral mas mecanismo causal incorreto e diagnosticos tecnicos que enterravam a primeira acao depois de uma introducao generica.

## Decisao

1. `ResponseContract` proibe encenacao corporal/subjetiva da IA em qualquer turno. A deteccao usa familias de stage directions e acoes em primeira pessoa, nao uma frase unica.
2. Emojis continuam permitidos como marcadores paralinguisticos; nao sao tratados como corpo ou sentimento interno.
3. O contrato `technical_first_step` exige que a primeira frase comece por uma acao investigativa e contenha mecanismo/evidencia observavel.
4. O E2E factual amplia familias causais e diferencia mecanismos proximos (por exemplo espalhamento x reflexao/absorcao) sem colocar respostas factuais hardcoded no runtime.
5. O anti-overfitting por familias lexicais, seed e ordem variavel permanece obrigatorio.

## Consequencias

- Naturalidade nao depende de teatro corporal da IA.
- O standard fica mais exigente com causalidade e diagnostico executavel.
- Factualidade aberta continua limitada pelo modelo; o E2E mede regressao, nao substitui grounding futuro.
- Se standard + revisao humana aprovarem, executar mega; depois refatorar antes de agentes.
