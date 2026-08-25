# Personalidade e evolucao dos agentes

## Teste rapido

No `CAMPANARIO.bat`, use **Testar personalidades Todd/Morgana**.

O teste envia os mesmos dilemas e falas cotidianas para os dois agentes. O relatorio mostra Todd e Morgana identificados separadamente.

## Mega teste

Use **Mega teste de personalidades** antes de congelar uma versao de persona. Ele executa varios seeds e formulacoes diferentes para reduzir o risco de ajustar o codigo a uma conversa especifica.

## Como interpretar

`PASS` automatico significa que invariantes objetivas foram respeitadas. Nao significa sozinho que a personalidade esta perfeita. Leia o `review_focus` e compare os transcripts.

## Aprendizado futuro

Os agentes nao serao retrainados automaticamente a cada conversa. A evolucao sera feita por uma camada de experiencia/memoria com proveniencia, mantendo uma personalidade-core versionada e protegida contra drift acidental.
