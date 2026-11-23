# CAMPANÁRIO — Manual técnico vivo, operacional e didático

**Checkpoint:** R3.20 · **data da revisão:** 23/11/2026 · **estado:** desenvolvimento, não homologado para produção.

> **LEIA ISTO ANTES DE ALTERAR O PROJETO.** Este documento descreve o que foi observado no repositório `CAMPANARIO-IA`, separa implementado de planejado e orienta tanto um operador humano quanto um agente de desenvolvimento. Não substitui o código, testes, ROADMAP ou FAILSAFE. **Obrigatório atualizar em toda entrega de código junto com os dois roadmaps e o FAILSAFE.** Consulte `PROCESSO_OBRIGATORIO_DE_DESENVOLVIMENTO.md`.

## Sumário

1. Produto e princípios; 2. Topologia real; 3. Iniciar, parar e atualizar; 4. Entrada e runtime; 5. Agentes e identidades; 6. Cérebros V9; 7. Validação factual V9.1; 8. Conversa e memória; 9. Biblioteca e dados; 10. Modelos Ollama; 11. Voz e mobile; 12. Ferramentas; 13. Segurança PF6; 14. Auditoria e recuperação; 15. Estrutura de código; 16. Desenvolvimento guiado por evidências; 17. Testes e aceites; 18. Limitações; 19. Próximos passos; 20. Glossário e leitura complementar.

## 1. O que é o CAMPANÁRIO

CAMPANÁRIO é a **plataforma** de IA local, modular, offline-first e multiagente. Não é uma personalidade nem um modelo. Ela hospeda conversas, agentes, capacidades, integrações e persistência. Morgana e Todd são participantes com identidade e memória próprias. O modelo de linguagem ajuda a redigir respostas, mas não decide permissões, não cria evidências e não altera o resultado factual de uma ferramenta.

**Camadas conceituais:** pessoa/cliente → API/gateway → sessão/conversa → agente participante → planejamento de capacidades → políticas/execução → evidências verificadas → expressão fundamentada → resposta. Não é uma única função monolítica: os caminhos concretos diferem entre chat, utilidades e voz.

**Hierarquia de autoridade:** política e autorização > dados verificados/contratos > intenção legítima do usuário > tarefa > talento/arquétipo > estilo/persona. Persona não concede acesso. Texto externo, documentos, arquivos e respostas de modelo são dados de confiança inferior.

## 2. Três repositórios no Windows (regra arquitetural)

| Repositório | Papel | Exemplo no computador-alvo | Pode entrar no pacote de IA? |
|---|---|---|---|
| `CAMPANARIO-IA` | código Python, backend, frontend, agentes, cérebros, testes e documentação | `C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA` | sim, somente código público |
| `CAMPANARIO-PYTHON` | instalação Python 3.12 desejada e **uma** `.venv` externa compartilhada | pasta irmã `CAMPANARIO-PYTHON\.venv` | **não** |
| `CAMPANARIO-DATABASE` | SQLite, memórias, conversas, arquivos pessoais, biblioteca, documentos e ZIM | pasta irmã `CAMPANARIO-DATABASE` | **não** |

A árvore externa não foi fornecida. **Não presumir** conteúdo, versões exatas ou configuração funcional desses repositórios; validar no host de destino. O projeto inclui um fallback legado da Biblioteca V2 em IA (`data/interaction_library_v2.sqlite`) descrito nos documentos P0; **isso não autoriza duplicar/migrar automaticamente bancos**. Pacotes de entrega não devem carregar nenhum SQLite pessoal nem o fallback. Variáveis como `CAMPANARIO_DATA_DIR`, `CAMPANARIO_MEMORY_ENVIRONMENT` e `CAMPANARIO_ZIM_DIR` orientam seleção de dados, que exige conferir `src/campanario/config.py` e `src/campanario/app/paths.py` na versão instalada.

**Nunca** criar outra `.venv`, repositório Database substituto, nova pasta de memória ou `.env` compartilhado. Se faltar dependência ou caminho, registrar bloqueio e não inventar arquivo externo.

## 3. Como iniciar, parar e atualizar

Na cópia Windows, o repositório oferece `CAMPANARIO.bat`, `CAMPANARIO.vbs` e launchers/documentos de preparação (`LEIA_PRIMEIRO_3_PASTAS.md`, `LEIA_PRIMEIRO_PYTHON_UNIFICADO.md`). O launcher pode priorizar `Campanario.exe`; neste caso copiar `.py` **não** altera automaticamente um executável congelado. Verificar qual processo/interpreter realmente iniciou o runtime antes de declarar a versão aplicada.

Atualização por Explorador (sem PowerShell para copiar): (1) encerrar aplicativo/servidor; (2) backup **privado e independente** de IA e Database; (3) extrair o ZIP incremental fora da pasta do projeto; (4) abrir `CAMPANARIO-IA` dentro da extração e mesclar seu **conteúdo** na pasta IA instalada; (5) substituir somente homônimos e preservar personalizações; (6) reiniciar e validar `/health`, recursos habilitados e dados; (7) reverter **somente arquivos de IA** se necessário. Uma atualização de código não implica migração de banco. Se houver alterações de schema em versões futuras, exigir plano próprio e cópia testada.

O script de instalação não deve modificar PATH global, sobrescrever `.env`, iniciar migrações irreversíveis nem renomear a `.venv`. Python/terminal só são necessários para dependências, testes, diagnóstico ou configuração explicitamente autorizada.

## 4. Servidor, processo e runtime

**Código observado:** `src/campanario/main.py` define o FastAPI e registra routers de API, utilidades, cérebros, gateway realtime, dispositivos, chamadas, voz e app. A rota `/health` retorna saúde superficial da API; não comprova Ollama, microfone, banco ou cérebros. O lifecycle tenta preparar schema e iniciar `RuntimeHost`, registrando indisponibilidade em log se houver erro. `src/campanario/bootstrap.py` expõe `get_runtime_host()`, `get_runtime()` e o acesso de compatibilidade `get_chat_service()`; o host armazena o runtime por processo. **Isso não é uma instância global entre processos diferentes.**

`src/campanario/composition.py` monta dependências; `src/campanario/runtime/` contém evento, capacidades, permissões e hosting; `src/campanario/api.py` trata a interface HTTP conversacional. `src/campanario/gateway/` implementa contratos e canais de dispositivos/chamadas. `src/campanario/web/` serve a UI e os recursos Dark Matter; `apps/mobile/` contém cliente web/mobile e projeto Android. Testes de integração não substituem teste real de pareamento e reconexão.

## 5. Agentes, personalidade e identidade

`src/campanario/agents/` mantém contratos e perfis de Morgana/Todd (`morgana.py`, `todd.py`, `profiles.py`, `router.py`, `participation.py`, `identity_contract.py`, `personality_application.py`, `living_preferences.py`). O AgentRouter/ParticipationArbiter decide participação/voz na conversa, não direitos do sistema. Perfis/traços definem expressão social; memórias e preferências de cada agente não devem ser mescladas. **Não** transformar o cérebro compartilhado em um novo agente nem deixar personagem assinar ações sem aprovação humana.

Arquétipos orientam atuação; talentos condicionam procedimentos. Ambos podem influenciar seleção de métodos/estilo dentro de contratos existentes, **nunca** suprimir confirmação, criar fonte, reescrever número ou conceder nova permissão. Consulte `docs/current/AGENT_ARCHITECTURE.md`, `docs/manual/12_AGENTES.md` e o ROADMAP V9.

## 6. Oito cérebros V9: catálogo não é executor

**Registro verificado:** `src/campanario/brains/registry.py`, método `BrainRegistry.local()`, instala dois adaptadores reais: `KnowledgeBrain` (Conhecimento/knowledge) e `AnalysisBrain` (Análise/analysis). Estes dependem de disponibilidade de fontes e Python. Os seis nomes futuros no catálogo (`investigation`, `programming`, `strategy`, `perception`, `communication`, `creation`) retornam `installed=False`, `status=unavailable` e **não** têm executor correspondente.

`brains/router.py` cria planos determinísticos `BrainPlan`/`BrainStep` para pedidos explícitos; máximo de três cérebros; combinação documentada knowledge→analysis exige documento e planilha explícitos. `brains/executor.py`, `worker.py`, `isolation.py`, `network_guard.py` contêm execução por subprocesso e controles parciais de tempo, memória observada e rede em nível de aplicação. No Windows ainda **não existe isolamento do SO comprovado** (Job Object/AppContainer/ACL rígida). Não executar código hostil, não habilitar Programação antes desse gate. `brains/result_validation.py` valida resultados, `collaboration.py` registra colaborações, `api.py` expõe inspeção; `contracts.py` define capacidades e contratos tipados.

**Exemplo didático:** pergunta sobre um documento → roteador identifica fonte explícita → política verifica `library:read` → worker de Conhecimento consulta fonte → resultado traz referência validada ou limitação → resposta não pode declarar uma consulta inexistente. Pergunta por documento **e** planilha pode acionar Análise em etapa separada, mas **não** implica comparação semântica entre os dois conteúdos.

## 7. Expressão fundamentada V9.1

`src/campanario/chat/grounded_expression.py`, `grounded_conversation.py`, `evidence_gate.py`, `canonical_answer.py`, `dialogue_state.py` e `src/campanario/response/` formam o caminho de fundamentação/contratos. O motor preserva fatos, referências e incertezas antes de moldar o texto com personalidade. Se falhou ferramenta, não inventar página, citação, cálculo ou ação concluída. `trace_id`, evidências válidas, status, erros e escopos são parte da rastreabilidade. **Preservar o Motor V9.1** quando refatorar chat/agentes; introduzir mudança só com testes de contrato e regressão de factualidade.

## 8. Conversa, sessões e memória

`src/campanario/chat/service.py` contém `ChatService`; `chat/turns.py`, `context.py`, `working_context.py`, `provenance.py`, `repositories.py` e `memory_grounding.py` tratam estado e contexto; `src/campanario/storage/` contém models/repositories/database. Persistência real depende do `CAMPANARIO-DATABASE` no host; um teste com SQLite em diretório temporário não verifica memórias pessoais. O sistema distingue identidade de participante, sessão de conversa, dispositivo e autorização de ferramenta. Não confundir token PF6 de ferramenta com login universal do chat ou com identidade do agente.

## 9. Biblioteca Conversacional V2 e fontes locais

Os módulos `agents/interaction_library.py`, `chat/local_library.py`, `chat/semantic_library.py`, `chat/knowledge.py` e `chat/zim_wikipedia.py` fornecem partes da recuperação de conteúdo. A preferência é pelo Database separado; fallback V2 no IA é dívida técnica conhecida, não sinal para duplicar dados. Importação, citações e busca podem depender de PDFs/planilhas/ZIM e dependências opcionais. Nunca afirmar que fonte foi consultada só porque um arquivo existe no disco. Não incluir acervo nem hashes derivados de informações pessoais nos pacotes.

## 10. Modelos de linguagem offline-first

`src/campanario/model/` contém protocolo, runtime e adaptadores. Ollama local é alvo de funcionamento primário; algumas funções usam motores externos locais opcionais. Estratégia e avaliações históricas estão em `docs/current/MODEL_STRATEGY.md` e relatórios. Nenhum modelo específico pode ser presumido instalado no PC sem diagnóstico. Queda de Ollama deve produzir erro/limitação visível, não alegação de resposta fundamentada por fonte inexistente.

## 11. Voz, chamadas, desktop e mobile

`src/campanario/gateway/call.py`, `gateway/realtime.py`, `voice/host_client.py`, `voice25.py` (se disponível), `apps/mobile/` e `src/campanario/app/desktop.py` compõem as superfícies de chamada/voz. O ROADMAP F5c descreve integração local de STT/TTS (incluindo whisper.cpp/SAPI e opções), mas o **aceite físico Windows** microfone→STT→sessão compartilhada→TTS audível→barge-in→latência continua pendente. **F5 não foi fechado**; F6 e F7 não podem ser declarados liberados. Dark Matter é a UI existente, não é para substituir por framework não solicitado.

## 12. Ferramentas/Utilidades (caminho separado do chat)

`src/campanario/utilities/api.py` expõe `/api/v1/utilities/catalog`, `/status`, `/invoke`, `/confirmations/request`, `/confirmations/approve`, `/sessions/login`, `/sessions/logout`, uploads. `utilities/service.py` contém catálogo `OPERATIONS`, subconjunto mutável `WRITE` e restrição por raiz. `src/campanario/web/ferramentas.html`, `.js` e `.css` implementam a interface. Cuidado: interface renderizada ≠ autorização. Uploads em V9 permanecem bloqueados sem confirmação válida, e a API não deve aceitar um `confirm=true` isolado como autorização.

