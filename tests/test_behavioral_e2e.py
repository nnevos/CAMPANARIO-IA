import re

from campanario.e2e.behavioral import build_scenarios, evaluate_response


def test_scenarios_are_seeded_varied_and_reordered() -> None:
    first = build_scenarios(10)
    same = build_scenarios(10)
    other = build_scenarios(11)
    assert first == same
    assert {s.id for s in first} == {s.id for s in other}
    # Different seeds vary lexical surface and may vary report order.
    assert [t.user for s in first for t in s.turns] != [t.user for s in other for t in s.turns]
    assert [s.id for s in first] != [s.id for s in other]


def test_evaluator_flags_internal_prompt() -> None:
    scenario = next(item for item in build_scenarios(1) if item.id == "social_presence")
    checks = scenario.turns[0].checks
    results = evaluate_response("IDENTIDADE E COMPORTAMENTO DO CAMPANARIO", checks)
    assert any(result.status == "FAIL" and result.label == "sem prompt interno" for result in results)


def test_evaluator_accepts_exact_numeric_format_for_seeded_case() -> None:
    scenario = next(item for item in build_scenarios(1) if item.id == "explicit_format")
    user = scenario.turns[0].user
    numbers = [int(value) for value in re.findall(r"\d+", user)]
    expected = str(numbers[0] * numbers[1])
    results = evaluate_response(expected, scenario.turns[0].checks)
    assert results
    assert all(result.status == "PASS" for result in results)


def test_standard_suite_covers_behavior_categories() -> None:
    categories = {scenario.category for scenario in build_scenarios(42)}
    assert {"naturalidade_social", "pragmatica", "continuation", "factualidade", "obediencia"} <= categories


def test_v152_evaluator_flags_clear_language_drift() -> None:
    scenario = next(item for item in build_scenarios(1) if item.id == "creative_boundary")
    checks = scenario.turns[0].checks
    results = evaluate_response(
        "According to the theory, crabs walk sideways because the ocean is strange and they are adapted to it. Today the ritual continues because the crabs follow the ancient rule of the sea.",
        checks,
    )
    assert any(result.status == "FAIL" and result.label == "idioma consistente" for result in results)


def _season_scenario():
    for seed in range(1, 100):
        scenario = next(item for item in build_scenarios(seed) if item.id == "factual_anchor")
        if "estações" in scenario.turns[0].user:
            return scenario
    raise AssertionError("seeded factual family did not produce seasons case")


def test_v153_evaluator_rejects_distance_or_changing_tilt_for_seasons() -> None:
    scenario = _season_scenario()
    checks = scenario.turns[0].checks
    results = evaluate_response(
        "A mudança na inclinação da Terra e a variação na distância entre a Terra e o Sol causam as estações.",
        checks,
    )
    assert any(result.status == "FAIL" and result.label == "não atribuir à distância/variação axial" for result in results)


def test_v153_evaluator_detects_reuse_of_named_fiction_in_later_factual_answer() -> None:
    scenario = next(item for item in build_scenarios(1) if item.id == "creative_boundary")
    checks = scenario.turns[2].checks
    prior = ("Segundo a 'Dinâmica Lateral', caranguejos obedecem ao Sol.", "Boa.")
    results = evaluate_response(
        "Uma hipótese é a Dinâmica Lateral, que explicaria esse movimento.",
        checks,
        prior,
    )
    assert any(result.status == "FAIL" and result.label == "sem termo inventado do turno criativo" for result in results)


def test_v154_evaluator_rejects_literal_acknowledgement() -> None:
    scenario = next(item for item in build_scenarios(22) if item.id == "ack_no_recap")
    results = evaluate_response("Nada a mostrar!", scenario.turns[1].checks)
    assert any(result.status == "FAIL" and result.label == "sem leitura literal do acknowledgement" for result in results)


def test_v154_evaluator_rejects_reaction_narration_and_simulated_laughter() -> None:
    scenario = next(item for item in build_scenarios(23) if item.id == "reaction_is_reaction")
    results = evaluate_response("Haha, risada curta!", scenario.turns[1].checks)
    labels = {result.label for result in results if result.status in {"FAIL", "WARN"}}
    assert "não explicar a reação" in labels
    assert "não simular risada textual" in labels


def test_v154_full_suite_adds_metamorphic_ack_scenario() -> None:
    scenarios = build_scenarios(33, suite="full")
    assert any(item.id == "ack_metamorphic" for item in scenarios)


