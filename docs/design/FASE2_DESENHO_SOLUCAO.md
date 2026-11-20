# CAMPANARIO-IA — Fase 2: Desenho da solução (SEM implementação)

**Data:** 19/11/2026  |  **Base:** `CAMPANARIO_IA_ETAPA3_CORRIGIDO_COMPLETO.zip` (v0.8.0) e relatório Fase 1.  
**Status:** proposta para aprovação, nenhum código alterado, nenhuma validação física com Ollama/Qwen, Windows ou Kiwix executada nesta fase.  
**Premissas inegociáveis:** Campanario = sistema autônomo; agentes = somente personalidades; funcionamento offline como modo principal; evidência > fluência; um núcleo factual neutro para um ou N agentes; usuário decide; internet somente opt-in.

## 0. Evidências que comandam as decisões

**FATO VERIFICADO (projeto/auditoria):**

- `src/campanario/utilities/service.py`, `UtilityService._execute`: `library.import` armazena TXT/MD/PDF, páginas e SHA-256 no SQLite `utilidades.sqlite3`; `library.search` faz busca por substring nas páginas. Funciona de forma isolada, não é RAG integrado ao chat; PDF escaneado sem texto requer OCR (não é prioridade atual).
- `src/campanario/chat/service.py`, `stream_turn`/`_stream_turn_impl`/`_run_agent`: a decisão prévia consulta caminhos de pesquisa **web**, não `library.search`; em grupo passa o mesmo `research_guard` web, mas recria contexto/memória por participante. A prova da Fase 1 recuperou trecho sobre Ada Lovelace na biblioteca e mesmo assim obteve recusa no chat offline.
- `src/campanario/chat/knowledge.py`, `natural_uncertainty`/`sourced_definition_answer`: respostas factuais ramificam por `agent_id`, violando a separação sistema/persona.
- `src/campanario/agents/profiles.py`/`personality_application.py`/`addressing.py`/`participation.py`: há regras fixas para Todd/Morgana; o terceiro agente não funciona só com perfil novo. `chat/service.py` requer uma persona mesmo em consulta factual.
- `src/campanario/config.py`: `web_auto_search=True` como default de código, versus `CAMPANARIO_WEB_AUTO_SEARCH=false` no `.env.example` (risco offline); `model_context_window=4096` por padrão. `model/adapters/ollama.py`, `_build_payload`, transmite `num_ctx` ao Ollama.
- Baseline Fase 1, Linux/Python 3.13.5: **655 aprovados, 30 falhas, 14 avisos** na suíte geral; 73 aprovados no recorte. Ambiente fora da faixa `>=3.12,<3.13` declarada em `pyproject.toml`. As falhas G2 não são somente stubs obsoletos.
- `docs/current/AGENT_ARCHITECTURE.md` descreve agentes que compartilham sistema, prioridade de fala e ausência de duplicação factual. Referência conceitual no ZIP é **v2.0**, não v2.2.

**HIPÓTESE (a testar):** a soma de prompts, histórico e pesquisa pode exceder a janela de 4096 tokens, gerando perdas de conteúdo. Não há demonstração do efeito no Qwen real; não tratar aumento de contexto como correção de grounding.

## 1. Arquitetura-alvo (desacoplada de persona)

```text
[Usuário / API direta / cliente]
                |
       [Session + TurnCoordinator]
                |
    [consulta factual é necessária?]
                |
        [FactService NEUTRO] -----------------------┐
                |                                  |
  [1 local: biblioteca + Kiwix/ZIM]               |
                |                                  |
       [2 memória com proveniência]                |
                |                                  |
   [3 web SOMENTE com autorização]                 |
                |                                  |
      [FactSheet imutável, 1/turno] <---------------┘
                |
     +----------+------------------+
     |          |                  |
[API neutra] [Router por perfis] [auditoria comum]
     |          |                  ^
 [fontes]    [0/1/N personas] -------+
                |
   [respostas com os mesmos IDs de fatos]
                |
        [persistência + saída]
```

**PROPOSTA:** criar serviço de consultas (`FactService`) próprio do **sistema**, independente de agentes e sem instanciar persona. Não duplicar bancos, provedores, busca, memória nem normas de verdade. O `TurnCoordinator` produz **um snapshot de fontes e uma ficha por turno**, e entrega exatamente a mesma ficha a cada persona; nenhuma geração de outro agente é promovida a fonte. Conservar roteador, sessão, provider, event bus e failsafes existentes, substituindo gradualmente a decisão web-first, não empilhando mais regex.

