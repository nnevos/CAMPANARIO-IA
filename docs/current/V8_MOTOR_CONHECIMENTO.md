# CAMPANÁRIO V8 — motor documental e de análise (incremento verificável no IA)

> Escopo: **somente `CAMPANARIO-IA`**, sobre a base 0.8.0 recebida. Não foram enviados os repositórios `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE` nem o acervo real de Ordem Paranormal. A V8 aqui é **incremental**, não a implementação integral de todas as 15 seções da especificação. O número V8 nomeia este incremento funcional; o projeto continua declarando a versão de pacote `0.8.0` até uma release integrada.

## Auditoria do projeto recebido

| Capacidade | Encontrada antes da atualização | Atualização neste incremento |
|---|---|---|
| Importação | `utilities/service.py` importava TXT, MD e PDF e armazenava texto/páginas em `documents` | `utilities/document_v8.py` amplia para DOCX, CSV, XLSX, JSON; preserva cópia original inclusive quando a extração falha |
| Extração PDF | `pypdf`, sem OCR e sem metadados detalhados | Preserva páginas, usa modo de layout quando possível, OCR seletivo opcional (`pdftoppm` + Tesseract), avisos de perda de fidelidade |
| Banco de utilidades | SQLite `utilidades.sqlite3`, tabela antiga `documents`; separado de conversas e memórias | Adiciona `document_details`, `document_sections` e `document_fts` (quando FTS5 disponível) sem reescrever o legado |
| Busca | `chat/local_library.py` FTS5 em RAM e modo lexical; `chat/semantic_library.py` Ollama embeddings opcionais | Recuperação explícita por seção, título, pista de nome, página e ID de evidência; mantém a busca antiga e embeddings locais |
| Agentes | `chat/service.py`, `chat/fact_sheet.py`, `chat/grounded_conversation.py`; Morgana/Todd compartilham fontes por turno | Resolução de pedidos de fonte no histórico **do usuário**; resposta extrativa com referência ou declaração de não encontrado |
| Dados | Cálculos básicos (`calc.*`), sem análise de tabelas | `data.inspect`, `data.analyze` (describe, missing, group, trend, growth, filter) com operações determinísticas e limites de entrada |
| UI | `/ferramentas`, com biblioteca e upload, navegação em dispositivos pequenos | Biblioteca, Documentos e Análises com teste de busca, estados finais reais, original, Markdown, tabelas e barras calculadas |

A arquitetura das personalidades (`agents/morgana.py`, `agents/todd.py` e os perfis), memórias, Modo Patrulha, Biblioteca Conversacional V2 e o sistema de permissões **não foi reescrita**. Arquivos importados não são transformados em memórias pessoais dos agentes.

## Fluxo efetivamente implementado

`Upload local / arquivo autorizado → cópia com UUID → SHA-256 → extração → Markdown e páginas → avisos → SQLite legado + metadados/seções → índice FTS5 → recuperação com evidência → resposta extrativa ou cálculo de planilha`

O documento original fica em `CAMPANARIO-DATABASE/dados/<ambiente>/utilidades/documentos/<id>.<ext>` **conforme `CAMPANARIO_DATA_DIR` e `CAMPANARIO_MEMORY_ENVIRONMENT` da instalação**, não na pasta IA. A localização exata é a que `UtilityService` configura. Nunca sobrescreva a pasta `dados` com dados de um ZIP de código.

O SQLite existente `utilidades.sqlite3` mantém `documents(id,name,category,sha256,content,pages,source,created)` sem alteração de colunas. As novas tabelas são criadas na primeira inicialização da Central de Ferramentas. Documentos legados seguem consultáveis por seus registros de páginas, com método marcado `legacy`; o processo não reimporta nem apaga originais anteriores. Na primeira execução de um banco já atualizado, se houver seções ainda fora do FTS5, o índice é preenchido incrementalmente.

### Estados reais e limitações

- `available`: texto extraído e nenhuma ressalva registrada.
- `partial`: texto incompleto, dependência opcional/etapa problemática, OCR, ausência de página ou limite de fidelidade declarado. O original continua armazenado.
- `error`: a cópia do original foi concluída, mas a extração falhou; detalhes contêm o tipo e a mensagem resumida do erro.

A interface exibe somente estados **consolidados após o processamento síncrono**. Fila persistente, etapas intermediárias ao vivo, cancelamento, execução assíncrona e telemetria de fila **ainda não foram implementados**; a interface não simula essas operações.

