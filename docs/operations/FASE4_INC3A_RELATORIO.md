# CAMPANARIO-IA — Fase 4, Incremento 3A: busca FTS5 local

Data: 2026-11-19. Base: Fase 4 Inc.2 + patch de limpeza SQLite FIX2.

## FATO VERIFICADO — escopo efetivamente implementado

- `ReadOnlyLocalLibrary` cria um índice FTS5 **somente em memória**, com texto extraído dos registros do banco `utilidades.sqlite3` aberto em `mode=ro` e `PRAGMA query_only=ON`. O banco existente não recebe tabelas, migrações, índices, inserções nem atualizações por este componente.
- Índice reutilizado entre consultas no processo; reconstruído se mudarem tamanho ou carimbo de data do banco SQLite ou arquivo WAL. Limites existentes preservados: 300 documentos, até 500 mil caracteres por campo `pages`, orçamento de 4 milhões de caracteres de registros. Limite adicional de 80 mil trechos e 1.600 candidatos por consulta.
- Busca FTS5 `MATCH` gera **candidatos**, mas cada resultado continua exigindo sobreposição mínima de termos, âncora explícita de assunto, evidência textual literal e tratamento de conflitos. Não são usados embeddings nem respostas geradas por LLM. Variações controladas de plural/singular, inclusive `revisões`/`revisão`, ampliam a recuperação sem usar prefixo aproximado generalizado.
- SQLite Python sem FTS5 utiliza automaticamente o mecanismo lexical anterior (`backend='legacy'`). Não cria banco paralelo em disco.
- Ficha factual neutra do Inc.2 e respostas literais do Inc.1 seguem inalteradas. Arquivo de produção modificado: apenas `src/campanario/chat/local_library.py`.

## FATO VERIFICADO — benchmark no ambiente de desenvolvimento (Linux, Python 3.13; não Windows/Ollama)

Amostra: `eval/v1/documentos.jsonl` (20 questões em 5 documentos sintéticos), mais seis perguntas com flexões e cinco controles negativos. Mesmas fontes temporárias em ambas as buscas. Avaliador `tools/eval_fase4_inc3.py`.

| Medida | Busca anterior (legacy) | Nova busca FTS5 em RAM |
|---|---:|---:|
| Trechos literais e arquivo correto, corpus fixo | 20/20 | 20/20 |
| Variantes singular/plural com trecho esperado | 0/6 | 6/6 |
| Controles negativos com abstenção | 5/5 | 5/5 |
| Primeira consulta (inclui montagem do índice) | 1,011 ms | 1,755 ms |
| Mediana das 19 consultas seguintes, base pequena | 0,445 ms | 0,163 ms |
| Respostas do chat com citação, provedor simulado | 20/20 | 20/20 |

As latências descrevem apenas essa execução local e não predizem desempenho com bibliotecas grandes, Windows, Qwen ou Kiwix. Não se mediu precisão de afirmações, VRAM, uso do Ollama, consultas reais na biblioteca pessoal nem melhora das 50 perguntas enciclopédicas.

**Regressão:** 56/56 testes direcionados aprovados; suíte completa: 722 aprovados, 30 falhas. A lista das 30 falhas foi comparada com o resultado do Inc.2/FIX2: idêntica, nenhuma nova falha conhecida. Após adicionar o teste de subprocesso, a suíte dirigida terminou com 56 aprovados; não se afirma que o Windows já passou.

**Privacidade:** comparação em `tempfile.TemporaryDirectory`, bloqueando conexão de rede durante as consultas e o chat. Hash SHA-256 do SQLite sintético igual antes/depois. Nenhum índice persistente criado pelo avaliador. `UtilityService` temporário fecha conexões SQLite explicitamente para compatibilidade com WinError 32.

## LIMITAÇÃO CONHECIDA — relevância parcial não é verificação factual

A pergunta **“O Projeto Faro teve autorização de Zeus?”** recupera um trecho não relacionado sobre Faro tanto na busca antiga quanto na FTS5. É um problema preexistente de cobertura lexical suficiente, não uma confirmação de autorização. O Inc.3A **não** resolve inferência de implicação, desambiguação semântica nem a verificação de todas as afirmações. A resposta literal informa o que o documento afirma, mas pode não responder à pergunta. Esse caso permanece aberto para avaliação de relevância/entailment, **não é classificado como sucesso**.

## NÃO IMPLEMENTADO

- 3B: embeddings com `embeddinggemma` ou comparação semântica com modelo local. Depende de benchmark real, avaliação de segurança e disponibilidade de Ollama no Windows.
- 3C: integração de Kiwix/ZIM e enciclopédia offline. Depende de ZIM e serviço local disponíveis, verificação de referências e permissão do usuário.
- Respostas sobre Ada Lovelace sem documentos locais, resolução de todo conflito de fontes, execução sem agentes, terceiros agentes por JSON, garantia de zero invenções e avaliação real com Qwen.

## Recuperação / reversão

O instalador do ZIP verifica hashes da base, realiza backup da versão anterior de `local_library.py` e recusa arquivos desconhecidos. O script de reversão verifica hashes do backup e do estado instalado antes de restaurar; não altera dados, `.env`, biblioteca, memórias nem Ollama. Execute ambos somente com o Campanario fechado e mantenha backup independente.
