# Fase 4 — Inc.3B: identidades de codigo + calibracao de candidatos

Data da entrega: 2026-11-19. Implementacao incremental posterior ao Inc.3B e ao diagnostico de scores.

## Fontes conceituais realmente consultadas

Do arquivo `CAMPANARIO-IA.rar` enviado pelo criador:

- `docs/reference/Projeto_Campanario_v2.0_Documento_de_Conceito.docx` — o Campanario e **sistema**, modelos sao componentes, Morgana e Todd sao agentes dentro dele; principio offline/local/modular; memoria, conhecimento e personalidade sao camadas separadas. Voz, dispositivos e demais modulos descritos no conceito NAO sao automaticamente capacidades ativas.
- `docs/reference/personas/MORGANA_BACKGROUND.md` — identidade de Morgana, analise e curiosidade, nao imitar uma personagem existente.
- `docs/reference/personas/TODD_BACKGROUND.md` — identidade de Todd, estrategia e protecao sem controle, nao imitar uma personagem existente.
- `docs/current/AGENT_PERSONALITY_CONCEPT.md`, `AGENT_PERSONALITY_CORE.md` — tendencias observaveis, anti-caricaturas, core estavel e contrato compartilhado de evidencia.
- `docs/manual/16_PERSONALIDADE_E_EVOLUCAO_DOS_AGENTES.md` — experiencia persistida fica fora do PersonalityCore.
- Descricao do usuario desta conversa — quatro camadas: identidade central; preferencias; memorias individuais/compartilhadas/relacionais; comportamento contextual.

## Alteracoes reais no codigo

1. `src/campanario/identity.py`: contrato imutavel `CAMPANARIO_IDENTITY` que descreve o Campanario como orquestrador, nao agente nem LLM. `chat/prompts.py` inclui esse contrato tanto no modo compacto quanto no completo, mantendo o antigo cabecalho para compatibilidade.
2. `agents/morgana.py`, `agents/todd.py` e `agents/identity_contract.py`: identidades centrais separadas e `frozen=True`; `profiles.py` usa as identidades na renderizacao do prompt de cada agente e preserva os `PersonalityCore` preexistentes.
3. `agents/development.py`: propostas tipadas de preferencias/experiencias individuais, compartilhadas, relacionamento agente-usuario e relacionamento Morgana-Todd. **Propor nao persiste nada**; `approve(proposal, user_approved=True)` insere apenas no `ExperienceRepository` existente e `revoke(..., user_approved=True)` marca como esquecido. O servico nao e exposto ainda por API/UI; a camada de aplicacao deve autenticar uma futura aprovacao em Central de Agentes. O booleano e somente uma barreira tecnica basica, nao autenticacao suficiente.
4. `chat/service.py`: apenas notas de desenvolvimento **anteriormente aprovadas** entram no contexto do agente correto (ou nos dois, para memoria compartilhada). Nao entram na ficha factual neutra.
5. `runtime/experience.py`: notas `agent.development.*` excluidas da recuperacao geral de fatos pessoais (lexical e hibrida). Fonte administrativa nunca vira fala declarada pelo usuario.
6. `tools/eval_fase4_inc3b_calibracao.py`: benchmark sem alterar producao, com cinco perguntas parafraseadas e **12 negativos dificeis** que mencionam os MESMOS projetos documentados. Compara 0,72 e 0,50 no mesmo indice/vetores; reporta candidatos possivelmente enganosos, inclusive precedencia lexical.

## Evidencias tecnicas

- FATO: scores reais que o usuario mediu no `embeddinggemma` para os cinco trechos corretos: 0,68108; 0,69622; 0,68697; 0,66019; 0,51096; o maior candidato correto era o primeiro em 5/5.
- FATO: com limiar 0,50 o diagnostico do usuario encontrou 5/5 candidatos corretos e nenhum dos 4 negativos simples foi aceito. Isso NAO prova seguranca em perguntas negativas do mesmo assunto.
- FATO local (simulado): nos 12 negativos dificeis adicionais, a busca lexical existente retornou trechos para 8/12, mesmo sem haver no corpus a informacao perguntada. O benchmark revela a limitacao preexistente; nao a corrige artificialmente com palavras-chave.
- No ambiente Linux de teste, 107/107 testes direcionados passaram. Na suite integral: 775 passaram, 30 falharam; **as 30 falhas coincidem com as 30 do Inc.3B anterior**, sem nova falha.
- Sem Ollama local neste ambiente: a acuracia real dos 12 negativos dificeis e a latencia dos embeddings permanecem **NAO MEDIDAS**. A execucao real no Windows e obrigatoria.

## Invariantes

- Nao cria/migra banco; nenhum `.env` real e alterado; sem indice persistente novo.
- Nao muda `CAMPANARIO_LIBRARY_SEMANTIC_ENABLED` nem `library_semantic_min_similarity`, que continuam `False` e `0.72` por padrao.
- Similaridade de vetores nunca transforma candidato semantico em fato confirmado.
- Personalidades mudam perspectiva e estilo, nunca base de fatos, capacidade, ferramentas ou permissao.
- Adaptacao so mediante registro revisado, com origem, data, escopo e reversao; nenhuma conversa altera o core nem grava memoria de desenvolvimento automaticamente.
- Memorias aprovadas sao **contexto** e podem conter interpretacoes; nao sao provas de eventos externos.
- Novos agentes por perfil e UI de revisao da evolucao continuam fora deste incremento.

## Pendencias e decisao

1. Rodar `tools/eval_fase4_inc3b_calibracao.py --engine ollama --model embeddinggemma --timeout 30` no Windows e comparar numeros de candidatos dos 12 negativos dificilies com os 5 positivos.
2. So recomendar uma mudanca de limiar quando houver estrategia de verificacao de *pertinencia da resposta* para casos negativos do mesmo assunto (a propria FTS5 tambem apresenta correspondencia parcial). NAO habilitar `0.50` automaticamente.
3. Criar mais tarde a Central de Agentes para revisar propostas, corrigir/revogar memorias, inspecionar escopo e controlar autenticacao, e avaliar com Qwen real se a personalidade nao ficou caricata.
4. Ainda faltam validacoes de 0 agentes, terceiro perfil, funcionamento de Kiwix, claims sem evidencia e algumas falhas historicas.
