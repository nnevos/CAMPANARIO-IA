from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.models import ChatSession, Message, MessageRole
from campanario.chat.service import ChatService
from campanario.model.protocol import FakeModelProvider


class InMemorySessions:
    def __init__(self) -> None:
        self.items: dict[UUID, ChatSession] = {}

    def create(self, session: ChatSession) -> ChatSession:
        self.items[session.id] = session
        return session

    def get(self, session_id: UUID) -> ChatSession | None:
        return self.items.get(session_id)

    def list(self) -> list[ChatSession]:
        return list(self.items.values())

    def set_primary_agent(self, session_id: UUID, agent_id: str) -> ChatSession | None:
        current = self.items.get(session_id)
        if current is None:
            return None
        updated = ChatSession(
            id=current.id,
            title=current.title,
            status=current.status,
            created_at=current.created_at,
            updated_at=current.updated_at,
            primary_agent_id=agent_id,
        )
        self.items[session_id] = updated
        return updated


class InMemoryMessages:
    def __init__(self) -> None:
        self.items: list[Message] = []

    def append(self, message: Message) -> Message:
        self.items.append(message)
        return message

    def list_by_session(self, session_id: UUID) -> list[Message]:
        return [message for message in self.items if message.session_id == session_id]


@pytest.mark.asyncio
async def test_chat_service_persists_user_and_assistant_messages() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    service = ChatService(
        sessions,
        messages,
        FakeModelProvider("resposta"),
        RecentMessagesContextManager(20),
        "fake-model",
    )
    session = service.create_session()

    streamed = "".join([chunk async for chunk in service.stream_reply(session.id, "olá")])

    assert streamed == "resposta"
    history = service.get_messages(session.id)
    assert [message.content for message in history] == ["olá", "resposta"]
    assert history[1].model == "fake-model"


class FailingModelProvider:
    async def health(self) -> bool:
        return False

    async def stream(self, request):
        from campanario.model.protocol import ModelUnavailableError

        if False:
            yield
        raise ModelUnavailableError("model unavailable")


@pytest.mark.asyncio
async def test_chat_service_keeps_user_message_and_does_not_persist_assistant_on_model_failure() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    service = ChatService(
        sessions,
        messages,
        FailingModelProvider(),
        RecentMessagesContextManager(20),
        "fake-model",
    )
    session = service.create_session()

    from campanario.model.protocol import ModelUnavailableError

    with pytest.raises(ModelUnavailableError):
        _ = [chunk async for chunk in service.stream_reply(session.id, "mensagem importante")]

    history = service.get_messages(session.id)
    assert [message.content for message in history] == ["mensagem importante"]
    assert history[0].role.value == "user"


class RecordingContextManager:
    def __init__(self) -> None:
        self.history: list[Message] | None = None

    async def build(self, history):
        from campanario.model.protocol import ModelMessage

        self.history = list(history)
        return (ModelMessage(role=self.history[-1].role, content="context-selected"),)


class RecordingProvider:
    def __init__(self) -> None:
        self.request = None

    async def health(self) -> bool:
        return True

    async def stream(self, request):
        from campanario.model.protocol import ModelChunk

        self.request = request
        yield ModelChunk(text="ok")


@pytest.mark.asyncio
async def test_chat_service_delegates_context_selection() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    context_manager = RecordingContextManager()
    provider = RecordingProvider()
    service = ChatService(sessions, messages, provider, context_manager, "fake-model")
    session = service.create_session()

    _ = [chunk async for chunk in service.stream_reply(session.id, "mensagem atual")]

    assert context_manager.history is not None
    assert [message.content for message in context_manager.history] == ["mensagem atual"]
    assert provider.request is not None
    assert provider.request.messages[-1].content == "context-selected"
    assert "AGENTE COM PRIORIDADE DE FALA: MORGANA" in provider.request.messages[0].content

@pytest.mark.asyncio
async def test_chat_service_switches_agent_per_session_and_persists_response_provenance() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = RecordingProvider()
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
    )
    session = service.create_session(agent_id="todd")

    _ = [chunk async for chunk in service.stream_reply(session.id, "oi")]
    assert service.get_messages(session.id)[-1].agent_id == "todd"
    assert provider.request is not None
    assert "AGENTE COM PRIORIDADE DE FALA: TODD" in provider.request.messages[0].content

    updated = service.set_session_agent(session.id, "morgana")
    assert updated.primary_agent_id == "morgana"
    _ = [chunk async for chunk in service.stream_reply(session.id, "continua")]
    assert service.get_messages(session.id)[-1].agent_id == "morgana"
    assert provider.request is not None
    assert "AGENTE COM PRIORIDADE DE FALA: MORGANA" in provider.request.messages[0].content
    assert "outros agentes: todd" in provider.request.messages[0].content.lower()