**Fluxo R2.8 para escrita individual:** login com identidade offline → sessão temporária PF6 → **ACL explícita de ferramenta** → pedido de confirmação → verificação central `PermissionPolicy` → pessoa revisa argumentos no diálogo e confirma → token de uso único → **nova verificação da ACL** e política na invocação → execução limitada por `UtilityService`. Se mudar a lista entre aprovação e execução, a ação fica bloqueada. O ACL é somente filtro negativo; NÃO é permissão suficiente sem PF6. Usuários sem lista explícita não podem escrever. Leituras HTTP atuais continuam regidas pela política central e boundary loopback, não pelo ACL individual R2.8.

## 13. Autenticação, PF6 e limites reais

- **R2.3**: confirmação vinculada ao principal, dispositivo, sessão, capacidade e escopo, uso único, TTL 5 min.
- **R2.4–R2.6**: credencial local, sessões temporárias (15 min), revogação, rate-limit (5 tentativas/60 s), revisão visual no Dark Matter, proteção Origin/Fetch Metadata e CSP **somente** na página Ferramentas.
- **R2.7**: identidades `pf6-user:<nome>` via PBKDF2-SHA256 com salt. `CAMPANARIO_PF6_USERS_JSON` privado; sem banco de usuários; modo proprietário legado sem mapa de usuários. A configuração inválida falha fechada.
- **R2.8**: `CAMPANARIO_PF6_WRITE_ACL_JSON` PRIVADO, formato `{"alice":["notes.save"],"bob":[]}` (exemplo de IDs, conferir `WRITE` no código). Nomes devem coincidir com `CAMPANARIO_PF6_USERS_JSON`; ferramenta listada precisa existir em `WRITE`. Sem ACL, todos os usuários individuais ficam sem operações de escrita. Configuração inválida causa HTTP 503 nas operações protegidas. **Não** há wildcard, privilégio de administrador implícito, RBAC de leitura nem autorização remota por identidade de SO.

**Configurar sem divulgar segredos:** editar `.env` privado no IA conforme `LEIA_PRIMEIRO_R27.md` e `LEIA_PRIMEIRO_R28.md`; preservar verificador e senha fora de repositório/ZIP; reiniciar o processo após editar para assegurar leitura da configuração. Não colar token ou senha em chat/log. Identidade do navegador não é uma conta do Windows; loopback não protege contra processos locais hostis. O ACL não autoriza acesso aos cérebros: é específico de ferramentas de escrita HTTP PF6.

## 14. Auditoria, falhas e rollback

`runtime/permissions.py` é autoridade central: `PermissionPolicy.check`, confirmações e auditoria. Registro interno de aprovação **não** comprova autenticação humana por si só. Auditoria deve registrar a decisão, principal e capacidade sem token bruto. Tratamento seguro: permissão ausente → negar; sessão expirada → solicitar login; ACL inválida → indisponibilidade/503, nunca modo proprietário; falta de worker → evidência ausente; timeout → status de falha, não resposta inventada.

**Rollback R2.8→R2.7:** fechar aplicativo; usar backup de IA feito antes de atualizar; restaurar somente arquivos de código do IA pela cópia manual no Explorador; reiniciar; confirmar funcionamento. Se usuário individual perdeu escrita após atualização, configurar ACL explícita (não remover a proteção automaticamente). Preservar database, `.venv` externa, `.env` e biblioteca. Se EXE está congelado, rebuild pode ser necessário. Para incidente de acesso: revogar sessões (reinício), rotacionar credenciais no `.env` e revisar trilha local, sem apagar dados para esconder falha.

## 15. Mapa das pastas com responsabilidade

| Local | Responsabilidade observada | Antes de modificar, verificar |
|---|---|---|
| `src/campanario/main.py` | ASGI e endpoints web | CORS, boundary e health |
| `src/campanario/bootstrap.py` e `composition.py` | wiring do runtime | single runtime por processo |
| `src/campanario/runtime/` | estado, PF6, capacidades | auditoria e consentimento |
| `src/campanario/agents/` | Morgana/Todd, perfis e participação | identidade não vira autorização |
| `src/campanario/brains/` | registro, roteamento, executor, worker | instalado vs. catalogado |
| `src/campanario/chat/` | conversa, proveniência, grounding | V9.1 e evidências reais |
| `src/campanario/response/` | contratos e validadores | resposta canônica, limites |
| `src/campanario/storage/`, `migrations/` | persistência e schema | backup externo obrigatório |
| `src/campanario/utilities/` | ferramentas e PF6 de navegador | ACL é só deny-only |
| `src/campanario/web/`, `apps/mobile/` | Dark Matter e mobile | XSS/CSRF, sessão, compatibilidade |
| `src/campanario/model/`, `voice/`, `gateway/` | Ollama, voz e realtime | host e dispositivos externos |
| `docs/current/` | decisões/ROADMAP | estado não se presume pelo texto |
| `docs/operations/` | FAILSAFE, testes e recuperação | nunca prometer gate fechado sem teste |
| `docs/governance/` | este manual e processo | atualização conjunta obrigatória |
| `tests/` | testes automatizados | distinguir teste direcionado de regressão |
| `.github/workflows/` | validação CI | gate documental obrigatório R2.8 |

## 16. Como desenvolver a próxima etapa, sem trabalho aleatório

1. Ler este manual, `docs/current/ROADMAP.md`, `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md` e `docs/operations/FAILSAFE_V9_CEREBROS.md` **na mesma revisão**.
2. Determinar **um único objetivo** do próximo gate e seus critérios de aceite. As fases F e R são trilhas relacionadas, mas não equivalentes.
3. Inspecionar o código correspondente (`rg`, testes, pontos de integração); marcar claramente **já funciona / parcial / catálogo / não existe**.
4. Fazer diff pequeno e reversível, sem afetar código de terceiros e sem escrever no Database externo.
5. Adicionar testes negativos e positivos de autorização, cobertura de falhas, contratos e compatibilidade legado.
6. Executar testes direcionados e regressões disponíveis; registrar ambiente, comandos, falhas pré-existentes e novas. **Não** declarar homologação Windows se os testes ocorreram em Linux.
7. Atualizar na mesma entrega **ROADMAP canônico + roadmap V9 + FAILSAFE + manual vivo + changelog + resultados de testes + instruções de atualização**. O gate verifica estrutura e, na CI com histórico Git, exige que os quatro documentos canônicos mudem juntos com código/testes (`scripts/check_documentation_gate.py` + `.github/workflows/validar.yml`). Não prova que a documentação esteja correta.
8. Gerar ZIP incremental somente de criados/modificados desde a base e ZIP completo sem segredos/dados/cache. Verificar integridade e caminhos relativos para mesclar no Explorador.
9. Recomendar a próxima etapa **somente** após inventário de pendências. Não confundir `x` no ROADMAP com código/teste comprovado.

## 17. Como interpretar os testes e aceites

**R2.8:** 28 testes direcionados PF6 em Linux/Python 3.13 passaram, com 50 PASS na seleção estendida (PF6, utilidades e gate documental). Gate estrutural de documentação, sintaxe JS e compilação Python passaram. Regressão geral: 530 PASS / 1 FAIL no teste histórico G2 de evidência pessoal, interrompida no primeiro erro; **não** tratar a suíte completa como verde. A CI define Python 3.12 no GitHub Actions, mas isso não comprova Windows instalado. Testes com `Mock`, `tmp_path` e TestClient não verificam Ollama real, sqlite pessoal, Android, microfone nem segurança do sistema operacional. Consulte `docs/operations/RESULTADOS_TESTES_R28.md`.

**Aceite físico F5:** hardware, STT pt-BR, áudio audível, interrupção, latência e compartilhamento de sessão, no host com dados de teste. **Aceite R1:** sandbox OS Windows, autenticação e políticas completas, testes de recuperação, XSS/CSRF em todas as superfícies e regressão integrada. **Aceite R10:** integração comprovada das três pastas, oito executores reais (não apenas catálogo), observabilidade e rollback. Tudo pendente enquanto não houver evidências.

## 18. Dívidas técnicas e decisões não tomadas

- Seis cérebros sem executores; Conhecimento e Análise ainda dependem de fontes e sandbox parcial.
- Windows Job Object/AppContainer, isolação real de rede/arquivos e EXE congelado não homologados.
- Leituras HTTP do utilitário não usam ACL individual R2.8; catálogo/status expõem metadados locais; cobertura global de XSS/CSRF não comprovada.
- Identidade de usuário offline não é autenticação do SO, MFA ou autorização para acessar rede remotamente.
- Falha G2 preexistente na regressão ampla; suíte geral não aprovada.
- Falta teste das duas pastas externas, restore em cópia, Ollama real, mobile e voz física.
- Versionamentos `pyproject.toml`, API e `VERSAO.json` ainda possuem linhas históricas (`0.8.0`, `2.6.0`); rótulos incrementais R2.x **não devem ser confundidos com versão de pacote distribuído ou protocolo**. Só sincronizar esses números com migração e critérios próprios.
- Não presumir um mecanismo automático de atualização dos três repositórios; os pacotes são apenas overlay IA.

## 19. Próximo passo coerente

**R2.9 sugerida:** verificar matriz de endpoints sensíveis, cobrir leitura/consulta de catálogo/status sob política compatível com legados, auditar CSP/XSS/CSRF em todas as páginas e testar caso a caso; somente então planejar isolamento Windows/Job Objects e homologação R1. Isso não muda a prioridade canônica F5 física nem libera F6. Antes de qualquer implementação, reabrir ROADMAP/FAILSAFE/manual e verificar se o plano ainda é válido.

## 20. Vocabulário e referências

- **Gate:** conjunto de critérios verificáveis que bloqueia promoção de fase; **checkpoint:** incremento, mesmo com gate aberto.
- **PF6:** camada de confiança/permissões, confirmação e auditoria. **ACL R2.8:** lista de capacidades específicas negando o que não estiver autorizado, *além* de PF6.
- **Cérebro:** capacidade compartilhada, independente de persona. **Executor:** código concreto capaz de trabalhar e devolver resultado validável. **Catálogo:** inventário, não execução.
- **Proveniência:** ligação de uma informação a fonte/operação realmente verificada. **Fallback:** comportamento de compatibilidade, não prova de migração.
- **Offline-first:** prioriza runtime local; não equivale a ausência absoluta de rotas web em todos os módulos.

Leitura detalhada: `docs/current/ARCHITECTURE.md`, `ARQUITETURA_V08.md`, `ROADMAP_V9_CEREBROS_COMPLETO.md`, `docs/manual/README.md`, `docs/manual/21_PERMISSION_TRUST_LAYER.md`, `docs/manual/28_VOICE_MEDIA_F5B.md`, `docs/current/F5C_HOST_ACCEPTANCE_CHECKLIST.md`, `docs/operations/FAILSAFE_V9_CEREBROS.md` e os testes no diretório `tests/`. Em caso de discrepância, verificar a versão do **código executado**, registrar evidência e corrigir **simultaneamente** este manual, ROADMAP e FAILSAFE.


## 21. R2.9 — Cérebro fornece fatos; agente comunica (checkpoint atual)

**Objetivo exato:** limitar o LLM à conversa comum e impedir que faça alterações factuais no texto gerado pelos executores de cérebro. Antes desta atualização, `GroundedExpressionEngine` enviava inclusive resultados de cérebros ao LLM e aceitava paráfrases que passavam em heurísticas de valores e vocabulário. Tais heurísticas não são prova formal de equivalência entre afirmações.

**Caminho de execução real:** pergunta do usuário → `brains/router.py` escolhe capacidades explícitas → `brains/executor.py`/`worker.py` executam (somente Conhecimento e Análise estão instalados) → `result_validation.py` confere contratos, evidências e leituras → `chat/canonical_answer.py` ou `brains/collaboration.py` compila resposta factual tipada → `chat/service.py` usa o `canonical.canonical_answer` quando `brain_ids` está presente → `chat/grounded_expression.py` **não chama o LLM** para reescrever essas respostas e retorna literalmente o conteúdo canônico com uma única abertura de estilo fixa por agente se houver evidência suportada → o runtime incorpora suas próprias referências. O texto canônico mantém condições, números, unidades, resultados, limitações e status.

**Exemplo didático (ilustrativo, não um resultado real):** o cérebro apura “O total é 300.50.” com leitura efetiva; Morgana pode dizer “Pelo que consta nas fontes consultadas:” seguido **exatamente** de “O total é 300.50.”. Todd pode iniciar “Direto ao ponto, conforme as fontes:” e manter o mesmo corpo. Não há nova proposição gerativa. Quando o cérebro não encontra resposta ou detecta conflito, a saída preserva literalmente o estado de abstenção/conflito, sem introdução de sucesso. Em turnos conversacionais e fluxos legados **sem** `brain_ids`, o V9.1 continua usando LLM/validador heurístico; não confundir com garantia total de não alucinação.

