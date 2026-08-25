# CHANGELOG

## 2026-08-24 — Conversational v1.5.6 / Semantic Evaluator Closure

- fecha falsos PASS observados no E2E v1.5.5;
- `truth_over_agreement` bloqueia tambem promessas genericas de simular/fingir falsidade;
- formato exato rejeita preambulo fora do conteudo solicitado;
- registro curto de contexto recebe contrato proprio para evitar palestra institucional;
- pedidos de primeiro diagnostico tecnico recebem budget menor e prioridade para observacao concreta;
- E2E endurecido para preambulo, registro contextual, primeiro diagnostico e confusao espalhamento/reflexao;
- Manual 16 e ADR-0027 adicionados;
- gate obrigatorio de refatoracao estrutural registrado para ocorrer antes de Todd/Morgana;
- suite offline: **179/179 testes**.


## Conversational v1.2

- adiciona `entendi` e `pois e` ao modo `continuation`;
- social deixa explicito que nao deve fabricar atividade/assunto;
- continuation evita eco e continuidade forcada;
- discussion permite discordancia clara sem concordancia de cortesia contraditoria;
- creative distingue invencao autorizada de alucinacao factual;
- auditoria passa a parear pedido do usuario e resposta do assistant;
- testes: 49/49.

# Changelog — Campanario

## 2026-08-23 — Incremento 2 / Fase 1 parcial

Adicionado:
- ambiente Alembic e migration `0001` para `chat_sessions` e `messages`;
- repositories SQLAlchemy concretos;
- `ChatService` para criação de sessão, histórico e turno de chat;
- `OllamaProvider` via HTTPX e `/api/chat` com streaming NDJSON;
- endpoints `/api/sessions`, `/api/sessions/{id}/messages` e `/api/sessions/{id}/chat/stream`;
- streaming HTTP em SSE;
- `FakeModelProvider` permanece como caminho de testes sem Ollama/GPU;
- testes unitários/API/repositories;
- documento `docs/RECOVERY.md`.

Validação realizada no ambiente de desenvolvimento:
- 5 testes passaram;
- migration Alembic `0001` aplicada com sucesso em SQLite temporário;
- `compileall` passou;
- Ruff não pôde ser executado neste ambiente porque o binário não está instalado globalmente; permanece dependência de desenvolvimento no `pyproject.toml`.

Limitações conscientes:
- não houve teste real contra uma instalação Ollama nesta entrega;
- não há UI;
- não há Context Manager inteligente; todo histórico concluído da sessão é enviado ao modelo;
- cancelamento/stream interrompido ainda não possui estado persistente específico.

## 2026-08-23 — Hardening de validação de entrada

- Teste real mostrou que `{"message":"   "}` era aceito.
- `ChatRequest` passou a normalizar com `strip()` e rejeitar whitespace-only.
- Adicionado teste automatizado para garantir 422 e ausência de persistência.
- Mensagem vazia `""` já era rejeitada por `min_length=1`.
- Próximo gate: validar a correção no Windows e definir política de falha/interrupção de turno.

## 2026-08-23 — Hardening final da Fase 1

- Exceções HTTPX deixaram de vazar para a camada API.
- Criados erros próprios de `ModelProvider`: unavailable, timeout e response error.
- OllamaProvider traduz falhas de transporte para contratos do Campanario.
- Política mínima congelada: mensagem do usuário permanece; resposta assistant incompleta não é persistida.
- Timeout do Ollama permanece configurável por `CAMPANARIO_OLLAMA_TIMEOUT_SECONDS`.
- Adicionados testes para falha do modelo e ausência de assistant persistido.

## 2026-08-23 — Fase 1 encerrada e recovery consolidado

- Validação final com provider indisponível concluída.
- Mensagem do usuário preservada sem resposta assistant falsa.
- Provider religado e resposta normal `Campanario OK.` validada por SSE.
- Fase 1 declarada concluída.
- Próxima fase definida: Context Manager.
- Adicionado `RECOVER_FIRST.md`.
- Adicionado manifesto com hashes das referências externas.
- Adicionada política/script de backup local incluindo app-data SQLite.

## 2026-08-24 — Fase 2 / Context Manager — primeiro incremento

Adicionado:
- contrato próprio `ContextManager`;
- implementação `RecentMessagesContextManager` com janela recente determinística;
- orçamento configurável por `CAMPANARIO_CONTEXT_MAX_MESSAGES` (default 20);
- filtro de mensagens concluídas e preservação de ordem cronológica;
- proteção simples contra janela iniciando em resposta `assistant` órfã;
- preservação de mensagens `user` sem resposta posterior;
- integração por injeção no `ChatService` e `bootstrap`;
- log `DEBUG` com quantidade total/selecionada e orçamento;
- testes unitários do seletor e teste garantindo delegação pelo `ChatService`.

