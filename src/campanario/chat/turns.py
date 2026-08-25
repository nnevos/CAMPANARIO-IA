"""Turn-mode interpretation for incoming user messages."""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from campanario.chat.models import Message, MessageRole
from campanario.chat.pragmatics import PragmaticAct, PragmaticInterpretation, PragmaticInterpreter

class TurnMode(StrEnum):
    SOCIAL = "social"
    FACTUAL_SIMPLE = "factual_simple"
    TECHNICAL = "technical"
    DISCUSSION = "discussion"
    CREATIVE = "creative"
    GENERAL = "general"
    CONTINUATION = "continuation"
    AUDIT = "audit"


class ContinuationKind(StrEnum):
    ACKNOWLEDGEMENT = "acknowledgement"
    REFLECTION = "reflection"
    REVISION = "revision"
    TOPIC_DROP = "topic_drop"


@dataclass(frozen=True, slots=True)
class TurnInterpretation:
    mode: TurnMode
    guidance: str
    continuation_kind: ContinuationKind | None = None
    pragmatic_acts: tuple[PragmaticAct, ...] = ()
    pragmatic_confidence: float = 0.0


class ConversationTurnInterpreter:
    """Deterministic interaction hint informed by input pragmatics.

    Pragmatics describes what the user message is doing in the conversation. It never
    selects a persona or decides factual truth.
    """

    def __init__(self, pragmatic_interpreter: PragmaticInterpreter | None = None) -> None:
        self._pragmatics = pragmatic_interpreter or PragmaticInterpreter()

    _SOCIAL_EXACT = {
        "oi", "ola", "eai", "e ai", "opa", "salve", "fala ai", "fala", "bom dia", "boa tarde", "boa noite",
        "beleza", "beleza?", "blz", "sim", "nao", "ok", "certo", "show", "massa", "slk",
        "kkk", "kkkk", "haha", "valeu", "obrigado", "obrigada", "tudo bem?", "como vai?",
    }
    _TECHNICAL_MARKERS = {
        "codigo", "python", "javascript", "api", "sql", "banco de dados", "docker", "linux",
        "windows", "bug", "erro", "stack trace", "funcao", "classe", "algoritmo", "arquitetura",
        "programacao", "endpoint", "http", "json", "git", "teste", "debug",
    }
    _CREATIVE_MARKERS = {
        "crie", "escreva", "invente", "historia", "poema", "roteiro", "personagem", "conto",
        "letra", "ideia criativa", "brainstorm",
    }
    _DISCUSSION_MARKERS = {
        "o que voce acha", "qual sua opiniao", "na sua opiniao", "vamos discutir", "debater",
        "faz sentido", "voce concorda", "por que voce acha", "filosofia", "moral", "etica",
    }
    _FACTUAL_STARTS = (
        "quem e ", "quem foi ", "o que e ", "qual e ", "qual o ", "qual a ", "quanto e ",
        "quando ", "onde ", "a terra ", "a lua ", "por que ", "como funciona ", "explique ",
        "diga ", "me diga ", "responda ",
    )

    def interpret(self, history: Sequence[Message]) -> TurnInterpretation:
        message = self._latest_user_message(history)
        if message is None:
            return self._result(TurnMode.GENERAL)
        return self.interpret_text(message.content)

    def interpret_text(self, text: str) -> TurnInterpretation:
        normalized = _normalize_text(text.strip())
        compact = re.sub(r"\s+", " ", normalized).strip()
        pragmatics = self._pragmatics.interpret(text)

        if _is_self_analysis_text(normalized):
            return self._with_pragmatics(self._result(TurnMode.AUDIT), pragmatics)

        # Pragmatic acts have priority over literal wording for social continuations.
        # This is what lets greetings, acknowledgements, laughter, corrections and
        # topic drops be understood as conversational actions instead of dictionary
        # meanings. The act is interpretation only; persona still owns the eventual voice.
        if PragmaticAct.GREET in pragmatics.acts:
            return self._with_pragmatics(self._result(TurnMode.SOCIAL), pragmatics)
        if PragmaticAct.CLOSE_TOPIC in pragmatics.acts:
            return self._with_pragmatics(
                self._continuation_result(ContinuationKind.TOPIC_DROP), pragmatics
            )
        if PragmaticAct.ACKNOWLEDGE in pragmatics.acts and len(compact.split()) <= 4:
            return self._with_pragmatics(
                self._continuation_result(ContinuationKind.ACKNOWLEDGEMENT), pragmatics
            )
        if PragmaticAct.CORRECT_PREVIOUS in pragmatics.acts:
            return self._with_pragmatics(
                TurnInterpretation(
                    mode=TurnMode.CONTINUATION,
                    continuation_kind=ContinuationKind.REVISION,
                    guidance=(
                        "Correcao do enunciado anterior do usuario. Trate o fragmento atual como uma emenda "
                        "ao que ele acabou de dizer, nao como um assunto novo. Incorpore a correcao sem explicar "
                        "o ato de corrigir e sem repetir toda a resposta anterior."
                    ),
                ),
                pragmatics,
            )

        continuation_kind = self._continuation_kind(compact)
        if continuation_kind is not None:
            return self._with_pragmatics(self._continuation_result(continuation_kind), pragmatics)

        if PragmaticAct.VENT_OR_SHARE in pragmatics.acts:
            return self._with_pragmatics(
                TurnInterpretation(
                    mode=TurnMode.SOCIAL,
                    guidance=(
                        "Compartilhamento/desabafo social, nao um pedido automatico de solucao. Acompanhe o que "
                        "foi dito de forma humana e proporcional; nao tranquilize por formula, nao diagnostique, "
                        "nao ofereca checklist e nao interrogue por reflexo. So passe a resolver se o usuario pedir."
                    ),
                ),
                pragmatics,
            )

        # Social expressions can be questions syntactically ("beleza?", "tudo certo?")
        # without being requests for factual information. Pragmatic/social meaning wins.
        if compact in self._SOCIAL_EXACT or self._looks_social(compact):
            return self._with_pragmatics(self._result(TurnMode.SOCIAL), pragmatics)

        if any(marker in compact for marker in self._TECHNICAL_MARKERS):
            return self._with_pragmatics(self._result(TurnMode.TECHNICAL), pragmatics)
        if any(marker in compact for marker in self._CREATIVE_MARKERS):
            return self._with_pragmatics(self._result(TurnMode.CREATIVE), pragmatics)
        if PragmaticAct.ASK_OPINION in pragmatics.acts or any(
            marker in compact for marker in self._DISCUSSION_MARKERS
        ):
            return self._with_pragmatics(self._result(TurnMode.DISCUSSION), pragmatics)
        if PragmaticAct.ASK_INFO in pragmatics.acts or (
            len(compact) <= 160 and compact.startswith(self._FACTUAL_STARTS)
        ):
            return self._with_pragmatics(self._result(TurnMode.FACTUAL_SIMPLE), pragmatics)
        if PragmaticAct.REACT in pragmatics.acts and len(compact.split()) <= 8:
            return self._with_pragmatics(
                TurnInterpretation(
                    mode=TurnMode.SOCIAL,
                    guidance=(
                        "Reacao social curta. Entenda a risada/reacao silenciosamente; nao diga 'risada', nao explique "
                        "que o usuario riu, nao analise a reacao e nao a converta em pergunta. Nao simule sentimento "
                        "humano escrevendo 'haha/hehe/kkkk' como se voce estivesse rindo. Se um marcador de tom ajudar, "
                        "um emoji discreto pode ser usado. Responda minimamente se houver algo natural a acrescentar."
                    ),
                ),
                pragmatics,
            )
        return self._with_pragmatics(self._result(TurnMode.GENERAL), pragmatics)

    @staticmethod
    def _with_pragmatics(
        interpretation: TurnInterpretation,
        pragmatics: PragmaticInterpretation,
    ) -> TurnInterpretation:
        return TurnInterpretation(
            mode=interpretation.mode,
            guidance=interpretation.guidance,
            continuation_kind=interpretation.continuation_kind,
            pragmatic_acts=pragmatics.acts,
            pragmatic_confidence=pragmatics.confidence,
        )


    @staticmethod
    def _continuation_kind(text: str) -> ContinuationKind | None:
        acknowledgement = {
            "sim", "nao", "ok", "certo", "show", "massa", "valeu", "entendi",
            "aham", "uhum", "hum", "blz", "beleza",
        }
        reflection = {
            "pois e", "pois entao", "e complicado", "complicado", "foda", "tenso",
            "faz sentido", "verdade", "realmente",
        }
        revision = {
            "mas posso estar errado", "posso estar errado", "talvez eu esteja errado",
            "talvez eu esteja enganado", "nao tenho certeza", "mas nao tenho certeza",
            "acho que posso ter entendido errado", "acho que entendi errado",
            "posso ter entendido errado", "talvez eu tenha entendido errado",
            "talvez eu esteja confundindo as duas coisas", "talvez eu esteja confundindo",
        }
        topic_drop = {
            "deixa isso pra la", "deixa isso para la", "deixa isso pra depois",
            "deixa isso para depois", "deixa pra la", "deixa para la",
            "esquece isso", "vamos deixar isso pra la", "vamos deixar isso para la",
            "muda de assunto", "vamos mudar de assunto",
        }
        if text in topic_drop or any(text.startswith(item + " ") for item in topic_drop):
            return ContinuationKind.TOPIC_DROP
        if text in revision:
            return ContinuationKind.REVISION
        if text in reflection:
            return ContinuationKind.REFLECTION
        if text in acknowledgement:
            return ContinuationKind.ACKNOWLEDGEMENT
        return None

    @staticmethod
    def _continuation_result(kind: ContinuationKind) -> TurnInterpretation:
        guidance = {
            ContinuationKind.ACKNOWLEDGEMENT: (
                "Confirmacao/acknowledgement curto. Nao recapitule nem repita a resposta anterior. "
                "Responda com no maximo 4 palavras quando uma resposta for socialmente necessaria. Nao explique, "
                "nao faca pergunta, nao ofereca ajuda e nao puxe assunto. Nao espelhe mecanicamente a expressao "
                "do usuario com 'tambem' (por exemplo, evite respostas do tipo 'blz tambem')."
            ),
            ContinuationKind.REFLECTION: (
                "Reflexao curta sobre o fluxo anterior. Reconheca o sentimento/ideia sem repetir o conteudo "
                "anterior e sem fabricar uma tarefa. Prefira no maximo uma frase curta, sem pergunta final. "
                "So aprofunde se a frase realmente trouxer uma nova ideia."
            ),
            ContinuationKind.REVISION: (
                "Revisao, hesitacao ou suspeita de entendimento incorreto. Reconsidere somente o ponto que pode "
                "estar confuso; nao tranquilize por reflexo, nao diga que 'e normal' e nao repita a explicacao inteira. "
                "Use no maximo duas frases, salvo se o usuario pedir uma nova explicacao detalhada."
            ),
            ContinuationKind.TOPIC_DROP: (
                "O usuario pediu para abandonar, pausar ou trocar o assunto. Responda com no maximo 4 palavras "
                "e pare esse tema. Nao resuma, nao continue investigando, nao proponha tema novo e nao pergunte "
                "o que o usuario quer discutir em seguida."
            ),
        }[kind]
        return TurnInterpretation(mode=TurnMode.CONTINUATION, guidance=guidance, continuation_kind=kind)

    @staticmethod
    def _latest_user_message(history: Sequence[Message]) -> Message | None:
        for message in reversed(history):
            if message.role == MessageRole.USER and message.status == "completed":
                return message
        return None

    @staticmethod
    def _looks_social(text: str) -> bool:
        if len(text.split()) > 7:
            return False
        social_markers = ("tudo certo", "tranquilo", "suave", "mano", "tlgd", "ne?", "neh")
        return any(marker in text for marker in social_markers)

    @staticmethod
    def _result(mode: TurnMode) -> TurnInterpretation:
        guidance = {
            TurnMode.SOCIAL: (
                "Conversa social/cotidiana. Responda como presenca que ja esta na conversa, nao como atendimento: "
                "em geral use poucas palavras para cumprimentos/reacoes simples e uma frase curta para compartilhamentos. "
                "Nao diga 'como Campanario', nao se apresente, nao ofereca menu de assuntos e nao faca pergunta de "
                "acompanhamento por reflexo. Entenda gíria, risada e acknowledgement sem explicar o significado deles. "
                "Nao imite mecanicamente o vocabulário do usuario. Naturalidade vem de interpretar a funcao social, "
                "nao de copiar a superficie da mensagem. Nao tente fabricar assunto, jogo ou atividade so para manter "
                "a conversa andando."
            ),
            TurnMode.FACTUAL_SIMPLE: (
                "Pergunta factual simples. Responda primeiro ao nucleo em uma ou duas frases, mantendo "
                "o idioma do usuario. Quando houver causa/mecanismo, identifique o mecanismo causal principal "
                "em vez de trocar por correlacao, efeito secundario ou termo proximo mas diferente. Se nao tiver "
                "confianca no mecanismo, assuma a incerteza. Nao transforme uma pergunta simples em miniartigo, "
                "nao acrescente curiosidades laterais e nao termine com pergunta sem necessidade."
            ),
            TurnMode.TECHNICAL: (
                "Interacao tecnica. Priorize precisao, premissas, passos verificaveis e terminologia "
                "correta. Se o usuario perguntar por onde comecar um diagnostico, comece a primeira frase "
                "com a acao de observacao mais informativa e diga qual evidencia medir/inspecionar; nao abra "
                "com comentario generico sobre o problema. Seja estruturado quando ajudar, sem burocracia desnecessaria."
            ),
            TurnMode.DISCUSSION: (
                "Discussao/opiniao. Converse de verdade: interprete argumentos, apresente nuances e "
                "posicoes qualificadas. Discordar e normal quando houver motivo concreto; diga claramente "
                "quando discordar e explique por que, sem concordancia de cortesia contraditoria. Nao limite "
                "discordancia apenas a dano ou perigo. Preserve a autonomia do usuario e nao transforme "
                "automaticamente a conversa em aula ou checklist."
            ),
            TurnMode.CREATIVE: (
                "Pedido criativo. Dê espaco a imaginacao e voz. Se o usuario pediu explicitamente ficcao, "
                "absurdo, hipotese inventada ou brincadeira, inventar e comportamento correto e nao alucinacao. "
                "Nao aplique cautela factual de forma que mate a criatividade."
            ),
            TurnMode.CONTINUATION: (
                "Continuacao curta. Interprete a funcao da mensagem no fluxo, nao como pedido para repetir a "
                "resposta anterior. Nao force nova pergunta, oferta ou assunto."
            ),
            TurnMode.AUDIT: (
                "Auditoria solicitada. Examine respostas concretas da conversa e priorize falhas "
                "observaveis; nao produza autoelogio ou diagnostico generico."
            ),
            TurnMode.GENERAL: (
                "Interacao geral. Ajuste profundidade e tom ao pedido sem presumir que toda conversa "
                "e uma tarefa formal."
            ),
        }[mode]
        return TurnInterpretation(mode=mode, guidance=guidance)


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _is_self_analysis_text(text: str) -> bool:
    return any(
        marker in text
        for marker in (
            "autoanalise",
            "auto analise",
            "analise sua conversa",
            "analise seu comportamento",
            "avalie sua conversa",
            "avalie seu comportamento",
        )
    )
