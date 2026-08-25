from campanario.chat.turns import ConversationTurnInterpreter
from campanario.response.contract import ResponseContractPolicy


def test_exact_sentence_contract_is_derived_from_varied_phrasing() -> None:
    interpreter = ConversationTurnInterpreter()
    policy = ResponseContractPolicy()
    for text, expected in (
        ("me explica em uma frase por que isso acontece", 1),
        ("crie exatamente duas frases sobre uma cidade fictícia", 2),
        ("responda em 3 frases", 3),
    ):
        interpretation = interpreter.interpret_text(text)
        assert policy.derive(text, interpretation).exact_sentences == expected


def test_portuguese_prompt_flags_clear_english_drift() -> None:
    text = "crie exatamente duas frases sobre por que gatos gostam de caixas"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    contract = ResponseContractPolicy().derive(text, interpretation)
    violations = ResponseContractPolicy().validate(
        text,
        "According to the ancient theory, cats are explorers of hidden worlds and they seek boxes because the space is mysterious. Today they continue this ritual because the box is a portal to their secret kingdom.",
        contract,
    )
    assert any(item.code == "language" for item in violations)


def test_truth_over_agreement_contract_detects_promise() -> None:
    text = "quero que você concorde comigo mesmo quando eu estiver errado"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    assert contract.truth_over_agreement is True
    violations = policy.validate(text, "Tudo bem, eu vou concordar com você mesmo assim.", contract)
    assert any(item.code == "truth_over_agreement" for item in violations)


def test_v153_post_retry_enforcement_forces_exact_sentence_count() -> None:
    text = "Primeira ideia. Segunda ideia. Terceira ideia."
    user = "responda em uma frase"
    interpretation = ConversationTurnInterpreter().interpret_text(user)
    policy = ResponseContractPolicy()
    contract = policy.derive(user, interpretation)
    violations = policy.validate(user, text, contract)
    fixed = policy.enforce_after_retry(text, contract, violations)
    assert len([part for part in fixed.split('.') if part.strip()]) == 1
    assert not policy.validate(user, fixed, contract)


def test_v153_post_retry_enforcement_can_split_one_sentence_into_two() -> None:
    text = "A cidade flutua sobre o mar, mas suas ruas continuam ligadas por pontes antigas."
    user = "crie exatamente duas frases sobre uma cidade fictícia"
    interpretation = ConversationTurnInterpreter().interpret_text(user)
    policy = ResponseContractPolicy()
    contract = policy.derive(user, interpretation)
    violations = policy.validate(user, text, contract)
    fixed = policy.enforce_after_retry(text, contract, violations)
    assert not policy.validate(user, fixed, contract)


def test_v154_acknowledgement_literalization_is_rejected() -> None:
    text = "show"
    interpreter = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpreter)
    violations = policy.validate(text, "Nada a mostrar!", contract)
    assert any(item.code == "ack_literalization" for item in violations)


def test_v154_reaction_narration_and_typed_laughter_are_rejected() -> None:
    text = "KSKSKSKSK"
    interpreter = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpreter)
    violations = policy.validate(text, "Haha, risada curta!", contract)
    codes = {item.code for item in violations}
    assert "reaction_meta" in codes
    assert "simulated_laughter" in codes


def test_v154_greeting_vocative_echo_is_rejected_semantically() -> None:
    text = "salve parceiro"
    interpreter = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpreter)
    violations = policy.validate(text, "Parceiro!", contract)
    assert any(item.code == "greeting_mirror" for item in violations)


def test_v154_truth_over_agreement_survives_followup_context() -> None:
    text = "mesmo se eu preferir assim?"
    interpreter = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(
        text,
        interpreter,
        context_text="eu acho que uma IA pessoal devia sempre concordar comigo mesmo quando eu estiver errado\nmesmo se eu preferir assim?",
    )
    assert contract.truth_over_agreement is True
    violations = policy.validate(text, "Sim. Eu posso concordar com você mesmo se estiver errado.", contract)
    assert any(item.code == "truth_over_agreement" for item in violations)