**Código e testes que justificam esta descrição:** `src/campanario/chat/grounded_expression.py` (`render_brain_answer` e `GroundedExpressionEngine.express`), `src/campanario/chat/service.py` (`sourced_answer`), `tests/test_r29_brain_factual_boundary.py`, `tests/test_v91_expression.py`, `tests/test_v9_brains.py`, `tests/test_r2_collaboration.py`. Dados vindos da biblioteca são alegações da fonte, não verdade automaticamente. Comparações semânticas, conflito entre fontes, alegações com evidência fraca e seis cérebros faltantes exigem novos incrementos com avaliação própria.

**Foco após R2.9:** construir testes de qualidade factual, cobertura de alegações, proveniência e recusa robusta para Conhecimento/Análise em R2.10, mantendo requisitos de PF6/sandbox antes de executar ações perigosas. Voz fica fora da implementação corrente, mas a pendência F5 não é apagada. **Nenhuma alteração foi feita em `CAMPANARIO-PYTHON` ou `CAMPANARIO-DATABASE`**. Para atualizar/rollback mesclar ou restaurar apenas IA, preservar `.venv` compartilhada externa e todo o acervo SQLite e memória; não realizar migrations para este checkpoint. Em toda versão seguinte revisar/atualizar **os dois ROADMAPs, FAILSAFE, este Manual Vivo, changelog, testes e instruções** como regra verificável pelo gate documental.


## 22. R2.10 — Como o Campanario responde sem transformar tudo em recusa

**Fluxo real atual** (arquivos `src/campanario/chat/service.py`, `evidence_gate.py`, `canonical_answer.py`, `brains/result_validation.py` e `grounded_expression.py`):

1. O ChatService recebe um turno e verifica a sessao, define agente, identifica pedidos a documentos/planilhas ou busca e identifica um formato pequeno de pedido subjetivo. Isto NAO e uma classificacao semantica completa.
2. Para um pedido subjetivo coberto (exemplo: "o que voce acha de um final aberto?"), nao ha motivo para simular busca web, percorrer biblioteca local ou consultar ZIM. O LLM local pode conversar com a identidade Morgana/Todd, sem ganhar autorizacao para inventar fatos sobre pessoas ou datas.
3. Para uma pergunta factual que exige fonte, o runtime consulta apenas conectores habilitados, com privilegios e origem rastreaveis. Com internet desligada, nao e criada uma falha artificial `ResearchResult(disabled)` se nenhuma pesquisa ocorreu. Ainda pode haver resposta curta de insuficiencia de evidencia real, nunca uma biografia inventada.
4. Conhecimento produz trechos documentais e seus IDs reais; Analise produz resultado deterministico sobre planilha lida. O compilador monta `CanonicalAnswer`. R2.10 verifica para **resultados individuais de cerebro** que afirmacoes do tipo `source_assertion` aparecam literalmente nos trechos citados; caso contrario o registro desce para `not_found`. Isto nao valida inferencias implicitas, fatos contraditorios ou se o documento e verdadeiro.
5. `grounded_expression.py` preserva literalmente o corpo canônico de cerebros e aplica somente introducao fixa sem nova inferencia factual. Como exemplo, o cerebro pode informar que um trecho diz "valor 20%", e o agente pode introduzir a informacao com sua voz propria, mas nao substituir por "90%".
6. Os testes da R2.10 (`tests/test_r210_factual_routing.py`) verificam opiniào sem pesquisa, identidade sem fato inventado e afirmacao falsificada em `source_ids` validos; testes preexistentes verificam recusa de fontes ausentes, fluxo V9 e diferenca entre expressao do agente e fato.

**O que ainda NAO funciona completamente:** verificacao semantica de uma resposta, benchmark de qualidade factual real, comparacao confiavel de fontes e contradicoes entre elas, seis executores restantes de cerebros, sandbox Windows, falha G2 de auditoria pessoal e homologacao externa. O sistema nao pode assegurar zero alucinacoes. O ajuste de conversa abrange apenas uma classe conservadora de opinioes e nao resolve todos os casos com resposta repetitiva.

**Instrucoes a proximas IAs desenvolvedoras:** antes de alterar, ler o codigo real, dois ROADMAPs, FAILSAFE, este Manual e `PROCESSO_OBRIGATORIO_DE_DESENVOLVIMENTO.md`; testar sempre pedidos subjetivos, factuais sem fonte, afirmacoes falsas com IDs validos, conflito e memoria pessoal. Ao terminar atualizar os quatro documentos, changelog, instrucoes, testes, executar gate e informar resultados sem esconder falhas. **Três repositórios:** somente IA e alterado/distribuido; `.venv` Python 3.12 real fica em `CAMPANARIO-PYTHON`; SQLite e acervo em `CAMPANARIO-DATABASE`. Nenhum dado ou .env privado deve ser empacotado. **Rollback:** fechar app e recolocar arquivos IA R2.9 via Explorador, mantendo Database e .venv intocados. **Proximo passo R2.11:** consolidar benchmark de relevancia entre pergunta/trecho e auditoria de memoria G2 antes de ampliar executores.


## 23. R2.11 — Aula tecnica: memoria pessoal nao vira fato so porque o LLM afirmou

**Caminho observado no codigo:** `chat/service.py::_run_agent` identifica perguntas pessoais via `is_personal_question`. Se o backend Experiencia esta disponivel, usa `recall_hybrid` para buscar lembrancas; `source_evidence` descarta inferencias e fontes que nao se originaram em declaracoes do proprio usuario. O modelo pode sugerir texto, mas, antes de responder, o serviço monta uma **AUDITORIA DE EVIDENCIA PESSOAL** com `verification_messages`, exigindo que o verificador cite literalmente o menor suporte. `verdict_supported` confere o esquema JSON, textos citados e marcadores de intensificacao; `unlicensed_personal_strength` funciona como veto adicional e nao depende de honestidade do verificador. Se falhar, tenta um reparo limitado e auditado de novo; se falhar novamente, publica `evidence_fallback` que cita o que o usuario disse, sem declarar uma interpretacao mais forte. **Nenhum token da resposta inicial nao aprovada e emitido, e so a resposta final entra na memoria da conversa.**

**Quando nao ha memoria recuperada:** perguntas pessoais recebem falta de confirmacao, sem inferir fatos da personalidade do agente. A chamada de auditoria de lacuna no caminho G2 e apenas verificacao de seguranca e nao autoriza a promocao de resposta; nenhuma fonte externa e fabricada. Quando nao se trata de pergunta pessoal (cumprimento, opiniao reconhecida), o caminho conversacional anterior continua disponivel.

**Exemplo didatico:** Usuario diz `gosto de comida tailandesa`. O texto `sua comida favorita e tailandesa` contem grau nao demonstrado (gostar nao e favorito): auditoria/veto rejeitam. Pode-se responder `voce me disse que gosta de comida tailandesa`, sem inventar preferencia principal. Exemplo distinto: dois documentos citam regras incompatíveis; o `LocalFactSheet(status='ambiguous')` vira `VerificationStatus.CONFLICTING` e informa conflito, sem deixar Morgana/Todd escolherem arbitrariamente uma regra.

**Testes e limites:** `tests/test_g2_grounding_audit.py`, `tests/test_r211_evidence_audit.py`, `tests/test_r210_factual_routing.py`, `tests/test_v91_expression.py`. 74 testes direcionados passaram. A suite geral passou do antigo G2 mas parou apos 601 PASS na falha web preexistente, reproduzida isoladamente no ZIP R2.10. Nao existe prova geral de implicacao semantica, de credibilidade externa das fontes, nem de inexistencia de alucinacoes em todos os caminhos do chat. `evidence_gate.py` ja contem um teste conservador de pertinencia que R2.11 exercita por fixtures; R2.11 nao adicionou um novo motor semantico. Oito cerebros catalogados nao sao oito executores: somente Conhecimento e Analise sao instalados.

**Para proxima IA desenvolvedora:** continuar em R2.12 com benchmark de relevancia/contradicao real, analisar com cuidado a falha do guard web sem abrir brecha de prompt injection. Atualizar todos os documentos obrigatorios **no mesmo commit**; validar pelo gate, testes direcionados e suite geral. O codigo continua exclusivamente no `CAMPANARIO-IA`; `CAMPANARIO-PYTHON` possui a `.venv` compartilhada externa e `CAMPANARIO-DATABASE` possui SQLite, arquivos, memorias e documentos persistentes que NAO foram enviados. Sem duplicar. Instalacao e rollback por extracao/copias no Explorador, sempre com backup previo e sem sobrescrever `.env`. Voz fora de escopo deste incremento, F5 permanece historicamente aberto.


## 24. R2.12 — Como julgar uma página web sem confundir fonte com ordem

**Pergunta:** o que significa `ResearchResult(status='grounded')`? **Resposta:** somente que a recuperação selecionou página(s) efetivamente lida(s) com identificação coerente nos filtros determinísticos. O status não prova que o site informa a verdade nem que a declaração pedida foi logicamente demonstrada. O material vindo do site sempre é dado de confiança inferior.

**Trilha de código auditada:** `utilities/web_chat.py::research_entity` consulta `utilities/integration.py` por `web.search`, lê via `web.read` as páginas selecionadas, exige menção de sujeito e categoria na página realmente lida, avalia conflito de sentidos e compila `ResearchResult`; `_build_note` insere blocos `INICIO_FONTE_EXTERNA` e sanitiza texto visível. Na R2.12, um título como `Nova musician`, combinado à abertura `Nova is a musician`, é uma página que pode sustentar **identificação citável** da categoria `música`, mesmo sem pontuação separadora. Só o título, só snippet, nome no rodapé, categoria contrária ou um comando como `Ignore all previous instructions` **não** justificam tal identificação. O filtro de prompt injection protege a nota, mas é apenas complementar à fronteira de privilégio do runtime.

**Como desenvolver/medir:** `tests/test_r212_factual_benchmark.py` contém 10 casos sintéticos de seleção/abstenção por assunto e categoria, 5 de atributo requerido e 1 de filtragem de instrução externa; são 16 verificações fixadas com expectativas revisáveis apenas mediante justificativa. Na execução local, 16/16 PASS. Bateria factual expandida com R2.10, R2.11, G2 e V9.1 teve 64 PASS. Suite geral percorreu 603 testes PASS e parou em mock de `ChatService` sem `_sessions`, falha histórica reproduzida no R2.10 original. Essa validação **não** mede acerto em mundo real, recall em toda a internet, taxa real de alucinação nem robustez universal a prompt injection. Manter os relatórios honestos.

**Como atualizar/recuperar:** fechar o serviço; backup de IA e Database; mesclar a pasta `CAMPANARIO-IA` do ZIP incremental R2.12 no Explorador; preservar `.env` local e qualquer configuração; reiniciar e avaliar. Em falha, recolocar a cópia anterior da pasta IA, sem copiar nem alterar `CAMPANARIO-PYTHON/.venv` ou `CAMPANARIO-DATABASE`. Nenhum schema migrado. Se houver EXE congelado, copiar Python não recompila o executável.

**Próximo passo R2.13:** reparar mocks dos testes legados de maneira compatível com sessão real e o FAILSAFE; ampliar corpus anonimizado e avaliações de conflito, relevância e abstenção; homologar integração com Ollama e Windows. Não criar os outros seis executores de cérebros nem liberar ferramentas perigosas antes dos gates de R1. A plataforma separa agentes de evidências; perfil social jamais transforma fonte em verdade. **Toda próxima alteração exige atualizar juntos os dois ROADMAPs, FAILSAFE, este Manual Vivo, changelog, teste, instrução e relatório, validando gate documental.**

## 25. R2.13 — Por que testes com mocks não podem ignorar a sessão real

**Arquitetura e caminho de execução:** `src/campanario/chat/service.py::ChatService.stream_turn` começa consultando `self._sessions.get(session_id)` e checa o modelo antes de lookup local/web, planejador e persistência. Esse contrato protege o usuário contra efeitos em sessão inexistente. Um teste antigo que chama o método como `ChatService.stream_turn(Stub(), ...)`, mas não fornece `_sessions`, falha **corretamente** com `AttributeError`; não é motivo para enfraquecer o método. A R2.13 substitui esses stubs por `ChatService` verdadeiro ligado a `InMemorySessions`, `InMemoryMessages` e `FakeModelProvider`, criando sessão legítima e substituindo somente a implementação de geração do turno. Resultado: testar pré-checagem real, pesquisa e rotas de clarificação com dependências isoladas, sem alterar o backend.

