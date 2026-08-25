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