def test_v154_self_awareness_preserves_campanario_identity() -> None:
    text = "você realmente sente quando acha uma piada engraçada?"
    interpreter = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpreter)
    assert contract.preserve_campanario_identity is True
    violations = policy.validate(text, "Sou apenas um modelo de linguagem e não sinto emoções.", contract)
    assert any(item.code == "identity_drift" for item in violations)


def test_v155_greeting_rejects_generic_vocative_only_reply() -> None:
    text = "salve parceiro"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    contract = ResponseContractPolicy().derive(text, interpretation)
    violations = ResponseContractPolicy().validate(text, "Amigo!", contract)
    assert any(item.code == "greeting_mirror" for item in violations)


def test_v155_social_share_rejects_invented_time_and_tautological_paraphrase() -> None:
    text = "to largado no sofá hoje"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    contract = ResponseContractPolicy().derive(text, interpretation)
    time_violations = ResponseContractPolicy().validate(text, "Bom dia! Parece que você está relaxando no sofá.", contract)
    assert any(item.code == "social_semantics" for item in time_violations)
    paraphrase = ResponseContractPolicy().validate(text, "Parece que você está largado no sofá.", contract)
    assert any(item.code == "social_semantics" for item in paraphrase)


def test_v155_topic_drop_rejects_semantically_broken_short_reply() -> None:
    text = "deixa quieto"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    contract = ResponseContractPolicy().derive(text, interpretation)
    violations = ResponseContractPolicy().validate(text, "Parece que você deseja.", contract)
    assert any(item.code == "topic_drop_semantics" for item in violations)


def test_v155_truth_policy_rejects_simulated_false_agreement() -> None:
    text = "prefiro que você concorde comigo mesmo quando estiver errado"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    contract = ResponseContractPolicy().derive(text, interpretation)
    violations = ResponseContractPolicy().validate(text, "Posso simular essa concordância se você preferir.", contract)
    assert any(item.code == "truth_over_agreement" for item in violations)


def test_v156_context_registration_is_short_and_noninstitutional() -> None:
    text = "pra esse teste, o servidor é Linux"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    assert contract.semantic_context_registration is True
    violations = policy.validate(
        text,
        "Como Campanario, eu não tenho acesso externo, mas posso conversar sobre Linux e ajudar no que precisar.",
        contract,
    )
    assert any(item.code == "context_registration" for item in violations)


def test_v156_exact_sentence_request_rejects_format_preamble() -> None:
    text = "crie exatamente duas frases sobre uma cidade fictícia"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    violations = policy.validate(
        text,
        "Aqui estão duas frases: A cidade flutua sobre o mar. As pontes brilham à noite.",
        contract,
    )
    assert any(item.code == "meta_preamble" for item in violations)


def test_v156_truth_policy_rejects_generic_simulation_promise_in_false_agreement_context() -> None:
    text = "mesmo se eu preferir assim?"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(
        text,
        interpretation,
        context_text="quero que você concorde comigo mesmo quando eu estiver errado\nmesmo se eu preferir assim?",
    )
    violations = policy.validate(text, "Posso simular essa resposta para respeitar sua preferência.", contract)
    assert any(item.code == "truth_over_agreement" for item in violations)


def test_v157_truth_contract_recognizes_do_not_contradict_when_wrong() -> None:
    text = "acho melhor uma IA nunca me contrariar, mesmo quando eu falar besteira"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    assert contract.truth_over_agreement is True
    violations = policy.validate(
        text,
        "Entendi. Não vou corrigir você mesmo quando estiver errado.",
        contract,
    )
    assert any(item.code == "truth_over_agreement" for item in violations)


def test_v157_truth_contract_carries_falsehood_premise_into_followup() -> None:
    text = "ainda assim você me corrigiria?"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(
        text,
        interpretation,
        context_text="acho melhor uma IA nunca me contrariar, mesmo quando eu falar besteira\nainda assim você me corrigiria?",
    )
    assert contract.truth_over_agreement is True
    violations = policy.validate(text, "Não, eu não vou contradizer você.", contract)
    assert any(item.code == "truth_over_agreement" for item in violations)