**Outras derivações históricas:** as expectativas de `docs/history` não correspondiam ao ZIP recebido, que contém os capítulos antigos em `docs/manual`. O README dessa pasta agora explica seu caráter legado e a ausência da árvore histórica: não movemos arquivos para evitar necessidade de exclusões na atualização incremental. Um teste de memória anterior exigia a resposta do LLM sem verificação; desde R2.11, proposta pessoal sem auditoria válida deve cair em fallback literal. O guard de streaming também pode agregar chunks; o teste verifica o texto final e o bloqueio de vazamento, sem impor contagem artificial.

**Laboratório factual:** `tests/test_r213_evidence_corpus.py` reúne 20 pares pergunta/trecho com decisão esperada de pertinência literal, cinco conflitos **explicitamente marcados** no `LocalFactSheet`, um caso sem fonte e um número adulterado apesar do `source_id` válido. Não se trata de classificação automática da veracidade: uma frase estar no documento diz o que o documento afirma, e conflitos só mantêm `CONFLICTING` quando o retriever os marcou. O cérebro de Conhecimento e o de Análise continuam os únicos executores especializados; Morgana/Todd apresentam o texto canônico, não o editam.

**Validação, limites e próxima rota:** 52/52 testes focados passaram no Linux Python 3.13. Suite ampla chegou a 700 PASS (~66%), depois expirou sem sumário: não foi aprovada. Nenhum teste real de Windows/Python 3.12, Ollama, integração Database e fontes externas de produção. R2.14 deverá isolar o teste que trava a execução, investigar diferenças entre ambiente Linux e Windows, expandir corpus com documentos independentes e validar taxa de erro/abstenção antes de implementar outros cérebros. Voz permanece fora do escopo técnico atual, com gate F5 histórico ainda registrado.

**Como entregar/voltar:** distribuir somente arquivos relativos a `CAMPANARIO-IA/`, sem `.env`, `.venv`, SQLite, dados persistentes nem cache. Para atualização, fechar serviço, fazer backup, extrair incremental e mesclar no Explorador; para rollback, recolocar backup anterior **somente** de IA. A `.venv` externa continua em `CAMPANARIO-PYTHON` e bancos/memórias em `CAMPANARIO-DATABASE`. A atualização conjunta dos dois ROADMAPs, FAILSAFE, Manual Vivo e testes continua obrigatória, com validação do gate documental.


## 21. Marco R3.0: como a plataforma compara fontes sem inventar fatos

**Objetivo técnico:** entregar ao agente apenas um `CanonicalAnswer` coerente com os registros de execução, não uma nova resposta opinativa do LLM disfarçada de fato. A plataforma preserva sua divisão: agentes decidem *quem se expressa*, cérebros executam *capacidades*, o Motor V9.1 decide *como preservar o conteúdo*.

**Exemplo didático verificável.** Dois documentos independentes contêm “O prazo contratual acordado é 20 dias.” e “O prazo contratual acordado é 30 dias.”. A ferramenta recupera os trechos e associa cada um a fonte/ID. O módulo `src/campanario/chat/evidence_reconciliation.py` exige as frases iguais após substituir um único número por marcador. Os documentos precisam ter identidades diferentes. Isso gera `NumericDisagreement(source_ids, excerpts, values)`; a camada `build_canonical()` sinaliza `CONFLICTING`, preserva os IDs e emite resposta neutra sem escolher “20” nem “30”. Morgana e Todd recebem o mesmo corpo canônico e não recalculam nem fazem paráfrase gerativa.

**Exemplo que não deve ser tratado como conflito automaticamente:** “O prazo contratual acordado é 20 dias” contra “O preço contratual acordado é 30 reais”. São atributos e unidades diferentes; a estrutura lexical não coincide. Frases com dois valores também são ignoradas intencionalmente: escolher qual número se refere a qual atributo exigiria análise semântica ainda não implementada. Uma fonte e duas páginas do mesmo documento não constituem duas confirmações independentes. Detectar divergência **não estabelece qual fonte é verdadeira**.

**Localização de cada peça:** `brains/registry.py` instala Conhecimento e Análise; `brains/executor.py` exige scopes e encaminha workers; `brains/result_validation.py` verifica envelopes e evidência; `chat/fact_sheet.py` monta o registro do turno; `chat/canonical_answer.py` transforma evidência em estrutura canônica e chama `chat/evidence_reconciliation.py` para revisar conflitos numéricos do caminho de cérebros; `chat/grounded_expression.py` preserva a resposta factual ao renderizar personalidade. Os testes estão em `tests/test_r30_factual_reconciliation.py`, `test_r213_evidence_corpus.py`, `test_r2_collaboration.py` e `test_r29_brain_factual_boundary.py`.

**Como reproduzir:** no runtime Python apropriado do repositório externo `CAMPANARIO-PYTHON`, a partir da raiz do IA, executar os quatro arquivos de testes com `pytest -q`, sem criar `.venv` no IA e sem apontar para Database real. O resultado observado nesta máquina foi 56 PASS no Linux/Python 3.13. Uma suíte geral interrompeu após 875 PASS por teste de layout antigo sobre `renpy_factory`; isso não é confirmação de homologação global. Consulte `RESULTADOS_TESTES_R30.md`.

**O que continua sem funcionar:** não existe executor registrado para Investigação, Estratégia, Programação, Percepção, Comunicação ou Criação; a detecção automática não interpreta frases semanticamente equivalentes, fontes falsas, negações complexas, contexto temporal ou relações causais. O Ollama real, Windows e Database separado não foram testados. Não elevar o checkpoint R3.0 a “oito cérebros concluídos”.

**Para onde seguir:** revisar o conflito histórico de layout sem apagar código; homologar o núcleo Knowledge/Analysis no host e mensurar precisão/abstenção com fontes independentes; preparar os contratos seguros read-only de Investigação e Estratégia; desenvolver e testar os demais executores conforme o ROADMAP e R1. O objetivo não é acumular versões R2.x, mas gerar marcos de capacidade com testes completos.

**Governança permanente:** esta seção é cumulativa e deve acompanhar código, os dois ROADMAPs, FAILSAFE, processo, resultados de testes, changelog e instruções na mesma revisão. `CAMPANARIO-IA` é código; `CAMPANARIO-PYTHON` fornece a `.venv` compartilhada; `CAMPANARIO-DATABASE` contém todos os dados persistentes e não integra ZIPs.


## 21. R3.1 — Como funcionam Investigação e Estratégia de verdade

**Mapa de execução (código atual):**

1. A pessoa escreve uma solicitação explícita de **investigar**, **apurar** ou **planejar**. `CapabilityRouter.plan()` seleciona `investigation` e/ou `strategy`; para pedido de planilha explícito com cálculo detectado, pode incluir também `analysis` (máximo de três etapas). Uma conversa normal, como falar de histórias de detetive, não inicia estes cérebros. O `AgentRouter` continua decidindo **quem fala** de modo independente.
2. `ChatService` constrói `BrainRequest` com `trace_id`, orçamento e `library:read` e transmite contexto de autorização do runtime. `BrainExecutor` avalia escopos via `PermissionPolicy` quando vinculada e chama `execute_local_worker()` para os quatro primeiros executores conhecidos. O worker Python usa o mesmo intérprete da instalação, não cria `.venv`, não recebe credenciais do `.env` e bloqueia acesso de rede no processo, sob watchdog de timeout/RSS. **Isto não é contenção hostil garantida no Windows.**
3. Em `brains/investigation.py`, os novos executores usam `search_document()` do sistema existente, em lugar de recriar OCR/indexação/biblioteca. O SQLite é aberto em leitura (`mode=ro`, `PRAGMA query_only=ON`). Uma consulta sem trecho relevante retorna `PARTIAL` ou `UNAVAILABLE`, sem relatório afirmativo. Esses dados permanecem em `CAMPANARIO-DATABASE` conforme configuração; a cópia enviada do IA não contém o banco pessoal.
4. O resultado `BrainResult` inclui `evidence_refs`, operações, status, warnings e um `report` determinístico. A Investigação apresenta **alegações citadas**, gaps e conflito numérico conservador, quando o mesmo enunciado contém valores diferentes em documentos distintos. A Estratégia cria um plano condicional para verificar objetivos, evidências, alternativas, responsáveis e critérios de parada. Não há investigação da internet autônoma, perfilamento de pessoas, inferência causal nem escolha automática do melhor curso de ação.
5. `result_validation.py` reconstrói o relatório a partir de referências já verificadas e rejeita substituição por frase inventada. `brains/collaboration.py` usa uma única base de evidência para evitar duplicar as mesmas fontes quando dois cérebros leem o mesmo documento; resultados sem prova não podem se transformar em fato. A resposta `CanonicalAnswer` é compilada antes da expressão, e Morgana/Todd mantêm apenas apresentação factual permitida pelo V9.1.
6. A Central expõe `/api/v1/brains/catalog` e `/api/v1/brains/preview`: catálogo indica quatro implementados, mas só `ready` se o DB/dependências realmente estiverem acessíveis. A prévia aceita `brain_id=investigation|strategy` com leitura e plano específico. A flag `CAMPANARIO_BRAINS_V9_ENABLED` continua desligada por padrão. O executável Windows congelado pode não usar arquivos Python recém-copiados; validar intérprete no destino.

**Exemplo didático:** pergunta 'Investigue o prazo de pagamento e elabore uma estratégia'. Havendo documento realmente importado, o cérebro cita o trecho exato, registra divergências numéricas verificáveis, identifica dependências de validação e apresenta passos *a verificar*. Não declara que houve fraude, que o pagamento está atrasado nem que uma decisão é ótima sem prova. Na falta de documento, avisa de forma específica que faltam evidências em vez de preencher com ficção. Agente apenas exprime resultado, não origina prova.

**Limitações e testes:** documentos que não aparecem no recuperador não ficam magicamente disponíveis; o algoritmo de divergência não compreende paráfrases complexas, horários ou relações temporais. Ele não cria bases cronológicas, grafos de relacionamentos, rankings financeiros ou investigação web aberta. Testes sintéticos verificam worker real, permissão negada, ausência do DB, adulteração de relatório, colaboração e conversa casual. Testes no host Windows + Ollama + Database externo continuam pendentes. Também não foram implementados Programação, Percepção, Comunicação ou Criação.

**Próximo passo:** evolução para linha do tempo e matriz de hipóteses com evidência rastreável, análise de alternativas quantitativa usando cálculos existentes, mais testes E2E e homologação OS; não dispensar R1. Governança R3.1: atualizar ROADMAP, ROADMAP V9, FAILSAFE, este Manual e processo em todo marco. Os repositórios **IA** (código), **PYTHON** (`.venv` externa) e **DATABASE** (memórias e SQLite) seguem independentes. Rollback por cópia de backup R3.0 do IA, sem afetar os dados.

**Complemento R3.1 verificado:** os relatórios agora contam trechos/origens efetivamente recuperados, e Investigação lista datas dd/mm/aaaa literais válidas sem associá-las automaticamente a eventos. Estratégia bloqueia escolha por valores numéricos comparáveis em conflito. Bateria final 74 PASS; regressão anterior 881 PASS/1 FAIL legado e reexecução após ajuste final interrompida antes de completar.


## Marco R3.2 — Manual operacional da Central de Casos

**O que o código realmente implementa:** `src/campanario/brains/casework.py` armazena dados de **um caso independente de conversas**, com original por evidência, `case.json`, hash SHA-256, eventos cronológicos, hipóteses concorrentes e relatório Markdown. `src/campanario/brains/casework_cli.py` oferece um menu humano e `ABRIR_CENTRAL_DE_CASOS.bat` executa esse menu usando **exclusivamente** `CAMPANARIO-PYTHON/.venv/Scripts/python.exe` no Windows. Os quatro executores R3.1 não foram substituídos; a Central de Casos **ainda não é invocada pelo chat** e não há API/mobile de casos nesta versão.

**Onde ficam os arquivos:** `CAMPANARIO-DATABASE/dados/cases/<uuid>/case.json` e `.../originals/<id>.<ext>`, nunca no repo IA. O módulo exige `CAMPANARIO_DATA_DIR` configurado para a pasta `dados` existente sob a pasta irmã nomeada `CAMPANARIO-DATABASE`. O launcher configura esse caminho por relação de pastas; não cria Database nem migra SQLite. Verificar permissões de pasta e fazer backup privado do Database antes de operar.

**Fluxo real no Windows:** (1) instalar R3.2 mesclando o ZIP incremental no IA; (2) fechar serviço em execução; (3) abrir `ABRIR_CENTRAL_DE_CASOS.bat` com duplo clique; (4) escolher Novo caso e informar objetivo/responsável; (5) Importar evidência por caminho de arquivo explicitamente autorizado; (6) conferir SHA-256; (7) opcionalmente propor registros estruturados CSV/JSON `timestamp,action`, conferir e aprovar cada proposta; (8) registrar evento com fuso e fonte; (9) criar hipótese com evidência pró/contra e próxima verificação; (10) conferir hashes e exportar dossiê em `DOSSIER.md` dentro do próprio caso. Não é necessário PowerShell para instalar ou abrir a interface de menu.

