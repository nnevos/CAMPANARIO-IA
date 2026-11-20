# Relatório de implementação CAMPANÁRIO V8 — repositório IA

Versão de processamento: `8.0.1`, pacote Python permanece `0.8.0` até integração/homologação. O projeto original foi lido a partir de `CAMPANARIO-IA (2).zip`; os outros dois repositórios não estavam disponíveis.

## Código alterado

- `src/campanario/utilities/document_v8.py` **novo** — extratores, OCR opcional, metadados, migração aditiva SQLite, indexação FTS5 persistente, recuperação de trechos com evidências e diff literal.
- `src/campanario/utilities/data_v8.py` **novo** — leitura segura de CSV/XLSX/JSON e operações numéricas determinísticas.
- `src/campanario/utilities/service.py` — adiciona as novas operações mantendo a API de `UtilityService` e a tabela `documents` antiga; migração inicial sem remoção.
- `src/campanario/utilities/api.py` — habilita extensões DOCX/XLSX e exposição **somente local** de originais, com validação de ID.
- `src/campanario/chat/document_intent.py` **novo** — intenção explícita e seguimento contextual de consulta documental, usando apenas mensagens de usuário e SQLite real.
- `src/campanario/chat/data_intent.py` **novo** — seleção e análise de planilhas por intenção limitada, sem gerar números no modelo.
- `src/campanario/chat/local_library.py` — metadados opcionais de seção/método/ID de evidência e aviso OCR em resposta extrativa.
- `src/campanario/chat/fact_sheet.py` — incorpora resultados documentais e cálculos como evidências distintas de memória e web.
- `src/campanario/chat/grounded_conversation.py` — impede síntese generativa sobre resultados matemáticos já computados.
- `src/campanario/chat/service.py` — consulta documental/data antes da geração, fonte compartilhada entre agentes, resposta sem citação inventada quando há falha.
- `src/campanario/web/ferramentas.js` — ferramentas de Biblioteca, Documentos e Análises com visualização de resultados reais.
- `src/campanario/web/ferramentas.css` — estilos responsivos de tabelas e barras.
- `pyproject.toml` — declara extra opcional `knowledge` (`python-docx`, `openpyxl`, `pandas`). O lock **não foi atualizado** (sem Python 3.12 aqui).
- `README.md` — referência à atualização e documentação de instalação.
- `tests/test_v8_knowledge.py` **novo** — testes de ingestão, evidências, persistência, dados e multi-turno.
- `tests/test_upload_pdf_grande_stream.py` — atualiza a expectativa antiga de descartar PDF digitalizado: V8 preserva seu original.
- `tools/windows/APLICAR_V8_SEGURA.ps1` **novo** — instalador somente IA, simulação e backup, usando hashes do manifesto.
- `docs/current/V8_MOTOR_CONHECIMENTO.md` **novo** — explicação completa, instruções de atualização e pendências.
- `docs/current/RELATORIO_V8_ENTREGA.md` **novo** — este documento de entrega.

## Demonstrações automatizadas

**Ordem Paranormal (fictício para teste, NÃO regra oficial)**: o teste cria e importa realmente o documento `Ordem Paranormal Exemplo.md` com o trecho *“No exemplo fictício, Ocultista recebe Talento Simulado T12”*, menciona o documento no Database e repete a pergunta sobre 20% NEX. A resposta final só atribui o trecho que o SQLite retornou, com o nome do documento. Sem o arquivo, responde que não encontrou trecho e não inventa página. Nenhum arquivo oficial de Ordem Paranormal foi recebido.

**Cálculo real**: o teste cria CSV com `mes,produto,valor`, 6 meses e dois produtos. O valor do Livro passa de **10 para 50** entre janeiro e junho de 2026; pandas calcula `(50 - 10) / 10 × 100 = 400%`, com arquivo e hash citados. O teste verifica que o modelo falso não foi chamado. Para produtos ausentes em um dos extremos, a comparação é sinalizada como insuficiente, não como valor zero.

## Testes executados

Resultados de execução real no ambiente Linux Python **3.13.5** (a aplicação-alvo requer Python **3.12**):

| Execução | Aprovados | Falhas | Observação |
|---|---:|---:|---|
| Repositório recebido **sem modificações** (`pytest -q`) | **963** | **32** | baseline auditado antes de alterar a base |
| Código V8, suíte completa (`pytest -q`) | **974** | **32** | **nenhuma falha nova**, comparando nomes dos 32 testes que falham |
| Testes V8 e regressão direcionada (`pytest -q tests/test_v8_knowledge.py tests/test_fase4_inc1_biblioteca.py tests/test_utilities_offline.py tests/test_upload_pdf_grande_stream.py`) | **35** | **0** | ingestão, análise, chat, SQLite, originais e regressões locais |

`node --check src/campanario/web/ferramentas.js` e `python -m compileall -q src/campanario` também passaram. Foram usados arquivos sintéticos criados nos testes; não foi importado nenhum arquivo RPG real, não foi acionado um Ollama real, o instalador PowerShell não foi executado e o projeto externo não foi testado. Há **32 falhas preexistentes** na suíte global, principalmente com dublês de serviços, expectativas de respostas/memórias e testes web. A alteração de um teste legado de PDF foi intencional para preservar o original em vez de descartá-lo. O mesmo conjunto de 32 nomes falha na versão original e na versão V8; a V8 **não corrige** essas 32 falhas.

Os resumos dos comandos e nomes dos testes que falham acompanham o patch em `RESULTADOS_TESTES_V8.txt`. O arquivo `DEMONSTRACAO_V8_EXECUTADA.json` contém saídas efetivas de importação, recuperação com `evidence_id` e cálculo `growth` contra arquivos de demonstração: Livro +400% e Jogo −20% (dados inteiramente fictícios). Executar os mesmos testes no Windows/Python 3.12 com os três repositórios reais continua obrigatório. A versão do pacote e o `uv.lock` não foram sincronizados para uma release completa.

## Pendências

Consulte `docs/current/V8_MOTOR_CONHECIMENTO.md`, seção **Pendências**. Não foi implementada a totalidade do pipeline V8, nem foi possível verificar compatibilidade em execução com as instalações externas do Python e Database sem seus conteúdos.
