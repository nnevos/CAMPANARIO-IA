# CAMPANARIO-IA — Roadmap operacional Neptune / Evolucao dos agentes

**Estado de referencia:** 29/10/2026, baseline Fase 5 (Qwen3.5:9b + Ollama, Windows 11, RTX 5060 Ti 16 GB).  
**Regra de evidencia:** este documento e planejamento. `docs/current/ROADMAP.md` registra gates historicos, muitos validados com Gemma, e nao e prova de funcionamento no Qwen/Neptune. Codigo, logs novos e testes de execucao sao a evidencia final.  
**Foco:** Todd e Morgana sao agentes originais que coexistem no Campanario e evoluem a partir de experiencias registradas. Nao possuem passado humano ficticio nem consciencia comprovada. O Ponto Zero de producao so ocorre depois da validacao.

## Diagnostico do projeto real

- **Preservar** `src/campanario/chat/service.py` (orquestracao e streaming), `chat/context.py` (janela de contexto), `runtime/experience.py` (memorias com origem, confianca, correcao), `runtime/events.py` (eventos com proveniencia), `agents/` (identidades, roteamento e participacao), `runtime/capabilities.py` e `runtime/permissions.py` (infraestrutura para ferramentas).
- **Problemas observados no Neptune:** primeira resposta lenta; falas com apresentacoes burocraticas; alegacao de ter lido logs sem ferramenta; perda de referente em 'o que e isso?'; resposta generica a 'quem sou eu?'. A Fase 5 alterou apenas o prompt compacto. O efeito real ainda precisa ser medido.
- **Divida tecnica:** caminhos legado e leve de resposta; o historico antigo marca gates como concluidos mas sob Gemma e criterios distintos; a experiencia/memoria existente ainda nao comprovou a recuperacao e a evolucao pretendidas; isolamento `desenvolvimento/producao` e comprovado para SQLite, nao para todas as superficies.
- **Nao duplicar** memoria, orquestrador ou roteador. Estender a camada existente com migracoes e testes, preservando API e compatibilidade.

## Regras de implementacao

1. Um gate por vez, sempre em `CAMPANARIO_MEMORY_ENVIRONMENT=desenvolvimento`; snapshot e plano de reversao antes de migracoes.
2. Nao escrever respostas esperadas no banco, prompt ou avaliador; testes devem variar formulacao, contexto e tema, com casos cegos.
3. Distinguir **fato observado**, **fala do usuario**, **inferencia do agente** e **resultado de ferramenta**. Nao promover inferencia a lembranca factual.
4. Individualidade: Todd e Morgana compartilham recursos e fatos com origem, mas mantem perspectivas, interesses e memorias relacionais individualizadas.
5. Responder primeiro a mensagem atual; memoria e personalidade dao continuidade, nao dominam a resposta. Nenhuma pergunta de engajamento obrigatoria.
6. Toda mudanca de gate atualiza este roadmap, `docs/handoff/CONTINUIDADE_CHAT_NOVO.md` e um log de resultados (sem dados pessoais). Arquivos de recuperacao historicos nao podem substituir o estado vigente.

## G0 — Congelar baseline e medir (INSTRUMENTACAO PARCIAL, GATE NAO CONCLUIDO)

**Implementar:** confirmar hotfix UI no navegador real; registrar versao/modelo/Ollama; medir `tempo_ate_primeiro_token`, `tempo_total`, `tokens_por_segundo`, tempo de carregamento, tamanho do prompt, quantas chamadas ao modelo por mensagem e `ollama ps`; adicionar tracing da composicao do contexto com conteudo redigido/contadores por padrao. Rodar 30 conversas novas: social, ambiguous follow-up, identidade, contradicoes, rotina, dependencia da memoria; testar cada um dos dois agentes separadamente.

**Entrega:** benchmark reproduzivel via `tools/diagnostics/`, relatorio anonimo comparando Qwen isolado x Campanario e dataset de prompts cegos sem respostas literais.

**Aprova se:** frontend nao quebra, historico e horarios persistem; nenhuma resposta fixa por chave; nenhuma alegacao falsa de ferramenta na amostra; latencias reais medidas e gargalo localizado. Nao fixar uma meta arbitraria de segundos antes da primeira medicao.