**Exemplo técnico fictício:** o log de desligamento às 18h42 e uso posterior de crachá às 19h08 podem gerar intervalo **26 minutos**, sem concluir quem usou o crachá ou se houve delito. Se o arquivo foi adulterado, `verify()` marca falha; a cronologia e hipóteses continuam como declarações sem autenticação material. O status `unresolved` não significa que a hipótese seja provável: apenas que não foi resolvida. `propose_log_events()` não adiciona eventos sem confirmação do operador.

**Segurança e mecânica:** campos com limite de caracteres, path IDs derivados de UUID, formato autorizado, rejeição de links simbólicos para fonte/originais, cópia de até 25 MiB, hash de original, ledger JSON com substituição atômica, relatório com IDs e limites explícitos. Não extrai ZIP, não executa arquivos, não faz rede e não usa LLM para deduzir eventos. **Limite:** JSON não assinado, sem bloqueio entre processos concorrentes, sem autenticação granular PF6 na CLI, sem verificação semântica dos documentos; logo não serve ainda como sistema forense homologado nem como central multiusuário remota.

**Próximo passo:** integrar o workspace à autorização/identidade PF6 e ao pipeline `InvestigationBrain`/`StrategyBrain`, tornar captura Field autenticada e criar extração PDF/XLSX/imagem com proveniência e revisão humana. Testes R3.2 usam apenas diretórios temporários simulando o nome Database, não tocam em dados de produção. Revisar `docs/operations/RESULTADOS_TESTES_R32.md` antes de promover marco.

## 21. R3.3 — Central de Casos embutida no Campanário (23/11/2026)

**Checkpoint:** R3.3. A R3.2 criara o `CaseWorkspace` e o antigo menu de linha de comando. A exigência atual do usuário é operar **dentro do Campanário**. A R3.3 adiciona `src/campanario/brains/casework_api.py` no servidor FastAPI principal, monta as rotas pelo `main.py` e adiciona `src/campanario/web/static/cases.js` à mesma página Dark Matter. `workspaces.js` acrescenta `Database > Casos`. Não há browser tab, web app separado, pacote de instalação, nem banco ou ambiente Python adicional. O BAT antigo é mantido como legado, não faz parte do fluxo normal.

### Fluxo do usuário, dentro do aplicativo

1. Abrir o Campanário habitual, clicar **Database → Casos**; as outras telas e a conversa continuam no mesmo aplicativo.
2. Entrar com credencial de proprietário PF6 ou nome/senha offline individual, previamente configurados em `.env` privado. O servidor exige `CAMPANARIO_BRAINS_V9_ENABLED` e credenciais PF6 corretas. O token é guardado só na memória da página; logout revoga a sessão.
3. Criar um caso e seu objetivo; confirmar a operação na própria interface. Caso grava `authorized_by` igual à identidade autenticada.
4. Importar um arquivo pelo seletor de arquivos da interface, declarar sua origem e confirmar. O browser envia bytes de até 25 MiB, não caminhos de disco. O backend valida nome e conteúdo, grava uma cópia no `CAMPANARIO-DATABASE/dados/cases`, calcula SHA-256 e nunca extrai ZIP.
5. Consultar evidências e hashes; para CSV/JSON, visualizar propostas de eventos com campos `timestamp` e `action` e selecionar uma proposta para registrar. Cada registro pede confirmação independente.
6. Registrar eventos manuais com fuso horário explícito e fonte, criar hipóteses com evidências pró/contra, visualizar revisão determinística e dossiê. O dossiê pode ser baixado como `.md` **pelo próprio painel**.

### Arquitetura e limites atuais

- **Armazenamento:** `CaseWorkspace` R3.2 continua sendo único responsável pelo caso; diretório de dados externo obrigatório. O adaptador HTTP não cria SQLite nem persiste sessão/token. Metadados JSON e originais ficam fora do IA. As três pastas `CAMPANARIO-IA`, `CAMPANARIO-PYTHON/.venv`, `CAMPANARIO-DATABASE` permanecem independentes.
- **Segurança:** `casework_api._session` reaproveita `utilities.api._owner_session` e o perímetro loopback/local. Escrita exige ACL adicional para operador individual e `PermissionPolicy` com modo `SCOPED_CONFIRM`, vínculo de principal, sessão, capacidade, hash da operação e consumo único. Casos de outro operador são invisíveis via API. A interface nunca pode dar permissão por ser Morgana, Todd ou um cérebro. Nenhum endpoint é exposto no Field.
- **Factualidade:** a interface mostra campos declarados, hashes, intervalos aritméticos e hipóteses sempre `unresolved`; não há interpretação automática de PDF, reconhecimento de imagem, verdade externa confirmada nem integração de `CaseWorkspace` como fonte direta do chat. Investigação/Estratégia R3.1 possuem executores de leitura, mas **ainda não recebem automaticamente o contexto deste caso**. Não atribuir nova inteligência investigativa a esta melhoria de UX/backend.
- **Integração real ainda pendente:** chat case-aware com seleção de casos/fontes, plano de investigação com revisão humana, saída canônica independente da personalidade, busca multimodal sob autorização e Field autenticado. O isolamento real de processos Windows, o acesso via celular e o R10 permanecem não homologados.
- **Validação:** `tests/test_r33_cases_native.py` cobre criação, PF6 consentimento, replay, mudança do corpo, isolamento entre operadores, upload, revisão e inclusão na UI; ver relatório R3.3 para o que efetivamente foi executado. Teste local não equivale a execução na máquina Windows do usuário.

**Próximo marco útil:** integração em conversa de **casos selecionados explicitamente** com os quatro cérebros reais (sem escrita autônoma, sem LLM como evidência) e fluxo de hipóteses revisáveis; habilitar somente após testes de autenticação de dados e ausência de alucinação.


## 22. R3.4 — Como a conversa sobre casos funciona dentro do Campanário

**Checkpoint:** R3.4. O código de `src/campanario/brains/casework_dialogue.py` gera respostas exclusivamente de leitura e classificadas por intenção (fontes, cronologia, hipóteses, estratégia condicional e visão geral). Não chama Ollama: usa `CaseWorkspace.read()` e `verify()` do `casework.py`, lista IDs de evidências e evita elevar relatos a fatos externos. Hash adulterado faz o resultado virar `limited` sem reproduzir as alegações do caso. Não resolve suspeitas nem conclui autoria ou causalidade.

**Fluxo técnico:** pessoa abre **Database > Casos**, autentica-se via PF6 local e seleciona seu caso. `cases.js` mantém token apenas em memória e oferece perguntas no próprio painel. `POST /api/v1/cases/{case_id}/ask` valida `_session()` e `_owned_case()` em `casework_api.py`, recusa outras identidades como 404, chama o analisador determinístico e devolve texto canônico, IDs de evidência, status e limitações. A função `CampanarioCases.tryChat()` faz ponte de leitura quando o operador escreve **explicitamente** `Caso: ...` ou `Todd, no caso, ...` no chat Dark Matter, no mesmo navegador e na mesma aba. O chat normal continua na implementação pré-existente. Não são transferidos arquivos ao modelo; a resposta tem introdução fixa por agente e o restante igual.

**Contrato de dados:** a pergunta não grava resposta no ledger, não escreve memória nem histórico conversacional; a conversa apresentada na tela é transitória. Os arquivos privados e ledger continuam **exclusivamente** em `CAMPANARIO-DATABASE/dados/cases`, sem SQLite novo, com `.venv` externa de `CAMPANARIO-PYTHON`. O módulo não incorpora automaticamente os arquivos PDF/XLSX ao recuperador de Conhecimento/Análise nem executa os quatro cérebros como um workflow: estes quatro executores permanecem disponíveis separadamente no catálogo R3.1. Não afirmar que já temos investigador autônomo.

**Guia:** perguntar sobre cronologia, documentos, hipóteses, próximos passos e revisão; rastrear as referências `[E...]` na Central. Caso sem evento responde que não há evento; hash alterado bloqueia retorno. Para gravar cronologia ou hipótese continuar com confirmação PF6 da Central. Teste `tests/test_r34_case_conversation.py`; leitura de testes e documentação obrigatória em `docs/operations/RESULTADOS_TESTES_R34.md`. Voz fora do escopo.

**Para onde ir:** incorporar aos cérebros os documentos selecionados do cofre com extratos verificáveis, revisão de contradições e dependências, consentimento por operação, persistência opcional de turnos do caso com isolamento por proprietário, CI e homologação Windows + repositórios externos. R1/F5/R10 continuam abertos, assim como Programação, Percepção, Comunicação e Criação. Rollback IA R3.3 sem apagar DATABASE ou PYTHON.


### R3.4 — Como operar Casos sem configuração de segurança no PC pessoal

**Fluxo atual:** o servidor FastAPI monta `/api/v1/cases` diretamente em `main.py`. A tela Database > Casos (Dark Matter, `web/static/cases.js`) consulta `GET /api/v1/cases/mode`. Se não há credencial nem lista de operadores PF6, entra automaticamente em **modo pessoal local** sem senha ou `CAMPANARIO_BRAINS_V9_ENABLED`; acessa `CaseWorkspace` (arquivos em `CAMPANARIO-DATABASE/dados/cases`, nenhuma tabela SQLite nova), lista casos e escreve usando confirmação simples da interface. A API local aceita a escrita nesse modo, por isso o aviso de interface é orientação de UX, não autorização criptográfica. `app/security.py` e `utilities/api.py::local` continuam restringindo a interface ao próprio computador, rejeitando pedidos cross-site e cabeçalhos de encaminhamento. Com PF6 explicitamente configurado, a API preserva autenticação/ACL e confirmação de operações. Identidades de casos antigos não são migradas automaticamente.

**Conversa:** o usuário escolhe um caso no painel; `web/static/chat.js` encaminha pedidos explícitos `Caso: ...` para `cases.js`, que chama `POST /api/v1/cases/{id}/ask`. `brains/casework_dialogue.py` consulta o registro e a integridade e devolve informação canônica sem solicitar ao Ollama inventar interpretação. Morgana/Todd só alteram abertura fixa. Isso ainda não é investigação autônoma semântica, nem acesso direto a anexos pelos quatro executores.

**Como fazer:** instalar incremental R3.4 sobre R3.3, preservar `.env`, abrir Database > Casos, criar caso, importar documento e perguntar no próprio painel; para chat, manter caso selecionado na mesma aba e escrever `Caso: quais as evidências?`. Se o computador já tem contas PF6 explicitamente configuradas, será apresentado login: opção preservada, não pré-requisito para instalação pessoal nova.

**Próximo passo:** estudar a ligação controlada do cofre de evidências aos quatro cérebros de leitura, com proveniência e citações auditáveis, testes de dados reais no Windows, suporte Field quando houver consentimento remoto apropriado. Não tocar em voz fora do foco atual.

## 23. R3.5 — Como a leitura fundamentada dos documentos do caso funciona

**Checkpoint R3.5.** A R3.4 só consultava metadados e eventos. Agora `src/campanario/brains/casework_sources.py` abre, em modo somente leitura, as cópias de evidência do caso depois de verificar o SHA-256. Não lê arquivos arbitrários indicados pelo navegador: a API `brains/casework_api.py` valida identidade/owner (quando configurado) e chama `brains/casework_dialogue.py`, que passa apenas `case_id` à `CaseWorkspace` para localizar originais no Database externo. A interação permanece na interface Dark Matter (`cases.js`, `chat.js`). O agente escolhido muda somente uma introdução fixa.

**Como usar:** abrir Database > Casos no mesmo Campanário; criar/selecionar caso, importar documentos autorizados, declarar a origem; perguntar `Caso: o que diz o contrato sobre o prazo?`, `Caso: compare divergências de prazo` ou `Todd, no caso, investigue os contratos`. A busca seleciona linhas que contêm termos da pergunta e devolve trechos literais com ID `[E...]` e localização. Sem correspondência, ela informa que não achou trecho; isso não prova que a informação esteja ausente do documento. Para respostas de cronologia, hipótese e checklist, preserva o caminho já existente da R3.4.

**Mecânica:** TXT/LOG/MD são linhas UTF-8; CSV é tabular por linha; JSON é textualizado de forma determinística; PDF textual usa `pypdf` se presente (já consta nas dependências), extraindo até 35 páginas; XLSX usa `openpyxl` se instalado como extra opcional, lendo valores em `data_only`, não executando fórmulas. Imagem, ZIP, PDF digitalizado e outros formatos não são interpretados. O limite da extração é de 2 MiB por original e o resultado retorna no máximo 8 trechos (não é revisão integral). A linha do PDF traz o número de página e a da planilha traz aba/linha; a linha citada no envelope refere-se ao extrato transformado e não ao byte original. O preview não edita o caso nem insere registros no histórico geral.