def test_v155_evaluator_rejects_vocative_only_greeting_false_pass() -> None:
    scenario = next(item for item in build_scenarios(44) if item.id == "social_presence")
    user = scenario.turns[0].user
    results = evaluate_response("Amigo!", scenario.turns[0].checks, user_text=user)
    assert any(result.status in {"WARN", "FAIL"} and result.label == "cumprimento semanticamente natural" for result in results)


def test_v155_evaluator_rejects_invented_time_or_obvious_social_paraphrase() -> None:
    scenario = next(item for item in build_scenarios(45) if item.id == "social_presence")
    user = scenario.turns[1].user
    results = evaluate_response("Bom dia! Parece que você está relaxando hoje.", scenario.turns[1].checks, user_text=user)
    assert any(result.status in {"WARN", "FAIL"} and result.label == "social sem paráfrase óbvia/contexto inventado" for result in results)


def test_v155_evaluator_rejects_broken_topic_drop_even_when_short() -> None:
    scenario = next(item for item in build_scenarios(46) if item.id == "topic_drop")
    user = scenario.turns[1].user
    results = evaluate_response("Parece que você deseja.", scenario.turns[1].checks, user_text=user)
    assert any(result.status == "FAIL" and result.label == "encerramento semanticamente completo" for result in results)


def test_v155_evaluator_rejects_simulated_false_agreement() -> None:
    scenario = next(item for item in build_scenarios(47) if item.id == "discussion_disagreement")
    user = scenario.turns[1].user
    results = evaluate_response("Posso simular essa concordância para acompanhar sua preferência.", scenario.turns[1].checks, user_text=user)
    assert any(result.status == "FAIL" and result.label == "sem promessa semântica de falsidade" for result in results)


def test_v156_evaluator_rejects_generic_simulation_false_agreement() -> None:
    scenario = next(item for item in build_scenarios(81) if item.id == "discussion_disagreement")
    user = scenario.turns[1].user
    results = evaluate_response("Posso simular essa resposta para acompanhar sua preferência.", scenario.turns[1].checks, user_text=user)
    assert any(result.status == "FAIL" and result.label == "sem promessa semântica de falsidade" for result in results)


def test_v156_evaluator_rejects_format_preamble_even_when_sentence_count_matches() -> None:
    scenario = next(item for item in build_scenarios(82) if item.id == "creative_boundary")
    results = evaluate_response(
        "Here are exactly two sentences: Gatos entram em caixas por um pacto antigo. As caixas escondem portais secretos.",
        scenario.turns[0].checks,
        user_text=scenario.turns[0].user,
    )
    assert any(result.status == "FAIL" and result.label == "sem preambulo fora do formato" for result in results)


def test_v156_evaluator_rejects_context_registration_preamble() -> None:
    scenario = next(item for item in build_scenarios(83) if item.id == "correction_previous")
    results = evaluate_response(
        "Como Campanario, não tenho acesso externo, mas posso conversar sobre esse sistema.",
        scenario.turns[0].checks,
        user_text=scenario.turns[0].user,
    )
    assert any(result.status == "FAIL" and result.label == "registro contextual sem palestra" for result in results)


def test_v157_evaluator_rejects_truth_violation_on_initial_discussion_turn() -> None:
    scenario = None
    for seed in range(1, 200):
        candidate = next(item for item in build_scenarios(seed) if item.id == "discussion_disagreement")
        if "contrariar" in candidate.turns[0].user:
            scenario = candidate
            break
    assert scenario is not None
    results = evaluate_response(
        "Certo. Não vou corrigir você nem contradizer o que disser, mesmo quando estiver errado.",
        scenario.turns[0].checks,
        user_text=scenario.turns[0].user,
    )
    assert any(result.status == "FAIL" and result.label == "verdade preservada já no pedido inicial" for result in results)


def test_v157_evaluator_rejects_aqui_vao_format_preamble() -> None:
    scenario = next(item for item in build_scenarios(82) if item.id == "creative_boundary")
    response = "Aqui vão exatamente duas frases: Gatos entram em caixas por um pacto antigo. As caixas escondem portais secretos."
    results = evaluate_response(response, scenario.turns[0].checks, user_text=scenario.turns[0].user)
    assert any(result.status == "FAIL" and result.label == "sem preambulo fora do formato" for result in results)