## G1 — Simplificar o caminho conversacional (NAO INICIADO)

**Implementar:** mapear `chat/service.py -> context -> agent profile -> ModelRequest -> Ollama -> UI`, inventariar notas sistemicas e filtros, detectar colisoes de prompts e substituicoes deterministicas; eliminar apenas respostas roteirizadas ativas ou redundantes mantendo seguranca, identidade do emissor e verificacao factual. Criar tratamento de referencias ambiguas e dependencia do ultimo turno (sem frases prontas); limitar prompt conforme prioridade; reduzir chamadas extras em conversa casual.

**Aprova se:** em prompts novos Todd e Morgana respondem de forma distinta mas flexivel, nao repetem avisos de identidade, nao supoem referente sem evidencia e nao inventam acoes. Revisao humana cega de pelo menos 30 pares de respostas, com regressao de latencia e testes de contratos.

## G2 — Memoria confiavel individual e compartilhada (FUNDACAO PARCIAL, NAO APROVADO)

**Implementar sobre `runtime/experience.py` e seus repositorios:** auditoria do que e extraido e recuperado hoje; tipar episodios/fatos/preferencias/inferencias/resultados, autor e participantes; distinguir armazenamento `user`, `todd`, `morgana` e `shared` por politica explicita; vincular memoria a evento/mensagem/data/ambiente; corrigir, invalidar, esquecer e buscar memórias contraditorias. Expor painel ou comando para inspecionar/editar/apagar memorias. Recuperacao por relevancia + confianca + recencia + permissao, com limite de tokens e sem vazamento entre usuarios/ambientes.

**Aprova se:** informa nome/preferencia mencionados antes e admite quando nao os conhece; persiste apos reiniciar; nao reutiliza memórias excluidas; divergencias entre Todd e Morgana nao alteram fatos compartilhados; nenhum registro de teste entra na producao. Testar 2+ sessoes, correcoes e revisitas no dia seguinte.

## G3 — Relacoes e evolucao lenta (NAO INICIADO)

**Implementar:** identidade-base versionada e imutavel por padrao; estado relacional Todd–usuario, Morgana–usuario e Todd–Morgana, sempre ancorado em eventos; reflexao eventual assíncrona/ sob demanda baseada em experiencias, sem inventar novas; interesses iniciais como tendencias e interesses adquiridos com justificativa; registrar mudancas e permitir desfaze-las. Nao atribuir sentimentos, maturidade ou confianca arbitrariamente por contagem de mensagens.

**Aprova se:** em semanas simuladas e interacoes reais os dois mostram preferencias/relacoes consistentes, podem mudar de opiniao diante de evidencia e citar a experiencia que motivou a mudanca; ambos continuam reconheciveis apos reiniciar, sem biografias falsas. Evitar auto-dialogo infinito ou consumo de GPU em segundo plano.

## G4 — Conhecimento, curiosidade e pesquisa real (NAO INICIADO)

**Implementar:** conector de pesquisa real sob `runtime/capabilities.py` + permissoes ja existentes; busca, leitura de fontes, timestamps, citacoes e tratamento de erro; decisor simples `responder do contexto / perguntar / pesquisar`; politica de pesquisas autonomas opt-in, limites de consultas e privacidade; memoria de descobertas com fonte e data de validade. Conhecimento do Qwen nao equivale a observacao atual.

**Aprova se:** quando desconhece pergunta ou pesquisa de verdade, distingue fato externo de opiniao, nao fabrica sites nem alega busca nao feita; suporta internet indisponivel; logs verificam execucao real e fontes.

## G5 — Habilidades, ferramentas e convivencia multiagente (NAO INICIADO)

**Implementar:** catalogo de capacidades reais e comprovadas (arquivos, diagnostico, pesquisa, etc.), perfis de acesso por agente, confirmacao antes de acoes com efeitos externos; participacao do segundo agente apenas quando adiciona valor; episodios conjuntos com perspectiva individual e registro do que cada um de fato fez. Nao declarar habilidade adquirida sem ferramenta/teste.

**Aprova se:** permissoes impedem acao nao autorizada; Todd e Morgana sabem diferenciar sugestao de execucao; conversam entre si sem redundancia ou obrigatoriedade; historico registra autoria e resultado.

