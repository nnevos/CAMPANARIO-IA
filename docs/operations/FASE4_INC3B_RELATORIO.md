# CAMPANARIO-IA - Fase 4 / Incremento 3B - relatorio tecnico

Data: 2026-11-19. Base instalada pelo usuario: Inc.3A (Windows, 56/56 testes).

## FATO VERIFICADO - codigo e testes locais

- Pesquisa lexical FTS5 prioritaria, mesma fonte e mesmo trecho retornados antes do incremento. Apenas quando a busca nao encontra resultado, o backend semantico opcional consulta vetores locais.
- **Padrao de producao permanece FTS5**, com `CAMPANARIO_LIBRARY_SEMANTIC_ENABLED=false`. Nao ha nova chamada de embeddings sem opt-in.
- A comunicacao de embeddings aceita exclusivamente HTTP via `127.0.0.1` ou `[::1]`, ignora proxies do ambiente, proibe redirects, usa `/api/embed` e limita batch/tamanho/tempo. Nao faz download de modelo.
- O SQLite original e acessado somente por consultas read-only. Vetores em memoria, limite de 96 trechos por instancia, reconstrucao apos alteracao detectada no SQLite/WAL, nenhuma migracao nem arquivo de indice persistente.
- Falha de Ollama, vetor invalido ou dimensoes inconsistentes => volta ao FTS5, resfriamento de 90 segundos; o modelo Qwen nao e chamado para verificar resultados.
- `semantic_candidate` nao e um estado de fato apoiado; `TurnFactSheet.status='insufficient'`, nenhuma `FactClaim`, citacao com origem e SHA, texto na resposta afirma explicitamente que a fonte so pode estar relacionada e que nao foi verificada como resposta.
- Ficha permanece produzida uma vez por turno, entregue igualmente a Morgana e Todd. Memorias pessoais nao sao convertidas em fontes externas.

## FATO VERIFICADO - benchmark sintentico (NÃO E EVIDENCIA de qualidade do embeddinggemma)

Avaliacao: `tools/eval_fase4_inc3b.py --engine fixture`. Corpus de cinco arquivos ficticios e 20 perguntas documentais herdadas do Inc.3A; cinco parafrases novas com resultado pre-registrado, quatro controles negativos.

| Medida | FTS5 | Vetores SIMULADOS / modo candidato |
|---|---:|---:|
| Documentos antigos com fonte exata | 20/20 | 20/20 |
| Parafrases com trecho esperado | 0/5 | 5/5 |
| Parafrases promovidas a fato sem verificacao | n/a | 0/5 |
| Negativos sem afirmacao promovida | 4/4 | 4/4 |

O vetor de teste usa uma tabela artificial de associacoes de palavras, criada para comprovar o plumbing do software. **O numero 5/5 nao e uma nota do modelo embeddinggemma**. A comparacao verdadeira exige `--engine ollama` no Windows do usuario. Sem medida real, nao se deve habilitar o recurso por padrao.

Regressao: 84/84 testes dirigidos; suite completa `750 passed, 30 failed, 14 warnings` em Linux Python 3.13. Lista de 30 falhas exatamente igual a lista historica da base Inc.2+FIX2. A compatibilidade Python 3.12 e Windows exige confirmacao do usuario.

## HIPOTESES / PENDENCIAS

- Embeddinggemma podera recuperar algumas perguntas por significado; nao aferido neste ambiente (sem Ollama real).
- Recuperacao semanticamente semelhante pode trazer um documento sobre o assunto que NAO responde a pergunta. O modo candidato impede promover isso a fato, mas nao resolve relevancia ou entailment. O caso Faro/Zeus que o FTS5 ja retorna indevidamente permanece aberto.
- Limite RAM 96 trechos: bibliotecas acima disso podem ter recall reduzido; montar vetores localmente na primeira falha do FTS5 pode aumentar latencia. VRAM, latencia e custo no RTX 5060 Ti nao medidos.
- `Kiwix/ZIM` nao esta integrado. Zero agentes, terceiros agentes por perfil e respostas enciclopedicas fora da biblioteca permanecem fora deste incremento.

## PROPOSTA - criterio para prosseguir

1. Windows: 84/84 testes, fixture 20/20 e 5/5, sem `WinError 32`.
2. Windows: avaliar `--engine ollama` e revisar os cinco trechos retornados, quatro negativos e latencias. Nao habilitar se a precisao dos candidatos ou custo forem inadequados.
3. So depois decidir se o 3B e apto ao uso opcional em sua biblioteca real; continuar FTS5 default. Para respostas factuais confiaveis com Kiwix, ainda falta uma etapa de validacao de pertinencia.

Reversao e hashes: `LEIA_PRIMEIRO_FASE4_INC3B.md` e `MANIFESTO_SHA256_FASE4_INC3B.json`.
