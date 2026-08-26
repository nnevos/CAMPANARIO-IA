from datetime import UTC, datetime
from uuid import uuid4

from campanario.chat.dialogue_state import compile_dialogue_state
from campanario.chat.models import Message, MessageRole


def _msg(session_id, role, content, agent_id=None):
    return Message(
        id=uuid4(),
        session_id=session_id,
        role=role,
        content=content,
        created_at=datetime.now(UTC),
        agent_id=agent_id,
    )


def test_dialogue_state_binds_next_step_to_architecture_without_inventing_detail() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "quero pensar num app local que já funciona; tenho três semanas para uma entrega importante"),
        _msg(sid, MessageRole.ASSISTANT, "Vamos focar no que muda o risco.", "morgana"),
        _msg(sid, MessageRole.USER, "uma parte da arquitetura me incomoda, mas ela não está quebrando"),
        _msg(sid, MessageRole.ASSISTANT, "Então não há evidência de falha ainda.", "morgana"),
        _msg(sid, MessageRole.USER, "Todd, se fosse sua decisão hoje, qual seria o próximo passo?"),
    ])
    assert state is not None
    rendered = state.render().lower()
    assert "arquitetura me incomoda" in rendered
    assert "tres semanas" in rendered or "três semanas" in rendered
    assert "nao assumir/inventar" in rendered
    assert "roteamento" in rendered
    assert "pedido a responder agora" in rendered


def test_dialogue_state_same_question_resolves_exact_prior_user_question() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "é sobre presença durante meu trabalho"),
        _msg(sid, MessageRole.USER, "Morgana, qual sinal faria você ficar quieta em vez de entrar na conversa?"),
        _msg(sid, MessageRole.ASSISTANT, "Quando eu seria redundante.", "morgana"),
        _msg(sid, MessageRole.USER, "Todd, mesma pergunta pra você, mas não repete a Morgana."),
    ])
    assert state is not None
    assert "qual sinal faria você ficar quieta" in state.resolved_request.lower()
    assert state.immediate_referent is not None
    assert "qual sinal faria você ficar quieta" in state.immediate_referent.lower()


def test_dialogue_state_aterrissa_uses_previous_agent_answer_as_referent() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "o Campanário deveria parecer um lugar onde vocês já estão"),
        _msg(sid, MessageRole.USER, "Morgana, desenvolve essa parte de presença sem virar texto abstrato demais."),
        _msg(sid, MessageRole.ASSISTANT, "Presença é familiaridade, continuidade e sinais discretos.", "morgana"),
        _msg(sid, MessageRole.USER, "Todd, aterrissa isso sem matar o conceito."),
    ])
    assert state is not None
    assert state.immediate_referent == "Presença é familiaridade, continuidade e sinais discretos."
    assert "nao" not in state.resolved_request.lower() or "pedir" not in state.resolved_request.lower()
    assert "concreta" in state.resolved_request.lower()


def test_dialogue_state_short_sequence_binds_latency_problem() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "ontem tivemos um pico de latência sem erro nos logs. Por onde vocês começariam?"),
        _msg(sid, MessageRole.ASSISTANT, "CPU, rede e dependências.", "morgana"),
        _msg(sid, MessageRole.USER, "não quero vinte hipóteses; me deem uma sequência curta."),
    ])
    assert state is not None
    assert state.immediate_referent is not None
    assert "pico de latência" in state.immediate_referent
    assert "poucos passos" in state.resolved_request


def test_dialogue_state_meta_order_keeps_previous_content_request() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "se eu tiver que cortar escopo, corto observabilidade ou uma feature secundária?"),
        _msg(sid, MessageRole.ASSISTANT, "Eu cortaria a feature secundária.", "morgana"),
        _msg(sid, MessageRole.USER, "Morgana, responde primeiro e deixa o Todd complementar só se tiver algo novo."),
    ])
    assert state is not None
    assert "observabilidade" in state.resolved_request.lower()
    assert "feature secundaria" in state.resolved_request.lower() or "feature secundária" in state.resolved_request.lower()


def test_dialogue_state_summary_uses_previous_exchange_as_decision_material() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "voltando à arquitetura: vocês ainda mexeriam nela antes da entrega?"),
        _msg(sid, MessageRole.ASSISTANT, "Eu não reescreveria; faria só uma validação reversível antes da entrega.", "todd"),
        _msg(sid, MessageRole.ASSISTANT, "Eu preservaria a versão estável e registraria a dívida para depois.", "morgana"),
        _msg(sid, MessageRole.USER, "resume a decisão em uma frase, Morgana."),
    ])
    assert state is not None
    rendered = state.render().lower()
    assert "nao reescreveria" in rendered or "não reescreveria" in rendered
    assert "versao estavel" in rendered or "versão estável" in rendered
    assert "nao explique o ato de resumir" in state.resolved_request.lower()