**Separação explícita:**

- **Camada factual:** consulta, relevância, identidade/aliases, citações, ambiguidade, conflito, confiança de ligação pergunta↔trecho, ausência de fonte; devolve neutro. Não conhece `agent_id`.
- **Camada de persona:** só tom, ritmo, ângulo de interpretação, sugestões e preferências; pode discordar em recomendações, jamais mudar/omitir/introduzir fatos. Qualquer novo fato exige nova ficha feita pelo **sistema**, e não tool calling factual descontrolado por agente.
- **Camada de saída/auditoria:** exige cada afirmação factual verificável vinculada a `fact_id` presente na ficha. Falha de verificação => remove/reformula a afirmação ou abstém; não assume que um LLM verificador torna uma invenção verdadeira. Para respostas estritamente factuais curtas, preferir montagem determinística a partir de trecho atribuído.
- **Sem agente:** `/api/v1/facts/answer` (nome ilustrativo, **não existe hoje**) chama a mesma ficha e retorna resultado neutro com fontes, sem perfil ou geração de persona. A biblioteca e as ferramentas continuam independentes dos agentes.

## 2. Base offline e perímetro do conhecimento

### Fontes e estratégias

| Origem (ordem) | Alternativa | Escolha proposta | Por quê / limite |
|---|---|---|---|
| 1a. Biblioteca do usuário | Busca atual `substring`; embeddings locais; SQLite FTS5 + excertos | **SQLite FTS5 incremental**, mantendo a API e SQLite existentes, com fallback `substring` | CPU/SSD, previsível, fonte e página; demanda migração reversível e teste de acentos/nomes. Embeddings opcionais após baseline, não requisito offline. |
| 1b. Enciclopédia | Copiar ZIM inteiro ao SQLite; libzim nativa; **Kiwix-serve em loopback** | **Kiwix-serve + ZIM local**, index de busca do próprio ZIM | Evita duplicar muitos GB, fornece título, artigo e URL local, precisa processo local instalado; uma API pública do servidor deve ser escolhida e testada na Fase 4. |
| 2. Memória | Tomar mensagens antigas como verdade; registros com proveniência | **Somente registros com origem/escopo e tipo de afirmação** | `USER_CLAIM` pode apoiar preferências e dados pessoais atribuídos, **não prova independentemente** biografias ou obras do mundo externo. Fala de agente nunca é evidência. |
| 3. Internet | Auto-search; buscador local; busca manual | **Opt-in por pergunta/sessão, e somente após insuficiência local** | Se indisponível, retorna `offline` e segue local; SearXNG em `127.0.0.1` ainda depende da internet para recuperar sites. |

**Kiwix (fonte externa verificada; arquivos NÃO instalados):** catálogo oficial consultado em 19/11/2026 lista Wikipedia portuguesa `all_mini_2026-05` **1,6 GB**, `all_nopic_2026-05` **6,6 GB**, `all_maxi_2026-05` **19 GB**. Esses tamanhos são dos arquivos ZIM, não da RAM/VRAM nem de uma instalação medida; o catálogo muda. `mini` traz introdução/infobox, `nopic` traz texto completo sem imagens, `maxi` inclui imagens. **Escolha inicial:** `all_nopic` (6,6 GB) quando houver disco; `mini` (1,6 GB) para experimentar a integração, mas não equivale a cobertura enciclopédica completa. Os ZIM são arquivos externos opcionais, baixados/importados voluntariamente; Campanario não deve baixá-los na inicialização.

**Armazenamento planejado:** 1 ZIM selecionado (1,6 / 6,6 / 19 GB nessa amostra) + arquivos do usuário já existentes + índice textual da biblioteca. **Não construir índice FTS do ZIM inteiro**; o Kiwix aproveita seu próprio índice quando disponível. O tamanho do FTS5 de documentos do usuário é **desconhecido** até medição com coleção representativa; estimativa não deve virar requisito de capacidade. Ler ZIM e consultar FTS não exigem GPU. Se Kiwix estiver desligado, a biblioteca deve seguir operante.