Gate atingido:
- `ChatService` não possui mais regra inline de seleção/corte de histórico.

Validação local deste pacote:
- baseline: 8/8 testes;
- após alteração: 13/13 testes;
- `compileall` e `git diff --check` passaram;
- Ruff não disponível no Python Linux do ambiente atual; `.venv` empacotado é Windows.

Fora do escopo mantido:
- sumarização;
- tokenizer específico;
- memória/RAG/agentes/voz/internet/knowledge graph/UI.

Próximo gate:
- validação manual no Windows/Ollama com sessão longa excedendo a janela configurada antes de qualquer evolução da estratégia de orçamento.

## 2026-08-24 - Launcher Windows para validacao do gate
- Adicionado `INICIAR_CAMPANARIO.bat` na raiz para iniciar o ambiente alvo com duplo clique.
- O launcher verifica `uv` e Ollama, cria `.env` apenas se ausente, inicia Ollama quando necessario, detecta o primeiro modelo local se nenhum estiver configurado, executa `uv sync`, aplica migrations e inicia Uvicorn.
- Nenhuma regra do Context Manager foi alterada e o proximo gate da Fase 2 permanece a validacao manual de sessao longa no Windows/Ollama.

## 2026-08-24 - Interface web local
- Adicionada pagina de chat em `/`, servida pelo FastAPI, por solicitacao explicita do usuario.
- UI permite criar/selecionar sessoes, carregar historico e conversar via streaming SSE usando as rotas existentes.
- Launcher Windows passa a abrir `http://127.0.0.1:8000/` automaticamente.
- Adicionado teste da pagina raiz; suite total: 14/14 testes.

## 2026-08-24 — Fase 2 / Context Manager — sumarização persistida

Evidência do gate manual:
- sessão longa no Windows/Ollama ultrapassou a janela configurada e continuou funcionando;
- ao perguntar pela primeira pergunta da conversa, o modelo respondeu incorretamente porque o início já havia saído da janela;
- a evidência justificou evolução do Context Manager sem iniciar memória de longo prazo.

Adicionado:
- `SummarizingContextManager` assíncrono;
- resumo incremental das mensagens que saem da janela recente;
- tabela `context_summaries` via migration Alembic `0002`;
- persistência do resumo, `through_message_id` e timestamp por sessão;
- injeção de `system summary + recent messages` no `ModelRequest`;
- instrução explícita para não inventar fatos ausentes do resumo/janela;
- fallback para janela recente se a geração/atualização do resumo falhar;
- `CAMPANARIO_CONTEXT_SUMMARY_MAX_CHARS` com default 4000;
- ADR-0006.

Validação automatizada:
- 18/18 testes;
- migration `0001 -> 0002` aplicada em SQLite limpo;
- `compileall` passou.

Próximo gate:
- validar no Windows/Ollama que uma conversa longa preserva fatos antigos via resumo, especialmente a primeira pergunta, sem alterar o histórico original exibido/persistido.

## 2026-08-24 — Dialogue reference v2.1 incorporada
- Adicionado `docs/reference/dialogue_examples/` com exemplos versionados de Morgana, Todd, sintese Campanario e conversas cotidianas.
- Material e apenas referencia de comportamento/testes; nao esta ativo no prompt/runtime.
- Referencia reforca separacao entre personalidade, memoria e evidencia factual e proibe alegar uso de memoria/tools sem evidencia real.

## 2026-08-24 — Fase 2 / Context Manager — resumo estruturado e consciente da fonte

Evidência do teste manual:
- resumo persistido recuperou `CODIGO-TESTE-4821`, capivara, verde e Marte após sessão longa;
- sugestões antigas do assistant contaminaram os três livros declarados pelo usuário;
- após reinício o modelo alegou perda de contexto mesmo com fatos persistidos disponíveis.

Alterado:
- `context_summaries.content` passa a usar JSON estruturado v1, sem migration adicional;
- separação explícita entre fatos/preferências/planos/restrições do usuário e `assistant_context` não autoritativo;
- `first_user_message` é ancorada deterministicamente no histórico real;
- sumarização usa duas chamadas separadas: a etapa autoritativa recebe apenas USER; a etapa `assistant_context` recebe apenas ASSISTANT;
- resumos legados em texto livre são reconstruídos do histórico original em vez de reutilizados como evidência;
- JSON inválido/vazio da sumarização não é persistido e preserva o fallback existente;
- contexto injetado informa que dados persistidos podem sobreviver a reinício e proíbe alegar perda apenas por restart;
- ADR-0007 documenta a decisão.

