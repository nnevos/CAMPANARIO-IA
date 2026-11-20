# CAMPANARIO-IA — Fase 3: leitura dos baselines reais de Windows

Data da execução registrada: 19/11/2026. Estado: **baseline real coletado, Fase 3 não homologada integralmente**.
Escopo desta entrega: observações e correção do **avaliador** (`tools/eval_fase3.py`); núcleo `src/campanario/` intocado.

## Evidências inspecionadas

- `Texto colado.txt`: instalação com `httpx==0.28.1`, `probe` offline concluído e falha `WinError 32` na limpeza do SQLite temporário do modo online; modelos Ollama encontrados (`qwen3.5:9b`, `embeddinggemma:latest`); `--engine ollama --mode both` concluído, inclusive execução completa.
- `baseline_offline_probe_stub.json`: Python 3.12.10, Windows 11, corpus SHA-256 `dba8073d0f67423883ae45f549daf840a4194064c71f2487dd7308c4b921a886`, 24 decisões factuais por regex, 2 falsos positivos, 20/20 excertos recuperáveis pela biblioteca e 0/20 no prompt do chat.
- `baseline_offline_ollama_qwen3.5_9b.json` e `baseline_online_ollama_qwen3.5_9b.json`: mesmo modelo e mesmo corpus, 74 casos concluídos por modo (50 factuais, 20 documentais, 4 cenários grupais). `internet_opt_in=false` em ambos. A rede externa foi bloqueada no processo do avaliador; isso não é um ensaio de isolamento de rede no nível do SO.
- `eval/v1/factual.jsonl`, `eval/v1/documentos.jsonl`, `eval/v1/fixtures/*.md`: gabaritos versionados e documentos sintéticos usados para confrontar respostas.
- `eval/v1/baselines/baseline_offline_probe_stub.json`: baseline estrutural local anterior, mesmo corpus, 48/50 decisões factuais por regex (1 falso positivo).

## FATOS VERIFICADOS

1. **Dependências resolvidas no Windows.** `pip install -e .` concluiu e `httpx==0.28.1` foi importado pelo Python da `.venv`.
2. **O Qwen executou.** Ambas as avaliações reais registraram 74 casos com `status=executed`. Não foram avaliadas todas as 12 situações grupais com o modelo: apenas G001, G002, G006 e G007.
3. **Falhas factuais de dois sentidos:** 25/50 respostas factuais foram marcadas como abstinência no offline; 25 não foram. Há recusas sobre pessoas/obras conhecidas (F003 Marie Curie, F009 Einstein, F031 *Dom Casmurro*, F043 conceito RAG) porque a pesquisa estava desativada. Esse número de abstinências não equivale à quantidade de recusas *indevidas*: o corpus inclui homônimos e nomes fabricados que devem resultar em abstinência se não houver fonte.
4. **Duas invenções inequívocas no corpus sintético:** F046 descreveu `Célia Vornacz` como pioneira brasileira em IA; F050 atribuiu autoria, enredo e personagens ao livro fictício *O Eclipse de Pinavé*. Os dois referentes foram intencionalmente criados como armadilhas no corpus, não como entidades verificadas.
5. **Biblioteca desacoplada do chat:** o probe recuperou 20/20 excertos exatos dos cinco documentos sintéticos, mas inseriu 0/20 no contexto entregue ao provedor.
6. **Documentos reais mal utilizados:** 0/20 respostas documentais incluíram a citação exata esperada, e 0/20 obtiveram `document_citation_verified=true`. Há contradições inequívocas nos exemplos abaixo. A métrica de menção do nome de arquivo é auxiliar; sua ausência, isoladamente, não provaria resposta errada.
7. **Online sem web:** os dois JSONs têm `internet_opt_in=false` e `external_web_authorized=false`. Os hashes de todas as 50 respostas factuais e das 20 documentais são iguais entre os modos. A diferença de latência não é ganho causal atribuído à internet.
8. **Latência do primeiro conteúdo visível (inclui respostas instantâneas do guard):** offline p50=1.906 ms e p95=5.634 ms; online sem web p50=1.852 ms e p95=5.188 ms. Para perguntas factuais com `first_visible_ms >= 50`, a mediana offline foi ~4.205 ms, mas o limite de 50 ms é apenas um recorte descritivo, **não** uma identificação formal de chamadas ao modelo. Não há medição de VRAM.
9. **Divergência de versão/execução:** o baseline estrutural de referência marcou 48/50 perguntas factuais para busca (FP=1); o Windows marcou 24/50 (FP=2). Os 24 IDs divergentes incluem F001, F002, F006, F010, F016, F046, F050. Como corpus e sua SHA coincidem, o candidato prioritário a verificar é o código efetivamente importado de `src/campanario/utilities/web_intent.py`.
10. **Erro de limpeza Windows:** no `probe --mode both`, após gravar o relatório offline e executar a avaliação online, o processo falhou removendo `utilidades.sqlite3` em `tempfile.TemporaryDirectory` por `PermissionError: WinError 32`. Isto não invalida o baseline **real** salvo posteriormente, mas impede completar o probe em ambos os modos numa única execução Windows original.