## G6 — Validacao longitudinal e endurecimento (NAO INICIADO)

**Implementar:** suite de 30+ cenarios ineditos, com variacoes cegas; testes de 2+ sessoes e retorno apos reinicio, alteracao de preferencia e contradicao; testes de prompt injection em web/memoria, privacy boundary, ambiente e recuperacao de backup; painel de latencia/erros; avaliacao humana de naturalidade, autonomia, factualidade, memoria e diferenca entre agentes; comparar com G0.

**Aprova se:** zero vazamento de dados entre ambientes nos testes, zero acoes ficticias nos cenarios de ferramentas, testes criticos verdes, sem regressao funcional de chat/UI. Metricas de subjetividade e aceitacao humanas documentadas, nao pontuacoes inventadas.

## G7 — Lancamento do Ponto Zero (BLOQUEADO ATE G0–G6)

**Implementar:** congelar codigo/config/identidades, realizar backup verificavel, arquivar testes e experiencias em area sem acesso a producao; auditar SQLite, caches, indices, logs, anexos, eventos e integracoes; criar dados de producao vazios e identidades-base versionadas; registrar 'dia 0' sem historia biografica; oferecer procedimento de restauracao e exportacao de memórias. Nao apagar dados de desenvolvimento automaticamente.

**Aprova se:** inspecao de todas as fontes mostra producao sem memorias herdadas; Todd e Morgana conhecem a existencia um do outro e o sistema, mas nao afirmam experiencias nao ocorridas; testes de isolamento e backup/restauracao passam.

## Depois do Ponto Zero (nao bloquear o uso cotidiano)

- **Voz:** STT em portugues medido isoladamente, TTS distinto, interrupcao e latencia; so depois do texto estavel.
- **Modo Patrulha:** primeiro texto e estados seguros, depois voz e localizacao com consentimento; recursos de emergencia nao podem prometer seguranca que nao fornecem.
- **Outros agentes:** mesmos contratos de identidade, memoria, relacao e permissionamento.
- **Autonomia proativa:** tarefas curtas com agenda, limites de GPU/rede e opt-in; sem simular atividade offline.

## Sequencia operacional imediata

1. Confirmar em Windows a Fase 5 e hotfix UI, coletar evidencia de uma conversa de 10 minutos e benchmark Ollama vs UI.
2. Instrumentar contagem de tokens, chamadas e fontes de contexto sem salvar conteudo privado.
3. Revisar `src/campanario/chat/service.py`, `chat/context.py`, `agents/context.py`, `chat/prompts.py` e `runtime/experience.py`.
4. Congelar G0; so entao implementar G1 com testes cegos.

## Protocolo de recuperacao

Leia `docs/START_HERE.md`, `docs/handoff/CONTINUIDADE_CHAT_NOVO.md`, este arquivo e `docs/history/checkpoints/RECOVER_FIRST.md` antes de alterar. O `PROJECT_STATE.md` historico e informativo e pode representar o gate Gemma antigo; nao o trate como estado atual. Codigo/testes novos sao evidencia final. Atualize o gate neste documento e no handoff ao concluir cada entrega.

## Registro de implementacao — Fase 6 / G1 parcial (29/10/2026)

- Implementacao atual de relevancia lexical estrita e visibilidade por agente: `runtime/experience.py` e chamada em `chat/service.py`, sem schema novo nem LLM extra.
- Limitacao: matching lexical com normalizacao nao substitui embeddings; visibilidade por agente e somente primeiro recorte, nao memoria episodica relacional completa.
- `RuntimeTelemetry` agora registra quantidade de mensagens/caracteres do contexto e inicio de chamadas do caminho de resposta, sem texto. Nao cobre todos os adaptadores/servicos extras.
- Evidencia local: 72 testes direcionados; suite completa 502 pass, 4 falhas historicas de documentacao/interface experimental. Nao houve benchmark local Ollama nem validação Windows. Documento detalhado: `docs/handoff/FASE6_G1_PRIMEIRA_ONDA.md`.
- Proximo gate operacional continua baseline G0 + avaliacao real e humana do G1. G2 e Ponto Zero permanecem bloqueados.

