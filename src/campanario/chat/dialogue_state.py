from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from collections.abc import Sequence

from campanario.chat.models import Message, MessageRole
from campanario.chat.working_context import FocusFrame, build_focus_stack


_CONTROL_CUES = (
    "responde primeiro",
    "responda primeiro",
    "deixa o todd complementar",
    "deixe o todd complementar",
    "mesma pergunta",
    "so o essencial",
    "só o essencial",
    "resume a decisao",
    "resume a decisão",
    "resuma a decisao",
    "resuma a decisão",
    "qual coisa voce cortaria",
    "qual coisa você cortaria",
    "qual coisa voce preservaria",
    "qual coisa você preservaria",
    "aterrissa isso",
)
_CLOSURE_CUES = (
    "vou trabalhar agora",
    "vou voltar ao trabalho",
    "vou trabalhar",
    "fechado, seguimos assim",
    "nao precisa adicionar mais nada",
    "não precisa adicionar mais nada",
    "deixa quieto",
    "esquece isso",
)
_SHIFT_CUES = ("mudando totalmente", "mudando um pouco", "mudando de assunto", "agora:")
_RETURN_CUES = ("voltando", "volta ", "primeira ideia", "do comeco", "do começo", "do inicio", "do início")
_ACK_CUES = (
    "acho que e exatamente isso que eu quero",
    "acho que é exatamente isso que eu quero",
    "e exatamente isso que eu quero",
    "é exatamente isso que eu quero",
    "fechado, seguimos assim",
    "valeu",
    "obrigado",
    "obrigada",
)


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