def test_dialogue_state_product_choices_stay_user_owned() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "o Campanário deveria parecer um lugar onde vocês já estão, não uma ferramenta que eu abro"),
        _msg(sid, MessageRole.USER, "uma coisa que eu gosto é o círculo central respirando, quase um blom blom"),
        _msg(sid, MessageRole.USER, "e as cores: Todd vermelho, Morgana âmbar, resto preto e branco"),
        _msg(sid, MessageRole.USER, "eu estava pensando em colocar controles visíveis para tudo"),
        _msg(sid, MessageRole.ASSISTANT, "Minha capacidade de conectar informações é importante.", "morgana"),
        _msg(sid, MessageRole.USER, "Todd, qual coisa você cortaria primeiro?"),
    ])
    assert state is not None
    rendered = state.render().lower()
    assert "circulo central" in rendered or "círculo central" in rendered
    assert "controles visiveis" in rendered or "controles visíveis" in rendered
    assert "capacidade de conectar informacoes" not in rendered and "capacidade de conectar informações" not in rendered
    assert "trait/persona" in rendered


def test_dialogue_state_root_return_preserves_root_product_idea() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "o Campanário deveria parecer um lugar onde vocês já estão, não uma ferramenta que eu abro"),
        _msg(sid, MessageRole.USER, "eu gosto do círculo respirando"),
        _msg(sid, MessageRole.USER, "Todd vermelho, Morgana âmbar e o resto preto e branco"),
        _msg(sid, MessageRole.USER, "volta à primeira ideia da call e fecha um conceito único juntando só o que sobreviveu"),
    ])
    assert state is not None
    assert state.immediate_referent is not None
    assert "lugar onde vocês já estão" in state.immediate_referent
    rendered = state.render().lower()
    assert "circulo respirando" in rendered or "círculo respirando" in rendered
    assert "vermelho" in rendered and ("ambar" in rendered or "âmbar" in rendered)


def test_dialogue_state_closure_prevents_new_question() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "é exatamente isso que eu quero"),
        _msg(sid, MessageRole.ASSISTANT, "Ótimo.", "todd"),
        _msg(sid, MessageRole.USER, "vou trabalhar agora."),
    ])
    assert state is not None
    assert state.closure is True
    assert "nao abra uma nova pergunta" in state.render().lower()


def test_dialogue_state_binary_cut_request_preserves_verb_direction() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "se eu tiver que cortar escopo, corto observabilidade ou uma feature secundária?"),
    ])
    assert state is not None
    folded = state.resolved_request.lower()
    assert "qual opcao deve ser cortada" in folded
    assert "opcao que deveria ser preservada" in folded


def test_dialogue_state_add_or_enough_binds_previous_answer() -> None:
    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "Morgana, responde primeiro."),
        _msg(sid, MessageRole.ASSISTANT, "Eu cortaria a feature secundária e manteria observabilidade.", "morgana"),
        _msg(sid, MessageRole.USER, "Todd, você acrescentaria algo ou a resposta dela já basta?"),
    ])
    assert state is not None
    assert state.immediate_referent is not None
    assert "feature secundária" in state.immediate_referent
    assert "acrescente somente se houver algo novo" in state.resolved_request.lower()


def test_answer_contract_same_question_is_binding_and_rejects_clarification() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "é sobre presença durante meu trabalho"),
        _msg(sid, MessageRole.USER, "Morgana, qual sinal faria você ficar quieta em vez de entrar na conversa?"),
        _msg(sid, MessageRole.ASSISTANT, "Quando minha fala seria redundante.", "morgana"),
        _msg(sid, MessageRole.USER, "Todd, mesma pergunta pra você, mas não repete a Morgana."),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    rendered = contract.render().lower()
    assert "contrato de resposta" in rendered
    assert "qual sinal faria você ficar quieta" in rendered
    assert contract.reject_clarification is True
    assert not contract.validates("Eu fico quieto quando não tenho nada novo ou quando a resposta já é suficiente.")
    assert contract.validates("Eu fico quieto quando entrar não muda a decisão nem reduz um risco concreto.")
    assert not contract.validates("Qual foi a pergunta?")
    assert not contract.validates("Precisamos revisar a arquitetura e as APIs internas.")