@pytest.mark.asyncio
async def test_direct_wake_switches_bridge_agent_and_provenance() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = RecordingProvider()
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
    )
    session = service.create_session()
    assert session.primary_agent_id == "morgana"

    _ = [chunk async for chunk in service.stream_reply(session.id, "Todd, olha isso")]
    assert sessions.get(session.id).primary_agent_id == "todd"
    assert service.get_messages(session.id)[-1].agent_id == "todd"
    assert provider.request is not None
    assert "AGENTE COM PRIORIDADE DE FALA: TODD" in provider.request.messages[0].content

    _ = [chunk async for chunk in service.stream_reply(session.id, "Campanário")]
    assert sessions.get(session.id).primary_agent_id == "todd"
    assert service.get_messages(session.id)[-1].agent_id == "todd"

    _ = [chunk async for chunk in service.stream_reply(session.id, "Morgana")]
    assert sessions.get(session.id).primary_agent_id == "morgana"
    assert service.get_messages(session.id)[-1].agent_id == "morgana"

class QueueProvider:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.requests = []

    async def health(self) -> bool:
        return True

    async def stream(self, request):
        from campanario.model.protocol import ModelChunk
        self.requests.append(request)
        response = self.responses.pop(0)
        yield ModelChunk(text=response)
        yield ModelChunk(text="", done=True)


class JoinDecisionProvider:
    async def health(self) -> bool:
        return True

    async def stream(self, request):
        from campanario.model.protocol import ModelChunk
        yield ModelChunk(text="JOIN")
        yield ModelChunk(text="", done=True)


@pytest.mark.asyncio
async def test_explicit_group_turn_can_produce_two_agent_messages_in_same_session() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider(["Morgana primeiro.", "Todd complementa."])
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
    )
    session = service.create_session()

    events = [event async for event in service.stream_turn(session.id, "Morgana e Todd, o que vocês acham disso?")]

    starts = [event.agent_id for event in events if event.type == "speaker_start"]
    assert starts == ["morgana", "todd"]
    assistant_messages = [m for m in service.get_messages(session.id) if m.role.value == "assistant"]
    assert [(m.agent_id, m.content) for m in assistant_messages] == [
        ("morgana", "Morgana primeiro."),
        ("todd", "Todd complementa."),
    ]
    assert sessions.get(session.id).primary_agent_id == "morgana"


@pytest.mark.asyncio
async def test_secondary_can_spontaneously_join_open_discussion_when_arbiter_finds_distinct_value() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider(["Eu iria pelo caminho A.", "Eu discordo do A por causa do risco B."])
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
        participation_provider=JoinDecisionProvider(),
    )
    session = service.create_session()

    events = [event async for event in service.stream_turn(session.id, "o que você acha dessa decisão?")]

    assert [event.agent_id for event in events if event.type == "speaker_start"] == ["morgana", "todd"]
    history = service.get_messages(session.id)
    assert [m.agent_id for m in history if m.role.value == "assistant"] == ["morgana", "todd"]
    assert sessions.get(session.id).primary_agent_id == "morgana"


@pytest.mark.asyncio
async def test_closed_factual_turn_does_not_spawn_panel_even_if_decider_would_join() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider(["Wellington."])
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
        participation_provider=JoinDecisionProvider(),
    )
    session = service.create_session()

    events = [event async for event in service.stream_turn(session.id, "qual é a capital da Nova Zelândia?")]
    assert [event.agent_id for event in events if event.type == "speaker_start"] == ["morgana"]

