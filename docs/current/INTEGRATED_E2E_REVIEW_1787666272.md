# Integrated E2E Review — seed 1787666272

## Resultado real

- suite: `agent_integrated`
- modelo: `gemma3:12b`
- cenarios: 5 PASS / 0 WARN / 1 FAIL
- checks efetivamente avaliados: 53 PASS / 0 WARN / 0 FAIL

## Leitura

O Social Protocol melhorou de forma clara. Referencia-vs-convite, silencio seletivo, correcao aritmetica, colaboracao criativa e discordancia complementar passaram. O unico FAIL veio de um `RuntimeError` do Speaker Output Guard em `integrated_shared_decision`: a geracao de Morgana continuou tentando produzir painel/transcript mesmo depois do repair.

Isso e melhor que aceitar a saida contaminada, mas derrubar o turno inteiro e uma politica ruim para a futura call. A recuperacao foi refinada: depois do repair, se o texto ainda vier como painel, o runtime pode recuperar apenas um segmento explicitamente rotulado como o proprio agente. Segmentos estrangeiros nunca sao relabelados como fala do agente atual; sem um segmento proprio inequivoco, a violacao continua falhando fechado.

Personality Core permanece intacto.

## Decisao

O comportamento social curto esta suficientemente maduro para preparar o Long Call Behavioral E2E. A nova bateria longa deve continuar exercitando o guard estrutural e revelar se a recuperacao permanece estavel ao longo de episodios extensos.