def test_answer_contract_short_sequence_requires_bound_problem() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "ontem tivemos um pico de latência sem erro nos logs. Por onde vocês começariam?"),
        _msg(sid, MessageRole.ASSISTANT, "CPU, rede e dependências.", "morgana"),
        _msg(sid, MessageRole.USER, "não quero vinte hipóteses; me deem uma sequência curta."),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.reject_clarification is True
    assert any("latencia" in item or "logs" in item for item in contract.required_any)
    assert contract.validates("1. Confira latência e recursos. 2. Veja os logs/traces. 3. Teste dependências.")
    assert not contract.validates("Primeiro defina melhor o problema e depois formule hipóteses.")


def test_answer_contract_summary_is_about_previous_decision_not_summarizing() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "voltando à arquitetura: vocês ainda mexeriam nela antes da entrega?"),
        _msg(sid, MessageRole.ASSISTANT, "Eu não reescreveria; manteria a arquitetura estável e faria só uma validação reversível.", "todd"),
        _msg(sid, MessageRole.ASSISTANT, "Eu preservaria a versão estável e registraria a refatoração para depois.", "morgana"),
        _msg(sid, MessageRole.USER, "resume a decisão em uma frase, Morgana."),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.validates("Manter a arquitetura estável para a entrega e adiar a refatoração, fazendo apenas uma validação reversível agora.")
    assert not contract.validates("A decisão é sintetizar informações complexas em uma frase clara.")


def test_answer_contract_product_choice_rejects_agent_trait() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "o Campanário deveria parecer um lugar onde vocês já estão, não uma ferramenta que eu abro"),
        _msg(sid, MessageRole.USER, "uma coisa que eu gosto é o círculo central respirando"),
        _msg(sid, MessageRole.USER, "Todd vermelho, Morgana âmbar, resto preto e branco"),
        _msg(sid, MessageRole.USER, "eu estava pensando em colocar controles visíveis para tudo"),
        _msg(sid, MessageRole.USER, "Todd, qual coisa você cortaria primeiro?"),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.validates("Eu cortaria primeiro os controles visíveis para tudo; eles poluem a interface.")
    assert not contract.validates("Eu preservaria minha capacidade interna de análise e minha identidade como agente.")


def test_answer_contract_closure_forbids_new_question() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "beleza, acho que é exatamente isso que eu quero"),
        _msg(sid, MessageRole.ASSISTANT, "Ótimo.", "todd"),
        _msg(sid, MessageRole.USER, "vou trabalhar agora."),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.no_new_question is True
    assert contract.validates("Bom trabalho.")
    assert not contract.validates("Certo. Qual é a prioridade do seu trabalho?")


def test_p242_commitment_state_closes_accepted_decision_without_reopening() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "voltando à arquitetura: vocês ainda mexeriam nela antes da entrega?"),
        _msg(sid, MessageRole.ASSISTANT, "Não. Priorize a entrega e deixe a refatoração para depois.", "todd"),
        _msg(sid, MessageRole.USER, "resume a decisão em uma frase, Morgana."),
        _msg(sid, MessageRole.ASSISTANT, "A decisão é priorizar a entrega e evitar reestruturação antes do prazo.", "morgana"),
        _msg(sid, MessageRole.USER, "fechado, seguimos assim."),
    ])
    assert state is not None
    assert state.commitment is not None
    assert "priorizar a entrega" in state.commitment.decision.lower()
    contract = build_answer_contract(state)
    assert contract.acknowledgement_only is True
    assert contract.max_words == 18
    assert contract.validates("Entendido.")
    assert not contract.validates("Sim, mas eu ainda faria ajustes na arquitetura antes da entrega.")


def test_p242_same_question_contract_rejects_repeating_previous_contribution() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    previous = "Um sinal claro seria a discussão estar completa ou você estar pensando em voz alta."
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "Morgana, qual sinal faria você ficar quieta em vez de entrar na conversa?"),
        _msg(sid, MessageRole.ASSISTANT, previous, "morgana"),
        _msg(sid, MessageRole.USER, "Todd, mesma pergunta pra você, mas não repete a Morgana."),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.distinct_from == (previous,)
    assert not contract.validates("Eu ficaria quieto quando a discussão estivesse completa ou você estivesse pensando em voz alta.")
    assert contract.validates("Eu fico quieto quando minha intervenção não muda a decisão nem reduz um risco concreto.")


def test_p242_embodiment_boundary_allows_metaphor_but_rejects_factual_agent_body() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "o Campanário deveria parecer um lugar onde vocês já estão, não uma ferramenta que eu abro"),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.validates("Poderia lembrar uma biblioteca antiga, com luz difusa e sensação de continuidade.")
    assert not contract.validates("Todd está sentado no canto, rabiscando pergaminhos enquanto eu observo a luz pela janela.")