### 29/10/2026 — Hotfix observado no Neptune, G1 ainda em validacao
- Recuperacao da frase `editor de codigo favorito` ao perguntar genericamente `ferramentas de programacao` foi ampliada de modo lexical restrito, sem embeddings. A identificacao do atributo no contexto foi corrigida.
- UI agora permite iniciar outra conversa manualmente, separando episodios sem apagar memorias.
- Ver `docs/handoff/FASE6_HOTFIX_NOVA_CONVERSA_MEMORIA.md`; testes com provider ficticio e navegador simulado nao equivalem a aceite no Neptune.

### 29/10/2026 — limpeza de modulo fora do escopo
- Removida a experiencia de automacao Ren'Py sem afetar o caminho conversacional nem a memoria.
- Gate G0/G1 continuam pendentes de aprovacao no Neptune; G2 e Ponto Zero nao alterados.
- Ver `docs/handoff/FASE6_LIMPEZA_AUTOMACAO_EXPERIMENTAL.md`.

### 29/10/2026 — G2 subgate: fidelidade de fonte, ainda nao concluido
- Em dados de memoria enviados ao modelo, conservar texto original de declaracoes
  explicitas e distinguir intensidade de preferencia / expectativa / fato.
- 6 testes de integracao novos com SQLite e provider falso. Suite total 474 pass.
- Restam recuperacao semantica generica (nao baseada em palavras especificas),
  verificacao no Ollama real, criterio de confianca e validacao longitudinal.

### 29/10/2026 — G2: auditoria geral de afirmacoes pessoais, em validacao
- As declaracoes originais agora servem tambem para verificar a resposta final do modelo em perguntas sobre dados pessoais, nao apenas para instruir geracao. Evidencia rejeitada nunca e emitida ao cliente nesses turnos.
- Seguranca empirica limitada por auditor LLM e detector heuristico de perguntas; custo de chamada extra. Validacao real no Neptune obrigatoria. Suíte local: 481 testes aprovados.
- `docs/handoff/FASE7_G2_AUDITORIA_AFIRMACOES.md`. G2 nao encerrado e producao nao iniciada.

### Atualizacao G2: auditoria citada, ainda nao concluida (29/10/2026)
Aprovacao binaria do mesmo LLM deixou passar exagero de preferencia no teste real do R34. Implementado requisito de prova literal da fala e checagem conservadora independente de operadores gerais de intensidade/exclusividade. `docs/handoff/FASE7_G2_HOTFIX_VERIFICADOR.md` registra limites: nao substitui verificacao semantica geral, recuperacao semantica nem validacao Qwen Neptune.

### 29/10/2026 — G2 parcial: recuperacao por significado em caso de falha lexical
- Captura generica de afirmacoes pessoais em andamento (gerundio) e consulta de candidatos persistidos, limitados a 24 memorias; escolha de ate 3 IDs pelo modelo. Excluidas perguntas antigas da fonte de auditoria. Zero migracoes de banco.
- Suite local 491 pass; **nao validado no Neptune/Qwen**. Ainda faltam embeddings ou outro recuperador semantico escalavel, cobertura de extracao de linguagem natural, qualidade do seletor e medicao de latencia. Nao fechar G2.

### 29/10/2026 — G2 estrutura semantica hibrida (Fase 8, ainda nao aprovado)
- Implementado SQLite como fonte canônica + index de vetores local no mesmo banco, Ollama `/api/embed` `embeddinggemma`, fusao lexical e semantica, validacao de status/escopo, drop dos vetores ao esquecer/corrigir. O Qwen de conversa nao seleciona mais IDs no fallback.
- `tools/windows/PREPARAR_MEMORIA_SEMANTICA.bat` e opcao 14 do menu instalam/testam o modelo real no Neptune.
- Testes de integracao locais: 497 aprovados, 0 falhas; usam embeddings simulados; **a qualidade semantica, latencia e acerto no hardware alvo ainda NAO foram medidos.** A auditoria conversacional ainda pode demandar chamada adicional ao Qwen.
- Ver `docs/handoff/FASE8_G2_MEMORIA_SEMANTICA_HIBRIDA.md`. Proximo: baixar modelo no Neptune, executar diagnostico e casos ineditos com episodios separados; Ponto Zero continua bloqueado.