A extração de PDF usa a ordem de texto fornecida pelo `pypdf`; documentos com múltiplas colunas, tabelas aninhadas e notas complexas podem perder estrutura. Páginas digitalizadas têm OCR local opcional, identificado por `method=ocr_local`, com aviso de revisão. Ausência do Tesseract/pdftoppm impede a transcrição, mas nunca preenche a lacuna com texto inventado. As imagens de páginas permanecem no PDF original. Para DOCX, não se promete paginação nem notas de rodapé fiéis. Fórmulas XLSX nunca são executadas; só são utilizados os valores em cache. Arquivos inválidos e planilhas grandes demais retornam erro ou processamento parcial com detalhes.

### Recuperação e agentes

`library.retrieve` retorna apenas trechos encontrados, com `evidence_id`, `document_id`, `document`, `sha256`, `page`, `section`, `excerpt`, `method`, `extraction_method` e pontuação. Um hit é **candidato relevante**, não prova de veracidade externa. Sem trecho adequado, status `not_found`; nenhum número de página é inventado. Para referências a Database/PDF/documentos em mensagens anteriores do usuário, `chat/document_intent.py` consulta o SQLite real **antes** da geração. Um resultado de consulta é compartilhado por turno por Morgana e Todd. O resultado da busca não é produzido pelo modelo.

Quando fontes diferentes dão trechos distintos e com relevância comparável, o chat apresenta a divergência em vez de escolher uma só. Isso é uma detecção **textual**, não uma prova lógica de contradição. A pesquisa geral e a memória continuam separadas e mantêm as salvaguardas anteriores. A análise numérica gera uma resposta de origem `computed_analysis`, nunca reescrita livremente como se fosse citação textual do documento.

### Análises numéricas

Na interface: **Ferramentas → Biblioteca → importe CSV/XLSX/JSON → Análises → Inspecionar** para obter nomes de colunas e tipos. Configure operação e colunas antes de calcular. Para uma planilha com `mes,produto,valor`, a operação `growth` compara o primeiro e o último mês dentre até seis meses distintos presentes nos dados; agrupa os valores por produto/mês, calcula variação absoluta e percentual, e **não considera ausência de um produto como venda zero**. Valores iniciais zero têm crescimento percentual indefinido. A saída inclui o nome do arquivo e o SHA-256 do original.

No chat, um pedido explícito de análise de vendas pode selecionar uma **única** planilha importada ou um nome de arquivo identificável, inspecionar colunas comuns (`mes`, `produto`, `valor` etc.) e executar cálculo local. Se houver arquivos ambíguos, colunas não identificáveis ou dados insuficientes, a resposta comunica a limitação e remete à interface manual. Não há execução livre de Python, SQL ou scripts solicitados pelo modelo.

### Endpoints e ferramentas (somente loopback, política anterior preservada)

- `POST /api/v1/utilities/upload-stream?filename=...` — upload binário com limite atual de 200 MB, extensões permitidas; apenas salva no workspace autorizado.
- `POST /api/v1/utilities/invoke` com `library.import` e `confirm:true` — copia e processa arquivo permitido da pasta autorizada, limite de 500 MB para original.
- `library.list` / `library.search` — catálogo e busca literal legados, agora com estado, método e busca pelo nome.
- `library.retrieve` com `query`, opcionalmente `document_id`, `document_hint`, `limit`.
- `library.document` com `document_id`, opcional `include_markdown:true`.
- `library.compare` com `document_a` e `document_b` — diff literal de linhas, nunca análise semântica inventada.
- `data.inspect` com `document_id`, opcional `sheet`.
- `data.analyze` com `document_id`, `operation`, `column`, `group_by`, `period_column`, `aggregation`, `operator` e `value` conforme a operação.
- `GET /api/v1/utilities/documents/{id}/original` — arquivo de origem local; obedece à validação de host/origem existente.

A Central de Ferramentas no navegador remoto/mobile continua sujeita à **restrição de acesso localhost existente**. A experiência de visualização de evidências diretamente nas bolhas do chat e a autenticação para acesso móvel remoto são pendências; não se deve desativar indiscriminadamente a restrição de loopback.

## Como atualizar no Windows com as três pastas

