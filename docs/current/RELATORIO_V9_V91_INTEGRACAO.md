# Relatorio de entrega — CAMPANARIO V9 com motor de expressao fundamentada V9.1

## Resumo

Foi implementada a arquitetura de cerebros e fichas V9 **sobre a base de codigo V9.1** anteriormente entregue, sem reconstruir o Campanario. Alteracoes limitadas ao `CAMPANARIO-IA`; os repositorios `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE` nao foram enviados e permanecem intocados. O roteiro funcional e as interfaces estao em `V9_BRAINS_ARQUETIPOS_TALENTOS.md`.

## Auditoria e aproveitamento

- `agents/router.py` preservado para escolher o interlocutor; `CapabilityRouter` novo escolhe ferramentas/cerebros.
- `agents/profiles.py` preserva contratos de `AgentProfile`, `PersonalityCore` e `AgentRegistry`; adiciona registro seguro de novos perfis por composicao.
- `chat/document_intent.py`, `chat/knowledge.py`, `chat/grounded_conversation.py` e `chat/data_intent.py` mantem as responsabilidades V8/V9.1. Os novos cerebros encapsulam os fluxos preexistentes, nao reimplementam ingestao de documentos.
- `chat/canonical_answer.py`, `chat/fact_sheet.py`, `chat/grounded_expression.py` continuam a construir/verificar respostas, agora com rastros de cerebros e diretivas nao privilegiadas de ficha.
- `storage/database.py` preservado, migracao Alembic incremental `0010` adiciona tabelas V9.
- Flag `CAMPANARIO_BRAINS_V9_ENABLED` desativada por padrao e reversivel pelo `.env`.

## Entregas funcionais

1. `campanario/brains`: protocolos, contratos, registro, health-check, executor e `trace_id`.
2. Dois cerebros operacionais **Conhecimento** e **Analise** reaproveitando recuperacao/calculo real; seis cerebros futuros registrados como indisponiveis.
3. `CapabilityRouter` independente com planejamentos limitados; gatilhos explicitos deterministas.
4. `AgentBuild` versionado Pydantic, oito arquetipos, seis talentos declarativos e limite de dois talentos ativos/turno.
5. Persistencia de fichas, versoes, associacoes e execucoes observadas, com backfill livre para Morgana/Todd e migracao 0010.
6. APIs locais e interface Dark Matter: Central de Cerebros, Forja, editor de ficha, criacao de agente e previa de operacoes.
7. `.campagent` seguro (somente declaracao; checksum, tamanho, caminho; sem execucao automatica).
8. Integracao com resposta factual V9.1 sem conceder ao arquetipo/talento autoridade sobre fontes, fatos ou permissoes.

## Evidencias de testes

| Suite | Antes V9.1 | Depois V9 + V9.1 |
|---|---:|---:|
| Aprovados | 989 | 1004 |
| Falhas | 31 | 31 |
| Novas falhas em relacao a base | — | **0** |

Comparados por nome: todos os **31** testes que falham no incremento tambem falham na V9.1 anterior. Foram aprovados **14 testes V9 novos**, e **36 testes direcionados** incluindo regressao V8/V9.1. Nao declaramos a suite 100% aprovada.

Testes cobrem: separacao `AgentRouter`/`CapabilityRouter`, importacao e recuperacao de documento ficticio de Ordem Paranormal com `evidence_refs`, valores de CSV e XLSX, inexistencia de fonte, negacao de permissao, builds e talentos, migracao e downgrade de banco temporario com conversa preservada, pacote malicioso, flag desligada, endpoints locais e persistencia de agentes novos. O fluxo com modelo local real Ollama nao foi executado nesta sessao.

Demonstracao executada em `DEMONSTRACAO_V9_V91_INTEGRADAS.json`: consulta a um Markdown de **ficcao de teste**, com fonte real recuperada e texto inventado reprovado pela validacao; CSV importado com soma `100 + 200 = 300.00` confirmada por ferramenta, com operacoes `data.inspect` e `data.sum` e rastreio. **Nao descreve regras reais de Ordem Paranormal.**