@pytest.mark.asyncio
async def test_short_social_share_may_invite_secondary_but_greeting_does_not() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider(["Entendi.", "Eu acrescentaria uma coisa."])
    service = ChatService(
        sessions,
        messages,
        provider,
        RecentMessagesContextManager(20),
        "fake-model",
        participation_provider=JoinDecisionProvider(),
    )
    session = service.create_session()
    share_events = [event async for event in service.stream_turn(session.id, "hoje tô meio perdido")]
    assert [e.agent_id for e in share_events if e.type == "speaker_start"] == ["morgana", "todd"]

    sessions2 = InMemorySessions()
    messages2 = InMemoryMessages()
    provider2 = QueueProvider(["Opa."])
    service2 = ChatService(
        sessions2,
        messages2,
        provider2,
        RecentMessagesContextManager(20),
        "fake-model",
        participation_provider=JoinDecisionProvider(),
    )
    session2 = service2.create_session()
    greet_events = [event async for event in service2.stream_turn(session2.id, "eae")]
    assert [e.agent_id for e in greet_events if e.type == "speaker_start"] == ["morgana"]

@pytest.mark.asyncio
async def test_agent_output_strips_only_own_leading_speaker_header_before_persisting() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider(["**Morgana:** Meu ponto e manter a parte estavel."])
    service = ChatService(sessions, messages, provider, RecentMessagesContextManager(20), "fake-model")
    session = service.create_session()

    events = [event async for event in service.stream_turn(session.id, "Morgana, o que voce acha?")]
    tokens = "".join(event.text for event in events if event.type == "token")

    assert tokens == "Meu ponto e manter a parte estavel."
    assert service.get_messages(session.id)[-1].content == tokens


@pytest.mark.asyncio
async def test_agent_output_retries_instead_of_silently_accepting_foreign_speaker_transcript() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider([
        "Todd: Eu faria A. Morgana: Eu faria B.",
        "Eu manteria a parte estavel e testaria a alternativa em paralelo.",
    ])
    service = ChatService(sessions, messages, provider, RecentMessagesContextManager(20), "fake-model")
    session = service.create_session()

    events = [event async for event in service.stream_turn(session.id, "Morgana, decide esse ponto.")]
    tokens = "".join(event.text for event in events if event.type == "token")

    assert tokens == "Eu manteria a parte estavel e testaria a alternativa em paralelo."
    assert "Todd:" not in tokens and "Morgana:" not in tokens
    assert len(provider.requests) == 2
    assert "SPEAKER OUTPUT REPAIR" in provider.requests[1].messages[0].content


@pytest.mark.asyncio
async def test_arithmetic_social_correction_is_anchored_and_falls_back_deterministically() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider([
        "Dezesseis vezes sete e cento e doze, nao cento e vinte e quatro.",
        "Ainda acho que 16 vezes 7 e 112.",
    ])
    service = ChatService(sessions, messages, provider, RecentMessagesContextManager(20), "fake-model")
    session = service.create_session()

    text = "Todd, suponha que a Morgana tenha dito que 18 vezes 7 é 124. Corrige o ponto em uma frase."
    events = [event async for event in service.stream_turn(session.id, text)]
    tokens = "".join(event.text for event in events if event.type == "token")

    assert tokens == "18 vezes 7 e 126, nao 124."
    assert service.get_messages(session.id)[-1].content == tokens
    assert len(provider.requests) == 2
    assert "CORRECAO FACTUAL ANCORADA" in provider.requests[0].messages[0].content
    assert "resultado correto 126" in provider.requests[1].messages[0].content


@pytest.mark.asyncio
async def test_agent_output_recovers_explicit_own_segment_if_repair_still_returns_panel() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider([
        "Todd: Eu faria A. Morgana: Eu faria B.",
        "Todd: Eu faria C.  Morgana: Eu manteria a parte estável e validaria em paralelo.",
    ])
    service = ChatService(sessions, messages, provider, RecentMessagesContextManager(20), "fake-model")
    session = service.create_session()

    events = [event async for event in service.stream_turn(session.id, "Morgana, decide esse ponto.")]
    tokens = "".join(event.text for event in events if event.type == "token")

    assert tokens == "Eu manteria a parte estável e validaria em paralelo."
    assert "Todd:" not in tokens and "Morgana:" not in tokens
    assert service.get_messages(session.id)[-1].content == tokens


