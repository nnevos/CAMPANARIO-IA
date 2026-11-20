# Fase 4 — Incremento 3B.2: descoberta semântica com barreira de suficiência

Data da análise: 2026-11-19.

## Resultado entregue

**FATO VERIFICADO (código):** o `HybridLocalLibrary` consulta FTS5 primeiro. Se o FTS5 não produzir trecho aproveitável e a busca semântica estiver explicitamente habilitada, a busca por vetores descobre candidatos; **antes de mostrar qualquer trecho**, cada candidato deve passar também por `evidence_gate.assess_explicit_answer()`, já usado no FTS5 desde o 3B.1. Candidatos que não contêm uma indicação explícita do atributo pedido não são disponibilizados ao chat. O leitor pode examinar candidatos com pontuações inferiores ao primeiro, após o filtro, sem alterar a preferência pelo FTS5.

**Proteção:** mesmo após a barreira, um resultado encontrado pelos embeddings continua marcado `semantic_candidate`, com ficha neutra `insufficient`, `claims=()`, fonte literal, aviso de não confirmação e sem gerar nova proposição factual no Qwen. O filtro não é um avaliador de implicação lógica e **não garante** suficiência para perguntas arbitrárias; só impede as correspondências tópicas que consegue reconhecer como insuficientes.

**Proteção de dados:** banco de documentos de usuário abre somente em `mode=ro`, índice FTS5 e embeddings no processo/RAM. O patch não muda configurações, `.env`, memórias individuais/relacionais, perfis de identidade ou modelos. O endpoint Ollama aceita apenas HTTP loopback (`127.0.0.1` ou `::1`), desabilita proxy e redirecionamentos. O recurso continua `library_semantic_enabled=False` por padrão; limite de produção `0.72` não modificado. Experimentos podem pedir `--threshold 0.50` **somente no avaliador**, sem alterar a instalação.

## Experimento com corpus sintético

O corpus `eval/v1` traz cinco documentos Markdown fictícios, 20 perguntas com resposta, seis variações FTS5, cinco perguntas que usam sinônimos, cinco perguntas de teste com atributo literal mas baixa sobreposição lexical e 12 negativos difíceis com o mesmo assunto dos documentos.

| Avaliação executada | Resultado | Significado |
|---|---:|---|
| Documentos originais FTS5 | **20/20** | Não alterados pelo percurso híbrido |
| Variações FTS5 | **6/6** | Não alteradas |
| Cinco buscas por sinônimos: topo bruto correto | **5/5** com vetores simulados | Descoberta interna, NÃO evidência suficiente |
| Cinco buscas por sinônimos: exibidas | **0/5** | Recusa conservadora deliberada; sem equivalência literal de atributo |
| Cinco perguntas com atributo explícito, mas FTS5 não encontra | **5/5** candidatos, vetores simulados | Candidatos com fonte e aviso, NÃO fatos confirmados |
| Doze negativos difíceis sem trecho exibido | **12/12** | Sem alegação e sem fonte falsa; também recusados no chat sem modelo simulado |
| Testes direcionados (Etapas 1 a 3B.2) | **157/157** | Aprovados no Linux deste ambiente |
| Suíte completa | **825 aprovados / 30 falhas** | Mesmas 30 falhas históricas (28 identidades de teste distintas) |
| Falhas novas na suíte completa | **0** | Comparação nominal com 3B.1 |

Os cinco exemplos de atributo explícito incluem frases artificialmente longas para distinguir o ranking FTS5 da recuperação por vetor. Eles **não representam precisão geral** e a simulação usa vetores programados. O desempenho real do `embeddinggemma`, o custo da GPU e a acurácia factual do Qwen **não foram medidos** nesta execução. Python local 3.13; o usuário testa Windows/Python 3.12 separadamente.

### Diagnóstico real já disponível, mas anterior ao 3B.2

O usuário mediu cinco top-1 corretos no embeddinggemma com cosines 0,68108; 0,69622; 0,68697; 0,66019; 0,51096. Com 0,50 havia **9/12 negativos difíceis com candidatos apenas por similaridade**. Esse número é o motivo para exigir a barreira de suficiência **antes de exibir candidatos**. O 3B.2 não inventa resultados de Ollama novo: o comando abaixo os medirá no Windows.

## Comandos de validação

```powershell
.\.venv\Scripts\python.exe tools/eval_fase4_inc3b2.py --engine fixture
.\.venv\Scripts\python.exe tools/eval_fase4_inc3b2.py --engine ollama --model embeddinggemma --timeout 30 --threshold 0.50
.\.venv\Scripts\python.exe -m pytest tests/test_fase4_inc1_biblioteca.py tests/test_fase4_inc2_ficha_neutra.py tests/test_fase4_inc2_avaliador_windows.py tests/test_fase4_inc2_avaliador_inc1_windows.py tests/test_fase4_inc3_busca_local.py tests/test_fase4_inc3b_semantic.py tests/test_fase4_inc3b_identidade_evolutiva.py tests/test_fase4_inc3b_calibracao.py tests/test_fase4_inc3b1_suficiencia.py tests/test_fase4_inc3b2_guarded_semantic.py -q
```

O avaliador grava `reports/fase4_inc3b2/baseline_{fixture,ollama}.json`. Todos os bancos SQLite usados nos testes são temporários e fechados explicitamente. Não escrever nem acessar a biblioteca pessoal ao executar essas ferramentas.

## Contratos e limitações

- O benchmarking legado 3B (`tools/eval_fase4_inc3b.py`) passou a relatar **candidatos exibidos após a barreira**; portanto o antigo 5/5 de *candidatos brutos* deve ser comparado com `raw_synonym_queries`, não com o novo `hybrid_semantic_paraphrases`. A alteração explícita do script mantém o avaliador executável com o contrato atualizado.
- As cinco paráfrases apenas semânticas agora são **recusadas** quando o filtro textual não consegue estabelecer o atributo. É uma redução deliberada de cobertura para diminuir a chance de exposição enganosa; não equivale a afirmar que o trecho correto inexiste.
- A barreira textual exige indícios literais do atributo e qualificadores na mesma frase; pode falhar para sinônimos, negações, condições, múltiplas frases ou perguntas que compartilham termos com afirmações irrelevantes. Não substitui uma avaliação de implicação lógica devidamente testada.
- Embeddings continuam `OFF` por padrão. Mesmo com o teste real aprovado, não há autorização automática para alterar `.env`; mudanças futuras exigem homologação separada.
- As identidades centrais de Campanario/Morgana/Todd e sua evolução controlada não foram modificadas.
- As 30 falhas históricas da suíte geral não estão no escopo do patch.

**Critério de aceitação no Windows:** 157/157 testes direcionados; avaliador fixture 20/20 documentos + 6/6 variações + 5/5 admissíveis + 12/12 negativos sem trecho; Ollama real deve manter **12/12 negativos protegidos**, mas a taxa de casos positivos deve ser reportada sem assumir 5/5 previamente. A operação é só leitura; não mudar o `.env` para homologar.