## Limites/pendencias

- Nao homologado no Windows, mobile fisico ou nos dois repositorios nao fornecidos; instalador nao executado em Windows real.
- Python de testes do container 3.13, enquanto o projeto declara suporte >=3.12,<3.13.
- Sem Ollama real neste teste; o contrato e integracao do provider preexistente foram preservados.
- Cerebros Investigacao/Programacao/Estrategia/Percepcao/Comunicacao/Criacao so catalogados; NAO executam.
- O timeout nao encerra threads internamente, nem constitui sandbox de RAM/CPU. Entrada CSV/XLSX usa limites do modulo V8 existente.
- Validacao factual V9.1 usa checagens conservadoras e fallback; nao e prova matematica contra toda mudanca semantica.
- Catalogo de talentos define o schema, mas `preconditions` complexas ainda nao possuem um mecanismo geral de politica/avaliacao.
- Verificacao visual por navegador mobile real ainda pendente; foram validados JavaScript e endpoints.
- Falhas antigas documentadas em `RESULTADOS_TESTES_V9.txt` continuam abertas.

## Arquivos criados/alterados (em relacao a V9.1 fornecida)

| Acao | Arquivo |
|---|---|
| MODIFICADO | `.env.example` |
| NOVO | `CHANGELOG_V9_INTEGRADA.md` |
| NOVO | `LEIA_PRIMEIRO_V9_INTEGRADA.md` |
| MODIFICADO | `README.md` |
| NOVO | `docs/current/RELATORIO_V9_V91_INTEGRACAO.md` |
| NOVO | `docs/current/V9_BRAINS_ARQUETIPOS_TALENTOS.md` |
| MODIFICADO | `pyproject.toml` |
| MODIFICADO | `src/campanario/agents/profiles.py` |
| NOVO | `src/campanario/brains/__init__.py` |
| NOVO | `src/campanario/brains/adapters.py` |
| NOVO | `src/campanario/brains/agents.py` |
| NOVO | `src/campanario/brains/api.py` |
| NOVO | `src/campanario/brains/builds.py` |
| NOVO | `src/campanario/brains/contracts.py` |
| NOVO | `src/campanario/brains/executor.py` |
| NOVO | `src/campanario/brains/models.py` |
| NOVO | `src/campanario/brains/package.py` |
| NOVO | `src/campanario/brains/registry.py` |
| NOVO | `src/campanario/brains/router.py` |
| NOVO | `src/campanario/brains/store.py` |
| MODIFICADO | `src/campanario/chat/data_intent.py` |
| MODIFICADO | `src/campanario/chat/grounded_expression.py` |
| MODIFICADO | `src/campanario/chat/service.py` |
| MODIFICADO | `src/campanario/composition.py` |
| MODIFICADO | `src/campanario/config.py` |
| MODIFICADO | `src/campanario/main.py` |
| NOVO | `src/campanario/migrations/versions/0010_v9_brains.py` |
| MODIFICADO | `src/campanario/storage/models.py` |
| MODIFICADO | `src/campanario/web/ferramentas.css` |
| MODIFICADO | `src/campanario/web/ferramentas.js` |
| NOVO | `tests/test_v9_brains.py` |
| NOVO | `tools/__init__.py` |
| NOVO | `tools/demo_v9_integrada.py` |

## Seguranca e atualizacao

O patch inclui manifesto SHA-256 da base V9.1 e do novo codigo, instalador PowerShell inicialmente em modo simulacao e backup dos arquivos substituidos. Em caso de personalizacao local, o instalador recusa sobrescrever; faca conciliacao manual. Proteja o Database e o `.env` com um backup externo antes de aplicar. A flag de runtime e reversivel; downgrade Alembic `0010` retira tabelas **novas** V9 e seus dados, portanto so deve ser utilizado com backup. Para procedimento, consulte `LEIA_PRIMEIRO_V9_INTEGRADA.md`.