**Limites honestos do offline:** conhecimento coberto apenas pelos ZIM instalados e pela biblioteca/memória efetivamente autorizadas e recuperáveis; snapshots possuem data e podem estar desatualizados. Nunca tratar “não achei” como “não existe”. Se nenhum trecho adequado: **“Não encontrei uma fonte sobre X na minha biblioteca e enciclopédia offline instaladas. Posso pesquisar na internet se você autorizar.”** Se usuário proibir internet, remover oferta naquele turno. Se o assunto for contemporâneo, indicar explicitamente que um acervo de 2026-05 não garante atualização em 2026-11.

### Recuperação e segurança

- Biblioteca: importar com autorização, preservar SHA-256, caminho original, título, página/parágrafo, data e faixa de trecho, normalizar acentos/aliases com testes; chunking por parágrafo/seção com sobreposição pequena e limite de tokens. Uma busca por pessoa deve usar título, redirecionamentos e contexto suficiente para distinguir homônimos, sem exigir igualdade literal absoluta de título.
- ZIM: registrar `collection_id`, nome, snapshot, título, URL local `http://127.0.0.1:<porta>/...`, trecho e posição; em resposta, fornecer citação/identificador recuperável em modo offline. **Não abrir URLs externas sugeridas por páginas ZIM** como parte da recuperação.
- Tratamento de fonte: conteúdos documentais/web são **dados não confiáveis** para instruções; limitar bytes/tempo, impedir SSRF/endpoints arbitrários, isolar origem; manter controles de leitura/permissão do `UtilityService`. As permissões de biblioteca do usuário não são elevadas por perfis.
- Conflitos: hierarquia determina **sequência de consulta**, não afirma que uma memória do usuário prova fatos universais. Registrar divergência, datas e fontes, sem “resolver” silenciosamente com texto do modelo.

## 3. Ficha única de fatos por turno

**PROPOSTA de contrato, exemplo ilustrativo (não implementado):**

```json
{
  "turn_id": "...", "query": "quem foi Ada Lovelace?",
  "status": "supported", "offline": true,
  "intent": "entity_identity", "subject": "Ada Lovelace",
  "facts": [
    {"id":"F1","claim":"...","source_ids":["S1"],"scope":"encyclopedic",
     "evidence_span":"excerto original que suporta a afirmação"}
  ],
  "sources": [
    {"id":"S1","kind":"zim","collection":"wikipedia_pt_all_nopic_2026-05",
     "title":"Ada Lovelace","url":"http://127.0.0.1:8080/...",
     "retrieved_at":"...","snapshot":"2026-05","locator":"seção e trecho"}
  ],
  "candidates": [], "conflicts": [], "gaps": [],
  "web_permission": "denied", "provenance":"local"
}
```

`claim` deve ser uma paráfrase **limitada ao trecho**, não nova inferência de identidade; `source_ids` apontam para texto íntegro recuperável. `FactSheet` pode estar `supported`, `partial`, `insufficient`, `ambiguous`, `conflict` ou `unavailable`. A ficha contém identidade de candidato e categoria quando justificadas por evidência; em `ambiguous`, oferece A/B com título, categoria e fonte; sem candidatos confirmados, não inventa nomes plausíveis. Para nome possivelmente inexistente usar `insufficient`, sem afirmar inexistência.

**Um turno, um snapshot:** preparar uma vez antes de `AgentRouter`/gerações; agrupar recuperação lexical + memória pertinente + opcional web com limites; calcular fingerprint da consulta, escopos e fontes. Todos recebem os **mesmos `facts/sources/status`**, mesmo que cada um tenha memória **relacional** de tom ou preferências individuais. Memória pessoal que influencia afirmações factuais também deve entrar na ficha, com proveniência, para evitar evidências divergentes entre agentes.

**Grupo com ficha vazia:** o sistema mostra *uma única indicação neutra* de falta de fonte; os agentes podem comentar com perspectivas breves **sem inventar fatos nem repetir duas vezes a recusa**. Para uma pergunta apenas factual, apresentação neutra direta é preferível a gerar duas negativas. Correções do usuário atualizam o **contexto como alegação do usuário**, invalidam a ficha anterior e provocam nova recuperação no próximo turno; não viram prova universal até confirmação.

**Fiscalização:** resposta persona pode referenciar somente IDs da ficha e separar opiniões explicitamente. Validador compara alegações com trechos e impede que se cite uma fonte incompatível; alegações relevantes sem suporte => resposta editada, pedida novamente no máximo uma vez, ou abstida. Nunca permitir que um segundo agente herde erro factual do texto do primeiro.