def test_working_conversation_state_preserves_long_call_object_and_return_anchors() -> None:
    from campanario.chat.working_context import working_conversation_note

    sid = uuid4()
    def msg(role, content, agent_id=None):
        return Message(id=uuid4(), session_id=sid, role=role, content=content, created_at=datetime.now(UTC), agent_id=agent_id)

    history = [
        msg(MessageRole.USER, "quero pensar numa ferramenta local de produtividade que já funciona e tenho três semanas para entregar"),
        msg(MessageRole.ASSISTANT, "Vamos separar o que precisa mudar do que só incomoda.", "morgana"),
        msg(MessageRole.USER, "uma parte da arquitetura me incomoda, mas ela não está quebrando"),
        msg(MessageRole.ASSISTANT, "Eu deixaria a parte estável quieta por enquanto.", "todd"),
        msg(MessageRole.USER, "ontem tivemos um pico de latência sem erro nos logs"),
        msg(MessageRole.ASSISTANT, "Comece medindo onde o atraso aparece.", "morgana"),
        msg(MessageRole.USER, "não quero vinte hipóteses; me deem uma sequência curta"),
        msg(MessageRole.ASSISTANT, "Meça cliente, servidor e banco nessa ordem.", "todd"),
        msg(MessageRole.USER, "voltando à arquitetura do começo: vocês ainda mexeriam nela antes da entrega?"),
    ]
    note = working_conversation_note(history)
    folded = note.lower()
    assert "ferramenta local de produtividade" in folded
    assert "arquitetura me incomoda" in folded
    assert "pico de latência" in folded
    assert "voltando à arquitetura do começo" in folded
    assert "nao troque pelo funcionamento interno do campanario" in folded


def test_focus_stack_suspends_tangent_and_restores_presence_frame() -> None:
    from campanario.chat.working_context import build_focus_stack, working_conversation_note

    sid = uuid4()
    def msg(role, content, agent_id=None):
        return Message(id=uuid4(), session_id=sid, role=role, content=content, created_at=datetime.now(UTC), agent_id=agent_id)

    history = [
        msg(MessageRole.USER, "é sobre deixar o Campanário rodando como presença durante meu trabalho"),
        msg(MessageRole.ASSISTANT, "Vamos pensar nessa presença.", "morgana"),
        msg(MessageRole.USER, "vocês dois acham que isso pode ficar irritante depois de algumas horas?"),
        msg(MessageRole.USER, "mudando totalmente: 24 vezes 6 dá quanto, Morgana?"),
        msg(MessageRole.ASSISTANT, "144.", "morgana"),
        msg(MessageRole.USER, "Todd, suponha que eu diga agora que ela respondeu 142. Corrige só esse ponto."),
        msg(MessageRole.ASSISTANT, "O cálculo correto é 144.", "todd"),
        msg(MessageRole.USER, "boa. voltando ao assunto de presença: eu não quero precisar chamar vocês pelo nome toda hora."),
    ]
    stack = build_focus_stack(history)
    assert stack is not None
    assert len(stack.frames) == 2
    assert "presença" in stack.active.text.lower()
    assert "24 vezes 6" in stack.frames[1].text.lower()

    note = working_conversation_note(history).lower()
    assert "assunto atualmente retomado/ativo" in note
    assert "outros assuntos mencionados antes" in note
    assert "24 vezes 6" in note
    assert "mantenha separados" in note


def test_focus_stack_keeps_user_product_focus_over_agent_memory_tangent() -> None:
    from campanario.chat.working_context import working_conversation_note

    sid = uuid4()
    def msg(role, content, agent_id=None):
        return Message(id=uuid4(), session_id=sid, role=role, content=content, created_at=datetime.now(UTC), agent_id=agent_id)

    history = [
        msg(MessageRole.USER, "o Campanário deveria parecer um lugar onde vocês já estão, não uma ferramenta que eu abro"),
        msg(MessageRole.USER, "uma coisa que eu gosto é o círculo central respirando"),
        msg(MessageRole.USER, "e as cores: Todd vermelho, Morgana âmbar, resto preto e branco"),
        msg(MessageRole.USER, "eu estava pensando em colocar controles visíveis para tudo"),
        msg(MessageRole.USER, "acho que vocês estão complicando. Me deem só o essencial"),
        msg(MessageRole.ASSISTANT, "Talvez a memória do Campanário também possa aparecer na interface.", "morgana"),
        msg(MessageRole.USER, "Todd, qual coisa você cortaria primeiro?"),
    ]
    note = working_conversation_note(history).lower()
    assert "controles visíveis" in note
    assert "circulo central" in note or "círculo central" in note
    assert "sugestao lateral" in note
    # The agent-introduced memory tangent is not promoted into the user-owned focus stack.
    assert "memória do campanário também" not in note


