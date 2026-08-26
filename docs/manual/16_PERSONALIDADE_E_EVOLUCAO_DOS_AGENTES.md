# Personalidade e evolucao dos agentes

## Personality Core v1

Todd e Morgana agora possuem um contrato de personalidade estruturado no codigo, com traits, anti-traits, tendencias, limites e comportamento por contexto (social, tecnico, criativo, discussao e urgencia). O prompt ativo e gerado desse contrato; ele nao contem respostas prontas de benchmark.

O core e estavel. Adaptacao aprendida continua bloqueada ate o fechamento dos testes de personalidade e, no futuro, deve ficar em uma camada separada com proveniencia e protecao contra drift.

## Teste rapido

No `CAMPANARIO.bat`, use **Testar personalidades Todd/Morgana**.

O teste cobre oito eixos: decisao/trade-off, simplicidade, discordancia, incerteza, urgencia, diagnostico tecnico, criatividade e conversa social. Cada eixo envia a mesma situacao para Todd e Morgana, totalizando 16 cenarios.

O relatorio abre com **Analise conceitual de personalidade** e marca cada eixo como `BATE`, `REVISAR` ou `SEM DADO`. `REVISAR` e um sinal heuristico para ler o transcript, nao uma ordem automatica para alterar a persona. Ao terminar uma execucao valida, `TESTAR_PERSONALIDADES.bat` abre automaticamente o ultimo `report.html` no navegador padrao. Se houver erro de runtime antes de gerar um novo relatorio, o launcher nao abre um resultado antigo.

## Mega teste

Use **Mega teste de personalidades** antes de congelar uma versao de persona. Ele executa oito lotes semanticamente variados da bateria completa (128 cenarios) para reduzir o risco de ajustar o codigo a uma conversa especifica. Ao terminar uma execucao valida, o launcher Mega tambem abre automaticamente o ultimo relatorio no navegador.

## Como interpretar

`PASS` automatico significa que invariantes duras foram respeitadas. A secao `BATE/REVISAR` avalia sinais observaveis do conceito por eixo, mas continua sendo heuristica. Leia o `review_focus`, compare Todd e Morgana no mesmo prompt e somente ajuste o core quando o transcript confirmar um padrao de desvio.

O gabarito conceitual completo esta em `docs/current/AGENT_PERSONALITY_CONCEPT.md`.

## Aprendizado futuro

Os agentes nao serao retrainados automaticamente a cada conversa. A evolucao sera feita por uma camada de experiencia/memoria com proveniencia, mantendo uma personalidade-core versionada e protegida contra drift acidental.

## Experience Layer ativa — F4

A adaptacao aprendida agora existe no ADR 0061, mas continua separada do Personality Core. Ela pode lembrar preferencias, contexto e experiencias que funcionaram/falharam; nao altera traits/anti-traits automaticamente.

Inferencias permanecem marcadas como hipotese e com confianca menor. Uma conversa comum nao tem autoridade para reescrever a identidade de Todd ou Morgana.