## 4. Quando consultar? Alternativas antes da escolha definitiva

| Política | Vantagens | Riscos/custo | Decisão nesta fase |
|---|---|---|---|
| A. Regex acumulada | Sem chamada de modelo, rápida | Lacunas “quem foi”, paráfrases, manutenção onerosa | **Não ampliar regex** como núcleo; usar regras explícitas só para comandos/intenção inequívoca. |
| B. Tool calling autônomo pelo LLM | Flexível para formulações novas | Pode deixar de consultar ou chamar web sem permissão; 1+ turnos LLM, maior latência/VRAM do modelo carregado | **Experimento controlado** com schema restrito, primeiro local, nunca ferramenta web sem opt-in do sistema. |
| C. Toda pergunta factual consulta primeiro | Simples, previsível, reduz bypass; consulta local rápida | Pode consultar demais e gerar respostas lentas | **Preferência provisória**, usando classificador determinístico de “possível factual” com *fail-open para consulta local*; conversa social simples não exige busca. |
| D. Recuperar local para toda mensagem | Máxima cobertura de possíveis factos | Maior ruído e risco de expor memória irrelevante | Não escolher sem medição. |

**Experimento obrigatório na Fase 3:** 50 perguntas e paráfrases, modos offline e online, comparar **qwen3.5:9b e gemma3:12b** com mesmo prompt, mesmo ZIM e mesmas permissões em A/B/C, avaliando consultas perdidas, identidades inventadas, custo de chamadas e p50/p95 de primeira resposta **segura**, não apenas primeiro token. Critério: priorizar **0 invenções no conjunto**, maior cobertura offline com evidência, menos recusas indevidas; desempate por latência. Se ferramenta nunca é chamada para pergunta factual, B perde. Nenhuma arquitetura deve confiar na autoclassificação da persona para autorizar internet.

**Falhas:** timeouts não transformam `unavailable` em `insufficient` (fonte fora do ar ≠ fonte inexistente); reter nível de evidência e texto parcial auditável; informar explicitamente rede/Kiwix indisponíveis, seguir SQLite. Sem Ollama, API neutra consegue devolver trecho atribuído ou falta de fonte deterministicamente, mas **conversa livre com persona continua indisponível** — requisito de disponibilidade deve distinguir serviço do modelo.

## 5. Agentes como perfis declarativos; grupo N, sem consenso forçado

**PROPOSTA:** perfis `profiles/<id>.json`, loader genérico validado por Pydantic (já dependência do projeto); **nenhuma alteração de código para criar o quarto ou quinto perfil após a implantação**. A migração inicial substitui os hardcodes identificados na Fase 1, preservando IDs `morgana`/`todd` e preferências legadas. Campos: `schema_version`, `id`, `name`, `aliases`, `persona.identity`, `tone`, `analysis_angle`, `empathy`, `interests`, `prompt_rules`, `tool_allowlist`, `memory.shared_read`, `memory.private_namespace`, `memory.private_write`, `tts.voice_id` (reservado, ignorado agora), `is_default`.

- **Permissões:** permitido ao agente = perfil.allowlist ∩ política global de ferramenta ∩ autorização do usuário ∩ sessão. Sem autorização, o perfil nunca amplia acesso. O sistema/facts tem seu próprio controle, **não pertence ao agente**.
- **Memória:** fatos compartilhados e dados declarados pelo usuário com ACL; contexto relacional individual só para ângulo/tom. Memória privada **não é prova externa** e não deve entrar em fatos compartilhados sem autorização explícita do usuário.
- **Endereçamento:** parser recebe aliases do registry; `@id`, vocativo por nome e “Campanario, ...” (sistema). Sem vocativo: sessão usa prioridade padrão configurável (Morgana na experiência padrão); modo neutro responde diretamente; “todos”/“os três” consulta registry, não lista hardcoded.
- **Participação:** `single(id)` = só id; `selected(ids)` = conjunto explícito; `all` = todos elegíveis; `automatic` = primário e outro apenas se acrescentar algo com motivo; `system` = nenhum agente. **Default: uma fala por agente selecionado e até 2 falas no total no automático**; modo all obedece teto configurável e recusa/exibe resumo de participação quando excedido. Sem rodadas de followup infinitas. Nunca há uma síntese do Campanario quando o usuário não pediu.
- **Sequência:** gerações **sequenciais** do mesmo modelo para manter VRAM e ficha constante; na segunda geração, textos anteriores de agente são contexto social e opiniões marcadas, **não fonte**. O segundo não incorpora fatos não registrados na ficha. Correção feita por usuário vale para os participantes a partir de nova ficha.
- **Migração de persona:** retirar todo `agent_id == 'todd'` e strings fixas de `chat/knowledge.py`; mover `natural_uncertainty` e `sourced_definition_answer` para versão factual *neutra* (`status`, candidatos, trechos) e deixar `tone/style` em perfis/apresentadores. Revisar `agents/router.py`, `addressing.py`, `participation.py`, `personality_application.py`, `output.py`, `profiles.py`, `chat/prompts.py` e outros acoplamentos da matriz Fase 1; não tocar em migrations históricas. Se uma frase de persona aparecer em fatos/fontes, a regra falhou.

