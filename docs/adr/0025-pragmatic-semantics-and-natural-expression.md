# ADR-0025 — Pragmatic Semantics + Natural Expression

## Status
Accepted — Conversational v1.5.4.

## Context

O E2E real da v1.5.3 chegou a 9 PASS / 2 WARN / 0 FAIL, mas a revisao humana encontrou falsos positivos de naturalidade: `show` foi lido literalmente, uma risada foi narrada como `risada curta`, cumprimento com vocativo virou eco mecanico, correcoes receberam metalinguagem e respostas tecnicas abriram com elogio do tema.

Esses defeitos nao justificam respostas hardcoded para frases especificas. O problema e distinguir **funcao pragmatica** da superficie lexical e impedir que a IA verbalize a propria interpretacao social.

## Decisao

1. `PragmaticInterpreter` passa a representar explicitamente `greet` e amplia familias semanticas de acknowledgement, topic-drop, reaction e personal-state sharing.
2. A camada de saida continua persona-agnostica: ela nao escolhe bordoes nem imita o usuario.
3. `ResponseContractPolicy` ganha contratos para:
   - eco mecanico de vocativo em greeting;
   - acknowledgement interpretado literalmente;
   - narracao/simulacao textual de risada;
   - preambulo metalinguistico/institucional;
   - reassurance automatico em compartilhamento social;
   - preservacao da identidade Campanario em perguntas self-aware;
   - `truth_over_agreement` mantido em follow-ups por contexto recente.
4. O Behavioral E2E usa familias lexicais maiores, casos factuais/tecnicos/correcao variados e ordem de cenarios embaralhada por seed.
5. O mesmo seed permanece reproduzivel. Seeds diferentes nao precisam manter a mesma ordem nem as mesmas frases.
6. Falhas devem ser corrigidas por classe semantica/comportamental, nunca por resposta factual ou dialogo hardcoded.

## Consequencias

- Naturalidade deixa de ser medida apenas por comprimento/pergunta e passa a incluir erros pragmaticos observaveis.
- A IA pode entender linguagem coloquial sem copiar a forma de falar do usuario.
- Personas futuras continuam responsaveis pela voz; pragmatica e contratos apenas delimitam o significado/erros objetivos.
- Nenhum dado privado ou perfil pessoal e adicionado.