def _clip(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _user_messages(history: Sequence[Message]) -> list[Message]:
    return [m for m in history if m.role == MessageRole.USER and m.content.strip()]


def _assistant_messages(history: Sequence[Message]) -> list[Message]:
    return [m for m in history if m.role == MessageRole.ASSISTANT and m.content.strip()]


def _assistant_since_previous_user(history: Sequence[Message]) -> tuple[str, ...]:
    """Assistant contributions belonging to the exchange immediately before the current user turn."""
    if not history:
        return ()
    current_user_index = max(
        (idx for idx, message in enumerate(history) if message.role == MessageRole.USER and message.content.strip()),
        default=-1,
    )
    if current_user_index <= 0:
        return ()
    previous_user_index = max(
        (
            idx
            for idx, message in enumerate(history[:current_user_index])
            if message.role == MessageRole.USER and message.content.strip()
        ),
        default=-1,
    )
    if previous_user_index < 0:
        return ()
    return tuple(
        message.content.strip()
        for message in history[previous_user_index + 1 : current_user_index]
        if message.role == MessageRole.ASSISTANT and message.content.strip()
    )


def _last_user_question_before_current(users: Sequence[Message]) -> str:
    for message in reversed(users[:-1]):
        text = message.content.strip()
        folded = _fold(text)
        if "?" in text or any(cue in folded for cue in ("qual ", "como ", "onde ", "quando ", "por que", "porque ")):
            return text
    return users[-2].content.strip() if len(users) > 1 else ""


def _last_substantive_user_before_current(users: Sequence[Message]) -> str:
    for message in reversed(users[:-1]):
        text = message.content.strip()
        folded = _fold(text)
        if not any(cue in folded for cue in _CONTROL_CUES):
            return text
    return users[-2].content.strip() if len(users) > 1 else ""


def _user_owned_choices(frame: FocusFrame, current: str, limit: int = 6) -> tuple[str, ...]:
    """Recent product/decision lines owned by the user, excluding conversational control turns."""
    result: list[str] = []
    current_folded = _fold(current)
    for line in reversed(frame.user_lines[:-1]):
        folded = _fold(line)
        if folded == current_folded:
            continue
        if any(cue in folded for cue in _CONTROL_CUES):
            continue
        if folded.startswith(("morgana,", "todd,")) and len(line.split()) < 12:
            continue
        if len(line.split()) < 4:
            continue
        result.append(_clip(line, 260))
        if len(result) >= limit:
            break
    result.reverse()
    return tuple(result)


def _is_architecture_uncertain(frame: FocusFrame) -> bool:
    folded = _fold(frame.text)
    return "arquitetur" in folded and "incomod" in folded and (
        "nao esta quebr" in folded or "nao quebr" in folded or "nao esta falh" in folded
    )


def _resolve_request(
    *,
    current: str,
    users: Sequence[Message],
    previous_assistant: str,
    previous_exchange: Sequence[str],
    active: FocusFrame,
    root: FocusFrame,
) -> tuple[str, str | None]:
    folded = _fold(current)
    referent: str | None = None
    request = current

    if "mesma pergunta" in folded:
        question = _last_user_question_before_current(users)
        if question:
            referent = question
            request = f"Responda agora, da sua propria perspectiva e sem repetir o outro agente: {question}"

    elif any(cue in folded for cue in ("voce acrescentaria", "você acrescentaria", "resposta dela ja basta", "resposta dela já basta", "resposta dele ja basta", "resposta dele já basta")):
        if previous_assistant:
            referent = previous_assistant
            request = "Avalie a fala imediatamente anterior: acrescente somente se houver algo novo e util; se ela ja for suficiente, diga isso brevemente sem inventar outro problema."

    elif any(cue in folded for cue in ("resposta dele", "resposta dela", "ponto dele", "ponto dela")):
        if previous_assistant:
            referent = previous_assistant
            request = f"Responda diretamente ao ponto da fala anterior citado pelo usuario: {current}"

    elif "aterrissa" in folded:
        if previous_assistant:
            referent = previous_assistant
            request = "Torne concreta e executavel a ideia da fala imediatamente anterior, preservando o conceito em vez de pedir contexto novamente."

    elif "sequencia curta" in folded or "sequência curta" in current.casefold():
        problem = _last_substantive_user_before_current(users)
        if problem:
            referent = problem
            request = f"Entregue uma sequencia curta de poucos passos para este problema, sem abrir novas hipoteses: {problem}"

    elif "proximo passo" in folded or "próximo passo" in current.casefold():
        problem = _last_substantive_user_before_current(users)
        if problem:
            referent = problem
            request = f"Diga o proximo passo concreto para a situacao ja descrita pelo usuario, sem pedir o contexto novamente: {problem}"

    elif "so o essencial" in folded or "só o essencial" in current.casefold():
        problem = _last_substantive_user_before_current(users)
        if problem:
            referent = problem
            request = f"Resuma apenas o essencial da decisao/discussao imediatamente anterior: {problem}"

    elif any(cue in folded for cue in ("resume a decisao", "resume a decisão", "resuma a decisao", "resuma a decisão")):
        material = " | ".join(previous_exchange[-2:])
        if material:
            referent = material
            request = "Resuma em uma frase a decisao concreta tomada na troca imediatamente anterior; nao explique o ato de resumir."

    elif any(cue in folded for cue in ("qual coisa", "o que voce cortaria", "o que você cortaria", "o que preservaria")):
        choices = _user_owned_choices(active, current)
        if choices:
            referent = " | ".join(choices)
            request = current + " Escolha entre os elementos do produto/discussao definidos pelo usuario, nao entre traits ou capacidades internas do agente."

    elif "primeira ideia" in folded or "do comeco" in folded or "do começo" in folded or "do inicio" in folded or "do início" in folded:
        referent = root.user_lines[0]
        request = "Retome a ideia inicial da call e sintetize-a usando somente escolhas/restricoes que o usuario adicionou depois."

    elif any(cue in folded for cue in ("responde primeiro", "responda primeiro")):
        prior = _last_substantive_user_before_current(users)
        if prior:
            referent = prior
            request = f"Responda primeiro ao pedido anterior do usuario; a instrucao atual regula ordem de participacao, nao substitui o conteudo: {prior}"

    elif "corto " in folded and " ou " in folded:
        referent = current
        request = (
            "O usuario pediu uma escolha binaria sobre o que cortar. Diga explicitamente qual opcao deve ser cortada e por que; "
            "nao responda com o nome da opcao que deveria ser preservada como se ela fosse o corte. " + current
        )

    return request, referent


_CLARIFICATION_FALLBACKS = (
    "preciso de mais contexto",
    "preciso de contexto",
    "qual foi a pergunta",
    "qual e a pergunta",
    "qual é a pergunta",
    "isso se refere a que",
    "isso se refere a quê",
    "poderia detalhar o conceito",
    "qual conceito voce quer",
    "qual conceito você quer",
    "por favor, especifique o topico",
    "por favor, especifique o tópico",
)

_META_ROLE_FALLBACKS = (
    "campanario e o sistema",
    "campanário é o sistema",
    "eu sou todd",
    "eu sou morgana",
    "sou um agente",
    "identidade de um agente",
    "capacidades internas",
)

_STOPWORDS = {
    "agora", "ainda", "alguma", "algum", "antes", "assim", "aquela", "aquele",
    "aquilo", "como", "comigo", "coisa", "depois", "desde", "dessa", "desse",
    "disso", "entao", "então", "essa", "esse", "esta", "estao", "estão",
    "faria", "fazer", "fosse", "mesma", "mesmo", "muito", "naquela", "naquele",
    "nao", "não", "onde", "outra", "outro", "parte", "pelo", "pela", "porque",
    "qual", "quando", "quero", "resposta", "sobre", "tambem", "também", "tudo",
    "usuario", "usuário", "voce", "você", "voces", "vocês",
}


def _anchor_terms(value: str, limit: int = 8) -> tuple[str, ...]:
    """Extract stable topical words for lightweight contract validation.

    This is deliberately lexical and conservative: it is not a semantic judge. It only prevents
    obvious loss of the bound object after the compiler already resolved the discourse act.
    """
    seen: list[str] = []
    for raw in re.findall(r"[A-Za-zÀ-ÿ0-9_-]+", value):
        folded = _fold(raw)
        if len(folded) < 5 or folded in _STOPWORDS or folded.isdigit():
            continue
        if folded not in seen:
            seen.append(folded)
        if len(seen) >= limit:
            break
    return tuple(seen)



def _semantic_terms(value: str) -> set[str]:
    return {
        token
        for token in (_fold(raw) for raw in re.findall(r"[A-Za-zÀ-ÿ0-9_-]+", value))
        if len(token) >= 4 and token not in _STOPWORDS and not token.isdigit()
    }


def _semantic_overlap(a: str, b: str) -> float:
    """Conservative lexical-semantic overlap used only for explicit 'do not repeat' contracts."""
    left = _semantic_terms(a)
    right = _semantic_terms(b)
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def _silence_criteria(text: str) -> set[str]:
    """Narrow semantic buckets for explicit same-question / do-not-repeat social turns."""
    folded = _fold(text)
    criteria: set[str] = set()
    if any(cue in folded for cue in ("apenas morgana", "apenas todd", "pergunta direcionada", "direcionada a mim", "pedido explicito")):
        criteria.add("explicit_direction")
    if any(cue in folded for cue in ("nao agreg", "nao e necess", "nao precisa", "sem valor", "redund")):
        criteria.add("no_added_value")
    if any(cue in folded for cue in ("topico conclu", "discussao completa", "ponto completo", "ja abordou")):
        criteria.add("topic_complete")
    if any(cue in folded for cue in ("pensando em voz alta", "processo de reflexao", "fluxo de pensamentos", "so reflet")):
        criteria.add("thinking_aloud")
    if "risco" in folded:
        criteria.add("risk_reduction")
    if any(cue in folded for cue in ("muda a decisao", "alterar a decisao", "mudar a decisao")):
        criteria.add("decision_change")
    if any(cue in folded for cue in ("acao util", "proximo passo", "acao concreta", "executavel")):
        criteria.add("actionability")
    return criteria


def _clear_embodiment_violation(text: str) -> bool:
    """Detect clear factual embodiment, while leaving hypothetical atmosphere/metaphor alone.

    This deliberately targets strong assertions about Todd/Morgana/self having bodies or performing
    physical actions. It does not reject phrases such as 'poderia lembrar uma biblioteca'.
    """
    folded = _fold(text)
    patterns = (
        r"\b(?:todd|morgana)\s+(?:esta|estava|fica|ficou)\s+(?:absort|sentad|em pe|caminh|rabisc|segur|tocand|olhando|observando|encostad)",
        r"\b(?:todd|morgana)\s+(?:rabisc|caminh|segur|toc|senta|levanta|olha pela|observa a luz)",
        r"\b(?:eu\s+)?(?:estou|estava)\s+(?:sentad|em pe|caminh|rabisc|segur|tocand|olhando pela|observando a luz|encostad)",
        r"\b(?:eu\s+)?(?:caminho ate|caminho até|me levanto|me sento|pego um|seguro um|toco em)",
    )
    return any(re.search(pattern, folded) for pattern in patterns)


@dataclass(frozen=True, slots=True)
class CommitmentState:
    """A user-accepted decision that must not be silently reopened by an acknowledgement turn."""

    decision: str
    status: str = "accepted"

    def render(self) -> str:
        return (
            "DECISAO JA ACEITA PELO USUARIO: " + _clip(self.decision, 420) + "\n"
            "STATUS: aceita/fechada. Nao reabra, reverta ou substitua esta decisao sem fato novo ou pedido explicito do usuario."
        )

@dataclass(frozen=True, slots=True)
class AnswerContract:
    """Binding generated from DialogueState and appended after persona/system guidance.

    DialogueState describes the conversation. AnswerContract turns the resolved discourse act into
    a narrow obligation for the current generation. Critical bindings can be validated locally and
    retried once without a second interpretive LLM call.
    """

    exact_request: str
    subject: str
    evidence: tuple[str, ...] = ()
    required_any: tuple[str, ...] = ()
    forbidden_any: tuple[str, ...] = ()
    distinct_from: tuple[str, ...] = ()
    max_semantic_overlap: float = 0.50
    reject_clarification: bool = False
    no_new_question: bool = False
    acknowledgement_only: bool = False
    max_words: int | None = None
    enforce_embodiment_boundary: bool = True
    require_novel_silence_criterion: bool = False

    def render(self) -> str:
        lines = [
            "CONTRATO DE RESPOSTA — OBRIGATORIO PARA ESTE TURNO; nao cite nem explique este bloco.",
            f"RESPONDA EXATAMENTE A: {_clip(self.exact_request, 460)}",
            f"SUJEITO/REFERENTE JA RESOLVIDO: {_clip(self.subject, 460)}",
            "Nao troque o sujeito por outro problema e nao peça contexto que ja foi resolvido acima.",
        ]
        if self.evidence:
            lines.append("MATERIAL QUE PODE SER USADO PARA RESPONDER:")
            lines.extend(f"- {_clip(item, 300)}" for item in self.evidence[-3:])
        if self.required_any:
            lines.append("A resposta deve permanecer semanticamente ancorada neste assunto; termos-ancora de verificacao: " + ", ".join(self.required_any))
        if self.forbidden_any:
            lines.append("NAO DESVIE PARA: " + "; ".join(self.forbidden_any))
        if self.distinct_from:
            lines.append("CONTRIBUICAO ANTERIOR QUE NAO DEVE SER REPETIDA:")
            lines.extend(f"- {_clip(item, 280)}" for item in self.distinct_from[-2:])
            lines.append("Responda a mesma funcao por um criterio realmente diferente; nao parafraseie a contribuicao anterior.")
        if self.require_novel_silence_criterion:
            lines.append("Para esta pergunta social, acrescente pelo menos UM criterio de silencio que nao esteja na resposta anterior (por exemplo: nao mudar a decisao, nao reduzir risco ou nao acrescentar proximo passo util).")
        if self.reject_clarification:
            lines.append("O referente necessario ja esta resolvido. Nao responda pedindo para repetir a pergunta, explicar 'isso' ou fornecer mais contexto.")
        if self.no_new_question:
            lines.append("Nao abra nova pergunta, tarefa ou proximo assunto neste turno.")
        if self.acknowledgement_only:
            lines.append("Este turno apenas confirma/encerra uma decisao ja aceita: reconheca brevemente; nao reanalise nem proponha mudanca.")
        if self.max_words is not None:
            lines.append(f"Seja breve: no maximo {self.max_words} palavras neste turno.")
        if self.enforce_embodiment_boundary:
            lines.append("Atmosfera/metafora e permitida, mas nao afirme como fato que Todd/Morgana possuem corpo, estao fisicamente em um local ou executam acoes corporais, salvo roleplay/ficcao explicitamente pedido pelo usuario.")
        return "\n".join(lines)

    def violations(self, text: str) -> tuple[str, ...]:
        folded = _fold(text)
        problems: list[str] = []
        if self.reject_clarification and any(_fold(marker) in folded for marker in _CLARIFICATION_FALLBACKS):
            problems.append("asked_for_already_resolved_context")
        if self.no_new_question and "?" in text:
            problems.append("opened_new_question")
        if self.forbidden_any and any(_fold(marker) in folded for marker in self.forbidden_any):
            problems.append("entered_forbidden_topic")
        if self.required_any and not any(_fold(marker) in folded for marker in self.required_any):
            problems.append("lost_required_subject")
        if self.distinct_from and any(_semantic_overlap(text, previous) > self.max_semantic_overlap for previous in self.distinct_from):
            problems.append("repeated_previous_contribution")
        if self.require_novel_silence_criterion and self.distinct_from:
            prior_criteria: set[str] = set()
            for previous in self.distinct_from:
                prior_criteria.update(_silence_criteria(previous))
            current_criteria = _silence_criteria(text)
            if not (current_criteria - prior_criteria):
                problems.append("no_novel_silence_criterion")
        if self.acknowledgement_only and any(marker in folded for marker in (
            "ainda faria", "ainda mexeria", "eu mudaria", "recomendo", "deveriamos", "deveríamos",
            "precisamos revisar", "por outro lado", "no entanto", "porem", "porém"
        )):
            problems.append("reopened_accepted_decision")
        if self.max_words is not None and len(text.split()) > self.max_words:
            problems.append("too_long_for_turn")
        if self.enforce_embodiment_boundary and _clear_embodiment_violation(text):
            problems.append("invented_physical_embodiment")
        return tuple(problems)

    def validates(self, text: str) -> bool:
        return not self.violations(text)

    @property
    def retry_note(self) -> str:
        return (
            self.render()
            + "\nA tentativa anterior violou este contrato. Gere novamente apenas a resposta pedida, "
              "preservando o sujeito resolvido e sem comentar a correcao."
        )


def build_answer_contract(state: "DialogueState") -> AnswerContract:
    folded = _fold(state.current_request)
    subject = state.immediate_referent or state.active_topic or state.root_goal
    evidence: tuple[str, ...] = ()
    required: tuple[str, ...] = ()
    forbidden: list[str] = []
    distinct_from: tuple[str, ...] = ()
    reject_clarification = False
    acknowledgement_only = False
    max_words: int | None = None
    max_semantic_overlap = 0.50
    require_novel_silence_criterion = False

    if state.previous_exchange and any(
        cue in folded for cue in ("resposta", "ponto", "mesma pergunta", "resume", "resuma", "aterrissa", "acrescent", "basta", "responde primeiro", "responda primeiro")
    ):
        evidence = state.previous_exchange[-2:]

    if any(cue in folded for cue in ("mesma pergunta", "aterrissa", "sequencia curta", "proximo passo", "próximo passo", "resposta dele", "resposta dela", "ponto dele", "ponto dela", "responde primeiro", "responda primeiro")):
        reject_clarification = True

    if any(cue in folded for cue in ("responde primeiro", "responda primeiro")) and state.previous_exchange:
        # Ordering instructions do not authorize a content reversal. Keep the agent's immediately
        # preceding position unless the user supplied new evidence (which this control turn does not).
        evidence = state.previous_exchange[-1:]

    if "mesma pergunta" in folded and any(token in _fold(subject) for token in ("quiet", "silencio", "silêncio")):
        required = ("silenc", "quiet", "redund", "suficiente", "nao agreg", "não agreg", "nao precisa", "não precisa", "muda", "risco", "decis")
        if state.previous_exchange:
            distinct_from = state.previous_exchange[-1:]
            # Explicit "nao repete" means a genuinely new criterion, not a close paraphrase.
            # Keep this local to explicit same-question contribution turns so ordinary agreement
            # elsewhere remains natural.
            max_semantic_overlap = 0.34
            require_novel_silence_criterion = True
    elif "aterrissa" in folded:
        required = _anchor_terms(subject, 8)
    elif "sequencia curta" in folded or "sequência curta" in state.current_request.casefold():
        required = _anchor_terms(subject, 6)
    elif "proximo passo" in folded or "próximo passo" in state.current_request.casefold():
        required = _anchor_terms(subject, 6)
    elif any(cue in folded for cue in ("responde primeiro", "responda primeiro")):
        required = _anchor_terms(subject, 8)
    elif any(cue in folded for cue in ("resume a decisao", "resume a decisão", "resuma a decisao", "resuma a decisão")):
        material = " ".join(state.previous_exchange)
        required = _anchor_terms(material or subject, 7)
    elif any(cue in folded for cue in ("qual coisa", "cortaria", "preservaria", "so o essencial", "só o essencial")):
        # Product ellipses bind to user-owned product choices. A cut usually targets the most
        # recent branch; preservation/essential summaries may legitimately retain the root idea.
        if "cortaria" in folded:
            material = " ".join(state.user_choices[-3:])
        else:
            material = state.root_goal + " " + " ".join(state.user_choices)
        required = _anchor_terms(material or subject, 20)
        forbidden.extend(_META_ROLE_FALLBACKS)
    elif any(cue in folded for cue in ("primeira ideia", "do comeco", "do começo", "do inicio", "do início")):
        required = _anchor_terms(state.root_goal + " " + " ".join(state.user_choices), 8)
        forbidden.extend(_META_ROLE_FALLBACKS)

    # Freeze-candidate naturality: social call semantics should sound like conversation, not
    # internal documentation. Keep architecture vocabulary available everywhere else.
    social_naturality_turn = any(cue in folded for cue in (
        "ficar quiet", "pensando em voz alta", "chamar voces pelo nome", "chamar vocês pelo nome",
        "nao quero precisar chamar", "não quero precisar chamar",
    ))
    if social_naturality_turn:
        forbidden.extend((
            "o protocolo", "protocolo social", "participation arbiter", "o arbiter",
            "o sistema avalia", "contrato de resposta", "dialogue state", "focus stack",
        ))

    # Directed arithmetic/factual micro-turns should stay micro-turns. The arithmetic anchor still
    # guarantees fidelity later in the pipeline; this only prevents unnecessary commentary.
    trivial_arithmetic = bool(re.search(
        r"\b\d+(?:[.,]\d+)?\s*(?:vezes|x|×|\*|mais|\+|menos|-|dividido\s+por|/)\s*\d+(?:[.,]\d+)?\b",
        state.current_request,
        re.IGNORECASE,
    )) and any(cue in folded for cue in ("quanto", "da quanto", "dá quanto", "igual a", "resultado"))
    if trivial_arithmetic:
        max_words = 14
        no_new_question = True

    if state.closure or state.acknowledgement:
        no_new_question = True
    if state.closure and any(cue in folded for cue in ("vou trabalhar agora", "vou voltar ao trabalho", "vou trabalhar")):
        max_words = 6
        forbidden.extend(("ponto de convergencia", "ponto de convergência", "chegamos a um ponto", "parece que chegamos"))
    else:
        no_new_question = locals().get("no_new_question", False)

    if state.commitment is not None and (state.closure or state.acknowledgement):
        subject = state.commitment.decision
        evidence = (state.commitment.decision,)
        acknowledgement_only = True
        max_words = 18
        # An acknowledgement must not silently re-enter internal Campanario architecture either.
        forbidden.extend(("papéis e responsabilidades", "papeis e responsabilidades", "funcionalidades de cada agente", "roteamento de agentes"))

    return AnswerContract(
        exact_request=state.resolved_request,
        subject=subject,
        evidence=evidence,
        required_any=required,
        forbidden_any=tuple(forbidden),
        distinct_from=distinct_from,
        max_semantic_overlap=max_semantic_overlap,
        reject_clarification=reject_clarification,
        no_new_question=no_new_question,
        acknowledgement_only=acknowledgement_only,
        max_words=max_words,
        enforce_embodiment_boundary=True,
        require_novel_silence_criterion=require_novel_silence_criterion,
    )


@dataclass(frozen=True, slots=True)
class DialogueState:
    root_goal: str
    active_topic: str
    current_request: str
    resolved_request: str
    immediate_referent: str | None
    user_choices: tuple[str, ...]
    previous_exchange: tuple[str, ...]
    other_topics: tuple[str, ...]
    forbidden_assumptions: tuple[str, ...]
    commitment: CommitmentState | None
    closure: bool
    acknowledgement: bool

    def render(self) -> str:
        """Compact model-facing state. It contains conversational facts, not compiler mechanics."""
        lines = [
            "ESTADO DA CONVERSA — use silenciosamente; nao cite nem explique este bloco.",
            f"OBJETO/OBJETIVO RAIZ: {_clip(self.root_goal, 320)}",
            f"ASSUNTO ATIVO: {_clip(self.active_topic, 320)}",
            f"PEDIDO A RESPONDER AGORA: {_clip(self.resolved_request, 420)}",
        ]
        if self.immediate_referent:
            lines.append(f"REFERENTE IMEDIATO: {_clip(self.immediate_referent, 480)}")
        if self.user_choices:
            lines.append("ESCOLHAS/RESTRICOES DO USUARIO NESTE ASSUNTO:")
            lines.extend(f"- {_clip(item, 240)}" for item in self.user_choices[-5:])
        if self.previous_exchange and any(
            cue in _fold(self.current_request)
            for cue in ("resposta", "ponto", "resume", "resuma", "acrescent", "basta", "aterrissa")
        ):
            lines.append("TROCA IMEDIATAMENTE ANTERIOR RELEVANTE:")
            lines.extend(f"- {_clip(item, 300)}" for item in self.previous_exchange[-2:])
        if self.other_topics:
            lines.append("ASSUNTOS SUSPENSOS (nao misturar sem o usuario voltar a eles):")
            lines.extend(f"- {_clip(item, 180)}" for item in self.other_topics[-3:])
        if self.forbidden_assumptions:
            lines.append("NAO ASSUMIR/INVENTAR:")
            lines.extend(f"- {item}" for item in self.forbidden_assumptions)
        if self.commitment is not None:
            lines.append(self.commitment.render())
        if self.closure:
            lines.append("ESTE TURNO E DE ENCERRAMENTO/RETORNO AO TRABALHO: responda curto e nao abra uma nova pergunta ou tarefa.")
        elif self.acknowledgement:
            lines.append("ESTE TURNO E UM ACKNOWLEDGEMENT/CONFIRMACAO: reconheca brevemente e nao abra um novo assunto, pergunta ou tarefa.")
        lines.extend(
            (
                "Use o historico para estilo e detalhes, mas este estado decide qual problema esta sendo respondido agora.",
                "Se o contexto necessario ja aparece acima, nao peça que o usuario o repita.",
                "Termos genericos como arquitetura, sistema, ferramenta e produto pertencem ao objeto do usuario, nao ao Campanario interno, salvo pedido explicito.",
            )
        )
        return "\n".join(lines)


def compile_dialogue_state(history: Sequence[Message]) -> DialogueState | None:
    """Compile a deterministic, typed short-term dialogue state without another LLM call."""
    stack = build_focus_stack(history)
    users = _user_messages(history)
    if stack is None or not users:
        return None

    current = users[-1].content.strip()
    active = stack.active
    root = stack.root
    previous_assistant = next(
        (message.content.strip() for message in reversed(history[:-1]) if message.role == MessageRole.ASSISTANT and message.content.strip()),
        "",
    )
    previous_exchange = _assistant_since_previous_user(history)
    resolved_request, referent = _resolve_request(
        current=current,
        users=users,
        previous_assistant=previous_assistant,
        previous_exchange=previous_exchange,
        active=active,
        root=root,
    )

    forbidden: list[str] = []
    if _is_architecture_uncertain(active):
        forbidden.append(
            "qual parte/modulo/integracao da arquitetura esta errada, gargalos, filas, roteamento, performance ou seguranca que o usuario nao informou"
        )
    forbidden.append("trocar o objeto do usuario pela arquitetura, agentes, memoria ou mecanismos internos do Campanario")

    folded = _fold(current)
    if any(cue in folded for cue in ("qual coisa", "cortaria", "preservaria", "primeira ideia", "so o essencial", "só o essencial")):
        forbidden.append("responder com trait/persona/capacidade interna quando o pedido e sobre o produto ou decisao em discussao")

    other_topics = tuple(
        frame.user_lines[0]
        for frame in stack.frames
        if frame.id != active.id and frame.user_lines
    )
    closure = any(cue in folded for cue in _CLOSURE_CUES)
    acknowledgement = any(cue in folded for cue in _ACK_CUES)
    commitment: CommitmentState | None = None
    decision_acceptance = any(cue in folded for cue in (
        "fechado, seguimos assim",
        "acho que e exatamente isso que eu quero",
        "acho que é exatamente isso que eu quero",
        "e exatamente isso que eu quero",
        "é exatamente isso que eu quero",
        "nao precisa adicionar mais nada",
        "não precisa adicionar mais nada",
    ))
    if decision_acceptance and previous_exchange:
        # Only explicit acceptance closes a decision. Pure social departure (e.g. "vou trabalhar
        # agora") must not bind the previous acknowledgement as a new decision.
        decision = " | ".join(previous_exchange[-2:]).strip()
        if decision:
            commitment = CommitmentState(decision=decision)

    # For a return move, active.user_lines[-1] is the return command itself. The first line is a
    # better human-readable topic label; root_goal remains available separately.
    active_topic = active.user_lines[0]
    if any(cue in folded for cue in _SHIFT_CUES):
        active_topic = active.user_lines[-1]
    elif not any(cue in folded for cue in _RETURN_CUES) and len(active.user_lines) > 1:
        candidate = _last_substantive_user_before_current(users)
        if candidate and candidate in active.user_lines:
            active_topic = candidate

    return DialogueState(
        root_goal=root.user_lines[0],
        active_topic=active_topic,
        current_request=current,
        resolved_request=resolved_request,
        immediate_referent=referent,
        user_choices=_user_owned_choices(active, current),
        previous_exchange=previous_exchange,
        other_topics=other_topics,
        forbidden_assumptions=tuple(forbidden),
        commitment=commitment,
        closure=closure,
        acknowledgement=acknowledgement,
    )


class DialogueStateCompiler:
    """Stateless compiler boundary used by ChatService and future realtime clients."""

    def compile(self, history: Sequence[Message]) -> DialogueState | None:
        return compile_dialogue_state(history)