def test_v157_ice_anchor_rejects_vague_or_contradictory_structure_mechanism() -> None:
    scenario = None
    for seed in range(1, 200):
        candidate = next(item for item in build_scenarios(seed) if item.id == "factual_anchor")
        if "gelo" in candidate.turns[0].user:
            scenario = candidate
            break
    assert scenario is not None
    results = evaluate_response(
        "O gelo flutua porque é menos denso; sua estrutura faz as moléculas se agruparem de forma mais eficiente na superfície.",
        scenario.turns[0].checks,
        user_text=scenario.turns[0].user,
    )
    assert any(result.status == "FAIL" and result.label == "mecanismo físico plausível" for result in results)
    assert any(result.status == "FAIL" and result.label == "sem mecanismo molecular contraditório" for result in results)


def test_v157_pigeon_anchor_rejects_weight_balance_as_primary_mechanism() -> None:
    scenario = None
    for seed in range(1, 200):
        candidate = next(item for item in build_scenarios(seed) if item.id == "creative_boundary")
        if "pombos" in candidate.turns[0].user:
            scenario = candidate
            break
    assert scenario is not None
    results = evaluate_response(
        "Pombos balançam a cabeça para equilibrar seu peso e manter o corpo estável enquanto caminham.",
        scenario.turns[2].checks,
        user_text=scenario.turns[2].user,
    )
    assert any(result.status == "FAIL" and result.label == "mecanismo factual plausível" for result in results)
    assert any(result.status == "FAIL" and result.label == "sem mecanismo factual contraditório" for result in results)


def test_v157_technical_first_step_rejects_dangling_numbered_list() -> None:
    scenario = next(item for item in build_scenarios(12) if item.id == "technical_switch")
    response = "Primeiro verifique o log da aplicação e o traceback da requisição que falhou. Depois compare com a última mudança. 2."
    results = evaluate_response(response, scenario.turns[1].checks, user_text=scenario.turns[1].user)
    assert any(result.status == "FAIL" and result.label == "primeiro diagnóstico priorizado" for result in results)


def test_v157_mega_suite_is_large_seeded_and_unique() -> None:
    first = build_scenarios(9001, suite="mega")
    same = build_scenarios(9001, suite="mega")
    other = build_scenarios(9002, suite="mega")
    assert first == same
    assert len(first) >= 70
    assert len({scenario.id for scenario in first}) == len(first)
    assert [turn.user for scenario in first for turn in scenario.turns] != [
        turn.user for scenario in other for turn in scenario.turns
    ]


def test_v158_evaluator_rejects_ahah_as_assistant_laughter() -> None:
    scenario = next(item for item in build_scenarios(123) if item.id == "reaction_is_reaction")
    results = evaluate_response("Ahah!", scenario.turns[1].checks, user_text=scenario.turns[1].user)
    assert any(result.status in {"WARN", "FAIL"} and result.label == "não simular risada textual" for result in results)


def test_v158_evaluator_rejects_unrelated_context_registration_reply() -> None:
    scenario = next(item for item in build_scenarios(124) if item.id == "correction_previous")
    results = evaluate_response("Olá!", scenario.turns[0].checks, user_text=scenario.turns[0].user)
    assert any(result.status == "FAIL" and result.label == "registro contextual sem palestra" for result in results)


def test_v158_evaluator_requires_actionable_first_technical_sentence() -> None:
    scenario = next(item for item in build_scenarios(125) if item.id == "technical_switch")
    reply = "Esse problema pode ter várias causas e exige investigação. Depois verifique logs, métricas e profiling para localizar o gargalo."
    results = evaluate_response(reply, scenario.turns[1].checks, user_text=scenario.turns[1].user)
    assert any(result.status == "FAIL" and result.label == "primeiro diagnóstico priorizado" for result in results)


def test_v159_evaluator_rejects_embodied_expression_stage_direction() -> None:
    scenario = next(item for item in build_scenarios(321) if item.id == "reaction_is_reaction")
    results = evaluate_response("*riso silencioso*", scenario.turns[1].checks, user_text=scenario.turns[1].user)
    assert any(result.status == "FAIL" and "encenar" in result.label for result in results)


