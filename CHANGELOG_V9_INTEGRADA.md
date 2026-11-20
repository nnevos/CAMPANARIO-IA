# Changelog - V9 cerebros + V9.1 expressao fundamentada

- Adicionado `campanario/brains/`: contratos, executor, roteamento independente, adaptadores e rastros.
- Implementados Conhecimento e Analise a partir das ferramentas existentes; seis outros cerebros catalogados como indisponiveis.
- Adicionadas fichas versionadas, 8 arquetipos, 6 talentos, ate 2 ativos por turno, sem alterar permissao, fatos ou personalidade base.
- Adicionada migracao Alembic aditiva `0010`; preserva conversas/memorias e cria fichas livres iniciais de Morgana/Todd.
- Integradas Forja de Agentes, Central de Cerebros, APIs locais e importacao/exportacao declarativa `.campagent`.
- O motor V9.1 continua a gerar resposta factual canonica, validar expressao e aplicar fallback; agora recebe rastros de cerebros e sugestoes nao autoritativas de ficha.
- Flag `CAMPANARIO_BRAINS_V9_ENABLED=false` por padrao preserva fluxo anterior.
- Testes locais: **1004 passed, 31 failed**; mesmas 31 falhas que a base V9.1; sem regressao nova por nome.
- Pendencias: seis cerebros, sandbox rigido, teste do Ollama real, Windows/mobile e outros dois repositorios.
