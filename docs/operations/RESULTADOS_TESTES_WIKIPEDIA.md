# Validação do incremento Wikipédia offline (base enxuta)

Ambiente de testes: Linux, Python disponível no contêiner, HTTP simulado (sem ZIM real).

- Testes específicos: `tests/test_wikipedia_zim_offline.py`: **26 passed**.
- Testes dirigidos: Wikipédia, chamada de agentes, ficha factual, retomada das 3 pastas e Python unificado: **81 passed**.
- Suíte completa: **899 passed, 30 failed**. As 30 falhas são **as mesmas** registradas na base limpa (`873 passed, 30 failed`); sem novas falhas detectadas.
- Novos testes cobrem: cliente só em loopback, caminho de artigo malicioso, arquivo ZIM ausente, servidor indisponível, titulo duplicado, citação literal, não vazamento de conteúdo HTML para prompts, documento local prioritário e Todd respondendo com fonte offline.

**Limitação importante:** isto não é homologação com um arquivo `.zim` real nem com `kiwix-serve.exe` no Windows. Esse teste final deve ser realizado no computador do usuário após instalação do conteúdo e do Kiwix.