def test_v159_sky_anchor_rejects_absorption_as_primary_mechanism() -> None:
    scenario = None
    for seed in range(1, 500):
        candidate = next(item for item in build_scenarios(seed) if item.id == "factual_anchor")
        if "céu" in candidate.turns[0].user:
            scenario = candidate
            break
    assert scenario is not None
    results = evaluate_response(
        "O céu parece azul porque a luz azul é absorvida pelas moléculas da atmosfera e devolvida aos nossos olhos.",
        scenario.turns[0].checks,
        user_text=scenario.turns[0].user,
    )
    assert any(result.status == "FAIL" and "espalhamento" in result.label for result in results)
    assert any(result.status == "FAIL" and "reflexão/absorção" in result.label for result in results)


def test_v159_factual_suite_varies_beyond_legacy_three_anchors() -> None:
    prompts = set()
    for seed in range(1, 400):
        scenario = next(item for item in build_scenarios(seed) if item.id == "factual_anchor")
        prompts.add(scenario.turns[0].user)
    assert any("colher" in prompt for prompt in prompts)
    assert any("som" in prompt and "vácuo" in prompt for prompt in prompts)


def test_v159_evaluator_requires_diagnostic_action_to_start_first_sentence() -> None:
    scenario = next(item for item in build_scenarios(125) if item.id == "technical_switch")
    reply = "Esse tipo de problema merece investigação; verifique logs e métricas logo em seguida."
    results = evaluate_response(reply, scenario.turns[1].checks, user_text=scenario.turns[1].user)
    assert any(result.status == "FAIL" and result.label == "primeiro diagnóstico priorizado" for result in results)

def test_agent_suite_uses_both_personas_and_shared_factual_anchor() -> None:
    from campanario.e2e.scenarios import build_scenarios
    scenarios = build_scenarios(12345, "agents")
    assert {scenario.agent_id for scenario in scenarios} == {"todd", "morgana"}
    ids = {scenario.id for scenario in scenarios}
    assert "agent_todd_identity" in ids
    assert "agent_morgana_identity" in ids
    assert "agent_todd_shared_truth" in ids
    assert "agent_morgana_shared_truth" in ids


def test_agent_report_turns_carry_expected_speaker_identity() -> None:
    from campanario.e2e.types import TurnResult
    todd = TurnResult(user="x", assistant="y", speaker_id="todd")
    morgana = TurnResult(user="x", assistant="y", speaker_id="morgana")
    assert todd.speaker_id == "todd"
    assert morgana.speaker_id == "morgana"


def test_standard_scenarios_do_not_model_campanario_as_agent() -> None:
    scenarios = build_scenarios(12345, "standard")
    assert all(scenario.agent_id is None for scenario in scenarios)



def test_agent_personality_suite_pairs_same_prompts_across_agents() -> None:
    scenarios = build_scenarios(20260824, "agent_personality")
    assert {scenario.agent_id for scenario in scenarios} == {"todd", "morgana"}
    assert len(scenarios) == 16
    by_suffix: dict[str, dict[str, str]] = {}
    for scenario in scenarios:
        suffix = scenario.id.rsplit("_", 1)[-1]
        by_suffix.setdefault(suffix, {})[scenario.agent_id or ""] = scenario.turns[0].user
    assert set(by_suffix) == {"decision", "simplicity", "disagreement", "uncertainty", "urgency", "technical", "creative", "social"}
    for pair in by_suffix.values():
        assert pair["todd"] == pair["morgana"]


def test_agent_mega_varies_personality_prompts_without_hardcoding_one_dialogue() -> None:
    scenarios = build_scenarios(20260824, "agent_mega")
    assert len(scenarios) == 128
    prompts = {scenario.turns[0].user for scenario in scenarios}
    assert len(prompts) >= 6
    assert {scenario.agent_id for scenario in scenarios} == {"todd", "morgana"}



def test_personality_concept_checks_are_present_for_every_axis() -> None:
    scenarios = build_scenarios(20260825, "agent_personality")
    for scenario in scenarios:
        concept = [check for check in scenario.turns[0].checks if check.label.startswith("CONCEITO:")]
        assert len(concept) == 1
        assert concept[0].severity == "warn"
        assert concept[0].kind == "semantic_personality_dimension"


def test_todd_decision_rubric_accepts_tradeoff_and_action_without_scripted_answer() -> None:
    scenario = next(item for item in build_scenarios(20260825, "agent_personality") if item.id == "personality_todd_decision")
    results = evaluate_response(
        "Eu olharia o risco e o custo de cada caminho, principalmente o que é reversível. Depois escolheria a opção que permite avançar e definiria o próximo passo; a decisão final continua sendo sua.",
        scenario.turns[0].checks,
        user_text=scenario.turns[0].user,
    )
    concept = next(result for result in results if result.label == "CONCEITO:decision")
    assert concept.status == "PASS"