def test_p242_order_instruction_keeps_previous_answer_as_evidence() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    previous = "Eu cortaria a feature secundária e manteria observabilidade."
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "se eu tiver que cortar escopo, corto observabilidade ou uma feature secundária?"),
        _msg(sid, MessageRole.ASSISTANT, previous, "morgana"),
        _msg(sid, MessageRole.USER, "Morgana, responde primeiro e deixa o Todd complementar só se tiver algo novo."),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert previous in contract.evidence
    assert "observabilidade" in contract.exact_request.lower()


def test_p243_same_question_seed_like_paraphrase_is_rejected() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    previous = (
        "A ausência de uma pergunta direta direcionada a mim seria um sinal claro. "
        "Se a interação for um fluxo de pensamentos sem solicitação de contribuição, prefiro observar. "
        "A conclusão explícita de um tópico por outro agente também indicaria que meu input não é necessário."
    )
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "Morgana, qual sinal faria você ficar quieta em vez de entrar na conversa?"),
        _msg(sid, MessageRole.ASSISTANT, previous, "morgana"),
        _msg(sid, MessageRole.USER, "Todd, mesma pergunta pra você, mas não repete a Morgana."),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.max_semantic_overlap == 0.34
    assert not contract.validates(
        "A ausência de uma pergunta direcionada a mim e a conclusão do tópico por outro agente "
        "seriam sinais para eu permanecer em silêncio."
    )
    assert contract.validates(
        "Eu fico quieto quando entrar não muda a decisão, não reduz risco e não acrescenta uma ação útil."
    )


def test_p243_social_naturality_rejects_internal_runtime_jargon() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "se eu estiver só pensando em voz alta, como vocês evitam virar duas pessoas me interrompendo?"),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.validates("Se você estiver só pensando, a gente fica quieto até haver algo útil para acrescentar.")
    assert not contract.validates("O protocolo social e o arbiter avaliam o contexto antes de permitir uma intervenção.")


def test_p243_trivial_arithmetic_prefers_short_answer() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "mudando totalmente: 24 vezes 6 dá quanto, Morgana?"),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.max_words == 14
    assert contract.no_new_question is True
    assert contract.validates("24 vezes 6 é 144.")
    assert not contract.validates(
        "24 vezes 6 é 144, e essa mudança abrupta de assunto é interessante porque pode indicar uma busca por padrões inesperados na conversa."
    )


def test_p243_thanks_is_acknowledgement_without_new_question() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "me ajuda com isso"),
        _msg(sid, MessageRole.ASSISTANT, "Claro.", "morgana"),
        _msg(sid, MessageRole.USER, "valeu"),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert state.acknowledgement is True
    assert contract.no_new_question is True


def test_p244_same_question_requires_a_semantically_new_silence_criterion() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    previous = (
        "Um sinal claro seria um pedido explícito para que apenas um agente responda, "
        "quando o outro já abordou o ponto de forma completa e satisfatória, ou quando você estiver pensando em voz alta; "
        "nesses casos minha contribuição não é necessária."
    )
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "Morgana, qual sinal faria você ficar quieta em vez de entrar na conversa?"),
        _msg(sid, MessageRole.ASSISTANT, previous, "morgana"),
        _msg(sid, MessageRole.USER, "Todd, mesma pergunta pra você, mas não repete a Morgana."),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.require_novel_silence_criterion is True
    assert not contract.validates(
        "Uma instrução direta para só a Morgana responder, ou perceber que minha contribuição não é necessária, "
        "seriam sinais para eu ficar quieto enquanto você reflete."
    )
    assert contract.validates(
        "Eu fico quieto quando entrar não muda a decisão, não reduz risco e não acrescenta um próximo passo útil."
    )


def test_p244_work_closure_is_short_and_does_not_recycle_convergence_ack() -> None:
    from campanario.chat.dialogue_state import build_answer_contract

    sid = uuid4()
    state = compile_dialogue_state([
        _msg(sid, MessageRole.USER, "beleza, acho que é exatamente isso que eu quero."),
        _msg(sid, MessageRole.ASSISTANT, "Entendido. Parece que chegamos a um ponto de convergência.", "todd"),
        _msg(sid, MessageRole.USER, "vou trabalhar agora."),
    ])
    assert state is not None
    contract = build_answer_contract(state)
    assert contract.max_words == 6
    assert contract.no_new_question is True
    assert contract.validates("Bom trabalho.")
    assert not contract.validates("Entendido. Parece que chegamos a um ponto de convergência.")
