# 05 - Relatorios de teste

No menu `CAMPANARIO.bat`, escolha **Abrir ultimo relatorio**.

Arquivos gerados localmente em `test_reports/behavioral_e2e/`:

- `latest.html` - leitura humana;
- `latest.json` - analise estruturada;
- `latest.md` - texto.

`PASS` significa que checks objetivos passaram; nao transforma o evaluator em juiz absoluto de naturalidade/factualidade aberta. Em milestones, leia uma amostra do transcript.

`test_reports/` e artefato local e nao deve entrar no ZIP/repo.

## Latencia em Long Call

Nos relatorios `agent_long_call`, a secao **Latencia conversacional** mostra media, mediana, p95 e pior caso para primeira resposta utilizavel, turno total, turnos solo, turnos multiagente e gap ate o segundo agente. O transcript tambem mostra os tempos por turno.

Para futura voz/call, TTFR e mais importante que o tempo total: duas contribuicoes podem terminar mais tarde sem parecer lentas se o primeiro agente comecar a responder cedo.

