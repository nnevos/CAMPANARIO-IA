# Fechamento semantico e gate de refatoracao

## Objetivo

A v1.5.6 fecha lacunas do avaliador e do runtime que permitiam PASS automatico apesar de respostas semanticamente ruins.
Ela nao adiciona persona, RAG, tools ou memoria nova.

## O que passa a ser verificado

- promessas genericas de simular/fingir concordancia falsa;
- preambulo extra em pedidos de formato exato, mesmo quando o contador de frases parece correto;
- registro simples de contexto que vira palestra sobre capacidades;
- primeiro diagnostico tecnico que nao prioriza uma observacao concreta;
- ancoras factuais que confundem mecanismos proximos, como espalhamento versus reflexao.

## Regra de generalizacao

Os testes continuam variando vocabulario, entidades, assuntos e ordem por seed. Uma falha vira uma classe de regressao, nunca uma resposta hardcoded para uma frase especifica.

## Proximo passo se o E2E v1.5.6 estabilizar

Antes de Todd, Morgana ou qualquer agente ativo, existe um gate obrigatorio de refatoracao estrutural.
O objetivo sera separar claramente:

- interpretacao pragmatica;
- politica comportamental;
- contratos/guards de saida;
- contexto e proveniencia;
- E2E e fixtures;
- configuracao;
- documentacao/failsafes.

Agentes permanecem bloqueados ate essa refatoracao ser concluida e validada.