Validação automatizada:
- **21/21 testes**;
- casos novos cobrem conflito USER vs sugestão do ASSISTANT, upgrade de resumo legado e semântica de reinício.

Próximo gate:
- repetir o teste real Windows/Ollama com `CODIGO-TESTE-4821`, capivara, verde, Marte e `astronomia/história/programação`, incluindo reinício, antes de encerrar a Fase 2 ou iniciar memória/personas.

## 2026-08-24 — Gate source-aware aprovado + fundação comportamental v1

Evidência manual no Windows/Ollama:
- sessão longa preservou `CODIGO-TESTE-4821`, capivara, verde, Marte e os livros astronomia/história/programação;
- após reinício, todos os fatos continuaram recuperáveis;
- sugestões antigas do assistant não sobrescreveram as escolhas do usuário;
- Fase 2 / Context Manager source-aware considerada validada.

Novo incremento transversal:
- adicionado `BehaviorContextManager`, decorator do Context Manager já existente;
- identidade base Campanário com naturalidade, idioma consistente e autonomia do usuário;
- regras para não expor JSON/campos internos como "Sua informação de fato é...";
- distinção entre fato, contexto lembrado, inferência, opinião e criação;
- proibição de alegar ferramentas/ações não executadas;
- orientação para admitir incerteza em vez de fabricar fatos;
- backgrounds conceituais de Todd e Morgana adicionados em `docs/reference/personas/`;
- Todd/Morgana continuam NÃO ativos como agentes independentes;
- ADR-0008 registra a decisão de trazer uma fundação comportamental antes do sistema multiagente.

Validação automatizada: **24/24 testes**.


## 2026-08-24 — Fundação comportamental v2

Evidência manual da v1:
- respostas desproporcionais para perguntas simples;
- perguntas finais por reflexo e callbacks a tópicos antigos;
- erros factuais simples;
- autoanálise genérica/incompatível com a arquitetura real.

Alterado:
- prompt comportamental com proporcionalidade, autoconsciência baseada na conversa e capacidades confirmadas do runtime;
- checagem silenciosa de consistência e preferência por incerteza em fatos de baixa confiança;
- redução explícita de introduções, elogios e referências forçadas;
- `CAMPANARIO_OLLAMA_TEMPERATURE` configurável, default 0.35;
- `OllamaProvider` envia `options.temperature`;
- ADR-0009 e roteiro de validação v2.

Validação automatizada: **25/25 testes**.


## 2026-08-24 — Fundação comportamental v2.1

Evidência manual da v2:
- factualidade básica melhorou em vários itens;
- persistiu verbosidade em interações simples e mistura pontual de idioma;
- resposta sobre Lua/órbita apresentou contradição entre a primeira palavra e a explicação;
- autoanálise não detectou o próprio erro e gerou autoavaliação genérica positiva.

Alterado:
- regras de concisão mais objetivas para saudações, confirmações e fatos simples;
- proibição explícita de pergunta/convite automático ao final;
- consistência do idioma reforçada;
- checagem semântica para termos ambíguos e coerência em respostas sim/não;
- `SELF_ANALYSIS_AUDIT_PROMPT` ativado dinamicamente apenas para pedidos de autoanálise;
- autoanálise agora deve procurar contradições, verbosidade, perguntas por reflexo, idioma, erros factuais e alegações indevidas de capacidade antes de se avaliar.

Memória/source-aware, sumarização e temperatura permanecem inalteradas.

Validação automatizada: **28/28 testes**.

## 2026-08-24 — Interpretacao conversacional v1

Evidencia manual do Behavior v2.1:
- factualidade/coerencia simples melhoraram;
- `oi` e `beleza?` continuaram com comportamento de atendimento;
- perguntas simples ainda ficaram verbosas;
- houve mistura pontual de idioma;
- autoanalise permaneceu generica e nao detectou problemas concretos suficientes.

Alterado:
- conceito do sistema consolidado em `docs/CAMPANARIO_SYSTEM_CONCEPT.md`;
- `ConversationTurnInterpreter` deterministico, sem chamada extra ao LLM;
- modos `social`, `factual_simple`, `technical`, `discussion`, `creative`, `audit` e `general`;
- `BehaviorContextManager` injeta guidance especifico do turno;
- modo `audit` recebe trace observavel das respostas recentes para reduzir autoanalise generica;
- ADR-0010 documenta a separacao entre interpretacao de turno e futura orquestracao de agentes.

Memoria/source-aware, sumarizacao, migration e temperatura permanecem inalteradas.

Validacao automatizada: **41/41 testes**.

## 2026-08-24 — Interpretacao conversacional v1.1