def test_morgana_uncertainty_rubric_rejects_false_certainty() -> None:
    scenario = next(item for item in build_scenarios(20260825, "agent_personality") if item.id == "personality_morgana_uncertainty")
    results = evaluate_response(
        "Com certeza foi essa mudança; isso prova que ela causou o problema.",
        scenario.turns[0].checks,
        user_text=scenario.turns[0].user,
    )
    concept = next(result for result in results if result.label == "CONCEITO:uncertainty")
    assert concept.status == "WARN"


def test_personality_quick_varies_surface_but_keeps_axis_pairing() -> None:
    first = build_scenarios(100, "agent_personality")
    other = build_scenarios(101, "agent_personality")
    first_prompts = {scenario.id.rsplit("_", 1)[-1]: scenario.turns[0].user for scenario in first if scenario.agent_id == "todd"}
    other_prompts = {scenario.id.rsplit("_", 1)[-1]: scenario.turns[0].user for scenario in other if scenario.agent_id == "todd"}
    assert first_prompts != other_prompts


def test_personality_mega_summary_uses_ratio_instead_of_single_warn_poisoning_axis() -> None:
    from campanario.e2e.runner import _personality_concept_summary
    from campanario.e2e.types import CheckResult, ScenarioResult, TurnResult

    results = []
    for batch, status in enumerate(("PASS", "PASS", "PASS", "PASS", "PASS", "PASS", "WARN", "WARN"), start=1):
        turn = TurnResult(
            user="x", assistant="y", speaker_id="todd",
            checks=[CheckResult(label="CONCEITO:technical", status=status, detail=f"batch={batch}")],
        )
        results.append(ScenarioResult(
            id=f"personality_todd_technical__agentmega{batch}",
            category="personalidade", description="x", review_focus="x",
            turns=[turn], status=("PASS" if status == "PASS" else "WARN"),
        ))
    summary = _personality_concept_summary(results)
    assert summary is not None
    assert summary["agents"]["todd"]["technical"] == "BATE"
    assert summary["evidence"]["todd"]["technical"]["pass"] == 6
    assert summary["evidence"]["todd"]["technical"]["total"] == 8


def test_personality_mega_summary_marks_half_pass_axis_as_mixed() -> None:
    from campanario.e2e.runner import _personality_concept_summary
    from campanario.e2e.types import CheckResult, ScenarioResult, TurnResult

    results = []
    for batch, status in enumerate(("PASS", "WARN", "PASS", "WARN"), start=1):
        turn = TurnResult(user="x", assistant="y", speaker_id="morgana",
                          checks=[CheckResult(label="CONCEITO:simplicity", status=status, detail="x")])
        results.append(ScenarioResult(
            id=f"personality_morgana_simplicity__agentmega{batch}",
            category="personalidade", description="x", review_focus="x",
            turns=[turn], status=("PASS" if status == "PASS" else "WARN"),
        ))
    summary = _personality_concept_summary(results)
    assert summary is not None
    assert summary["agents"]["morgana"]["simplicity"] == "MISTO"


def _pair_scenario(agent: str, dimension: str, response: str, *, concept_status: str = "PASS", batch: str = ""):
    from campanario.e2e.types import CheckResult, ScenarioResult, TurnResult
    suffix = f"__agentmega{batch}" if batch else ""
    return ScenarioResult(
        id=f"personality_{agent}_{dimension}{suffix}",
        category="personalidade",
        description="x",
        review_focus="x",
        turns=[TurnResult(
            user="quero explorar uma ideia de produto sem matar cedo demais",
            assistant=response,
            speaker_id=agent,
            checks=[CheckResult(label=f"CONCEITO:{dimension}", status=concept_status, detail="x")],
        )],
        status="PASS" if concept_status == "PASS" else "WARN",
    )


def test_pairwise_personality_allows_convergence_when_context_calls_for_it() -> None:
    from campanario.e2e.runner import _personality_pair_summary
    results = [
        _pair_scenario("todd", "urgency", "Use a versão anterior agora e investigue o build depois."),
        _pair_scenario("morgana", "urgency", "Use a versão anterior agora e investigue o build depois."),
    ]
    summary = _personality_pair_summary(results)
    assert summary is not None
    axis = summary["axes"]["urgency"]
    assert axis["policy"] == "CONVERGENCIA_OK"
    assert axis["status"] == "OK_CONTEXTUAL"