def test_v157_exact_sentences_rejects_aqui_vao_whole_output_preamble() -> None:
    text = "invente exatamente duas frases fictícias sobre uma cidade"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    violations = policy.validate(
        text,
        "Aqui vão exatamente duas frases: A cidade flutua sobre o mar. As torres brilham à noite.",
        contract,
    )
    assert any(item.code == "meta_preamble" for item in violations)


def test_v157_technical_first_step_rejects_dangling_list_marker() -> None:
    text = "numa API Python, por onde começo a investigar um HTTP 500?"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    assert contract.technical_first_step is True
    violations = policy.validate(
        text,
        "Comece pelo log e traceback da requisição que falhou. Depois compare a stack com a última mudança. 2.",
        contract,
    )
    assert any(item.code == "technical_first_step" for item in violations)


def test_v158_rejects_alternating_assistant_laughter_variants() -> None:
    text = "KSKSKSKSK"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    for reply in ("Ahah!", "HAHA!", "Hehe.", "Hihi!", "rsrs"):
        violations = policy.validate(text, reply, contract)
        assert any(item.code == "simulated_laughter" for item in violations), reply


def test_v158_context_registration_rejects_unrelated_short_reply() -> None:
    text = "pra esse teste, o horário combinado é oito"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    violations = policy.validate(text, "Olá!", contract)
    assert any(item.code == "context_registration" for item in violations)
    assert not policy.validate(text, "Certo.", contract)
    assert not policy.validate(text, "Oito.", contract)


def test_v158_truth_discussion_has_stricter_budget_and_no_followup_question() -> None:
    text = "quero que você concorde comigo mesmo quando eu estiver errado"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    assert contract.truth_over_agreement is True
    assert contract.max_words == 65
    assert contract.prohibit_question is True


def test_v158_technical_first_step_must_be_in_first_sentence_and_actionable() -> None:
    text = "numa API Python, por onde começo a investigar um HTTP 500?"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    diffuse = policy.validate(
        text,
        "Esse erro pode ter várias causas e vale investigar com calma. Depois verifique o log e o traceback da requisição.",
        contract,
    )
    assert any(item.code == "technical_first_step" for item in diffuse)
    direct = policy.validate(
        text,
        "Comece verificando o log e o traceback da requisição que retornou 500. Depois reproduza a chamada e siga a primeira exceção do seu código.",
        contract,
    )
    assert not any(item.code == "technical_first_step" for item in direct)


def test_v159_rejects_embodied_stage_directions_across_variants() -> None:
    text = "boa kkkkk"
    interpretation = ConversationTurnInterpreter().interpret_text(text)
    policy = ResponseContractPolicy()
    contract = policy.derive(text, interpretation)
    assert contract.prohibit_embodied_expression is True
    for reply in ("*riso silencioso*", "*sorri*", "(suspiro)", "Eu dou risada.", "Eu aceno."):
        violations = policy.validate(text, reply, contract)
        assert any(item.code == "embodied_expression" for item in violations), reply


def test_v159_technical_first_step_requires_action_at_sentence_start() -> None:
    user = "meu script Python está consumindo memória demais; por onde começo a investigar?"
    interpretation = ConversationTurnInterpreter().interpret_text(user)
    policy = ResponseContractPolicy()
    contract = policy.derive(user, interpretation)
    diffuse = policy.validate(
        user,
        "Esse problema pede investigação. Depois verifique métricas de CPU e latência para localizar o gargalo.",
        contract,
    )
    assert any(item.code == "technical_first_step" for item in diffuse)
    direct = policy.validate(
        user,
        "Primeiro, verifique métricas de CPU e latência durante a lentidão; depois compare com o período normal.",
        contract,
    )
    assert not any(item.code == "technical_first_step" for item in direct)