**Exemplo de terceiro perfil de teste** (será criado na Fase 3 como fixture de teste, **não nesta fase**):

```json
{"schema_version":1,"id":"analista_teste","name":"Analista Teste",
 "aliases":["analista teste"],
 "persona":{"identity":"Analista local de abordagem didática","tone":"claro e cordial",
            "analysis_angle":"explica alternativas","empathy":"respeitoso",
            "interests":["ciência"],"prompt_rules":[]},
 "tool_allowlist":[],
 "memory":{"shared_read":true,"private_namespace":"analista_teste","private_write":false},
 "tts":{"voice_id":null},"is_default":false}
```

**Não é um perfil funcional no projeto atual:** o exemplo especifica o contrato que a Fase 4 deverá implementar. Todd e Morgana têm empatia e análise em comum, com ângulos distintos; nenhum é reduzido a “frio” vs “afetuosa”, nem a personagem ou prontuário de risco.

## 6. Internet opcional, importação e revogação

1. **Offline por padrão real no código**, não apenas no `.env`: a busca externa nasce proibida, `WEB_ALLOWED=false` na política do turno. A camada de rede aplica o veto **antes** de qualquer request; exigir opt-in explícito para cada busca externa ou autorização de sessão com revogação fácil. `/pesquisar` pode pedir confirmação, nunca desrespeita proibição explícita de web.
2. **Local insuficiente:** exibir status e opção para usuário solicitar internet, se permitida. Resultados externos aparecem atribuidos, com `retrieved_at`, URL, texto lido e estado de sucesso/erro; opcionalmente entrar na mesma ficha do turno seguinte quando autorizado. SearXNG local não significa conteúdo offline.
3. **Persistência em biblioteca:** `web.save`/importação da fonte só por ação explícita do usuário; salvar em staging, mostrar origem/licença, hash e resumo, exigir confirmação e então importar. **Cache transitório de sessão ≠ incorporação permanente.** Desligar cache Meili autoindexador ou exigir conformidade com consentimento.
4. **Sem rede:** nenhuma consulta web ocorre; se ela cai depois de autorização, marcar `network_error`, manter as evidências locais já coletadas, não inventar e não iniciar retries indefinidos. Nunca comprometer inicialização, chat local ou leitura de arquivos por indisponibilidade web.

## 7. Hardware e custo (informação externa x hipóteses)

| Item | Evidência verificável | Previsão operacional / decisão |
|---|---|---|
| RTX 5060 Ti 16 GB | Hardware fornecido pelo usuário; execução local nesta GPU **não medida** | Usar **um modelo quantizado por vez**, 1 geração em andamento; VRAM de KV + runtime e drivers não incluída no tamanho do download. |
| Qwen3.5 9B | Catálogo Ollama consultado: `qwen3.5:9b` aproximadamente **6,6–7,6 GB** conforme tag/variante | Baseline do `.env.example`, não considerar gratuito rodar em paralelo com Gemma/embeddinggemma. |
| Gemma3 12B Q4_K_M | Catálogo Ollama: `gemma3:12b` **8,2 GB** (pesos/distribuição) | Comparar factualidade e latência, sem promessa de qualidade. Ambas as versões quantizadas parecem caber como pesos na 16 GB, mas **a utilização real total não foi medida**. |
| Contexto | `CAMPANARIO_MODEL_CONTEXT_WINDOW=4096` no pacote; Ollama pode configurar `num_ctx` | Testar 4096 vs 8192 com orçamento de contexto/truncamento explícito; maior janela aumenta memória e pode mudar velocidade. Nunca corrigir fonte ausente com contexto maior. |
| Dois/N agentes | Mesmo modelo local chamado repetidamente | Latência final tende a crescer com número de respostas; **não carrega dois modelos distintos se ambos usam o mesmo tag**. Paralelismo aumenta KV/VRAM e não é padrão antes de medir. |
| FTS5/Kiwix local | CPU + armazenamento e servidor local | Consultas locais devem custar menos que chamada gerativa extra, mas tempo p50/p95 é **hipótese**, mede-se no Windows. |
| Tool calling | Ollama suporta ferramentas em modelos compatíveis, mas integração atual não foi validada com os tags citados | Chamada adicional pode dobrar número de passes de LLM para algumas perguntas; política C tende a menor latência quando consulta FTS/ZIM é rápida. |