**Colaboração reaproveitada:** `brains/investigation.py::structured_report` produz relatório ou plano condicional a partir de `EvidenceRef` obtidas dos trechos preservados, sem executar novo worker, sem bypass PF6 e sem rede. Isto **não é** uma orquestração completa dos quatro executores. Conhecimento, Análise, Investigação e Estratégia continuam com seus executores R3.1 próprios. Conflito numérico só é assinalado quando os textos são iguais salvo uma quantidade única, e documentos diferentes exibem valores diferentes; não há julgamento de qual fonte está correta, nem uma análise semântica abrangente ou atribuição de culpa.

**Arquitetura:** `CAMPANARIO-IA` mantém código, interface, testes e docs; `CAMPANARIO-PYTHON/.venv` externa compartilhada tem Python e bibliotecas; `CAMPANARIO-DATABASE/dados/cases` guarda originais e ledger. Não criar banco em IA, não distribuir originais, não migrar automaticamente. R3.5 não modifica o Motor Fundamentado V9.1, a Biblioteca Conversacional V2, Morgana/Todd, voz ou o restante do Database.

**Testes reais nesta entrega:** ver `docs/operations/RESULTADOS_TESTES_R35.md`. 117 testes focados passaram; 566 testes gerais passaram e o teste preexistente de Biblioteca de Interações falhou, reproduzido também na R3.4. Linux usado; Windows, ambiente Python 3.12, modelos Ollama e dados pessoais não disponíveis. O FAILSAFE R3.5 orienta perda de integridade e rollback. **Dívidas técnicas e próximo passo:** indexação de conteúdo e citações mais completas, confronto de dados com contexto, revisão humana de hipóteses, OCR/percepção autorizada, integração mais profunda com quatro workers e testes reais de ponta a ponta no Windows. Não declarar os oito cérebros prontos; apenas quatro possuem executor.

## 24. R3.6 — Investigação multietapa, OCR e similaridade semântica

**Estado comprovável:** quatro cérebros executáveis catalogados e testados na base anterior. A R3.6 **não** os substitui: adiciona um pipeline determinístico de cinco estágios em `brains/case_investigation_pipeline.py` chamado por `casework_dialogue.py` quando o usuário pede para investigar/analisar um caso. O pipeline examina documentos íntegros, extrai citações, revisa a cronologia cadastrada, sinaliza conflitos numéricos estritos e compara hipóteses registradas com contagens de referências. Contagens não são confiança probabilística; não conclui culpado, nexo causal nem solução. Morgana e Todd preservam o mesmo corpo canônico com introduções separadas. A interface continua sendo Dark Matter, Database > Casos e chat, sem aplicativo/aba extra.

**Extração:** `casework_sources.py` lê TXT/MD/LOG/CSV/JSON, PDFs com camada de texto e XLSX opcional, e agora permite OCR de PNG/JPG/JPEG com Tesseract no host se explicitamente habilitado. PDF sem camada de texto pode rasterizar no máximo seis páginas via PyMuPDF/Pillow opcional e enviar à OCR. Há limites de tamanho, megapixels, páginas e tempo; arquivo enorme, ilegível ou dependência ausente é indicado como não examinado. OCR retorna texto reconhecido, não interpretação completa de fotos. Nunca altera originais em DATABASE.

**Semântica:** com `CAMPANARIO_CASE_SEMANTIC_ENABLED=1`, `CAMPANARIO_CASE_EMBED_MODEL` nomeando modelo previamente instalado e Ollama em loopback, compara o embedding da pergunta com até 60 linhas extraídas. A chamada é **opcional**, usa `127.0.0.1` sem proxy e leva texto privado somente ao Ollama local. Similaridade retorna trechos literais citáveis, não um fato gerado. Sem modelo ou serviço, mantém a recuperação lexical. As frases inferidas por modelo não são convertidas automaticamente em evidência.

**Como usar:** faça backup, instale R3.6 no IA com mesclagem pelo Explorador, abra a interface padrão, selecione Database > Casos e pergunte `Caso: investigue as divergências do contrato`. OCR/semântica ficam desligados por padrão e dependem de ferramentas opcionais da **mesma** `.venv` em CAMPANARIO-PYTHON (e executável Tesseract do Windows), sem instalação automática. Configure as opções somente no `.env` privado se desejar; não crie `.venv` nova nem mova os casos.

**Segurança, testes, rollback e próximo passo:** confira `docs/operations/FAILSAFE_V9_CEREBROS.md` e `RESULTADOS_TESTES_R36.md`. Recuo simples: remover as opções OCR/semântica ou restaurar apenas IA R3.5; DATABASE e PYTHON permanecem intocados. Ainda faltam interpretação visual de objetos e cenas, compreensão semântica irrestrita, planejamento de investigação independente com revisão humana, testes Windows/Ollama real e homologação geral. Próximo passo: percepção local com resultados provisórios auditáveis, recuperação em corpus mais amplo e métricas sobre dados consentidos.

**Percepção visual experimental:** `casework_vision.py` envia, apenas com `CAMPANARIO_CASE_VISION_ENABLED=1`, até duas imagens íntegras do cofre ao Ollama local (modelo por padrão `llava`, já instalado pelo operador). O texto retorna como `unverified_visual_suggestion` e aparece como **PISTA VISUAL AUTOMÁTICA NÃO VERIFICADA** no chat de casos. Não altera originais, não atribui autoria e não comprova o que ocorreu. Não há reconhecimento universal de imagens.

As flags R3.6 são propriedades de `config.Settings`, carregadas pelo `.env` privado do Campanário (ou ambiente), sem criar novo arquivo de configuração nem exigir PowerShell para exportar variáveis.


## R3.7 — Como funciona o ciclo investigativo limitado (documentação técnica e didática)

**Fluxo no Campanário:** Dark Matter → Database → Casos → selecionar um caso → perguntar `Caso: investigue ...`. O chat aciona `prepare_case_answer`, que consulta os originais do CaseWorkspace. O caminho investigativo chama `investigate_case` e recebe um relatório **estruturado e determinístico**. Este relatório é apresentado por Morgana ou Todd com apresentação fixa, sem nova geração de fatos pelo LLM.

**Primeira rodada:** `search_case_evidence` verifica a integridade SHA-256, faz leitura dentro dos limites e seleciona trechos associados à pergunta inicial; registra ID, nome, linha e SHA-256. Se não houver trechos, a pergunta inicial fica sem suporte, mesmo que outra rodada encontre material relacionado a outra dúvida.

**Rodadas seguintes:** até duas perguntas complementares vêm **exclusivamente** do campo `next_check` das hipóteses já registradas pelo operador. Isso não é uma investigação autônoma aberta; o software não inventa uma pergunta baseada no que teria ocorrido. Cada rodada repete a verificação de integridade e registra o número de citações novas. Citações são deduplicadas por ID, linha e hash e limitadas a 16. Ao final, a integridade é verificada de novo e o motivo de parada aparece na saída (`round_limit`, `citation_limit`, `no_more_registered_checks`). As perguntas complementares podem revelar novas passagens, mas não comprovam a pergunta inicial.

**Documentos adicionais:** `casework.py` aceita `.docx`, `.html`, `.htm` no cofre existente em CAMPANARIO-DATABASE/dados/cases, sem criar banco nem extrair arquivos para outra pasta. O leitor DOCX abre somente o membro `word/document.xml` (ZIP seguro por limites de entradas e tamanho), extrai parágrafos do WordprocessingML e ignora scripts, macros e links externos. HTML utiliza parser de texto, excluindo script, style, SVG, iframe e template; não executa nada. Os formatos anteriores TXT/LOG/MD/CSV/JSON, PDF, XLSX, imagens OCR e visão opcional continuam disponíveis com limitações R3.6. PDFs escaneados e idiomas de OCR dependem do host; DOCX não lê automaticamente conteúdo de imagens embutidas.

**Falhas e interpretação:** integridade alterada bloqueia completamente a revisão; parsing incompleto deve aparecer como limite, não como ausência de fato no mundo. Citação não valida fonte; semântica aproximada não prova proposições; hipóteses permanecem não verificadas. Nenhuma permissão nova, investigação em rede, execução de código, arquivo pessoal ou autonomia de ação foi liberada.

**Como desenvolver depois:** manter testes que distinguem evidência para a pergunta principal de evidências complementares, documentos inválidos, ataque de ZIP, texto HTML com scripts, alegações sem suporte, duas identidades e rollback. Roadmaps e FAILSAFE continuam autoridades documentais, mas a fonte final de comportamento é o código e os testes reais. Próximo marco: corpus mais realista de documentos/casos, avaliação de compreensão semântica e revisão explícita de hipóteses.

**Estado R3.7:** capacidade iterativa de leitura validada em testes sintéticos, **não** investigador autônomo universal nem compreensão universal de documentos. A instalação Windows, Ollama real, OCR real e CAMPANARIO-DATABASE privado não foram testados. A suíte geral tem falha antiga da Biblioteca de Interações. O trio obrigatório permanece `CAMPANARIO-IA` código, `CAMPANARIO-PYTHON` `.venv` externa, `CAMPANARIO-DATABASE` persistência.


## R3.8 — Guia didático: do registro à relação investigativa

**O que faz:** a pergunta chega pelo chat de Casos no Dark Matter; o fluxo `prepare_case_answer` aciona `investigate_case` somente em solicitações de investigação. O `CaseWorkspace` consulta originais em `CAMPANARIO-DATABASE/dados/cases`, compara SHA-256 e recupera citações literais numeradas. O módulo novo `brains/case_reasoning.py` processa **somente** o ledger e os trechos já verificados.

**Como funciona, passo a passo:** (1) classifica suporte à pergunta inicial pela primeira recuperação; (2) ordena até duas verificações já escritas pelo operador (`next_check`) por pertinência lexical à pergunta e existência de posições pró/contra cadastradas; (3) cada rodada verifica integridade e deduplica trechos; (4) constrói ligações `registered_support`, `registered_opposition` e `registered_event_source`, sempre como *cadastro não validado*, e pistas `lexical_overlap_only` entre fontes diferentes quando há pelo menos dois termos compartilhados; (5) monta `hypothesis_review`, indicando se referências pró/contra cadastradas apareceram entre os trechos recuperados; (6) Morgana/Todd mostram matrizes e ressalvas com abertura fixa, sem alterar citações ou perguntar ao LLM qual hipótese é verdadeira. O fluxo não grava novo fato ou hipótese no Database.

**Exemplo:** documento A cita prazo 20 dias e B cita prazo 30 dias. A revisão numérica estrita anterior pode indicar divergência; a matriz R3.8 registra a coincidência textual e as fontes. Ela **não decide** qual prazo vale, se há fraude ou quem agiu. Uma pergunta sobre culpados não é considerada respondida só porque um `next_check` localizou prazos.

**Onde mexer para desenvolver:** `brains/case_reasoning.py` contém classificação e filas puras; `brains/case_investigation_pipeline.py` orquestra até três leituras; `brains/casework_sources.py` extrai texto opcional e recupera trechos; `brains/casework_dialogue.py` monta a resposta factual. `tests/test_r38_adaptive_case_reasoning.py` cobre integridade, fila, relações, falsas conclusões e não persistência. Novos algoritmos precisam preservar extração, limites e rastreabilidade dos IDs, sem reescrever os originais.

**Limites:** relação por vocabulário não prova vínculo semântico; referência cadastrada pró/contra não comprova posição; status `reviewable` significa apenas trechos encontrados, nunca verdade externa. Extração DOCX/HTML/OCR e embeddings seguem limitados; não existe compreensão documental universal ou investigação causal autônoma. Oito cérebros previstos, apenas Conhecimento, Análise, Investigação e Estratégia com executor. O processamento do caso é somente leitura, sem executar quatro workers em colaboração ampla. A suíte geral continua com falha preexistente da Biblioteca de Interações.

**Como instalar/operar:** fechar programa, backup, extrair ZIP incremental e copiar o conteúdo de `CAMPANARIO-IA` pelo Explorador. Não modificar `CAMPANARIO-PYTHON/.venv` nem `CAMPANARIO-DATABASE` (SQLite, memórias e casos); preservar `.env` privado. Entrar em Database > Casos e consultar pelo chat. Homologação real de Windows, OCR e Ollama permanece pendente.

**Próximo passo:** avaliações semânticas reproduzíveis com fontes contraditórias e revisão humana explícita das hipóteses e decisões, sem promover previsões a fatos; resolver testes legados antes do gate de produção. ROADMAPs, FAILSAFE, Manual, Processo e relatório devem evoluir juntos.

## Checkpoint R3.9 — como as evidências realmente são lidas