def test_focus_stack_save_then_return_to_architecture_frame() -> None:
    from campanario.chat.working_context import build_focus_stack, working_conversation_note

    sid = uuid4()
    def msg(role, content, agent_id=None):
        return Message(id=uuid4(), session_id=sid, role=role, content=content, created_at=datetime.now(UTC), agent_id=agent_id)

    history = [
        msg(MessageRole.USER, "quero pensar num app local simples; tenho três semanas para entregar"),
        msg(MessageRole.USER, "uma parte da arquitetura me incomoda, mas não está quebrando"),
        msg(MessageRole.USER, "mudando um pouco: ontem tivemos um pico de latência sem erro nos logs"),
        msg(MessageRole.USER, "não quero vinte hipóteses; me deem uma sequência curta"),
        msg(MessageRole.USER, "ok, guarda esse raciocínio. Agora: se eu tiver que cortar escopo, corto observabilidade ou uma feature secundária?"),
        msg(MessageRole.USER, "voltando à arquitetura do começo: vocês ainda mexeriam nela antes da entrega?"),
    ]
    stack = build_focus_stack(history)
    assert stack is not None
    assert len(stack.frames) == 3
    assert "arquitetura" in stack.active.text.lower()
    assert stack.frames[1].saved is True
    note = working_conversation_note(history).lower()
    assert "o usuario pediu para lembrar" in note
    assert "arquitetura" in note


@pytest.mark.asyncio
async def test_long_call_arithmetic_correction_anchors_previous_user_question() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider(["24 vezes 6 dá 144.", "Ela respondeu 143.", "Ainda 143."])
    service = ChatService(sessions, messages, provider, RecentMessagesContextManager(20), "fake-model")
    session = service.create_session()

    first = [event async for event in service.stream_turn(session.id, "24 vezes 6 dá quanto, Morgana?")]
    assert "144" in "".join(event.text for event in first if event.type == "token")

    second = [event async for event in service.stream_turn(session.id, "Todd, suponha que eu diga agora que ela respondeu 142. Corrige só esse ponto.")]
    answer = "".join(event.text for event in second if event.type == "token")
    assert "24" in answer and "6" in answer and "144" in answer
    assert "143" not in answer


def test_working_context_reinforces_same_question_and_deictic_referent_without_runtime_jargon() -> None:
    from campanario.chat.working_context import working_conversation_note

    sid = uuid4()
    def msg(role, content, agent_id=None):
        return Message(id=uuid4(), session_id=sid, role=role, content=content, created_at=datetime.now(UTC), agent_id=agent_id)

    history = [
        msg(MessageRole.USER, "é sobre deixar o Campanário rodando como presença durante meu trabalho"),
        msg(MessageRole.USER, "Morgana, qual sinal faria você ficar quieta em vez de entrar na conversa?"),
        msg(MessageRole.ASSISTANT, "Quando Todd já respondeu o suficiente e eu não agregaria nada novo.", "morgana"),
        msg(MessageRole.USER, "Todd, mesma pergunta pra você, mas não repete a Morgana."),
    ]
    note = working_conversation_note(history)
    folded = note.lower()
    assert "qual sinal faria você ficar quieta" in folded
    assert "quando todd já respondeu" in folded
    assert "frame ativo" not in folded
    assert "answer binding" not in folded
    assert "conversation focus stack" not in folded


def test_working_context_root_synthesis_is_user_owned_and_lists_product_anchors() -> None:
    from campanario.chat.working_context import working_conversation_note

    sid = uuid4()
    def msg(role, content, agent_id=None):
        return Message(id=uuid4(), session_id=sid, role=role, content=content, created_at=datetime.now(UTC), agent_id=agent_id)

    history = [
        msg(MessageRole.USER, "o Campanário deveria parecer um lugar onde vocês já estão, não uma ferramenta que eu abro"),
        msg(MessageRole.USER, "uma coisa que eu gosto é o círculo central respirando"),
        msg(MessageRole.USER, "e as cores: Todd vermelho, Morgana âmbar, resto preto e branco"),
        msg(MessageRole.USER, "eu estava pensando em colocar controles visíveis para tudo"),
        msg(MessageRole.ASSISTANT, "Eu preservaria minha capacidade de conectar informações díspares.", "morgana"),
        msg(MessageRole.USER, "volta à primeira ideia da call e fecha um conceito único juntando só o que sobreviveu"),
    ]
    note = working_conversation_note(history).lower()
    assert "lugar onde vocês já estão" in note
    assert "circulo" in note or "círculo" in note
    assert "vermelho" in note and "ambar" in note
    assert "primeira ideia" in note
    assert "capacidade de conectar informações díspares" not in note


