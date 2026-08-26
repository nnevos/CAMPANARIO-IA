# ADR 0042 — Long Call Grounding Hardening

## Status
Aceito para revalidacao P2.3d.

## Contexto
O Long Call seed `1787671154` mostrou 230 PASS / 7 WARN / 2 FAIL. O Focus Stack reduziu perdas graves, mas quatro falhas permaneceram: linguagem interna do mecanismo vazando na resposta, elipses/follow-ups sem referente imediato forte, correction anchor incapaz de atravessar turnos e hallucination de componentes tecnicos inexistentes.

## Decisao

1. O Focus Stack continua existindo internamente, mas a nota entregue ao modelo deixa de expor termos de implementacao (`frame`, `answer binding`, stack). O modelo recebe apenas um briefing temporario de continuidade com assunto inicial, assunto ativo, linha do usuario, decisoes/restricoes, assuntos pausados e pedido atual.
2. Follow-ups deiticos (`isso`, `mesma pergunta`, `aterrissa`, `sequencia curta`) recebem reforco do pedido anterior e, quando pertinente, da fala imediatamente anterior.
3. Correcoes aritmeticas podem ancorar operandos numa pergunta recente do usuario e o valor incorreto no turno atual.
4. O grounding explicita que componentes, modulos, integracoes, dados e requisitos nao fornecidos nao podem ser inventados.
5. Social Protocol proibe explicacao espontanea de mecanismos internos de routing/frames/arbiter/logs salvo pedido arquitetural explicito.
6. O E2E ganha checks adicionais para placeholders inventados, elipse de produto e sintese que perde o conceito raiz.

## Consequencias

- nenhuma segunda chamada de modelo para contexto;
- Personality Core permanece intacto;
- memoria aprendida continua fora de escopo;
- correction anchor fica mais robusto em calls longas;
- prompt leakage de metadados conversacionais passa a ser detectado pelo guard.
