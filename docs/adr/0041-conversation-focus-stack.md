# ADR 0041 — Conversation Focus Stack para calls longas

## Contexto

O Long Call seed `1787670418` mostrou 0 FAILs objetivos, mas revelou deriva de foco: o modelo lembrava informacoes do episodio sem distinguir consistentemente o assunto do usuario de tangentes introduzidas por agentes. Historico bruto e uma lista plana de ancoras nao expressam a estrutura discursiva de uma call longa.

## Decisao

Adicionar um `Conversation Focus Stack` temporario e deterministico em `campanario.chat.working_context`.

O stack e derivado de mensagens do usuario e mantem:

- foco raiz;
- frame ativo;
- frames suspensos;
- frames explicitamente guardados;
- restricoes/decisoes do usuario dentro do frame;
- movimentos de `mudando`, `voltando` e `guarda esse raciocinio`.

Tangentes geradas por Todd/Morgana nao substituem o foco do usuario apenas por serem a ultima resposta. A ultima fala do agente so entra explicitamente na nota de foco quando o pedido atual a referencia.

Tambem formalizamos `answer binding`: a resposta deve cumprir a funcao pedida no turno (cortar, preservar, resumir, decidir, explicar, permanecer em silencio), nao apenas permanecer no mesmo tema geral.

## Consequencias

- melhora continuidade longa sem uma segunda inferencia;
- evita promover alucinacoes/tangentes do assistant a estado dominante;
- nao cria memoria persistente;
- aumenta a importancia de testes de movimentos discursivos e retomada;
- Social Protocol passa a declarar que Todd/Morgana nao possuem autoridade social para silenciar um ao outro; participacao continua sob contexto/arbiter e precedencia do usuario.