def test_working_context_turns_same_question_into_explicit_referent() -> None:
    from campanario.chat.working_context import working_conversation_note
    sid = uuid4()
    def msg(role, content, agent_id=None):
        return Message(id=uuid4(), session_id=sid, role=role, content=content, created_at=datetime.now(UTC), agent_id=agent_id)
    history = [
        msg(MessageRole.USER, "Morgana, qual sinal faria você ficar quieta em vez de entrar na conversa?"),
        msg(MessageRole.ASSISTANT, "Quando minha fala seria redundante.", "morgana"),
        msg(MessageRole.USER, "Todd, mesma pergunta pra você, mas não repete a Morgana."),
    ]
    note = working_conversation_note(history).lower()
    assert "mesma pergunta" in note
    assert "qual sinal faria você ficar quieta" in note
    assert "nao peça que o usuario a repita" in note


def test_working_context_aterrissa_binds_previous_agent_idea() -> None:
    from campanario.chat.working_context import working_conversation_note
    sid = uuid4()
    def msg(role, content, agent_id=None):
        return Message(id=uuid4(), session_id=sid, role=role, content=content, created_at=datetime.now(UTC), agent_id=agent_id)
    history = [
        msg(MessageRole.USER, "o Campanário deveria parecer um lugar onde vocês já estão"),
        msg(MessageRole.USER, "Morgana, desenvolve essa parte de presença sem virar texto abstrato demais."),
        msg(MessageRole.ASSISTANT, "Presença aqui é familiaridade, ritmo e continuidade sem painel de controles.", "morgana"),
        msg(MessageRole.USER, "Todd, aterrissa isso sem matar o conceito."),
    ]
    note = working_conversation_note(history).lower()
    assert "isso' e a ideia explicada" in note
    assert "familiaridade, ritmo e continuidade" in note
    assert "sem pedir novamente" in note


def test_working_context_short_sequence_binds_previous_problem() -> None:
    from campanario.chat.working_context import working_conversation_note
    sid = uuid4()
    def msg(role, content, agent_id=None):
        return Message(id=uuid4(), session_id=sid, role=role, content=content, created_at=datetime.now(UTC), agent_id=agent_id)
    history = [
        msg(MessageRole.USER, "ontem tivemos um pico de latência sem erro nos logs. Por onde começariam?"),
        msg(MessageRole.ASSISTANT, "Eu verificaria CPU, rede e dependências.", "morgana"),
        msg(MessageRole.USER, "não quero vinte hipóteses; me deem uma sequência curta."),
    ]
    note = working_conversation_note(history).lower()
    assert "sequencia curta pedida" in note
    assert "pico de latencia" in note or "pico de latência" in note
    assert "sem pedir o contexto de novo" in note


def test_working_context_architecture_discomfort_forbids_invented_subsystems() -> None:
    from campanario.chat.working_context import working_conversation_note
    sid = uuid4()
    def msg(role, content, agent_id=None):
        return Message(id=uuid4(), session_id=sid, role=role, content=content, created_at=datetime.now(UTC), agent_id=agent_id)
    history = [
        msg(MessageRole.USER, "tenho um app local funcionando e três semanas para a entrega"),
        msg(MessageRole.USER, "uma parte da arquitetura me incomoda, mas ela não está quebrando"),
        msg(MessageRole.USER, "Todd, se fosse sua decisão hoje, qual seria o próximo passo?"),
    ]
    note = working_conversation_note(history).lower()
    assert "fato conhecido sobre a arquitetura" in note
    assert "nao invente qual parte" in note
    assert "prazo informado" in note

