# Relatorio de entrega - CAMPANARIO V9.1 (IA)

**Versao do incremento:** `9.1.0-ia`. A versao do pacote Python continua `0.8.0` ate homologacao de release; esta entrega **nao** inclui as implementacoes ausentes de cerebros, arquetipos e talentos V9.

## Inventario de alteracoes em relacao a V8 anterior

| Arquivo | Tipo | Alteracao |
|---|---|---|
| `src/campanario/chat/canonical_answer.py` | novo | Contrato Pydantic imutavel, `AnswerMode`, estados, fatos, fontes, execucoes, validadores e construcao canonica |
| `src/campanario/chat/grounded_expression.py` | novo | Gerador de expressao Ollama, validacao local, tentativas e fallback |
| `src/campanario/chat/service.py` | alterado | Compilacao antes dos agentes, reuso da ficha canonica, validacao antes de publicar, telemetria e trilha local |
| `src/campanario/agents/profiles.py` | alterado | `ExpressionProfile` e campos de extensao para arquétipos e talentos, sem substituir a Biblia |
| `src/campanario/chat/data_intent.py` | alterado | Identifica pedido de soma de faturamento/receita |
| `src/campanario/utilities/data_v8.py` | alterado | `data.sum` com `Decimal` e recusas em dados incompletos |
| `src/campanario/config.py` | alterado | Habilitacao e numero de novas tentativas |
| `src/campanario/composition.py` | alterado | Injetor de configuracao no chat |
| `src/campanario/api.py` | alterado | Endpoint local de observabilidade da fundamentacao |
| `src/campanario/web/index.html` | alterado | Acionador da visualizacao tecnica de evidencias |
| `src/campanario/web/static/chat.js` | alterado | Consulta e exibe trilha real, sem executar HTML das fontes |
| `src/campanario/web/static/dark-matter-v7.css` | alterado | Estilo Dark Matter para visor e estados |
| `.env.example` | alterado | Variaveis de controle opcionais |
| `tests/test_v91_expression.py` | novo | 15 testes de fidelidade, contradicao, contrato, perfil, importacao real ficticia, CSV e API |
| `tests/test_v8_knowledge.py` | alterado | Regressao para expressao controlada sobre dados calculados |
| `tests/test_resposta_conversacional_com_evidencia.py` | alterado | Expectativas mais restritivas: fallback quando auditor textual antigo permitiria expansao |
| `README.md` | alterado | Entrada para documentacao V9.1 |
| `docs/current/V91_EXPRESSAO_FUNDAMENTADA.md` | novo | Auditoria, arquitetura, operacao, instalacao e limites |
| `docs/current/RELATORIO_V91_ENTREGA.md` | novo | Inventario e resultados da entrega |

Instalador `tools/windows/APLICAR_V91_SEGURA.ps1`, manifesto de hashes e instrucoes acompanham o **ZIP incremental**, nao substituem o instalador V8 existente no repositorio.

## Validacao executada

| Ambiente / suite | Passaram | Falharam | Resultado |
|---|---:|---:|---|
| V8 original recebido para a V9.1, `pytest -q` | 974 | 32 | Comparacao antes de editar |
| V9.1 atualizado, `pytest -q` | **989** | **31** | Todas as 31 falhas ja existiam na V8 |
| V9.1 dirigida (`test_v91_expression.py`, `test_resposta_conversacional_com_evidencia.py`, `test_v8_knowledge.py`) | **32** | **0** | Fluxo de fatos, UI API local, erro e fallback |

A linha de base de **32** falhas refere-se especificamente a base V8 recebida nesta rodada, nao a versao do usuario no Windows. Os nomes das 31 falhas foram comparados com os nomes da V8. A suite executou em Linux com Python 3.13; o projeto instalado pode requerer Python 3.12. `node --check` e compilacao de sintaxe Python tambem foram executados.

**Falhas remanescentes:** testes legados principalmente de contratos de stubs e web, memórias, roteamento e formato de resposta. Nao declarar "suite completa sem falhas". Veja `RESULTADOS_TESTES_V91.txt` no patch para os identificadores e comandos.

## Evidencias dos testes

1. Valor de `R$ 15.000.` preservado em diferentes personagens; `R$ 16.000.` rejeitado.
2. Condicao literal "somente apos aprovacao" nao pode ser omitida na reformulacao.
3. Nenhum objeto desconhecido pode criar comprovante de consulta executada; fontes nao encontradas nao acionam invencao do modelo.
4. Contradicoes evitam o estado `verified` e nao enviam LLM a escolher arbitrariamente.
5. Pagina e nome de fonte falsos propostos pelo LLM sao rejeitados; referencias sao montadas com metadados reais.
6. Provedor simulado recebe valores corretos, inventa erros em duas tentativas e aciona fallback para a resposta canonica.
7. `Ordem Paranormal Exemplo.md` **e importado em SQLite de teste e consultado** apos tres mensagens; seu trecho e inventado **exclusivamente como fixture de teste**, nao regra de jogo verdadeira.
8. CSV de teste importado: `100.10 + 200.20 = 300.30`, calculo Decimal; ausencias geram `insufficient_data`.
9. Endpoint local responde sem trilha inexistente; endereco remoto recebe HTTP 403.

## Nao comprovado / pendente

- Execucao de Ollama realmente instalado, desempenho/latencia com modelos locais, validacao semantica completa e certidao de ausencia de alucinacao.
- V9 completa com roteador de cerebros/arquetipos/talentos, ausente na base recebida.
- O PDF oficial de Ordem Paranormal, ausente; nenhuma regra oficial foi citada.
- Integracao no Windows com `CAMPANARIO-PYTHON`, `CAMPANARIO-DATABASE`, uso mobile real e instalador PowerShell testado **no Windows**.
- Verificacao de arquivo original modificado por instalacoes locais (o aplicador abortara ate conciliacao).

O pacote e um incremento integrado ao fluxo de chat V8 **testado em ambiente de desenvolvimento**, nao uma homologacao da V9.1 integral solicitada. Consulte `V91_EXPRESSAO_FUNDAMENTADA.md` para instalacao e limites.