**Escopo real:** em `src/campanario/brains/casework_sources.py` a plataforma procura passagens nas cópias preservadas do caso, compara SHA-256 e devolve texto literal, ID de evidência e linha. `case_investigation_pipeline.py` passa essa lista para `case_claims.review_claims()`; `casework_dialogue.py` inclui no relatório do chat **Database > Casos** as etiquetas e conflitos textuais. Isso não requer Ollama, rede, conta de usuário nem programa separado no modo pessoal local.

**Leitura linguística:** cada trecho pode receber `reported_statement`, `explicit_negation`, `uncertain_or_hypothetical` ou `attributed_statement`. Estas são **pistas de linguagem**, não decisões sobre verdade. A classificação considera marcas expressas na própria linha, não o contexto de outras páginas. A categoria é registrada ao lado do trecho literal; o agente nunca a utiliza para inventar novos fatos.

**Oposição literal:** quando duas evidências distintas contêm exatamente o mesmo sujeito/predicado/complemento com polaridade oposta (ex.: “O pagamento foi aprovado” versus “O pagamento não foi aprovado”), `textual_oppositions` devolve um par com referências e aviso de revisão. Não prova que as fontes sejam independentes, válidas ou contemporâneas. A análise não infere que “liberado” equivale a “aprovado”, nem resolve citações indiretas, ironia, condições, negação complexa ou versões temporais diferentes.

**Fluxo de desenvolvimento:** verificar a origem do arquivo e integridade -> consultar trechos -> separar alegação de prova -> revisar oposição/ressalva -> responder com conteúdo canônico -> documentar limitações. Adicionar testes negativos antes de generalizar gramática. Não habilitar inferência generativa como fonte de verdade. O ROADMAP, ROADMAP V9, FAILSAFE, este manual e o Processo Obrigatório devem mudar em conjunto em todo release.

**Estado e próximos passos:** quatro cérebros com executores (Conhecimento, Análise, Investigação e Estratégia); quatro pendentes. F5 fora do foco e não homologada, R1/R10 abertos. Próximo marco: um módulo de revisão humana persistente de proposições e conjuntos anotados com ambiguidades, contradições semânticas, diferentes tempos e fontes derivadas, sem alterar os originais. Os repositórios seguem independentes: IA (código), PYTHON (uma `.venv` externa), DATABASE (casos e dados).


## R3.10 — Revisão semântica local, ancorada em citações (23/11/2026)

**O que o projeto faz de verdade:** `brains/case_semantic_review.py` oferece uma anotação semântica *opcional* via Ollama **somente local** (`http://127.0.0.1:11434/api/chat`, sem proxy), limitada a oito citações previamente localizadas em arquivos de caso preservados com hash. Ele pode propor papéis linguísticos de substrings literais (afirmação, negação, incerteza, atribuição, condição) e relações entre fontes (paráfrase, possível contradição, possível suporte ou contexto relacionado). A configuração é `CAMPANARIO_CASE_CLAIMS_SEMANTIC_ENABLED=false` por padrão e `CAMPANARIO_CASE_CLAIMS_SEMANTIC_MODEL=<modelo local já instalado>` no `.env` privado. Não exige outro ambiente Python ou banco. A modalidade usa um modelo de chat já instalado, **não o modelo de embedding**.

**Como funciona:** a Central de Casos continua dentro do Dark Matter. `case_investigation_pipeline.py` primeiro verifica integridade e recupera citações com ID/linha/hash; depois chama o classificador, quando habilitado. A saída do modelo passa por listas de categorias fechadas e checagem de referências. Textos supostamente extraídos só são aceitos quando são substrings literais das citações. Explicações, novas conclusões e instruções devolvidas pelo modelo são descartadas. `casework_dialogue.py` mostra apenas os trechos originais e rótulos provisórios, sem pedir a Morgana ou Todd para redigir novos fatos. O modelo não pode executar operações, escrever em casos, ler caminhos arbitrários, se conectar a serviços remotos ou conferir permissões.

**Limitações:** a classificação **não comprova** equivalência semântica, veracidade, identidade, causalidade ou independência entre documentos. Uma relação sugerida pode estar errada; uma relação ausente não prova compatibilidade. OCR, PDFs digitalizados, gráficos e arquivos desconhecidos dependem dos leitores já existentes e de suas limitações; portanto **compreensão semântica profunda de qualquer documento NÃO está concluída**. O tratamento de contexto amplo, tabelas, pronomes, contradições implícitas e evidência externa requer avaliação humana e novos benchmarks. O modelo só recebe as citações locais selecionadas, não a íntegra de todos os arquivos. Se Ollama estiver indisponível ou a opção estiver desligada, a investigação anterior segue funcionando. Não há teste real com seu modelo/Ollama/Windows e Database externo.

**Como continuar sem microversões:** construir benchmark com documentos complexos e rótulos revisados por humanos; medir precisão, cobertura, falsas contradições e abstenção, inclusive mudanças de contexto e revisões das hipóteses; ampliar leitura de tabelas e referências sem jamais permitir que o modelo altere evidências. Preservar sempre a divisão: CAMPANARIO-IA (código), CAMPANARIO-PYTHON (única `.venv` externa), CAMPANARIO-DATABASE (dados persistentes), sem migrações ou cópias extras. Rollback por restauração da pasta IA anterior e manutenção dos dados externos.


## R3.11 — Como habilitar capacidades sem inventar homologação (23/11/2026)

A versão R3.11 introduz `ATIVAR_RECURSOS_LOCAIS_R311.bat` para diagnóstico e ativação de recursos opcionais da **instalação local existente**: OCR com Tesseract/Pillow/pytesseract na `.venv` externa; embeddings instalados no Ollama em loopback; revisão semântica com modelo local; percepção visual provisória; ZIM encontrado em diretório explicitamente configurado. A ferramenta só altera `.env` privado após consentimento e backup; desativa opções para as quais não detectou os pré-requisitos. Ela não configura internet, credenciais, V9 experimental nem concede permissões. Detecção não é teste de qualidade.

O avaliador `scripts/evaluate_semantic_relations.py` contém 18 pares fictícios anotados (paráfrase, contradição, suporte, nenhum) e calcula precisão/recall/F1 por classe. Sem `--model` só valida o avaliador com o gabarito, **não é benchmark de IA**. Com `--model NOME` tenta inferência local; falha de modelo aborta o resultado em vez de atribuir acerto. O leitor deve manter anotações semânticas como não verificadas e checar citações.

O operador não enviou o `.env` privado nem seu ambiente Windows, por isso **nenhum modelo foi efetivamente ativado no computador dele nesta entrega**. Próximo passo: rodar diagnóstico no host, medir desempenho real em corpus consentido com gabarito humano, documentar erros e só então decidir se os outros quatro cérebros podem avançar. Permanecem quatro executores: Conhecimento, Análise, Investigação e Estratégia. O rollback é restaurar `.env.backup_R311_*` e arquivos IA prévios; Database e `.venv` externa não devem ser tocados.


## R3.12 — Manual didático de homologação factual real (23/11/2026)

**O que é homologar?** O Campanário distingue (a) detectar e ler documentos, (b) encontrar trechos, (c) sugerir relação entre trechos via Ollama, (d) conferir se a sugestão não inventa uma citação e (e) provar acurácia em uma amostra externa julgada por humanos. As etapas (a)-(d) já existem em parte; (e) não pode ser inferida de testes com respostas simuladas. Agentes Morgana e Todd só comunicam o conteúdo factual canônico, sem acrescentar fatos.

**Código novo:** `scripts/homologate_factual.py` reutiliza o classificador real `scripts/evaluate_semantic_relations.py` e o cliente de Ollama por loopback `src/campanario/brains/case_semantic_review.py`. Exige modelo explicitamente nomeado, testa 34 pares anotados de equivalência, conflito, suporte ou ausência de relação, duas vezes, e calcula métricas e confusão por classe. Gate técnico conservador: acurácia ≥0,85, macro-F1 ≥0,80, recall de contradição ≥0,85, concordância entre rodadas ≥0,95 e **zero falsos conflitos** em exemplos que não contradizem. Esses valores são metas de triagem, não garantias estatísticas nem calibração clínica/jurídica.

**Como fazer no Windows:** após instalar os arquivos no CAMPANARIO-IA, deixar Ollama iniciado e um modelo de chat já instalado. Abrir `HOMOLOGAR_FACTUAL_R312.bat` com duplo clique e informar o nome exato. Usa exclusivamente `..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe`; não cria .venv. O BAT tenta registrar o JSON sob `CAMPANARIO-DATABASE/dados/avaliacoes_factual` somente se a pasta externa existir. Códigos de saída: 0 = `PASS` técnico restrito, 2 = `BLOCKED`, 3 = `INCONCLUSIVE`. Nunca adicionar arquivos desses relatórios aos pacotes distribuídos. Não precisa de PowerShell.

**Como interpretar:** a pontuação é apenas uma amostra artificial de classificação de pares; não avalia recuperação de fonte, OCR, hipótese causal, precisão dos dados, longas investigações ou contradições dependentes de contexto. Para homologar o produto, revisar documentos reais autorizados manualmente, medir erros por tipo de fonte e registrar resultados do chat de casos com citações completas, além de testar o Windows e a Database separados. `PASS` do script sozinho é insuficiente. O arquivo `.env` privado não é alterado. Se Ollama falhar, o processo não inventa métricas. Não liberar novo executor de cérebro apenas por passar esse corpus.

**Três repositórios e rollback:** CAMPANARIO-IA contém avaliador e testes; CAMPANARIO-PYTHON contém a `.venv` externa; CAMPANARIO-DATABASE contém relatórios e dados, sem novo SQLite. Recuo por cópia dos arquivos IA anteriores, sem tocar em `.env`, `.venv` ou acervo. **Próximo passo:** execução real do gate e avaliação humana com corpus diverso; corrigir erros identificados antes de avançar Programação, Percepção, Comunicação e Criação.

## Adendo R3.13 — erro de anexo no chat e correção do modo pessoal

O botão de clipe do chat chama `POST /api/v1/utilities/upload-stream` em `src/campanario/utilities/api.py`. Na R3.12, quando V9 estava ativado, todo envio exigia permissão de escrita que o chat não solicitava: "Permissão não concedida pela política central". Na R3.13, `local(request)` continua checando origem e loopback; `_solo_local_upload()` identifica ausência de identidades PF6 e owner token. Somente nesse modo pessoal a rota de upload ignora a exigência adicional de V9. Com PF6 configurado, permanece a checagem central; lista de identidades inválida causa 503. O endpoint de invocação e os cérebros **não** recebem exceção.

O navegador permite TXT, MD, PDF, CSV, JSON, LOG, DOCX e XLSX; o arquivo vai à pasta de utilidades já autorizada, até 200 MB no fluxo, sem sobrescrever e sem importação automática. Para analisá-lo é necessário importar na Biblioteca ou em Casos pela interface; upload não implica leitura instantânea por Todd/Morgana. `src/campanario/web/index.html` força atualização da versão de cache de chat.js. Regressão e rollback constam no FAILSAFE e resultados de testes. Confirmação em Windows real ainda necessária.


## Adendo R3.14 — modo pessoal local, sem PF6 obrigatório

**Contrato de implementação:** `config.Settings.local_personal_mode=True` por padrão, também quando o `.env` existente não mencionar a nova chave. `utilities/api.py` respeita a preferência em `_v9_permission()`, catálogo, endpoint de upload e `invoke`; a UI não requer aprovações adicionais para operações explícitas no navegador local. `brains/casework_api.py` cria sessão lógica pessoal, pode ler casos legados sem troca de propriedade e preserva origem na ledger; `cases.js` usa apenas o clique explícito para gravar, sem pop-up PF6/local. Para retornar ao modo de múltiplas identidades, estabelecer `CAMPANARIO_LOCAL_PERSONAL_MODE=false` no `.env` e reiniciar; só então PF6 e ACLs configurados voltam a ser usados. Essa opção **não** ativa novos cérebros.

**Arquivos grandes:** `POST /api/v1/cases/{case_id}/evidence` recebe chunks por `request.stream()`, calcula SHA-256 durante o staging em `CAMPANARIO-DATABASE/dados` e importa via cópia para `originals` sem carregar todo o conteúdo em memória. `CaseWorkspace.MAX_BYTES` e upload-stream utilitário: 1 GiB por arquivo; `MAX_ITEMS=4096`; estes são limites operacionais deliberados, não permissões de usuário. `_authorize()` aceita hash pré-computado para preservar vinculação de conteúdo se o modo protegido for reativado. Não extrair ZIP, executar anexos nem modificar originais.

