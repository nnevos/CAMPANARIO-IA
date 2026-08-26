# 07 - Memoria e contexto

## O que existe hoje

O sistema persiste sessoes e mensagens e usa Context Manager com:

- janela recente configuravel;
- resumo incremental persistido no SQLite;
- separacao source-aware: declaracoes do usuario tem prioridade sobre sugestoes antigas do assistant;
- provenance para impedir que ficcao do assistant vire evidencia factual;
- contexto antigo + mensagens recentes para o modelo.

## O que isso ainda nao e

Nao e memoria cognitiva completa, knowledge graph ou RAG. O resumo serve para continuidade sem reenviar o historico inteiro.

## Correcoes explicitas (`*`)

Correcoes curtas como `verde*` sao tratadas como emendas ao enunciado anterior. O estado corrigido prevalece no contexto sem apagar o transcript original, preservando auditabilidade.

## Agentes futuros

Todd/Morgana nao terao memorias paralelas. Eles deverao consumir a mesma memoria/contexto do Campanario e apenas expressar o sistema por politicas/personas diferentes.

## Privacidade

Fontes privadas externas usadas para descobrir padroes nao ficam no projeto: sem copia, nome, hash ou identificador; permanecem apenas abstracoes generalizadas.

## Estado temporario de foco em calls longas

O `Conversation Focus Stack` e contexto de trabalho, nao memoria aprendida. Ele e reconstruido deterministicamente a partir do episodio atual e desaparece como estado cognitivo quando a call/episodio termina. Frames suspensos podem ser retomados pelo usuario sem promover automaticamente tangentes criadas pelos agentes.


## Dialogue State Compiler

Em calls longas, o Focus Stack organiza os ramos de assunto e o `DialogueStateCompiler` transforma o estado atual em um briefing curto antes da resposta. Isso resolve referencias como `isso`, `mesma pergunta`, `volta ao assunto`, `resume a decisao` e escolhas elipticas sem promover tangentes do assistant a fatos do usuario.

Esse estado e efemero: nao e aprendizado, nao e memoria relacional e desaparece com o episodio.

## Experience / Learning v1 — F4

Desde o ADR 0061 existe uma camada de memoria experiencial separada do resumo de contexto. Ela persiste fatos explicitos do usuario, preferencias, planos, experiencias compartilhadas e inferencias marcadas, sempre com provenance/evidence, confidence, recency e lineage de correcao.

Todd e Morgana usam a mesma memoria do Campanario. Nao existem bancos pessoais duplicados por agente.

A captura automatica e conservadora: o sistema aprende principalmente quando o usuario afirma algo de forma explicita, pede para lembrar, responde uma pergunta realmente necessaria ou informa se uma estrategia funcionou. Segredos e marcadores sensiveis de alto risco nao entram automaticamente.

A memoria aprendida pode ser inspecionada em `GET /api/v1/memory`, corrigida e esquecida. O reset de memorias de desenvolvimento para uso real continua reservado ao F7 Memory Clean Start.
