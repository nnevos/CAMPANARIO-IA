# P0 - evidencias da suite de testes (19/11/2026)

- Ambiente: container Linux/Python 3.13, nao Windows 3.12; nao houve acesso ao Ollama do usuario.
- Base anterior documentada V9+V9.1: 1004 aprovados, 31 falhas historicas.
- P0 final: `python -m pytest -q` -> **1011 aprovados, 31 falhas, 18 warnings** (status 1 pelas falhas historicas).
- IDs das 31 falhas P0: **identicos ao registro V9 integrado**; nenhuma nova falha por nome.
- Suite direcionada final: `python -m pytest -q tests/test_p0_three_folders.py tests/test_interaction_library.py tests/test_fase4_tres_pastas.py tests/test_ambiente_python_unificado.py tests/test_v9_brains.py tests/test_v91_expression.py` -> **53 aprovados, 4 warnings**.
- Sintaxe JS: `node --check src/campanario/web/ferramentas.js` -> aprovado.
- Compilacao: `python -m compileall -q src/campanario/brains tests/test_p0_three_folders.py` -> aprovado.

## IDs exatos das falhas herdadas (nao suprimidas)

```text
FAILED tests/test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved[gosto de comida tailandesa-qual minha comida favorita?-Sua favorita \xe9 comida tailandesa.]
FAILED tests/test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved[meu hobby \xe9 caminhar-em que esporte sou profissional?-Voc\xea \xe9 atleta profissional de caminhada.]
FAILED tests/test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved[pretendo estudar engenharia-qual curso eu j\xe1 terminei?-Voc\xea se formou em engenharia.]
FAILED tests/test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved[talvez me mude para Recife-onde eu moro?-Voc\xea mora em Recife.]
FAILED tests/test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved[uso o editor Helix-qual \xe9 o \xfanico editor que eu uso?-Voc\xea s\xf3 usa Helix.]
FAILED tests/test_g2_grounding_audit.py::test_false_positive_verifier_cannot_authorize_strengthening[gosto de jazz-qual meu estilo musical favorito?-Seu estilo musical favorito \xe9 jazz.]
FAILED tests/test_g2_grounding_audit.py::test_false_positive_verifier_cannot_authorize_strengthening[uso uma bicicleta-qual meu \xfanico transporte?-Voc\xea usa somente bicicleta.]
FAILED tests/test_g2_grounding_audit.py::test_rejected_answer_can_be_repaired_by_semantic_entailment
FAILED tests/test_g2_grounding_audit.py::test_repair_cannot_bypass_verifier_or_strength_gate
FAILED tests/test_g2_semantic_evidence_regression.py::test_general_memory_retrieval_uses_local_vectors_not_chat_selector[estou aprendendo o Blender-qual programa estou usando ultimamente?]
FAILED tests/test_g2_semantic_evidence_regression.py::test_general_memory_retrieval_uses_local_vectors_not_chat_selector[estou estudando astronomia-qual tema venho explorando?]
FAILED tests/test_g2_semantic_evidence_regression.py::test_general_memory_retrieval_uses_local_vectors_not_chat_selector[estou praticando viol\xe3o-em que atividade tenho me dedicado?]
FAILED tests/test_health.py::test_root_serves_web_chat
FAILED tests/test_knowledge_guard_v30.py::test_casual_chat_keeps_conversational_prompt_lightweight
FAILED tests/test_knowledge_guard_v30.py::test_correction_starts_fresh_identification_and_passes_category
FAILED tests/test_knowledge_guard_v30.py::test_web_data_is_not_allowed_to_rewrite_instructions
FAILED tests/test_manual_docs.py::test_historical_behavior_manuals_are_archived_not_active
FAILED tests/test_manual_docs.py::test_manual_redirects_to_current_version
FAILED tests/test_neptune_mode.py::test_new_streaming_turn_preserves_unseen_natural_response
FAILED tests/test_project_layout.py::test_root_is_intentionally_small_and_operational
FAILED tests/test_project_layout.py::test_windows_root_contains_only_current_operational_launchers
FAILED tests/test_removed_factory_boundary.py::test_experimental_factory_files_removed
FAILED tests/test_research_anti_hallucination.py::test_wikipedia_fallback_to_ddg_when_api_unavailable
FAILED tests/test_v08_platform.py::test_legacy_implementation_not_on_active_import_path
FAILED tests/test_web_auto_chat.py::test_model_can_decline_and_invalid_output_is_not_executed
FAILED tests/test_web_auto_chat.py::test_model_can_request_search_for_uncertain_information
FAILED tests/test_web_auto_chat.py::test_no_web_when_opted_out_or_no_reason
FAILED tests/test_web_auto_chat.py::test_normal_chat_retrieves_sources_before_agent_for_both_types
FAILED tests/test_web_auto_chat.py::test_search_failure_is_passed_as_failure_not_fake_evidence
FAILED tests/test_web_research.py::test_explicit_chat_command_calls_retrieval_without_changing_other_chat
FAILED tests/test_web_research.py::test_explicit_chat_research_note_records_real_sources_and_failure
```

**Limites:** testes com arquivos temporarios e SQLite sintetico nao validam backup/restore, schema real, Windows, Ollama, voz ou os repositorios externos. Nenhum R0/R1 deve ser marcado integralmente concluido so por estas contagens.