@pytest.mark.asyncio
async def test_chat_service_uses_compiled_dialogue_state_for_elliptical_direct_followup() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider([
        "Eu ficaria quieto quando minha entrada não acrescentasse nada novo.",
        "Eu fico quieto quando entrar não muda a decisão nem reduz um risco concreto.",
    ])
    service = ChatService(sessions, messages, provider, RecentMessagesContextManager(20), "fake-model")
    session = service.create_session()

    messages.append(Message(id=uuid4(), session_id=session.id, role=MessageRole.USER, content="é sobre presença durante meu trabalho", created_at=datetime.now(UTC)))
    messages.append(Message(id=uuid4(), session_id=session.id, role=MessageRole.USER, content="Morgana, qual sinal faria você ficar quieta em vez de entrar na conversa?", created_at=datetime.now(UTC)))
    messages.append(Message(id=uuid4(), session_id=session.id, role=MessageRole.ASSISTANT, content="Quando eu seria redundante.", created_at=datetime.now(UTC), agent_id="morgana"))

    _ = [event async for event in service.stream_turn(session.id, "Todd, mesma pergunta pra você, mas não repete a Morgana.")]

    assert len(provider.requests) == 2
    system = provider.requests[0].messages[0].content.lower()
    assert "estado da conversa" in system
    assert "qual sinal faria você ficar quieta" in system
    assert "responda agora, da sua propria perspectiva" in system
    assert "frame ativo" not in system
    assert "conversation focus stack" not in system

@pytest.mark.asyncio
async def test_answer_contract_is_last_system_binding_and_retries_lost_reference() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider([
        "Qual foi a pergunta?",
        "Eu fico quieto quando entrar não muda a decisão, não reduz risco e não acrescenta um próximo passo útil.",
    ])
    service = ChatService(sessions, messages, provider, RecentMessagesContextManager(20), "fake-model")
    session = service.create_session()

    messages.append(Message(id=uuid4(), session_id=session.id, role=MessageRole.USER, content="é sobre presença durante meu trabalho", created_at=datetime.now(UTC)))
    messages.append(Message(id=uuid4(), session_id=session.id, role=MessageRole.USER, content="Morgana, qual sinal faria você ficar quieta em vez de entrar na conversa?", created_at=datetime.now(UTC)))
    messages.append(Message(id=uuid4(), session_id=session.id, role=MessageRole.ASSISTANT, content="Quando eu seria redundante.", created_at=datetime.now(UTC), agent_id="morgana"))

    events = [event async for event in service.stream_turn(session.id, "Todd, mesma pergunta pra você, mas não repete a Morgana.")]
    text = "".join(event.text for event in events if event.type == "token")

    assert "fico quieto" in text.lower()
    assert len(provider.requests) == 2
    first_system = provider.requests[0].messages[0].content.lower()
    second_system = provider.requests[1].messages[0].content.lower()
    assert "contrato de resposta" in first_system
    assert first_system.rfind("contrato de resposta") > first_system.rfind("contrato de saida do speaker")
    assert "a tentativa anterior violou este contrato" in second_system


@pytest.mark.asyncio
async def test_p242_closed_commitment_retries_then_falls_back_to_short_ack() -> None:
    sessions = InMemorySessions()
    messages = InMemoryMessages()
    provider = QueueProvider([
        "Sim, mas eu ainda faria ajustes na arquitetura antes da entrega.",
        "Porém, precisamos revisar papéis e responsabilidades dos agentes.",
    ])
    service = ChatService(sessions, messages, provider, RecentMessagesContextManager(20), "fake-model")
    session = service.create_session()

    now = datetime.now(UTC)
    for role, content, agent in (
        (MessageRole.USER, "resume a decisão em uma frase, Morgana.", None),
        (MessageRole.ASSISTANT, "A decisão é priorizar a entrega e evitar reestruturação antes do prazo.", "morgana"),
    ):
        messages.append(Message(id=uuid4(), session_id=session.id, role=role, content=content, created_at=now, agent_id=agent))

    events = [event async for event in service.stream_turn(session.id, "fechado, seguimos assim.")]
    answer = "".join(event.text for event in events if event.type == "token")
    assert answer == "Entendido."
    assert len(provider.requests) == 2


def test_p242_arithmetic_anchor_rejects_guard_language_even_when_numbers_are_correct() -> None:
    from campanario.agents.output import extract_arithmetic_correction_anchor

    anchor = extract_arithmetic_correction_anchor(
        "Todd, suponha que eu diga agora que ela respondeu 142. Corrige só esse ponto.",
        ("24 vezes 6 dá quanto, Morgana?",),
    )
    assert anchor is not None
    assert not anchor.validates("O enunciado atribuído usa 24 vezes 6; preserve os operandos: o correto é 144.")
    assert anchor.validates("Não, 24 vezes 6 é 144.")
