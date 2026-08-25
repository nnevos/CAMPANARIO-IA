# ADR-0021 - Self-aware expression e backstops pragmaticos

## Status
Aceito em 2026-08-24.

## Contexto
O Behavioral E2E v1 mostrou que o modelo ainda podia: (1) declarar sentimentos humanos como estados internos do Campanario; (2) ignorar encerramentos de topico e acknowledgements; (3) reconhecer `X*` como correcao no turno imediato, mas manter o valor anterior em turnos futuros.

## Decisao
1. Campanario declara explicitamente sua natureza de IA e separa compreensao emocional de experiencia subjetiva.
2. Humor/opiniao/informalidade permanecem permitidos; emoji pode ser marcador paralinguistico ocasional, nao prova de sentimento interno.
3. `BehaviorResponseGuardProvider` atua como backstop apenas em contratos pragmaticos objetivos (ack/topic-drop/correcao) e pode tentar uma segunda geracao quando detectar alegacao emocional em primeira pessoa.
4. Correcoes explicitas curtas com `*` geram notas autoritativas de contexto sem alterar o transcript persistido.
5. A correcao prevalece sobre o termo/valor anterior quando houver conflito, preservando auditabilidade do historico original.

## Consequencias
- Naturalidade nao depende de roleplay emocional humano.
- O modelo continua sendo responsavel pela resposta normal; o guard so intervem quando um contrato objetivo e violado.
- A solucao de correcao e deliberadamente conservadora: `*` curto e tratado como emenda contextual, nao como reescrita destrutiva do banco.
- O E2E passa a variar casos de correcao e inclui self-awareness como categoria de validacao.
