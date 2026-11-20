# CAMPANARIO-IA — Fase 4, Incremento 3B.1

## Escopo e proveniência

**FATO VERIFICADO:** os registros da calibração real do `embeddinggemma` no Windows mostraram cinco trechos corretos em primeiro lugar, mas `0,50` produziu candidatos para 9/12 perguntas negativas difíceis. A busca textual anterior chegou a citar trechos para 8/12 negativos difíceis. Ambos são **candidatos/trechos**, e não necessariamente invenções no texto final do agente.

**ALTERAÇÃO IMPLEMENTADA:** o leitor `ReadOnlyLocalLibrary` agora aplica `evidence_gate.assess_explicit_answer()` **antes** de permitir que uma correspondência lexical seja apresentada como trecho responsivo. O verificador exige correspondência literal do atributo solicitado e de qualificadores relevantes; não utiliza modelo, rede, regex adicionais, memória pessoal ou banco próprio. Quando não pode conferir o atributo, **não promove o trecho** a resposta.

Uma pergunta objetiva sem fonte adequada também passa a gerar a ficha neutra `insufficient`, `origin=none`, impedindo a geração de detalhes factuais pelo modelo. A proteção se aplica aos agentes em modo individual e conjunto. As fichas existentes, as identidades do sistema e dos agentes, e as funcionalidades de memória evolutiva foram preservadas.

## Resultados medidos nesta execução

| Medida | Baseline da versão anterior | Após 3B.1 (Linux, corpus sintético) |
|---|---:|---:|
| Questões documentais positivas com trecho correto | 20/20 | 20/20 |
| Variações lexicais aceitas via FTS5 | 6/6 | 6/6 |
| Negativos difíceis com trecho lexical indevidamente selecionado | 8/12 (Windows, dado fornecido pelo usuário) | **0/12** |
| Negativos difíceis em que o chat se abstém | Não medido no baseline anterior | **12/12** |
| Geração com provedor simulado nos 12 negativos | Não medido no baseline anterior | **0 chamadas** |
| Respostas documentais do chat, com trecho e fonte | 20/20 | 20/20 |
| Bateria direcionada | 107/107 | **117/117** |
| Suíte completa | 775 aprovados; 30 falhas | **785 aprovados; 30 falhas** |
| Falhas novas | — | **0**, conferência nominal contra a lista anterior |

O corpus é composto de cinco documentos Markdown **sintéticos**. A execução local utiliza Python 3.13 fora da faixa declarada pelo projeto; Windows/Python 3.12 e o Ollama real precisam ser revalidados pelo usuário.

## Por que não reduzir simplesmente 0,72 para 0,50?

A busca semântica tem a obrigação de tratar seus resultados como **candidatos**. Os testes reais do usuário mostraram que `0,50` retorna trechos relevantes em cinco perguntas, mas também aceita candidatos semanticamente relacionados para 9/12 perguntas sem resposta. Este patch **não altera** `CAMPANARIO_LIBRARY_SEMANTIC_ENABLED`, nem o limiar de produção de `0,72`. O backend híbrido continua fornecendo apenas candidatos explicitamente insuficientes, nunca alegações confirmadas pela similaridade.

## Limitações e riscos conhecidos

- **Não é um verificador de implicação lógica (NLI)**. O filtro é uma condição textual conservadora: requer o atributo e qualificador na mesma frase/trecho, mas não demonstra se o trecho realmente implica a resposta, nem valida a veracidade externa do documento.
- Pode haver **recusas indevidas** quando a pergunta e a fonte expressam a mesma relação com sinônimos diferentes (ex.: `autor` e `escritor`), ou quando a resposta está espalhada por várias frases.
- O filtro de atributos reconhece algumas respostas estruturais explícitas, como nomes, cores e dias da semana, mas é propositalmente limitado. Os testes existentes cobrem os casos conhecidos, não todos os assuntos possíveis.
- A busca semântica em `0,50` **ainda não está homologada**. Candidatos não devem ser promovidos para a ficha factual sem verificação independente.
- `Kiwix/ZIM`, zero agentes, terceiro agente configurável, Qwen real após o patch, consistência semântica interagentes e avaliação de VRAM ainda estão pendentes.
- O pacote não corrige as 30 falhas históricas de outras áreas.

## Conservação do sistema

Sem alteração em banco SQLite real, `.env`, memória pessoal, perfis Python de Campanario/Morgana/Todd, modelos Ollama, transcrição da biblioteca ou internet. O backend FTS5 continua com índice exclusivamente RAM. O instalador não faz migração de dados nem escreve automaticamente em bibliotecas.

## Próximo teste no Windows

Depois do instalador e dos 117 testes direcionados, executar `tools/eval_fase4_inc3b1.py` para repetir os 20 positivos, 6 variações, 12 negativos e os mesmos 20 exemplos no chat. O avaliador usa SQLite temporário e um provedor simulado. Os resultados são escritos em `reports/fase4_inc3b1/baseline_suficiencia.json`.
