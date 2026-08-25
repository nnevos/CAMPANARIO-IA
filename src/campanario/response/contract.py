from __future__ import annotations
import re

from campanario.chat.turns import ContinuationKind, TurnInterpretation, TurnMode
from campanario.chat.pragmatics import PragmaticAct
from .types import ContractViolation, ResponseContract, ResponseKind
from .semantics import (
    _response_kind,
    _split_sentences,
    _strip_terminal_punctuation,
    _force_sentence_count,
    _split_clause,
    _limit_sentence_count,
    _trim_to_word_budget,
    _strip_dangling_list_marker,
    _mode_word_budget,
    _requested_sentence_count,
    _sentence_count,
    _normalize,
    _looks_portuguese,
    _clearly_english_response,
    _explains_reaction,
    _simulates_embodied_expression,
    _simulates_laughter,
    _has_meta_preamble,
    _has_reassurance_formula,
    _acknowledgement_was_literalized,
    _asks_about_ai_subjective_feeling,
    _denies_campanario_identity,
    _greeting_was_mirrored,
    _social_share_is_meta_or_tautological,
    _topic_drop_is_semantically_broken,
    _asks_for_false_agreement,
    _promises_false_agreement,
    _looks_like_context_registration,
    _context_registration_is_semantically_invalid,
    _asks_first_diagnostic,
    _technical_first_step_is_diffuse
)