1. **Feche Campanário e os serviços que acessam os bancos.** Faça seu backup dos dados de `CAMPANARIO-DATABASE` com procedimento de backup consistente de SQLite antes da primeira execução da V8. Mantenha `.env` e modelos de voz locais.
2. Extraia o ZIP **patch V8** em uma pasta temporária fora de `CAMPANARIO-IA`. No PowerShell, execute o aplicador primeiro sem `-Apply`, depois com `-Apply`:

   ```powershell
   $projeto = 'C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA'
   $patch = 'C:\CAMINHO\PARA\CAMPANARIO_V8_PATCH'
   & "$patch\tools\windows\APLICAR_V8_SEGURA.ps1" -ProjectRoot $projeto -PatchRoot $patch
   & "$patch\tools\windows\APLICAR_V8_SEGURA.ps1" -ProjectRoot $projeto -PatchRoot $patch -Apply
   ```

   O script valida o manifesto SHA-256 e só substitui arquivos **explicitamente listados** dentro de IA. Cria backup do código anterior em uma pasta irmã antes de copiar. Não toca nas outras duas pastas, `.env`, `.git`, `.onnx` ou bancos SQLite. O script foi **criado, mas não executado em PowerShell/Windows** neste ambiente.
3. No ambiente Python 3.12 instalado em `CAMPANARIO-PYTHON`, instale as dependências extras para DOCX/planilhas. A distribuição contém o extra `knowledge` em `pyproject.toml`, mas o `uv.lock` **não foi regenerado**, pois o ambiente de teste não possui interpretador Python 3.12 e a atualização offline do lock falhou. Instale explicitamente no Python externo (com acesso a pacotes previamente baixados ou conexão somente na instalação):

   ```powershell
   & 'C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-PYTHON\.venv\Scripts\python.exe' -m pip install 'python-docx>=1.1,<2' 'openpyxl>=3.1,<4' 'pandas>=2.2,<3'
   ```

   Se esse ambiente usa `uv` sem `pip`, prefira:

   ```powershell
   uv pip install --python 'C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-PYTHON\.venv\Scripts\python.exe' 'python-docx>=1.1,<2' 'openpyxl>=3.1,<4' 'pandas>=2.2,<3'
   ```

   Para OCR seletivo, instale Tesseract com português/inglês e Poppler (`pdftoppm`) no `PATH` de **Windows**, opcionais. Não instale nada por instruções presentes nos próprios documentos.
4. Ainda na pasta `CAMPANARIO-IA`, execute os testes com o Python externo e confirme caminhos antes de abrir com `CAMPANARIO.vbs`:

   ```powershell
   & '..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe' -m pytest tests/test_v8_knowledge.py tests/test_fase4_inc1_biblioteca.py tests/test_utilities_offline.py tests/test_upload_pdf_grande_stream.py -q
   & '.\TESTAR_3_PASTAS.ps1' -ProjectRoot '.'
   ```

5. Abra a **Central de Ferramentas**, confira a Biblioteca e importe um arquivo de teste. Inspecione `library.retrieve` ou a busca com evidências antes de confiar na resposta dos agentes. Seu acervo do Database real não foi enviado e precisa ser testado **na instalação local**.

Para reverter código, feche o aplicativo e restaure os arquivos do backup do aplicador. Uma reversão de esquema SQLite da V8 não é necessária para voltar ao código anterior: as tabelas extras são aditivas e podem permanecer no banco sem interferir no acesso legado. **Não apague as tabelas na tentativa de reverter.**

## Testes e status de aceitação

Os testes V8 usam arquivos fictícios construídos no próprio teste (incluindo material de RPG *não canônico*, explicitamente fictício). O arquivo de **Ordem Paranormal real não foi enviado** e nenhuma regra oficial ou página real foi afirmada/validada. O teste verifica que, após um usuário mencionar um documento importado no Database, os agentes só atribuem conteúdo de um arquivo realmente lido e falham com segurança caso ele não exista. O cálculo de crescimento usa dados numéricos reais de um CSV sintético, computados via pandas.

Resultados locais são registrados no relatório de entrega. Não há homologação com Ollama rodando, com os bancos e arquivos reais da sua instalação, com `CAMPANARIO-PYTHON` do Windows ou com o cliente mobile remoto.

## Pendências (não implementado como completo)

- Extração estrutural fiel de PDFs multicoluna, tabelas complexas e notas de rodapé, com revisão humana e confiança OCR por bloco.
- Indexação/embeddings persistentes e incrementais, reordenação semântica completa e cache de embeddings entre reinícios (a busca semântica opcional antiga permanece em memória).
- Fila com progresso por etapa, workers em segundo plano, cancelamento e limites de memória/CPU rígidos em Windows.
- Motor de contradições semânticas, cronologias automáticas, relatórios/gráficos exportáveis completos e exportação formal de análises.
- Planejamento geral de cálculos livres em linguagem natural; o roteador cobre intenções e colunas comuns, não análise arbitrária.
- Links de citação interativos diretamente nas bolhas da interface Dark Matter V7 e acesso remoto mobile autenticado a documentos.
- Teste com **o PDF real de Ordem Paranormal** e migração/compatibilidade verificada com os dois repositórios não enviados.