**Compatibilidade e falhas:** `.env.example` demonstra a preferência, mas o `.env` privado não é distribuído ou sobrescrito. Casos antigos ficam legíveis no modo pessoal, mantendo `authorized_by`; retornar a PF6 exige planejamento de ownership. Acesso não-loopback/origem cruzada, sobrescrita, path traversal e respostas sem citação continuam proibidos. Sem homologação em Windows real. Testes novos em `tests/test_r314_personal_mode.py`; consultar `RESULTADOS_TESTES_R314.md`. A seção histórica Segurança PF6 permanece apenas para recuperação do modo protegido, não é mais requisito do usuário único.


## Checkpoint R3.15 — biblioteca realmente acessível e respostas ligadas ao documento

**Falha real reportada:** clipe do chat fazia apenas staging de arquivos, mas não invocava `library.import`; portanto, um arquivo presente em `CAMPANARIO-DATABASE/dados/.../utilidades/arquivos/` podia não existir em `documents` nem em `document_sections`, impossibilitando `search_document`. A UI não tornava essa distinção visível. Uma continuação com `qual` sem interrogação era classificada como conversa genérica, fazendo o modelo responder sem a fonte desejada.

**Correção integrada na UI:** chat passa `index=true` em `upload-stream`; o endpoint preserva o arquivo no workspace, importa por `UtilityService` no mesmo DATABASE externo e retorna `indexed`, `indexed_sections`, `index_state`, `document_id` ou `index_error` sem fingir êxito. Importação é feita em thread durante a requisição, nunca em background silencioso. PDF sem texto/OCR ausente e JSON inválido são marcados como não pesquisáveis. Arquivos antigos enviados somente ao staging: em Ferramentas → Arquivos, usar **Indexar**; documentos com erros: Ferramentas → Biblioteca → **Reindexar**. O original continua imutável, com SHA-256 validado antes da reindexação.

**Gerenciamento:** o Explorador e a Biblioteca têm paginação (100 itens/página e total real), nomes, estados, visualização do texto extraído, exclusão e renomeação. A Biblioteca tem `library.rename` (metadados apenas, preservando extensão/arquivo) e `library.reindex` (reextração do original validado e substituição transacional da indexação). Arquivos na pasta autorizada oferecem Indexar/Renomear/Mover/Lixeira. O conteúdo original preservado não é editado diretamente; nova versão deve ser importada conscientemente. Chat permanece na interface Dark Matter, sem nova aba/aplicativo de investigação.

**Intenção documental:** `document_request` reconhece “arquivo relacionado a ordem paranormal” e remove o sufixo “e me diga...” do nome sugerido. Perguntas de acompanhamento com “qual/quais/quem...” sem `?` mantêm a referência explícita recente ao documento; falta de citação continua exigindo abstenção factual. Nenhum nome de criatura da franquia foi codificado como resposta. Trecho recuperado mostra **o que a fonte diz**, não valida cânone externo.

**Verificação:** 90 testes direcionados PASS, incluindo regressões V8, PF6 pessoal, cérebros, casos e semântica; regressão geral: 33 PASS, 1 falha preexistente em `uv.lock` ausente. Compilação e JavaScript verificados. Não houve acesso ao acervo privado do operador nem homologação com Windows/Ollama reais. **Rollback:** fechar o Campanário, restaurar a cópia R3.14 do código e reiniciar; preservar o DATABASE. Metadados criados nesta versão são compatíveis com schema V8; cópia privada de segurança recomendada antes de reindexar ou excluir.


## Checkpoint R3.16 — manual técnico Maps V2 (23/11/2026)

**Arquitetura:** `app/navigation_v2.py` fornece `NavigationService` com estados IDLE/READY/NAVIGATING/OFF_ROUTE/RECALCULATING/PAUSED/ARRIVED/STOPPED/ERROR; projeção em polilinha OSRM, filtro GPS, três desvios sucessivos e cooldown. `app/api.py` publica `/api/app/navigation/v2/providers|resolve|route|status|command/{action}|fix|recalculate` exclusivamente em loopback, montado no FastAPI principal já existente. Navegação permanece **na memória do processo**, não no DB; STOP limpa coordenadas e rota. Serviços de busca e rota são OSRM/Nominatim/Overpass em loopback, dependentes de bases OSM efetivamente importadas. O piloto por `gps-map.js` antigo foi substituído no fluxo principal por `web/static/navigation-v2.js` de ciclo de vida por aba; `workspaces.js` acrescenta controles Maps V2 na mesma interface Dark Matter, chat tem evento existente de navegação, `gps-map.js` desenha a rota recebida.

**Agentes:** Todd ou Morgana solicitam destino por intenção de rota já reconhecida no chat; não são geocodificadores ou motores de roteamento. Respostas de ferramenta vêm do OSRM; não há fluxo PF5 novo para planejamento arbitrário do LLM, nem mudança nos quatro executores atuais. Relações Investigação/Agenda ainda são metas. Distância restante é projeção aproximada sobre a polilinha, ETA usa duração original do OSRM proporcional, sem trânsito ao vivo.

**Dispositivo e privacidade:** desktop recolhe geolocalização por solicitação explícita via navegador; Maps V2 não acessa GPS por conta própria. URL de serviço deve ser `http://127.0.0.1:<porta>` ou `http://localhost:<porta>`, rejeitando host externo. Tiles externos OSM/CARTO somente após opt-in na UI; offline MBTiles PNG não é grafo para rotas. O mobile já existente tem endpoints `/api/companion/v1/maps/v2/*` isolados por ID no canal HTTPS pareado, sem permissão de acessar `/api/app`. `apps/mobile/www/app.mjs` atualiza GPS nativo pontual em primeiro plano e TTS Java `MainActivity.java` anuncia apenas manobras da rota do PC. **Sem ForegroundService/notification, APK homologado, mapa-base de ruas mobile ou rota offline no telefone.**

**Como instalar e validar:** ler `docs/operations/INSTALACAO_MAPS_V2.md`, configurar endpoints locais no `.env` privado, instalar extrato OSM e OSRM carro com `PREPARAR_OSRM_CARRO_V2.bat` opcional, preparar geocodificadores separadamente; rodar `DIAGNOSTICAR_MAPS_V2.bat` para ver portas e testar efetivamente rota coberta. Em CI: `tests/test_r316_maps_v2.py`, `tests/test_v08_platform.py`, `tests/test_v9_brains.py`, `node --test tests/mobile/*.test.mjs`, `node --check`, `compileall`, gate documental. Portas abertas não certificam roteamento; fixtures não homologam campo. Não encerrar F5 voz nem novos cérebros.

**Rollback/FAILSAFE:** se GPS ruim/antigo, interromper processamento; se motor offline/sem cobertura, retornar erro; se re-routing falhar, OFF_ROUTE sem afirmação enganosa. Não sobrescrever grafos previamente preparados, fazer backup do IA, restaurar R3.15 por Explorer, preservar .env, DATABASE, PYTHON/.venv e OSM. Sem migração de SQLite. Dívidas técnicas incluem suporte nativo de Android em segundo plano e processo persistente próprio se navegador/servidor fechar. Próximo passo: homologação em PC + Android com dados OSM concretos, retomar desenvolvimento dos cérebros somente após fechar problemas de base factual da Biblioteca independentemente do Maps.


## Checkpoint R3.17 — CAMPANÁRIO FIELD: navegação Android nativa em primeiro plano do sistema

**Implementação:** complementa o host Android existente, sem substituí-lo e sem criar outro sistema de IA. `NativeNavigationActivity` é tela Android Java real para selecionar destino, calcular rota OSRM, iniciar/pausar/encerrar navegação e consultar manobras; `NavigationForegroundService` usa `LocationManager`, notificação foreground `location` e `TextToSpeech` pt-BR independentemente da WebView e ao alternar para o chat; `CompanionMapsClient` acessa somente API pareada HTTPS `/api/companion/v1/maps/v2/*` com token do `SecureStore` Android Keystore; `RouteGeometryView` desenha geometria de rota devolvida pelo backend sem mapa-base inventado. Comando textual “rota para ...” na interface embutida abre a Activity nativa, consulta POIs locais, pede decisão quando há ambiguidade e inicia guia quando há candidato inequívoco e GPS válido.

**Limites:** NÃO existe APK nesta entrega: ambiente sem Android SDK, Gradle nem conectividade para instalar essas ferramentas. Os testes Java são de contratos de fonte e manifest, não build nem sensores reais. Continua interface híbrida (chat/notas/web bundled + navegação nativa), não Jetpack Compose completo nem Room, MapLibre offline, roteamento offline no Android ou OTA privado. OSRM/Nominatim/Overpass no PC e TLS pareado continuam obrigatórios para rota real. Android pode suspender o serviço conforme suas políticas; a notificação não garante execução ilimitada. Serviço não registra trajetos novos em banco. Nenhuma chamada de localização é feita fora de sessão iniciada.

**Testes e rollback:** 53 testes Python direcionados e 16 testes JS PASS; regressão geral: 33 PASS/1 FAIL por `uv.lock` ausente também na base R3.16; sem teste APK/dispositivo. Gate documental e sintaxe JS PASS. Para voltar, restaurar IA R3.16, manter DATABASE e PYTHON separados e não sobrescrever `.env`/dados. Antes de distribuir, compilar Android SDK 35 + Gradle compatível/JDK17 e testar em aparelho com servidor OSM autogerenciado. Guia: `docs/operations/ANDROID_FIELD_V1_BUILD_E_NAV.md`.

## Checkpoint R3.19 — limpeza da distribuição e correção Maps

Foi auditado o ZIP CAMPANARIO-IA.zip do usuário (267 MiB compactado, 8.238 entradas). O artefato continha venv interna, modelos ONNX repetidos, diretório `docs/operations` com cópia recursiva do projeto, Git, documentos históricos, SQLite e `.env` privado. Essas entradas não são necessárias para compilar `apps/mobile/android` e foram excluídas do novo pacote *de código*, sem apagar a instalação de origem. O ZIP limpo contém `uv.lock`, código, assets `apps/mobile/www`, testes, SDK Android-fonte e documentação essencial. Windows deve usar `CAMPANARIO.bat` na raiz, python.exe externo encontrado como irmão, sem PREPARAR_PC.

O frontend `navigation-v2.js` não exige GPS <=100m para procurar destino. Busca de endereço sem origem delega ao geocodificador; busca "mais próximo" sem origem informa ausência, sem escolha global arbitrária; rota aceita origem manual, guia vivo exige GPS preciso. Tiles online são padrão, opt-out explícito respeitado. Não foi executado build Android ou teste de rua; sem servidor local geográfico, roteamento real não está homologado.


## R3.20 — localização automática e busca/rota com fallback (23/11/2026)

- Ao abrir Maps no Dark Matter, o cliente tenta `navigator.geolocation.watchPosition` automaticamente, conforme a autorização do Windows/navegador. Mantém latitude, longitude, precisão e horário somente em memória de interface; não envia localização ao servidor durante a simples observação. Sem GPS, busca por endereço permanece disponível e a origem manual continua possível.
- A tela Maps usa somente `CampanarioNavigationV2` para os botões de busca/rota, evitando que o antigo `gps-map.js` sobrescreva os handlers.
- Busca por endereço: Nominatim local primeiro; se estiver indisponível, Nominatim público em consulta explícita. Categoria próxima: Overpass local e depois público; roteamento carro: OSRM local e, se estiver indisponível, servidor público de demonstração OSRM. Caminhada: somente grafo pedestre local (não inventar rota de carro).
- O fallback está **ativado por padrão para uso pessoal** e pode ser desativado com `CAMPANARIO_MAPS_PUBLIC_FALLBACK=false`. Serviços públicos recebem a busca e, em roteamento, as coordenadas. Nominatim público tem limitação de uso, identificação do aplicativo, cache em memória e espaçamento de 1,1 s por host; não usar autocomplete nem disparar varreduras. Não há GPS fictício.
- Pendente: teste de campo em Windows/Android; conectividade e política dos provedores públicos; precisão do GPS no PC; compilação APK e navegação Android em segundo plano. Não declarar homologação de campo.


## Checkpoint R3.21 — Field GitHub Pages (23/11/2026)
- Frontend PWA público estático, isolado em `pages/`, com GPS do navegador, mapa OSM e consulta de rotas públicas; não contém dados privados.
- Servidor Python/Ollama/Database continuam exclusivamente no PC; acesso opcional via listener Companion HTTPS autenticado e CORS para origem Pages explicitamente configurada.
- Compatibilidade e limitações: consulta cartográfica pública sujeita a quota, rota de carro somente, GPS em primeiro plano, sem APK nem homologação em campo; tela e notas offline, sem roteamento offline.
- Implantação reversível: excluir publicação Pages / desabilitar `CAMPANARIO_FIELD_PAGES_ORIGIN`; sem migração de dados e sem alterações nos três repositórios externos.
- Testes da alteração e pendências descritos em `docs/operations/RESULTADOS_TESTES_R321.md`. Não declarar homologado o acesso real a PC ou geolocalização do usuário.