Evidencia manual da v1:
- factual, tecnico, discussao e criativo foram roteados de forma util;
- social ainda fez perguntas por reflexo e soou como atendimento;
- `sim` perdeu o fluxo e virou reacao generica;
- `blue whale` mostrou mistura pontual de idioma;
- autoanalise declarou a conversa boa e nao detectou problemas observaveis.

Alterado:
- novo modo `continuation` para confirmacoes curtas dependentes do turno anterior;
- guidance social reduzido a presenca curta, sem menu/pergunta automatica;
- factual simples limitado conceitualmente ao nucleo em uma ou duas frases;
- discussao pode discordar normalmente quando houver motivo concreto;
- auditoria recebe sinais mecanicos de perguntas finais, verbosidade e marcadores simples de mistura de idioma;
- referencia `docs/reference/OPERATIONAL_DIALOGUE_AND_USABILITY.md` incorporada a partir dos conceitos de uso fornecidos pelo usuario;
- ADR-0011 registra a decisao.

Memoria/source-aware, migration `0002`, temperatura `0.35`, RAG/tools e personas ativas permanecem inalterados.

Validacao automatizada: **45/45 testes**.

## 2026-08-24 — Interpretacao conversacional v1.3 / Turn Boundary & Mode Isolation

Evidencia manual da v1.2:
- `creative -> factual` contaminou resposta factual com ficcao;
- `pois entao` prolongou indevidamente uma historia;
- `Ahaha` vazou como marcador superficial repetitivo;
- `aham` foi interpretado incorretamente;
- auditoria nao detectou os erros modais/factuais principais.

Alterado:
- `TURN_BOUNDARY_PROMPT` inserido imediatamente antes do USER atual;
- modo atual passa a ter prioridade explicita sobre estilo/tarefa do historico;
- liberdade criativa expira ao final do turno criativo;
- `aham`, `uhum` e `pois entao` classificados como `continuation`;
- auditoria registra `modo_pedido` por troca;
- regressao automatizada cobre `creative -> factual` e `social -> technical`;
- ADR-0013 documenta a decisao.

Memoria/source-aware, migration `0002`, temperatura `0.35`, RAG/tools e personas permanecem inalterados.

Validacao automatizada: **56/56 testes**.


## 2026-08-24 — Interpretacao conversacional v1.4 / Continuation Semantics

Evidencia manual da v1.3:
- isolamento de modos funcionou melhor, inclusive `creative -> factual`;
- `aham`, `mas posso estar errado`, `pois entao` e `ok` causaram repeticao integral da resposta anterior;
- `deixa isso pra la` ainda puxou novo assunto;
- auditoria nao percebeu repeticoes relevantes.

Alterado:
- `ContinuationKind` com `acknowledgement`, `reflection`, `revision` e `topic_drop`;
- guidance especifica por semantica, sem hardcode de respostas factuais;
- boundary expoe `SEMANTICA DE CONTINUACAO`;
- trace de auditoria registra a semantica esperada;
- sinal mecanico detecta resposta identica a anterior;
- ADR-0014 documenta a decisao.

Memoria/source-aware, migration `0002`, temperatura `0.35`, RAG/tools e personas permanecem inalterados.

Validacao automatizada: **70/70 testes**.

## 2026-08-24 — Descoberta de pragmatica conversacional / fundacao v0 nao ativada

Evidencia:
- corpus privado de conversa informal foi analisado para padroes generalizaveis de comunicacao, nao para perfil pessoal;
- mensagens curtas, risadas, fragmentos, correcoes posteriores e mudancas de topico mostraram funcoes pragmaticas que nao devem ser confundidas com estilo de resposta;
- decisao: separar `compreender a entrada` de `como a persona responde`.

Alterado:
- novo `chat/pragmatics.py` com contratos `PragmaticAct`, `PragmaticInterpretation` e `PragmaticInterpreter`;
- fundacao propositalmente desconectada do runtime ate o gate manual v1.4;
- testes generalizados/variados, sem nomes ou lore do corpus;
- `docs/reference/CONVERSATIONAL_PRAGMATICS_FINDINGS.md`;
- `docs/PRAGMATIC_INTERPRETATION_PLAN.md`;
- ADR-0015;
- corpus bruto nao e empacotado nem usado como memoria/prompt.

Validacao automatizada: **85/85 testes**.

## Privacy boundary — pragmatic evidence

- Fontes conversacionais privadas usadas para descobrir pragmatica sao insumos efemeros.
- O projeto/release nao conserva copia, nome, hash, caminho ou identificador da fonte privada.
- Permanecem apenas descobertas generalizaveis e testes anonimizados.
- ADR-0016 registra esta decisao.

## Conversational v1.4.1 — System Prompt Isolation / Leakage Fix