### Contradições diretas contra documentos sintéticos

| ID | Fonte sintética | Resposta observada | Classificação |
|---|---|---|---|
| D001 | Projeto Faro **não consulta** serviços externos por padrão | Afirma que usa serviços externos por padrão | Contradição |
| D005 | Selo do Guia Rumo **azul** | Responde **verde** | Contradição |
| D006 | Revisão Rumo em **18 minutos** | Responde **10 minutos** | Contradição |
| D009 | Etiqueta da Ponte **marfim** | Responde **azul** | Contradição |
| D010 | Revisão da Ponte na sala **T12** | Responde **Sala 4** | Contradição |
| D011 | Checagem Ponte na **segunda-feira** | Responde **quarta-feira** | Contradição |
| D012 | Checklist Ponte versão **7** | Responde **4.2** | Contradição |
| D016 | Inventário Aurora **14 amostras** | Responde **42 amostras** | Contradição |
| D017 | Estação Horizonte em **modo avião** | Responde **validação passiva** | Contradição |
| D019 | Símbolo Horizonte **círculo verde** | Responde círculo com linha horizontal | Contradição |

Esses são 10 **exemplos verificados**, não uma avaliação manual completa de 20/20 respostas. A ausência de evidência recuperada no prompt explica a incapacidade de fundamentar as respostas, mas a causalidade exata de cada invenção ainda exige instrumentação e novos testes.

## HIPÓTESES — NÃO CONFUNDIR COM RESULTADOS

- Há divergência entre a implementação do `web_intent.py` usada no Windows e aquela do ZIP completo da Etapa 3; outra possibilidade é importação de uma instalação/arquivo diferente. Precisa de hash de arquivo e caminho de importação para fechar o diagnóstico.
- `with sqlite3.Connection` gerencia transação, mas não faz `close()`; conexões não liberadas prontamente no ciclo do avaliador provavelmente explicam a impossibilidade de excluir `utilidades.sqlite3` no Windows. O avaliador agora acompanha e fecha explicitamente suas conexões, porém **não foi possível validar a correção no Windows neste ambiente**.
- A latência pode se elevar com ficha factual/local e 2 agentes. A medição aqui não permite estimar aumento de VRAM nem comparar Qwen/Gemma.

## PROPOSTA DE CONTINUIDADE

1. Antes de alterar `src/`, comparar o `web_intent.py` do Windows com o SHA-256 do ZIP da Etapa 3: **`1747c469878cff578ea850b63f8c8b880643e62a8ec1698ffc07aa1b3361b302`**. Verificar também `direct_decision('Quem foi Ada Lovelace?')` e caminho de importação. **Não sobrescrever automaticamente código local diferente:** enviar os resultados para comparação.
2. Aplicar, se o avaliador local for a mesma versão, somente as correções contidas nesta entrega; repetir o `probe --mode both` em diretório de relatórios novo. O teste em Linux passou (12 testes e execução offline+online); a correção Windows aguarda comprovação.
3. Preservar os baselines reais enviados com seu identificador da versão Windows atual, sem sobrescrevê-los. Reexecutar o baseline *após* confirmar/normalizar a versão de código; comparar IDs F046/F050 e D001/D005/D016 para checagem rápida.
4. Completar revisão semântica das 20 perguntas documentais, 50 factuais e 12 cenários grupais antes de encerrar plenamente a Fase 3. A versão atual não mensura precisão factual final, correção de citações, semântica em grupo, consumo de VRAM nem acesso a uma enciclopédia local.
5. Testar internet autorizada `--allow-web` **somente com permissão expressa do usuário**, depois que o offline estiver consistente; rede pública deve continuar desligada por padrão.

**Gate recomendado:** não iniciar a Fase 4 enquanto a divergência de versão do núcleo não estiver explicada. Depois, correções incrementais começam pela recuperação local para a ficha factual neutra, sem introduzir novos guardas regex.

## Validação da alteração do avaliador incluída neste pacote

- Código do núcleo: **nenhuma alteração**.
- `tools/eval_fase3.py`: criadas conexões SQLite de avaliação rastreadas explicitamente e `close()` no `finally` do probe/real; corrigida a nota de rodapé de relatórios que alegava que respostas não eram salvas mesmo com `--include-responses`.
- `tests/test_fase3_evaluation.py`: novo teste da liberação de conexões.
- Ambiente de validação disponível: Linux, Python 3.13; `pytest -q tests/test_fase3_evaluation.py` => **12 passed**. Probe offline e online executaram com sucesso e o processo terminou com código 0. A execução online do probe inclui uma exceção de rede **injetada intencionalmente**, que pode aparecer no log.
- Teste da correção Windows **não executado** nesta entrega.

Não modificar bases de usuários, arquivos `.env`, memórias, modelos Ollama, caches pessoais ou acervos reais para concluir este diagnóstico.
