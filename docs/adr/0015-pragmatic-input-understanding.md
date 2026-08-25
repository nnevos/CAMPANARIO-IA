# ADR-0015 — Pragmatic Input Understanding separado de persona

## Status

Aceito como fundacao nao ativada; integracao ao runtime depende do gate manual do Conversational v1.4.

## Contexto

Analise de um corpus real de conversa informal mostrou que naturalidade depende de entender a funcao social da mensagem, nao apenas seu conteudo literal. Risada, acknowledgement, correcao posterior, fragmentacao, abandono de topico e pensamento em voz alta carregam significado pragmatico. O mesmo entendimento deve servir a qualquer persona sem obrigar a persona a imitar o usuario.

## Decisao

Criar uma camada independente de pragmatica de entrada. Ela produz atos conversacionais potencialmente multiplos e metadados leves, mas nao escolhe persona, nao define resposta, nao decide factualidade e nao grava memoria.

O corpus bruto permanece fora do runtime. Apenas descobertas generalizadas e referencias de proveniencia sao mantidas no projeto.

## Consequencias

Positivas:
- separa compreender de responder;
- reduz overfitting a frases especificas;
- prepara futura adaptacao pessoal sem misturar identidade de persona;
- permite benchmark de comunicacao informal com exemplos anonimizados.

Custos/riscos:
- heuristicas deterministicas ainda sao incompletas;
- atos podem coexistir ou ser ambiguos;
- integracao prematura poderia duplicar/confundir `TurnMode` e `ContinuationKind`.

Por isso a fundacao fica desconectada ate o gate v1.4 ser fechado.
