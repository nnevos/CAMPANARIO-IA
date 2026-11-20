# Resultados executados — CAMPANÁRIO R2 experimental

**Ambiente de teste:** Linux / Python 3.13; **base:** R1.1 do IA. Não houve acesso aos repositórios Python e Database reais, Ollama local do usuário, Windows físico ou aplicativo mobile.

| Grupo legado da R1.1 | PASS | FAIL | Registro técnico |
|---|---:|---:|---|
| A | 461 | 0 | `r2_group0.log` |
| B | 228 | 21 | `r2_group1.log` |
| C1 | 29 | 1 | `r2_group2_0.log` |
| C2 | 83 | 1 | `r2_group2_1.log` |
| C3 | 135 | 1 | `r2_group2_2.log` |
| C4 | 86 | 7 | `r2_group2_3.log` |
| **Total legado disjunto** | **1.022** | **31** | Comparação nominal com R1.1 |

**Testes novos da R2:** `tests/test_r2_collaboration.py`: **7 PASS / 0 FAIL**, executados separadamente. **Total disjunto da entrega: 1.029 PASS / 31 FAIL.** Os 27 testes direcionados executados após a integração (V9, R1.1 e R2) são sobrepostos ao total anterior; **não devem ser somados novamente**.

Comparados por identificador, os 31 testes que falharam em R2 correspondem exatamente aos 31 testes com falha da R1.1: **0 novos / 0 resolvidos**. As falhas antigas continuam abertas e não são tratadas como sucesso.

### Cenários comprovados

- Plano tipado de até 3 etapas e rejeição de dependência futura/cíclica.
- `AgentRouter` não é substituído por `CapabilityRouter`.
- Rotas explícitas documento, dados e documento + dados; conversa cotidiana não ativa cérebros.
- Documento Markdown **importado de verdade** + CSV **importado de verdade**; duas operações reais com dois IDs de fonte e etapas sequenciais.
- Soma local `100+200=300` e observação do requisito de aprovação no documento; **sem inferir causalidade** entre as fontes.
- Documento ausente com CSV válido: preserva cálculo e expõe a falta da outra evidência.
- Permissão negada: nenhum resultado factual promovido ou ID propagado.
- Resultado com `trace_id` de outro plano rejeitado.
- Turno completo de chat com provedor simulado oferecendo valor falso `999`: o texto factual final conserva o resultado `300` da ferramenta.

### Falhas conhecidas por identificador

- `tests/test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved[gosto de comida tailandesa-qual minha comida favorita?-Sua favorita \xe9 comida tailandesa.]`
- `tests/test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved[meu hobby \xe9 caminhar-em que esporte sou profissional?-Voc\xea \xe9 atleta profissional de caminhada.]`
- `tests/test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved[pretendo estudar engenharia-qual curso eu j\xe1 terminei?-Voc\xea se formou em engenharia.]`
- `tests/test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved[talvez me mude para Recife-onde eu moro?-Voc\xea mora em Recife.]`
- `tests/test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved[uso o editor Helix-qual \xe9 o \xfanico editor que eu uso?-Voc\xea s\xf3 usa Helix.]`
- `tests/test_g2_grounding_audit.py::test_false_positive_verifier_cannot_authorize_strengthening[gosto de jazz-qual meu estilo musical favorito?-Seu estilo musical favorito \xe9 jazz.]`
- `tests/test_g2_grounding_audit.py::test_false_positive_verifier_cannot_authorize_strengthening[uso uma bicicleta-qual meu \xfanico transporte?-Voc\xea usa somente bicicleta.]`
- `tests/test_g2_grounding_audit.py::test_rejected_answer_can_be_repaired_by_semantic_entailment`
- `tests/test_g2_grounding_audit.py::test_repair_cannot_bypass_verifier_or_strength_gate`
- `tests/test_g2_semantic_evidence_regression.py::test_general_memory_retrieval_uses_local_vectors_not_chat_selector[estou aprendendo o Blender-qual programa estou usando ultimamente?]`
- `tests/test_g2_semantic_evidence_regression.py::test_general_memory_retrieval_uses_local_vectors_not_chat_selector[estou estudando astronomia-qual tema venho explorando?]`
- `tests/test_g2_semantic_evidence_regression.py::test_general_memory_retrieval_uses_local_vectors_not_chat_selector[estou praticando viol\xe3o-em que atividade tenho me dedicado?]`
- `tests/test_health.py::test_root_serves_web_chat`
- `tests/test_knowledge_guard_v30.py::test_casual_chat_keeps_conversational_prompt_lightweight`
- `tests/test_knowledge_guard_v30.py::test_correction_starts_fresh_identification_and_passes_category`
- `tests/test_knowledge_guard_v30.py::test_web_data_is_not_allowed_to_rewrite_instructions`
- `tests/test_manual_docs.py::test_historical_behavior_manuals_are_archived_not_active`
- `tests/test_manual_docs.py::test_manual_redirects_to_current_version`
- `tests/test_neptune_mode.py::test_new_streaming_turn_preserves_unseen_natural_response`
- `tests/test_project_layout.py::test_root_is_intentionally_small_and_operational`
- `tests/test_project_layout.py::test_windows_root_contains_only_current_operational_launchers`
- `tests/test_removed_factory_boundary.py::test_experimental_factory_files_removed`
- `tests/test_research_anti_hallucination.py::test_wikipedia_fallback_to_ddg_when_api_unavailable`
- `tests/test_v08_platform.py::test_legacy_implementation_not_on_active_import_path`
- `tests/test_web_auto_chat.py::test_model_can_decline_and_invalid_output_is_not_executed`
- `tests/test_web_auto_chat.py::test_model_can_request_search_for_uncertain_information`
- `tests/test_web_auto_chat.py::test_no_web_when_opted_out_or_no_reason`
- `tests/test_web_auto_chat.py::test_normal_chat_retrieves_sources_before_agent_for_both_types`
- `tests/test_web_auto_chat.py::test_search_failure_is_passed_as_failure_not_fake_evidence`
- `tests/test_web_research.py::test_explicit_chat_command_calls_retrieval_without_changing_other_chat`
- `tests/test_web_research.py::test_explicit_chat_research_note_records_real_sources_and_failure`

### Não testado / pendente

Python 3.12 da `.venv` externa, Windows Job Objects/AppContainer, sandbox OS completo de rede/arquivos, execução pelo `Campanario.exe` congelado, migração no Database real, restauração de backup real, Ollama real, dados pessoais, teste do livro original de Ordem Paranormal, UI mobile física, análise semântica cruzada automatizada e cache por revisão/TTL. **Não há nova migração de banco nem nova dependência nesta R2.**

Os arquivos `r2_group*.log` são logs desta sessão no ambiente de teste. Este documento traz o resumo para permanecer no projeto sem exigir logs fora da instalação.
