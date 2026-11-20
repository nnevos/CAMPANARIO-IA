# Fase 1 — Matriz de riscos (SEM correcoes aplicadas)

| Prioridade | Risco e fato verificavel | Consequencia | Evidencia |
|---|---|---|---|
| **P0** | Biblioteca offline nao alimenta automaticamente o chat factual | Recusa mesmo com resposta em documento local; conhecimento externo nao funciona offline | `utilities/service.py:181-215`; `chat/service.py:776-903`; `provas_offline.txt`; `prova_runtime_sem_ollama.txt` |
| **P0** | Testes mostram inferencias pessoais indevidas emitidas/persistidas | Informacoes falsas podem tornar-se historico | 9 falhas `test_g2_grounding_audit.py`; log suite |
| **P0** | Nao ha chat neutro, e terceiro agente nao e extensivel apenas por perfil | Viola exigencia de sistema independente de persona e N agentes | `chat/service.py:109-119,953-954`; `agents/personality_application.py:41-50`; `prova_runtime_sem_ollama.txt` |
| **P1** | Nenhuma ficha local/memoria/web unica por turno | Divergencia potencial de evidencia; repeticao de recusas em grupo | `chat/service.py:279-317,776-903,1029,1058-1084`; `prova_grupo_offline.txt` |
| **P1** | Condicoes de `web_intent` nao cobrem todas as formulacoes | Geracao sem consulta/grounding e risco de inventar | `utilities/web_intent.py:135-165`; `provas_offline.txt` |
| **P1** | `Settings` padrao habilita web automatica se `.env` ausente, mas `.env.example` desabilita | Saida para web nao intencional em instalacao sem configuracao | `config.py:35-36` vs `.env.example:22`; prova via import `Settings(_env_file=None)` |
| **P1** | Modo compacto contorna verificacao completa de proveniencia e `ResponseContractPipeline` | Regressoes factuais podem passar por verificacoes menos fortes | `composition.py:55-61`; `chat/behavior.py:45-54` |
| **P1** | Suíte falha 30/685 (ambiente fora da faixa declarada) | Nao homologado; nao assumir stubs como unica causa | `pytest_suite_completa.log`, `pyproject.toml:6` |
| **P1** | Camada de fatos ramifica por Todd/Morgana | Nao ha ficha de fatos neutra e nova persona exige alterar factualidade | `chat/knowledge.py:246-329` |
| **P2** | Web + Meili sao cache de paginas lidas, nao acervo offline verificado; opt-in do Meili indexa automaticamente | Confusao entre cache e conhecimento autorizado/permanente | `utilities/web_chat.py:51-65,343-360`, `utilities/web_research.py:360-372` |
| **P2** | Pesquisa Wikipedia/buscadores depende de endpoints publicos e validacoes por regex/titulo | Recusas indevidas/instabilidade quando rede cai ou bloqueia | `web_research.py:104-156,247-318`; `web_chat.py:385-419`; falhas da suite |
| **P2** | Janela 4096 e prompts podem exceder capacidade; evidencias apenas diagnosticas | Truncamento/incoerencia possiveis, **nao confirmados** | `.env.example:5`; `model/adapters/ollama.py:42-68,128-146` |
| **P2** | Documento v2.2 nao consta no ZIP (so v2.0) | Requisitos conceituais podem divergir | `docs/reference/Projeto_Campanario_v2.0_Documento_de_Conceito.docx` |

**Nao desativar para esconder falhas:** memoria, biblioteca, permissoes, auditoria de fontes e persistencia. **Sem alteracoes aplicadas nesta fase.**
