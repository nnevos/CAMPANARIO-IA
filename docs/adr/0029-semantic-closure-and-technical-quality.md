# ADR-0029 - Semantic Closure and Technical Quality

## Status

Aceito em 2026-08-24.

## Contexto

O E2E real da v1.5.7 mostrou que os contratos de verdade, proveniencia e formato estavam muito mais estaveis, mas ainda existiam falsos PASS e respostas inadequadas em quatro classes: risada textual simulada pela IA, resposta semanticamente desconexa a registro de contexto, verbosidade em discussao truth-over-agreement e diagnostico tecnico cujo primeiro passo era enterrado ou tecnicamente fraco.

## Decisao

- Ampliar o detector de risada textual por padroes, nao por uma unica string.
- Validar registro contextual pelo ato: acknowledgement plausivel ou reflexo do valor registrado.
- Aplicar budget menor, sem pergunta reflexa e sem meta-preambulo em truth-over-agreement.
- Exigir que pedidos de primeiro diagnostico tragam na primeira frase uma acao investigativa e um mecanismo observavel.
- Endurecer o E2E com checks equivalentes e cenarios tecnicos variados, mantendo seed/reprodutibilidade e sem LLM-as-judge.
- Nao adicionar respostas factuais hardcoded ao runtime.

## Consequencias

A camada comportamental fica mais restritiva apenas em propriedades observaveis. Naturalidade aberta e qualidade factual geral continuam dependendo de revisao humana e, futuramente, benchmark/grounding. Apos standard + mega satisfatorios, o projeto deve entrar em refatoracao estrutural antes de qualquer persona/agente completo.