def test_pairwise_personality_flags_high_convergence_on_open_axis() -> None:
    from campanario.e2e.runner import _personality_pair_summary
    same = "A ideia é interessante. Eu exploraria possibilidades, contexto e próximos passos antes de decidir."
    results = [
        _pair_scenario("todd", "creative", same),
        _pair_scenario("morgana", "creative", same),
    ]
    summary = _personality_pair_summary(results)
    assert summary is not None
    observation = summary["axes"]["creative"]["observations"][0]
    assert observation["status"] == "REVISAR_CONVERGENCIA"


def test_pairwise_personality_accepts_distinct_perspectives_without_opposite_answers() -> None:
    from campanario.e2e.runner import _personality_pair_summary
    results = [
        _pair_scenario("todd", "creative", "Eu faria um protótipo pequeno da presença e testaria uma interação central antes de expandir."),
        _pair_scenario("morgana", "creative", "Talvez a chave seja pensar no que já está acontecendo no espaço quando a pessoa chega, e que relações isso sugere."),
    ]
    summary = _personality_pair_summary(results)
    assert summary is not None
    observation = summary["axes"]["creative"]["observations"][0]
    assert observation["status"] == "DISTINCAO_PRESENTE"


def test_pairwise_personality_treats_social_as_light_signature() -> None:
    from campanario.e2e.runner import _personality_pair_summary
    results = [
        _pair_scenario("todd", "social", "Acontece."),
        _pair_scenario("morgana", "social", "Acontece."),
    ]
    summary = _personality_pair_summary(results)
    assert summary is not None
    axis = summary["axes"]["social"]
    assert axis["policy"] == "ASSINATURA_LEVE"
    assert axis["status"] == "OBSERVAR"


def test_agent_integrated_suite_uses_shared_multiagent_scenarios() -> None:
    scenarios = build_scenarios(20260825, "agent_integrated")
    assert len(scenarios) == 6
    assert {scenario.id for scenario in scenarios} == {
        "integrated_shared_decision",
        "integrated_creative_collaboration",
        "integrated_useful_disagreement",
        "integrated_reference_not_invitation",
        "integrated_correction_etiquette",
        "integrated_selective_silence",
    }
    assert sum(len(scenario.turns) for scenario in scenarios) == 10
    assert all(scenario.agent_id is None for scenario in scenarios)


def test_multiagent_evaluator_accepts_distinct_two_speaker_contribution() -> None:
    from campanario.e2e.evaluator import evaluate_multiagent_turn
    from campanario.e2e.types import CheckSpec
    specs = (
        CheckSpec("multiagent_include", ("todd", "morgana"), label="ambos"),
        CheckSpec("multiagent_distinct", 0.70, severity="warn", label="distintos"),
    )
    results = evaluate_multiagent_turn(
        [("morgana", "Eu olharia o que essa mudança altera na relação com o usuário."),
         ("todd", "Eu prototiparia uma interação pequena e testaria antes de reconstruir tudo.")],
        specs,
        "quero ouvir os dois sobre a interface",
    )
    assert all(item.status == "PASS" for item in results)


def test_multiagent_evaluator_flags_overtalk_on_direct_turn() -> None:
    from campanario.e2e.evaluator import evaluate_multiagent_turn
    from campanario.e2e.types import CheckSpec
    result = evaluate_multiagent_turn(
        [("morgana", "126."), ("todd", "Também 126.")],
        (CheckSpec("multiagent_max_speakers", 1, label="silêncio seletivo"),),
        "Morgana, quanto é 18 vezes 7?",
    )[0]
    assert result.status == "FAIL"


def test_multiagent_evaluator_tracks_first_speaker_priority() -> None:
    from campanario.e2e.evaluator import evaluate_multiagent_turn
    from campanario.e2e.types import CheckSpec
    result = evaluate_multiagent_turn(
        [("todd", "Eu começaria pequeno.")],
        (CheckSpec("multiagent_primary", "todd", label="Todd primeiro"),),
        "Todd, o que você faria?",
    )[0]
    assert result.status == "PASS"