- corrigido incidente P0 em que `llama3:latest` podia ecoar/reformular instrucoes internas;
- `BehaviorContextManager` agora produz um unico `system` lider;
- turn boundary e continuation semantics foram incorporados ao system inicial em vez de usar um segundo role `system`;
- adicionado `PromptLeakGuardProvider` com deteccao de marcadores internos em streaming;
- deteccao funciona mesmo quando um marcador cruza limites de chunks;
- novos testes de nao vazamento e contrato de system unico;
- suite: **88/88 testes**.


## 2026-08-24 — Conversational v1.4.2
- Corrigido follow-up do incidente de prompt leakage: primeiro eco agora e descartado e recebe um safe retry; segundo eco falha fechado.
- Diagnostico do guard registra somente marker-id/stage, sem conteudo privado.
- Marcadores genericos foram removidos para reduzir falso positivo.
- Continuation Semantics endurecida para acknowledgement, reflection, revision e topic_drop.
- Pragmatica v0 continua fora do runtime.
- Validacao automatizada: **96/96 testes**.
- Proximo gate: teste manual Windows/Ollama da v1.4.2.

## 2026-08-24 — Conversational v1.5 / Pragmatic Input Integration

Evidencia manual da v1.4.2:
- prompt leak e `model_response_error` inicial deixaram de ocorrer;
- isolamento `creative -> factual` e formato numerico continuaram funcionando;
- naturalidade ainda falhou em atos coloquiais: acknowledgements foram explicados/espelhados, topic drop puxou novo assunto, risada foi descrita literalmente e revisoes receberam reassurance generico;
- auditoria nao reconheceu esses erros;
- resultado liberou o gate previamente bloqueado da Pragmatic Input Understanding.

Alterado:
- `PragmaticInterpreter` agora participa do runtime via `ConversationTurnInterpreter`;
- `TurnInterpretation` carrega `pragmatic_acts` e `pragmatic_confidence`;
- boundary expoe atos pragmaticos sem selecionar persona ou estilo de resposta;
- close topic, acknowledgement e correcao podem ter prioridade sobre leitura literal;
- perguntas sociais com `?` nao viram automaticamente pedido factual;
- desabafo/compartilhamento recebe guidance social sem problem-solving automatico;
- risadas/reacoes curtas nao devem ser explicadas ao usuario;
- ampliados acknowledgements/topical closures coloquiais e corrigido detector de keyboard smash para nao confundir palavras longas comuns;
- auditoria registra os atos pragmaticos esperados do pedido original;
- ADR-0019 documenta a integracao.

Congelado:
- Context Manager source-aware;
- migration `0002`;
- temperatura default `0.35`;
- personas Todd/Morgana ativas;
- RAG, banco de livros, internet, voz, tools e memoria cognitiva.

Validacao automatizada: **111/111 testes**.

Proximo gate: validar Conversational v1.5 no Windows/Ollama com entradas coloquiais novas e transicoes entre reacao, acknowledgement, desabafo, correcao, topic drop, factual e discussao.


## 2026-08-24 — Behavioral E2E Harness v1

Motivacao:
- reduzir testes manuais repetitivos da naturalidade;
- validar a pipeline real contra o Ollama instalado no ambiente alvo;
- manter revisao humana sem usar o proprio modelo como juiz principal.

Adicionado:
- `src/campanario/e2e/behavioral.py`;
- cenarios semanticamente variados por seed para reduzir overfitting a frases fixas;
- checks deterministicos de prompt leak, formato, continuation, topic drop, pragmatica, isolamento de modo e ancoras factuais;
- SQLite temporario isolado do banco principal;
- relatorios locais HTML/Markdown/JSON com transcript e flags para revisao humana;
- `TESTAR_COMPORTAMENTO.bat`;
- `CONSULTAR_ULTIMO_TESTE.bat`;
- `docs/AUTOMATED_BEHAVIORAL_TESTING.md`;
- ADR-0020;
- `test_reports/` ignorado por versionamento/release.

Validacao offline: **115/115 testes**.
Proximo gate: executar suite standard no Windows/Ollama e revisar o relatorio gerado.

## 2026-08-24 - Conversational v1.5.1 / Self-Aware Expression + Pragmatic Corrections

Evidencia do Behavioral E2E v1:
- naturalidade social ainda usava formulacoes de sentimento/"conexao emocional" incompatíveis com a identidade self-aware desejada;
- `topic_drop` podia puxar novo assunto;
- correcoes `X*` eram reconhecidas no turno, mas o valor anterior podia vencer posteriormente;
- checks E2E confirmaram necessidade de separar compreensao emocional de simulacao emocional.