**Instrumentação mínima Fase 3:** `nvidia-smi`, `ollama ps`, versão/tag/hash/modelo, `num_ctx`, `prompt_eval_count`, `eval_count`, `load_duration`, `prompt_eval_duration`, `eval_duration`, p50/p95/timeout de recuperação, latência até primeira **resposta segura** e total para 1/2/N agentes. Definir orçamentos: fonte/trechos + prompt do sistema + histórico + saída **menores ou iguais a `num_ctx`**, com truncamento explícito de trechos menos relevantes (nunca da citação escolhida). Modelos não serão baixados automaticamente nem alterados na fase 2.

## 8. Decisões provisórias, alternativas descartadas e condições de aprovação

**Recomendado para teste:** biblioteca FTS5; Kiwix-serve/ZIM opcional e local; `FactService` independente; consulta factual local por padrão; ficha factual única por turno; dois agentes sequenciais sobre mesma ficha; perfis JSON por registry; sem agente por API; internet com opt-in; falhas com abstinência. **Não é autorização para implementar:** a Fase 3 deve fixar benchmark e baseline primeiro.

**Descartado nesta rodada:** copiar Wikipedia inteira para outro banco/índice, depender de Meilisearch para conhecimento, tratar texto de agente como prova, usar web automaticamente por falta de `.env`, adicionar regex v3.3 em lugar do serviço factual, carregar simultaneamente dois LLMs para o mesmo turno, autoaprender da internet sem consentimento, transformar toda conversa em debate, forçar síntese.

**Trade-off central:** um portão estrito de fatos produz mais **abstinência honesta** quando a base não cobre um tema. A cobertura melhora **instalando conhecimento real**, não enfraquecendo evidências. Zero identidades inventadas é **meta de avaliação em conjunto finito**, não garantia universal inferível de um prompt.

**Pendências antes da execução:** 1) Fase 3 define corpus e evidências de ouro; 2) medir Windows/Python 3.12/Qwen/Gemma; 3) confirmar que a instalação local contém ou receberá os ZIM/modelos manualmente; 4) usuário deve fazer backup antes de migrações, preservar `utilidades.sqlite3`, `campanario.db`, `.env` e Ollama; 5) projeto anexo não inclui o conceito v2.2 solicitado, só v2.0.

## 9. Referências rastreáveis

**Internas:** `docs/current/AGENT_ARCHITECTURE.md`; `docs/reference/Projeto_Campanario_v2.0_Documento_de_Conceito.docx`; Fase 1 (`FASE1_AUDITORIA_CAMPANARIO.md`, `FASE1_RISCOS_CAMPANARIO.md`, provas offline e log pytest); funções e caminhos citados acima.

**Externas (consultadas para desenho; não são dependências de runtime):**

- Catálogo ZIM com arquivos e tamanhos PT, snapshot observado: https://lb.download.kiwix.org/zim/wikipedia/ ; formato mini/nopic/maxi: https://get.kiwix.org/en/solutions/catalog/
- Servidor local Kiwix e busca nos ZIM: https://github.com/kiwix/kiwix-tools/blob/main/docs/kiwix-serve.rst
- Qwen3.5 9B Ollama: https://ollama.com/library/qwen3.5:9b ; Gemma3 12B Ollama: https://ollama.com/library/gemma3:12b
- Contexto, `ollama ps` e paralelismo/memória: https://docs.ollama.com/faq

**Ao fim da Fase 2:** nenhuma linha de produção modificada; o desenho pode ser aprovado, recusado ou ajustado sem efeitos no sistema existente.