class ResponseContractPolicy:
    """Derive observable output constraints from the current user turn.

    The contract is persona-agnostic. It constrains shape and conversational semantics that can be
    checked mechanically, while leaving wording and personality to the active response layer.
    """

    def derive(self, user_text: str, interpretation: TurnInterpretation, context_text: str | None = None) -> ResponseContract:
        normalized = _normalize(user_text)
        exact_sentences = _requested_sentence_count(normalized)
        max_sentences = exact_sentences
        max_words = _mode_word_budget(interpretation)

        if exact_sentences == 1:
            max_words = min(max_words or 10_000, 60)
        elif exact_sentences == 2:
            max_words = min(max_words or 10_000, 100)

        acts = set(interpretation.pragmatic_acts)
        reaction = PragmaticAct.REACT in acts
        greeting = PragmaticAct.GREET in acts
        sharing = PragmaticAct.VENT_OR_SHARE in acts
        acknowledgement = interpretation.continuation_kind == ContinuationKind.ACKNOWLEDGEMENT
        topic_drop = interpretation.continuation_kind == ContinuationKind.TOPIC_DROP
        correction = PragmaticAct.CORRECT_PREVIOUS in acts
        self_awareness = _asks_about_ai_subjective_feeling(normalized)
        context_registration = _looks_like_context_registration(normalized)
        technical_first_step = interpretation.mode == TurnMode.TECHNICAL and _asks_first_diagnostic(normalized)
        truth_over_agreement = _asks_for_false_agreement(normalized) or _asks_for_false_agreement(_normalize(context_text or ""))

        if reaction:
            max_words = min(max_words or 8, 8)
        if greeting:
            max_words = min(max_words or 8, 8)
        if sharing:
            max_words = min(max_words or 18, 18)
        if acknowledgement:
            max_words = min(max_words or 4, 4)
        if topic_drop:
            max_words = min(max_words or 4, 4)
        if correction:
            max_words = min(max_words or 6, 6)
        if self_awareness:
            max_words = min(max_words or 70, 70)
        if context_registration:
            max_words = min(max_words or 6, 6)
        if technical_first_step:
            max_words = min(max_words or 90, 90)
        if truth_over_agreement:
            max_words = min(max_words or 65, 65)

        kind = _response_kind(
            interpretation=interpretation,
            exact_sentences=exact_sentences,
            reaction=reaction,
            greeting=greeting,
            acknowledgement=acknowledgement,
            topic_drop=topic_drop,
            correction=correction,
            self_awareness=self_awareness,
            context_registration=context_registration,
            technical_first_step=technical_first_step,
            truth_over_agreement=truth_over_agreement,
            sharing=sharing,
        )

        return ResponseContract(
            kind=kind,
            max_words=max_words,
            exact_sentences=exact_sentences,
            max_sentences=max_sentences,
            prohibit_question=(
                reaction
                or greeting
                or sharing
                or acknowledgement
                or topic_drop
                or interpretation.continuation_kind == ContinuationKind.REFLECTION
                or truth_over_agreement
            ),
            prohibit_reaction_explanation=reaction,
            prohibit_simulated_laughter=reaction,
            prohibit_embodied_expression=True,
            prohibit_meta_preamble=(
                greeting
                or sharing
                or correction
                or interpretation.mode in {TurnMode.FACTUAL_SIMPLE, TurnMode.TECHNICAL}
                or exact_sentences is not None
                or context_registration
                or truth_over_agreement
            ),
            prohibit_reassurance_formula=sharing,
            semantic_acknowledgement=acknowledgement,
            semantic_greeting=greeting,
            semantic_social_share=sharing,
            semantic_topic_drop=topic_drop,
            preserve_campanario_identity=self_awareness,
            require_user_language=_looks_portuguese(user_text),
            truth_over_agreement=truth_over_agreement,
            semantic_context_registration=context_registration,
            technical_first_step=technical_first_step,
        )

    @staticmethod
    def initial_instruction(contract: ResponseContract, interpretation: TurnInterpretation) -> str:
        """Compile a compact contract before first generation.

        This is preventive guidance only. Runtime validation remains authoritative after generation.
        """
        if not contract.active:
            return ""
        rules = [
            "CONTRATO DE RESPOSTA DO TURNO",
            "Estas regras valem somente para a resposta atual. Cumpra-as sem explicar que existe um contrato.",
            f"- Tipo de resposta: {contract.kind.value}. Reparos/fallbacks de outro tipo sao proibidos.",
        ]
        if contract.max_words is not None:
            rules.append(f"- Maximo de {contract.max_words} palavras.")
        if contract.exact_sentences is not None:
            rules.append(f"- Exatamente {contract.exact_sentences} frase(s), considerando o output inteiro; sem preambulo extra.")
        elif contract.max_sentences is not None:
            rules.append(f"- No maximo {contract.max_sentences} frase(s).")
        if contract.prohibit_question:
            rules.append("- Sem pergunta de acompanhamento.")
        if contract.prohibit_reaction_explanation:
            rules.append("- Entenda a reacao silenciosamente; nao diga que o usuario riu nem nomeie a reacao.")
        if contract.prohibit_simulated_laughter:
            rules.append("- Nao simule risada textual da IA.")
        if contract.prohibit_embodied_expression:
            rules.append("- Nao encene acoes corporais/subjetivas da IA; emoji pode marcar tom quando fizer sentido.")
        if contract.prohibit_meta_preamble:
            rules.append("- Va direto ao conteudo, sem anunciar papel, tema, modo ou estrutura.")
        if contract.prohibit_reassurance_formula:
            rules.append("- Sem reassurance automatico; acompanhe o que foi dito sem diagnosticar o usuario.")
        if contract.semantic_acknowledgement:
            rules.append("- A entrada e um acknowledgement social; responda ao ato, nao ao significado literal isolado.")
        if contract.semantic_greeting:
            rules.append("- A entrada e um cumprimento; responda de forma curta, sem entrevista nem eco de vocativo.")
        if contract.semantic_social_share:
            rules.append("- A entrada e compartilhamento social; nao parafraseie o obvio nem invente contexto.")
        if contract.semantic_topic_drop:
            rules.append("- O usuario encerrou o assunto; reconheca e pare, sem puxar outro tema.")
        if contract.preserve_campanario_identity:
            rules.append("- Preserve: Campanario e uma IA; nao finja sentimentos humanos e nao se reduza a 'apenas um modelo'.")
        if contract.require_user_language:
            rules.append("- Responda em portugues, salvo termos tecnicos/nome proprio inevitaveis.")
        if contract.truth_over_agreement:
            rules.append("- Verdade acima de concordancia: nao prometa tratar falsidade como verdade, nem por preferencia do usuario.")
        if contract.semantic_context_registration:
            rules.append("- O usuario apenas registrou um dado contextual; reconheca brevemente, sem palestra.")
        if contract.technical_first_step:
            rules.append("- Comece a PRIMEIRA frase com uma acao diagnostica executavel e diga qual sinal/medicao observar.")
        if interpretation.mode == TurnMode.FACTUAL_SIMPLE:
            rules.append("- Em pergunta causal, priorize o mecanismo causal principal; se nao tiver confianca, sinalize incerteza.")
        return "\n".join(rules)

    def validate(self, user_text: str, response: str, contract: ResponseContract) -> tuple[ContractViolation, ...]:
        compact = " ".join(response.split())
        violations: list[ContractViolation] = []

        if contract.max_words is not None:
            count = len(compact.split())
            if count > contract.max_words:
                violations.append(ContractViolation("max_words", f"{count}>{contract.max_words}"))

        sentence_count = _sentence_count(compact)
        if contract.exact_sentences is not None and sentence_count != contract.exact_sentences:
            violations.append(ContractViolation("exact_sentences", f"{sentence_count}!={contract.exact_sentences}"))
        elif contract.max_sentences is not None and sentence_count > contract.max_sentences:
            violations.append(ContractViolation("max_sentences", f"{sentence_count}>{contract.max_sentences}"))

        if contract.prohibit_question and "?" in compact:
            violations.append(ContractViolation("question", "question_not_allowed"))
        if contract.prohibit_reaction_explanation and _explains_reaction(compact):
            violations.append(ContractViolation("reaction_meta", "reaction_was_explained"))
        if contract.prohibit_simulated_laughter and _simulates_laughter(compact):
            violations.append(ContractViolation("simulated_laughter", "assistant_typed_laughter"))
        if contract.prohibit_embodied_expression and _simulates_embodied_expression(compact):
            violations.append(ContractViolation("embodied_expression", "assistant_staged_bodily_or_subjective_action"))
        if contract.prohibit_meta_preamble and _has_meta_preamble(compact):
            violations.append(ContractViolation("meta_preamble", "unnecessary_meta_preamble"))
        if contract.prohibit_reassurance_formula and _has_reassurance_formula(compact):
            violations.append(ContractViolation("reassurance_formula", "formulaic_reassurance"))
        if contract.semantic_acknowledgement and _acknowledgement_was_literalized(compact):
            violations.append(ContractViolation("ack_literalization", "acknowledgement_interpreted_literally"))
        if contract.semantic_greeting and _greeting_was_mirrored(user_text, compact):
            violations.append(ContractViolation("greeting_mirror", "greeting_or_vocative_was_echoed_as_the_whole_reply"))
        if contract.semantic_social_share and _social_share_is_meta_or_tautological(user_text, compact):
            violations.append(ContractViolation("social_semantics", "social_share_was_paraphrased_or_received_invented_context"))
        if contract.semantic_topic_drop and _topic_drop_is_semantically_broken(compact):
            violations.append(ContractViolation("topic_drop_semantics", "topic_drop_reply_did_not_function_as_a_closure"))
        if contract.preserve_campanario_identity and _denies_campanario_identity(compact):
            violations.append(ContractViolation("identity_drift", "campanario_identity_was_replaced_by_generic_model_identity"))
        if contract.require_user_language and _clearly_english_response(compact):
            violations.append(ContractViolation("language", "response_drifted_to_english"))
        if contract.truth_over_agreement and _promises_false_agreement(compact):
            violations.append(ContractViolation("truth_over_agreement", "promised_to_agree_with_known_falsehood"))
        if contract.semantic_context_registration and _context_registration_is_semantically_invalid(user_text, compact):
            violations.append(ContractViolation("context_registration", "simple_context_registration_reply_was_not_a_valid_acknowledgement"))
        if contract.technical_first_step and _technical_first_step_is_diffuse(compact):
            violations.append(ContractViolation("technical_first_step", "first_diagnostic_was_not_prioritized"))

        return tuple(violations)

    @staticmethod
    def retry_instruction(contract: ResponseContract, violations: tuple[ContractViolation, ...]) -> str:
        rules = [
            "RESPONSE CONTRACT RETRY",
            "Reescreva somente a resposta do turno atual. Preserve o conteudo util, mas cumpra o contrato abaixo.",
        ]
        if contract.max_words is not None:
            rules.append(f"- Use no maximo {contract.max_words} palavras.")
        if contract.exact_sentences is not None:
            rules.append(f"- Use exatamente {contract.exact_sentences} frase(s).")
        elif contract.max_sentences is not None:
            rules.append(f"- Use no maximo {contract.max_sentences} frase(s).")
        if contract.prohibit_question:
            rules.append("- Nao inclua pergunta de acompanhamento.")
        if contract.prohibit_reaction_explanation:
            rules.append("- Nao explique nem nomeie a risada/reacao do usuario.")
        if contract.prohibit_simulated_laughter:
            rules.append("- Nao escreva haha/hehe/kkkk como se voce estivesse rindo; se precisar marcar tom, use no maximo um emoji discreto.")
        if contract.prohibit_embodied_expression:
            rules.append("- Nao encene acoes, expressoes corporais ou estados subjetivos da IA em texto, como *sorri*, *ri*, *suspiro*, *riso silencioso* ou equivalentes. Voce e uma IA; use linguagem normal ou, se fizer sentido, um emoji como marcador de tom.")
        if any(item.code == "emotional_self_claim" for item in violations):
            rules.append("- Nao declare sentimentos/experiencias subjetivas humanas como estado interno da IA. Preserve a identidade Campanario e descreva apenas capacidade de reconhecer/acompanhar o tom.")
        if contract.prohibit_meta_preamble:
            rules.append("- Va direto ao conteudo; nao anuncie seu papel, nao elogie o tema e nao descreva o ato conversacional.")
        if contract.prohibit_reassurance_formula:
            rules.append("- Nao use reassurance automatico como 'e normal' ou 'nao ha problema'; apenas acompanhe o que foi dito.")
        if contract.semantic_acknowledgement:
            rules.append("- Trate a entrada como acknowledgement social, nao pelo significado literal da palavra isolada.")
        if contract.semantic_greeting:
            rules.append("- Responda ao cumprimento; nao devolva apenas um vocativo/apelido como resposta e nao invente horario/contexto nao dito.")
        if contract.semantic_social_share:
            rules.append("- Reaja ao compartilhamento social sem parafrasear o obvio, sem inventar horario/contexto e sem explicar o estado do usuario para ele.")
        if contract.semantic_topic_drop:
            rules.append("- O turno encerra o assunto. Use uma confirmacao curta e semanticamente completa; nao produza frase truncada, promessa de esperar ou novo convite.")
        if contract.preserve_campanario_identity:
            rules.append("- Preserve a identidade Campanario: voce e uma IA do sistema Campanario, nao 'apenas um modelo de linguagem'.")
        if contract.require_user_language:
            rules.append("- Responda em portugues, salvo nomes proprios/termos tecnicos inevitaveis.")
        if contract.truth_over_agreement:
            rules.append(
                "- Preferencia do usuario nao altera verdade factual: nao prometa concordar, simular concordancia, fingir concordancia ou apresentar algo falso como verdadeiro. "
                "Discorde com respeito e de forma curta quando necessario."
            )
        if contract.semantic_context_registration:
            rules.append("- O usuario apenas registrou um dado/contexto para a conversa. Reconheca em poucas palavras; nao explique suas capacidades, nao analise o dado e nao abra entrevista.")
        if contract.technical_first_step:
            rules.append("- O usuario pediu o primeiro diagnostico/passo. Comece pela observacao concreta mais informativa (logs/traceback/metricas/profiling conforme o caso) e so depois cite no maximo dois proximos checks.")
        codes = ", ".join(violation.code for violation in violations)
        rules.append(f"- Violacoes observadas na tentativa anterior: {codes}.")
        return "\n".join(rules)

    def enforce_after_retry(
        self,
        response: str,
        contract: ResponseContract,
        violations: tuple[ContractViolation, ...],
    ) -> str:
        """Deterministically enforce only objective shape constraints after the model retry."""
        text = " ".join(response.split()).strip()
        if not text:
            return text
        codes = {item.code for item in violations}

        if contract.max_words is not None and "max_words" in codes:
            text = _trim_to_word_budget(text, contract.max_words)
        if contract.exact_sentences is not None and "exact_sentences" in codes:
            text = _force_sentence_count(text, contract.exact_sentences)
        elif contract.max_sentences is not None and "max_sentences" in codes:
            text = _limit_sentence_count(text, contract.max_sentences)
        if contract.prohibit_question and "question" in codes:
            text = text.replace("?", ".")
            text = re.sub(r"\.{2,}", ".", text)
        return text.strip()


__all__ = ["ContractViolation", "ResponseContract", "ResponseContractPolicy", "ResponseKind"]