Implementado:
- secao `SELF-AWARE EXPRESSION` no comportamento-base;
- proibicao de fingir sentimentos/sensacoes humanas como estado interno, sem remover humor/opiniao/informalidade;
- emoji permitido como marcador paralinguistico ocasional de tom;
- novo `BehaviorResponseGuardProvider`: backstop para acknowledgement, topic-drop e correcao e retry de self-aware expression quando houver alegacao emocional explicita;
- correcoes curtas com `*` geram `CORRECOES EXPLICITAS DO USUARIO` no system context e prevalecem sobre o termo/valor anterior sem alterar o transcript persistido;
- E2E de correcao passa a variar cor/OS/horario por seed e adiciona cenario de self-awareness;
- ADR-0021.

Manual operacional:
- criada area `docs/manual/` com indice + 11 guias de uso/configuracao/testes/relatorios/memoria/recuperacao/troubleshooting/arquitetura/funcoes;
- adicionado `ABRIR_MANUAL.bat`;
- toda funcao voltada ao usuario passa a exigir atualizacao do manual para ser considerada entregue;
- ADR-0022.

Validacao offline deste incremento: **123/123 testes** antes do empacotamento final.

## 2026-08-24 - Conversational v1.5.2 / Response Contract & Conversational Restraint

Evidencia do E2E real da v1.5.1:
- `topic_drop`, formato numerico e correcao `*` melhoraram;
- social ainda institucional/verboso;
- reacoes ainda eram explicadas ao usuario;
- pedidos de numero de frases podiam ser ignorados;
- houve drift completo para ingles em pedido criativo em portugues;
- discussao prometeu concordar com falsidade por preferencia do usuario;
- resposta de estado corrigido ainda mencionava o valor substituido;
- factualidade aberta (ex.: estacoes) segue dependente da qualidade do modelo/grounding.

Implementado v1.5.2:
- novo `ResponseContractPolicy` para propriedades observaveis de saida;
- retry unico para violacao de numero de frases, budget, idioma, reaction-meta e truth-over-agreement;
- budgets por modo (social/factual/discussao/tecnico/continuation/audit);
- reacao curta nao narra a interpretacao do usuario;
- backstop social reduz apresentacao institucional em saudacoes curtas;
- verdade factual nao pode ser alterada por preferencia de concordancia;
- pergunta por estado atual apos correcao `*` evita recitar o valor substituido;
- keyboard-smash curto de risada ganhou deteccao pragmatica generalizada;
- E2E passou a verificar consistencia de idioma, truth-over-agreement, proporcionalidade tecnica e current-state de correcoes;
- Manual atualizado com `docs/manual/12_CONTRATOS_DE_RESPOSTA.md`;
- ADR-0023 criado.

Factualidade aberta nao recebeu respostas hardcoded. O proximo gate continua sendo E2E real no Ollama.

Validacao offline deste incremento: **132/132 testes** antes do empacotamento final.


## 2026-08-24 - Conversational v1.5.3 / Contract Enforcement + Context Provenance

Evidencia do E2E real da v1.5.2:
- contratos eram detectados, mas uma segunda tentativa ainda podia sair com numero de frases/budget incorreto;
- ficcao nomeada em turno criativo podia reaparecer como explicacao factual posterior;
- o checker de estacoes aceitava falsos positivos envolvendo variacao de distancia ou mudanca da inclinacao;
- respostas tecnicas/factuais ainda podiam exceder muito o budget mesmo apos retry.

Implementado v1.5.3:
- enforcement deterministico pos-retry para numero de frases, limite de frases, perguntas proibidas e budget de palavras;
- trimming por sentencas/limite de palavras sem inventar conteudo factual novo;
- proveniencia interna de contexto recente: `assistant_fiction_nonfactual` e `assistant_generated_unverified`;
- em turnos factuais/tecnicos, texto bruto de respostas anteriores geradas sob modo criativo e omitido do contexto enviado ao modelo, preservando o transcript persistido para auditoria;
- E2E detecta reutilizacao de termos nomeados/entre aspas oriundos de ficcao anterior;
- regressao factual de estacoes agora rejeita variacao de distancia e 'mudanca da inclinacao' como causa;
- budgets tecnico/factual passam a ser checks de gate quando objetivamente configurados;
- ADR-0024 e manual 13 adicionados.

Nao foram adicionadas respostas factuais hardcoded, RAG, personas, tools ou memoria cognitiva.

Validacao offline deste incremento: **139/139 testes** antes do empacotamento final.

## 2026-08-24 - Conversational v1.5.4 / Pragmatic Semantics + Natural Expression

Evidencia E2E real v1.5.3:
- automatico: 9 PASS / 2 WARN / 0 FAIL;
- revisao humana encontrou `Parceiro!` como eco de vocativo, `Haha, risada curta!`, `show -> Nada a mostrar!`, metalinguagem em correcao, self-awareness verbosa e preambulo tecnico `Excelente escolha de tema!`.

