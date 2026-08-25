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