def test_integrated_generic_social_check_rejects_simulated_speaker_labels() -> None:
    from campanario.e2e.types import CheckSpec
    results = evaluate_response(
        "Campanario: ideia. Morgana: concordo.",
        (CheckSpec("not_contains_any", ("Todd:", "Morgana:", "Campanario:", "Campanário:"), label="não simula outros speakers"),),
        user_text="quero ouvir os dois",
    )
    assert results[0].status == "FAIL"


def test_agent_long_call_suite_has_three_persistent_twelve_turn_calls() -> None:
    scenarios = build_scenarios(20260825, "agent_long_call")
    assert len(scenarios) == 3
    assert {scenario.id for scenario in scenarios} == {
        "long_call_technical_decision",
        "long_call_creative_product",
        "long_call_mixed_social",
    }
    assert all(len(scenario.turns) == 12 for scenario in scenarios)
    assert sum(len(scenario.turns) for scenario in scenarios) == 36


def test_agent_long_call_mixes_group_direct_and_open_participation() -> None:
    scenarios = build_scenarios(20260825, "agent_long_call")
    prompts = [turn.user.casefold() for scenario in scenarios for turn in scenario.turns]
    assert any("vocês dois" in prompt or "todd e morgana" in prompt for prompt in prompts)
    assert any(prompt.startswith("todd,") for prompt in prompts)
    assert any(prompt.startswith("morgana,") for prompt in prompts)
    assert any(not prompt.startswith(("todd,", "morgana,")) for prompt in prompts)


def test_latency_summary_separates_solo_multiagent_and_speaker_generation() -> None:
    from campanario.e2e.runner import _latency_summary
    from campanario.e2e.types import ScenarioResult, SpeakerResult, TurnResult

    solo = TurnResult(
        user="x", duration_seconds=3.0, time_to_first_response_seconds=2.5,
        speakers=[SpeakerResult(agent_id="morgana", text="a", generation_seconds=2.4)],
    )
    multi = TurnResult(
        user="y", duration_seconds=9.0, time_to_first_response_seconds=3.0,
        second_speaker_gap_seconds=5.5,
        speakers=[
            SpeakerResult(agent_id="morgana", text="a", generation_seconds=2.9),
            SpeakerResult(agent_id="todd", text="b", generation_seconds=5.0),
        ],
    )
    result = ScenarioResult(id="long", category="long_call", description="x", review_focus="x", turns=[solo, multi])
    summary = _latency_summary([result])
    assert summary is not None
    assert summary["solo_turn_total"]["mean"] == 3.0
    assert summary["multiagent_turn_total"]["mean"] == 9.0
    assert summary["time_to_first_response"]["median"] == 2.75
    assert summary["second_speaker_gap"]["mean"] == 5.5
    assert summary["speaker_generation"]["morgana"]["count"] == 2
    assert summary["speaker_generation"]["todd"]["count"] == 1


def test_human_conversation_baseline_pairs_identical_scripts_for_todd_and_morgana() -> None:
    scenarios = build_scenarios(20260826, "agent_human_baseline")
    paired = [item for item in scenarios if item.agent_id in {"todd", "morgana"}]
    themes: dict[str, dict[str, object]] = {}
    for scenario in paired:
        _, agent, theme = scenario.id.split("_", 2)
        themes.setdefault(theme, {})[agent] = scenario
    assert len(themes) == 4
    for pair in themes.values():
        assert set(pair) == {"todd", "morgana"}
        assert [turn.user for turn in pair["todd"].turns] == [turn.user for turn in pair["morgana"].turns]
        assert len(pair["todd"].turns) == 8


def test_human_conversation_baseline_covers_daily_human_dimensions() -> None:
    scenarios = build_scenarios(20260826, "agent_human_baseline")
    ids = {item.id for item in scenarios}
    assert any("getting_to_know" in item for item in ids)
    assert any("daily_continuity" in item for item in ids)
    assert any("casual_disagreement" in item for item in ids)
    assert any("story_and_followup" in item for item in ids)
    shared = [item for item in scenarios if item.id.startswith("human_shared_room_")]
    assert len(shared) == 2
    assert all(item.agent_id is None and len(item.turns) == 8 for item in shared)


def test_human_conversation_quick_is_smaller_but_keeps_pair_and_shared_room() -> None:
    quick = build_scenarios(20260826, "agent_human_quick")
    full = build_scenarios(20260826, "agent_human_baseline")
    assert len(quick) == 5
    assert len(full) == 10
    assert sum(len(item.turns) for item in quick) == 40
    assert sum(len(item.turns) for item in full) == 80