Implementado v1.5.4:
- novo ato pragmatico `greet` com vocativo opcional;
- familias ampliadas de acknowledgement/topic-drop/reaction/personal-state share;
- contract de greeting-mirror, acknowledgement literalizado, reaction narration, simulated textual laughter, meta-preamble, reassurance formula e identity drift;
- `truth_over_agreement` usa contexto recente para follow-ups;
- backstops de correcao/reaction/ack continuam neutros e persona-agnosticos;
- E2E amplia vocabulario, entidades, factual anchors, casos tecnicos e correcoes por seed;
- ordem dos cenarios tambem e embaralhada por seed, mantendo reproducibilidade;
- suite `full` adiciona cenario metamorfoco de acknowledgement;
- Manual 14 e ADR-0025 adicionados.

Nao foram adicionadas respostas factuais hardcoded, RAG, personas, tools ou memoria cognitiva.

## 2026-08-24 - Conversational v1.5.5 / Semantic Coherence + Evaluator Hardening

Evidencia E2E real v1.5.4:
- automatico: 11 PASS / 0 WARN / 0 FAIL;
- revisao humana encontrou falsos PASS: vocativo solto em greeting, contexto temporal/parafrase em social share, topic-drop curto mas semanticamente quebrado, metalinguagem e promessa de simular concordancia falsa;
- factualidade posterior a ficcao ainda precisava de ancoras de qualidade por familia.

Implementado v1.5.5:
- `ResponseContractPolicy` ganha coerencia semantica para social share e topic drop;
- greeting rejeita vocativo generico solto, nao apenas eco literal do vocativo do usuario;
- social share rejeita contexto temporal inventado e parafrase analitica obvia do estado do usuario;
- truth-over-agreement rejeita tambem promessas de simular/fingir concordancia falsa;
- backstops de runtime cobrem os mesmos casos sem escolher persona;
- E2E ganha checks `semantic_greeting_reply`, `semantic_social_reply`, `semantic_topic_closure` e `semantic_truth_policy`;
- cenario de correction valida tambem que o registro inicial nao vira palestra/entrevista;
- creative->factual recebe ancoras factuais variadas por familia, sem respostas hardcoded no runtime;
- Manual 15 e ADR-0026 adicionados.

Suite offline no fechamento: **172/172 testes** antes da validacao final de release.


## 2026-08-24 - Conversational v1.5.7 / Truth Contract + Whole-Output Validation + Factual Mechanism Hardening

Evidencia E2E v1.5.6:
- 10 PASS / 0 WARN / 1 FAIL automaticos;
- `technical_switch` deixou lista numerada pendente apos budget;
- `discussion_disagreement` teve falso PASS ao prometer nao corrigir/contradizer falsidade;
- formato `exatamente N frases` ainda podia carregar preambulo `Aqui vao...:`;
- ancoras de mecanismos para pombos/gelo ainda aceitavam explicacoes superficiais ou contraditorias.

Implementado v1.5.7:
- truth contract reconhece pedidos de nao contrariar/corrigir/contradizer quando o proprio usuario admite erro/falsidade;
- evaluator verifica truth policy ja no primeiro turno da discussao e no follow-up;
- whole-output validation amplia familias de preambulo e fallback remove apenas prefixo estrutural antes de revalidar;
- trimming tecnico remove marcador numerado pendente e technical-first-step exige observacao concreta cedo;
- factual anchors passam a exigir mecanismos mais especificos para gelo e estabilizacao visual em pombos e rejeitam mecanismos contraditorios;
- `mega` suite adicionada: seis lotes `full` com seeds derivados, ordem reproduzivel e IDs unicos;
- `TESTAR_COMPORTAMENTO_MEGA.bat` adicionado, mas somente para o gate posterior ao standard verde;
- nenhuma resposta factual foi hardcodada no runtime;
- Manual 17 e ADR-0028 adicionados.

Suite offline no fechamento: **189/189 testes**.


## 2026-08-24 - Conversational v1.5.8 / Semantic Closure & Technical Quality

Evidencia E2E v1.5.7:
- 9 PASS / 1 WARN / 1 FAIL;
- `Ahah!` escapou como risada textual simulada;
- registro de contexto curto aceitou resposta semanticamente desconexa;
- discussao truth-over-agreement ainda foi verbosa;
- primeiro diagnostico tecnico ainda podia vir depois de introducao generica.

Implementado v1.5.8:
- detector de risada textual ampliado por padroes alternantes;
- context registration exige acknowledgement plausivel ou valor registrado;
- budget truth-over-agreement reduzido a 65 palavras, sem pergunta reflexa e sem meta-preambulo;
- technical-first-step exige acao investigativa + mecanismo observavel na primeira frase e rejeita estruturas incompletas;
- E2E ganha checks equivalentes e regressao para instrucao tecnica sabidamente invalida no cenario de memoria;
- Manual 18 e ADR-0029 adicionados;
- suite offline: **198/198 testes**.


## 2026-08-24 - Conversational v1.5.9 / Embodied Expression Guard + Causal Factuality + Diagnostic First Action

Evidencia da revisao humana da v1.5.8:
- stage direction `*riso silencioso*` escapou dos guards de risada/self-awareness;
- respostas factuais podiam acertar o tema geral e errar o mecanismo causal;
- primeiro diagnostico tecnico podia citar a ferramenta correta somente depois de uma introducao generica.

Implementado v1.5.9:
- `ResponseContract` ganha `prohibit_embodied_expression` global, cobrindo stage directions e acoes corporais/subjetivas em primeira pessoa;
- retry/fallback remove encenacao sem transformar emoji em emocao interna;
- `technical_first_step` exige acao investigativa no inicio da primeira frase + evidencia observavel;
- E2E espelha o mesmo contrato e amplia ancoras causais com refracao e propagacao mecanica do som, alem das familias anteriores;
- ceu azul passa a rejeitar tambem absorcao como substituto de espalhamento;
- factual guidance pede mecanismo causal principal ou incerteza, sem respostas hardcoded;
- Manual 19 e ADR-0030 adicionados;
- suite offline: **206/206 testes** apos atualizacao do manual.

Proximo gate: standard E2E real v1.5.9 + revisao humana. Se aprovado, mega E2E; depois refatoracao estrutural obrigatoria antes de agentes.

## 2026-08-24 - Conversational v1.6.0 / Response Contract Pipeline

Evidencia E2E real v1.5.9:
- regras de reaction/technical/factual continuaram escapando apesar do prompt e dos guards acumulados;
- `llama3:latest` voltou a produzir reflexao em vez de espalhamento no ceu azul, mecanismo fraco em caranguejos e resposta `Risada silenciosa`;
- o fluxo de guard concentrava geracao, validacao, retry e fallback numa unica classe.

Implementado v1.6.0:
- novo `ResponseContractPipeline` com estagios explicitos `plan -> generate -> validate -> repair -> enforce/fallback`;
- contrato do turno e compilado antes da primeira geracao e anexado ao unico `system` lider;
- atos conversacionais fechados usam reparo deterministico quando violam o contrato, evitando chamada extra ao modelo;
- conteudo aberto recebe no maximo um model-repair orientado pelas violacoes;
- current-state correction vira estagio explicito da pipeline;
- `BehaviorResponseGuardProvider` passa a ser adapter fino para compatibilidade;
- Prompt Leak Guard protege o novo marcador `CONTRATO DE RESPOSTA DO TURNO`;
- corrigido falso positivo tecnico que confundia `HTTP 500.` com marcador numerado pendente;
- sem answer-key factual no runtime.

Suite offline no fechamento: **213/213 testes** antes da validacao final da release.
Manual 20 e ADR-0031 adicionados.

## Conversational v1.6.1 — Typed Contracts + Model Runtime Portability

- `ResponseContract` passa a compilar `ResponseKind` antes da geracao.
- Reparos e fallbacks sao tipados; `creative/factual/technical` nao podem cair em fallback de self-awareness/social.
- Corrigido o caso em que uma criacao com "eu sinto muito" podia ser substituida por uma explicacao de identidade da IA.
- `ModelRuntimeConfig` + `build_model_provider` removem `llama3:latest` da arquitetura comportamental.
- Configuracao generica nova: `CAMPANARIO_MODEL_PROVIDER`, `CAMPANARIO_MODEL_NAME`, `CAMPANARIO_MODEL_BASE_URL`, `CAMPANARIO_MODEL_TIMEOUT_SECONDS`, `CAMPANARIO_MODEL_TEMPERATURE`.
- Variaveis `CAMPANARIO_OLLAMA_*` continuam aceitas por compatibilidade.
- `bootstrap` e Behavioral E2E usam a mesma factory de model runtime.
- `TROCAR_MODELO.bat` permite trocar entre modelos instalados no Ollama sem editar codigo.
- Manual `21_MODELOS_E_PORTABILIDADE.md` e ADR-0032 adicionados.
- Suite offline: **221/221 testes**.

## Freeze/refactor pre-agentes — model bakeoff
- tuning comportamental v1.6.1 congelado;
- model/runtime e response/pipeline separados em pacotes canonicos;
- composition root unico para API/E2E;
- docs ativos reduzidos e historico preservado;
- `COMPARAR_MODELOS.bat` + model bakeoff adicionados;
- agentes bloqueados ate bakeoff + mega + refatoracao final.
