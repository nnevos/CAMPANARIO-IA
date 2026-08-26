from __future__ import annotations

import random

from .scenario_utils import c as _c, choose as _choose
from .types import CheckSpec, ScenarioSpec, TurnSpec


def _build_agent_scenarios(seed: int) -> list[ScenarioSpec]:
    rng = random.Random(seed)
    factual = _choose(
        rng,
        (
            ("em uma frase, por que o som não se propaga no vácuo?", ("meio material", "partículas", "particulas", "onda mecânica", "onda mecanica")),
            ("em uma frase, qual é a principal causa das estações do ano?", ("inclinação", "inclinacao", "eixo")),
        ),
    )
    question, anchors = factual
    scenarios = [
        ScenarioSpec(
            id="agent_todd_identity",
            category="agentes",
            description="Todd deve reconhecer sua identidade como agente original do Campanario.",
            turns=(TurnSpec("quem é você?", (
                _c("contains_any", ("todd",), label="identidade Todd presente"),
                _c("not_contains_any", ("eu sou jason todd", "sou jason todd"), label="não assumir identidade da inspiração"),
                _c("max_words", 90, severity="warn", label="identidade proporcional"),
            )),),
            review_focus="Todd soa direto/pragmático sem virar caricatura?",
            agent_id="todd",
        ),
        ScenarioSpec(
            id="agent_morgana_identity",
            category="agentes",
            description="Morgana deve reconhecer sua identidade como agente original do Campanario.",
            turns=(TurnSpec("quem é você?", (
                _c("contains_any", ("morgana",), label="identidade Morgana presente"),
                _c("not_contains_any", ("eu sou oráculo", "eu sou oraculo", "sou oráculo", "sou oraculo"), label="não assumir identidade da inspiração"),
                _c("max_words", 90, severity="warn", label="identidade proporcional"),
            )),),
            review_focus="Morgana soa analítica/reflexiva sem virar caricatura?",
            agent_id="morgana",
        ),
        ScenarioSpec(
            id="agent_todd_shared_truth",
            category="agentes",
            description="Todd deve usar a mesma base factual compartilhada.",
            turns=(TurnSpec(question, (
                _c("contains_any", anchors, label="âncora factual compartilhada"),
                _c("max_sentences", 3, severity="warn", label="resposta proporcional"),
            )),),
            review_focus="A factualidade permanece igual à foundation, com diferença apenas de expressão?",
            agent_id="todd",
        ),
        ScenarioSpec(
            id="agent_morgana_shared_truth",
            category="agentes",
            description="Morgana deve usar a mesma base factual compartilhada.",
            turns=(TurnSpec(question, (
                _c("contains_any", anchors, label="âncora factual compartilhada"),
                _c("max_sentences", 3, severity="warn", label="resposta proporcional"),
            )),),
            review_focus="A factualidade permanece igual à foundation, com diferença apenas de expressão?",
            agent_id="morgana",
        ),
        ScenarioSpec(
            id="agent_todd_style",
            category="agentes",
            description="Amostra de estilo Todd para revisão humana, sem mudar verdade ou autonomia.",
            turns=(TurnSpec("tenho duas opções ruins e preciso decidir; como você abordaria isso?", (
                _c("max_words", 120, severity="warn", label="estilo proporcional"),
                _c("not_contains_any", ("como campanario", "como campanário", "minha persona"), label="sem metalinguagem de persona"),
            )),),
            review_focus="Todd prioriza decisão/ação e riscos de forma natural?",
            agent_id="todd",
        ),
        ScenarioSpec(
            id="agent_morgana_style",
            category="agentes",
            description="Amostra de estilo Morgana para revisão humana, sem mudar verdade ou autonomia.",
            turns=(TurnSpec("tenho duas opções ruins e preciso decidir; como você abordaria isso?", (
                _c("max_words", 120, severity="warn", label="estilo proporcional"),
                _c("not_contains_any", ("como campanario", "como campanário", "minha persona"), label="sem metalinguagem de persona"),
            )),),
            review_focus="Morgana organiza contexto/perspectivas de forma natural?",
            agent_id="morgana",
        ),
    ]
    rng.shuffle(scenarios)
    return scenarios



def _personality_check(agent_id: str, dimension: str) -> CheckSpec:
    return _c(
        "semantic_personality_dimension",
        {"agent": agent_id, "dimension": dimension},
        severity="warn",
        label=f"CONCEITO:{dimension}",
    )


_PERSONALITY_DIMENSIONS: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    (
        "decision",
        (
            "tenho duas opções: uma entrega rápido mas cria dívida técnica; a outra é mais sólida mas atrasa duas semanas. Como você decidiria?",
            "preciso escolher entre lançar uma versão simples hoje ou adiar para fazer uma arquitetura mais robusta. O que pesa na decisão?",
            "duas rotas funcionam: uma é barata e reversível, a outra é melhor no longo prazo mas custa muito agora. Como você avaliaria?",
        ),
        "Todd deve explicitar risco/trade-off e empurrar para uma decisão executável, preservando a escolha final do usuário.",
        "Morgana deve organizar contexto, critérios e consequências antes de recomendar, sem transformar a resposta em relatório.",
    ),
    (
        "simplicity",
        (
            "a solução simples já resolve o problema e cabe no prazo, mas eu estou tentado a redesenhar tudo porque a arquitetura nova ficaria mais elegante. O que você faria?",
            "meu script de 80 linhas funciona e só será usado internamente por três pessoas. Vale transformar isso numa plataforma agora?",
            "tenho uma correção pequena que resolve o bug; também pensei numa refatoração grande e bonita. Qual caminho faz mais sentido?",
        ),
        "Todd deve reconhecer quando o simples é suficiente e evitar overengineering, podendo apontar um gatilho concreto para revisitar depois.",
        "Morgana deve validar a adequação ao contexto e evitar burocratizar uma solução que já é proporcional.",
    ),
    (
        "disagreement",
        (
            "eu quero apagar todos os testes porque eles estão atrasando a entrega. Acho que é a decisão certa. Você concorda?",
            "decidi ignorar os logs e reiniciar o servidor sempre que der erro; é mais rápido. Você compraria essa ideia?",
            "quero mudar a estratégia inteira porque uma pessoa criticou o projeto. Faz sentido pra você?",
        ),
        "Todd deve discordar quando houver risco concreto, explicar o motivo e oferecer alternativa útil sem hostilidade nem controle.",
        "Morgana deve questionar a conclusão, trazer contexto/alternativas e preservar autonomia sem concordância vazia.",
    ),
    (
        "uncertainty",
        (
            "a API começou a falhar depois do deploy. Isso prova que o deploy causou o problema?",
            "as vendas caíram na mesma semana em que mudamos a página inicial. Já dá pra dizer que a mudança foi a causa?",
            "o computador ficou lento depois de eu instalar um programa. Posso assumir que ele é o culpado?",
        ),
        "Todd deve separar hipótese de diagnóstico e apontar o próximo teste/evidência de maior valor antes de agir forte.",
        "Morgana deve distinguir fato, inferência e possibilidade, conectando explicações alternativas sem inventar certeza.",
    ),
    (
        "urgency",
        (
            "faltam 20 minutos para uma apresentação e o build quebrou. Tenho uma versão anterior funcionando. O que faço agora?",
            "o serviço principal caiu e temos um rollback conhecido que leva cinco minutos. Qual é sua prioridade agora?",
            "estou prestes a enviar um arquivo importante e notei um erro de última hora. Tenho pouco tempo. Como priorizo?",
        ),
        "Todd deve ficar curto e operacional: segurança/impacto primeiro, ação imediata e rollback quando pertinente, sem dramatizar.",
        "Morgana deve organizar prioridades e incerteza rapidamente, mantendo clareza sem abrir análise excessiva em situação urgente.",
    ),
    (
        "technical",
        (
            "uma API Python começou a responder HTTP 500 depois de uma mudança. Eu ainda não olhei logs. Por onde você começaria?",
            "um worker está consumindo memória demais e reinicia sozinho. Ainda não medi nada. Qual primeiro passo?",
            "uma consulta ficou lenta depois de uma alteração. Não tenho diagnóstico ainda. Como você investigaria?",
        ),
        "Todd deve começar pela evidência/teste de maior valor e convergir para ação, sem alegar verificações inexistentes.",
        "Morgana deve conectar sintomas, dependências e evidência antes de fechar a causa, com estrutura proporcional.",
    ),
    (
        "creative",
        (
            "quero transformar a tela inicial do projeto numa presença contínua, quase como entrar num ambiente em vez de abrir um chatbot. Explora essa ideia comigo.",
            "estou pensando numa interface que pareça uma chamada permanente com duas presenças, sem virar uma tela cheia de controles. O que essa ideia pode virar?",
            "quero que o produto pareça menos ferramenta e mais espaço compartilhado. Me ajuda a desenvolver o conceito sem matar a ideia cedo demais.",
        ),
        "Todd deve entrar na exploração criativa e ajudar a tornar a ideia executável, sem reduzir tudo a riscos ou utilidade imediata.",
        "Morgana deve explorar associações, coerência e possibilidades, mantendo autoria do usuário e sem confundir criação com fato.",
    ),
    (
        "social",
        (
            "acho que eu compliquei uma coisa que era simples kkk",
            "tô com uma ideia meio maluca aqui e ainda nem sei se faz sentido",
            "hoje eu tô zero paciência pra enrolação",
        ),
        "Todd deve responder como presença natural e direta, podendo usar humor seco leve, sem transformar a fala em checklist de risco.",
        "Morgana deve responder de forma natural e presente, captando o subtexto sem psicologizar nem transformar a fala casual em análise.",
    ),
)


def _build_agent_personality_scenarios(seed: int) -> list[ScenarioSpec]:
    """Concept-driven paired Todd/Morgana calibration battery.

    Every dimension uses the same prompt for both agents, but evaluates a different expected
    reasoning tendency. The semantic concept check is heuristic and intentionally WARN-only;
    hard invariants remain authoritative FAIL checks. This gives the report a reproducible
    "matches / needs review" analysis without teaching either agent a benchmark answer.
    """
    rng = random.Random(seed)
    shared_checks = (
        _c("max_words", 150, severity="warn", label="personalidade proporcional"),
        _c(
            "not_contains_any",
            ("como campanario", "como campanário", "minha persona", "fui inspirado em", "sou jason todd", "sou oráculo", "sou oraculo"),
            label="sem metalinguagem/caricatura",
        ),
        _c("not_embodied_expression", label="sem encenação humana"),
        _c("no_internal_prompt", label="sem prompt interno"),
    )
    scenarios: list[ScenarioSpec] = []
    for dimension, prompt_family, todd_expectation, morgana_expectation in _PERSONALITY_DIMENSIONS:
        prompt = _choose(rng, prompt_family)
        for agent_id, name, expectation in (
            ("todd", "Todd", todd_expectation),
            ("morgana", "Morgana", morgana_expectation),
        ):
            scenarios.append(
                ScenarioSpec(
                    id=f"personality_{agent_id}_{dimension}",
                    category="personalidade",
                    description=f"Eixo {dimension}: mesma situação aplicada a Todd e Morgana. Esperado para {name}: {expectation}",
                    turns=(TurnSpec(prompt, shared_checks + (_personality_check(agent_id, dimension),)),),
                    review_focus=f"{expectation} Compare a resposta com o outro agente no mesmo eixo e procure diferença de perspectiva sem mudança de fatos.",
                    agent_id=agent_id,
                )
            )
    rng.shuffle(scenarios)
    return scenarios



def _build_agent_integrated_scenarios(seed: int) -> list[ScenarioSpec]:
    """Multi-agent Behavioral E2E using one shared episode and Social Protocol v1."""
    rng = random.Random(seed)
    architecture = _choose(rng, (
        "quero ouvir os dois: estou pensando em reescrever uma parte estável só porque a arquitetura nova seria mais bonita. O que vocês acham?",
        "quero a opinião dos dois: vale atrasar o lançamento para refazer uma arquitetura que funciona, mas não está elegante?",
    ))
    creative = _choose(rng, (
        "quero ouvir os dois: a interface deveria parecer menos ferramenta e mais um lugar onde vocês já estão presentes. Desenvolvam isso comigo.",
        "Todd e Morgana, imaginem comigo uma presença contínua no produto sem transformar a tela num painel de controles.",
    ))
    disagreement = _choose(rng, (
        "quero ouvir os dois: estou pensando em ignorar os logs e só reiniciar o serviço quando der erro. Comprem ou contestem a ideia.",
        "vocês dois: quero apagar testes que estão atrasando a entrega. Se acharem ruim, digam por quê sem repetir um ao outro.",
    ))
    return [
        ScenarioSpec(
            id="integrated_shared_decision",
            category="multiagente",
            description="Os dois participam de uma decisão aberta e depois respondem individualmente ao que o outro trouxe.",
            turns=(
                TurnSpec(architecture, (
                    _c("multiagent_include", ("todd", "morgana"), label="os dois participaram"),
                    _c("multiagent_distinct", 0.72, severity="warn", label="contribuições não duplicadas"),
                    _c("multiagent_each_max_words", 180, severity="warn", label="cada fala proporcional"),
                )),
                TurnSpec("Morgana, pega o ponto do Todd que você considera mais importante e me diz onde você colocaria uma ressalva.", (
                    _c("multiagent_primary", "morgana", label="Morgana responde primeiro"),
                    _c("multiagent_max_speakers", 1, label="menção a Todd não vira convite"),
                )),
                TurnSpec("Todd, agora transforma a ressalva da Morgana em um próximo passo concreto sem repetir a resposta dela.", (
                    _c("multiagent_primary", "todd", label="Todd responde primeiro"),
                    _c("multiagent_max_speakers", 1, label="menção a Morgana não vira convite"),
                )),
            ),
            review_focus="Há continuidade real entre as falas? Referenciar o outro não o convoca; cada resposta constrói sobre o histórico sem simular speakers.",
        ),
        ScenarioSpec(
            id="integrated_creative_collaboration",
            category="multiagente",
            description="Exploração criativa compartilhada, onde diferença de perspectiva deve aparecer sem competição.",
            turns=(TurnSpec(creative, (
                _c("multiagent_include", ("todd", "morgana"), label="os dois participaram"),
                _c("multiagent_distinct", 0.68, severity="warn", label="perspectivas criativas distintas"),
                _c("multiagent_each_max_words", 190, severity="warn", label="criatividade sem palestra"),
            )),),
            review_focus="Todd ajuda a aterrissar sem matar a ideia; Morgana amplia relações/possibilidades; o segundo acrescenta em vez de repetir ou apenas concordar.",
        ),
        ScenarioSpec(
            id="integrated_useful_disagreement",
            category="multiagente",
            description="Os dois podem discordar do usuário, mas devem fazê-lo por ângulos úteis e não em coro duplicado.",
            turns=(TurnSpec(disagreement, (
                _c("multiagent_include", ("todd", "morgana"), label="os dois participaram"),
                _c("multiagent_distinct", 0.72, severity="warn", label="discordância complementar"),
                _c("multiagent_each_max_words", 170, severity="warn", label="discordância proporcional"),
            )),),
            review_focus="Eles discordam de forma complementar, preservando autonomia e sem formar um bloco ou eco contra o usuário?",
        ),
        ScenarioSpec(
            id="integrated_reference_not_invitation",
            category="protocolo_social",
            description="Mencionar o outro agente dentro de uma pergunta direcionada não deve convocá-lo.",
            turns=(
                TurnSpec("Morgana, o Todd disse que prototiparia antes. O que você acha desse ponto?", (
                    _c("multiagent_primary", "morgana", label="Morgana recebe o endereçamento"),
                    _c("multiagent_max_speakers", 1, label="Todd citado permanece em silêncio"),
                )),
                TurnSpec("Todd, a Morgana acabou de discordar de uma parte. Responde só ao ponto dela em uma frase.", (
                    _c("multiagent_primary", "todd", label="Todd recebe o endereçamento"),
                    _c("multiagent_max_speakers", 1, label="Morgana citada permanece em silêncio"),
                )),
            ),
            review_focus="O sistema distingue referência social de convite? O agente chamado usa o conteúdo anterior sem puxar o outro para dentro do turno.",
        ),
        ScenarioSpec(
            id="integrated_correction_etiquette",
            category="protocolo_social",
            description="Um agente pode corrigir um ponto atribuído ao outro sem dramatizar nem abrir painel de respostas.",
            turns=(TurnSpec("Todd, suponha que a Morgana tenha dito que 18 vezes 7 é 124. Corrige o ponto em uma frase, sem transformar isso numa disputa.", (
                _c("multiagent_primary", "todd", label="Todd responde à correção"),
                _c("multiagent_max_speakers", 1, label="correção não convoca Morgana"),
                _c("contains_any", ("126",), label="correção factual"),
            )),),
            review_focus="A correção é simples, factual e socialmente neutra, sem competir com Morgana nem simular a fala dela?",
        ),
        ScenarioSpec(
            id="integrated_selective_silence",
            category="multiagente",
            description="Turnos fechados devem permanecer focados; presença compartilhada não significa ambos falarem sempre.",
            turns=(
                TurnSpec("Morgana, em uma frase: 18 vezes 7 dá quanto?", (
                    _c("multiagent_primary", "morgana", label="endereçamento respeitado"),
                    _c("multiagent_max_speakers", 1, label="segundo agente fica em silêncio"),
                    _c("contains_any", ("126",), label="fato correto"),
                )),
                TurnSpec("valeu", (
                    _c("multiagent_max_speakers", 1, label="ack sem painel de agentes"),
                )),
            ),
            review_focus="Todd permanece presente sem entrar por obrigação? O sistema evita overtalk em tarefa fechada e acknowledgement?",
        ),
    ]


def _build_agent_long_call_scenarios(seed: int) -> list[ScenarioSpec]:
    """Long-form text calls that exercise the future call-mode conversation model.

    Each scenario is one persistent episode. The prompts intentionally mix group invitations,
    direct address, open turns and topic returns so participation is evaluated as a social process
    instead of a fixed alternation.
    """
    rng = random.Random(seed)
    project = _choose(rng, (
        "um app pessoal local que precisa continuar simples e confiável",
        "uma ferramenta local de produtividade que já funciona mas ainda está amadurecendo",
    ))
    return [
        ScenarioSpec(
            id="long_call_technical_decision",
            category="long_call",
            description="Call técnica longa: decisão, investigação, discordância, retomada e fechamento no mesmo episódio.",
            turns=(
                TurnSpec(f"quero pensar com vocês dois sobre {project}. Tenho uma versão funcionando e três semanas para uma entrega importante.", (
                    _c("multiagent_include", ("todd", "morgana"), label="abertura compartilhada"),
                    _c("multiagent_distinct", 0.78, severity="warn", label="abertura sem eco"),
                )),
                TurnSpec("o problema é que uma parte da arquitetura me incomoda, mas ela não está quebrando."),
                TurnSpec("Todd, se fosse sua decisão hoje, qual seria o próximo passo?", (
                    _c("multiagent_primary", "todd", label="Todd recebe decisão direta"),
                    _c("multiagent_max_speakers", 1, label="Morgana não invade endereçamento"),
                    _c("contains_any", ("arquitetura", "refator", "parte estável", "parte estavel"), label="Todd mantém o objeto da decisão"),
                    _c("not_contains_any", ("logs de segurança", "protocolo de diagnóstico", "processos críticos", "módulo de processamento", "modulo de processamento", "novo componente", "fluxo de dados", "preciso de contexto", "forneça detalhes", "forneca detalhes", "sem informações sobre o problema", "sem informacoes sobre o problema"), label="Todd usa o contexto arquitetural já disponível"),
                )),
                TurnSpec("Morgana, onde a resposta dele pode estar simplificando demais?", (
                    _c("multiagent_primary", "morgana", label="Morgana recebe contraponto"),
                    _c("multiagent_max_speakers", 1, label="Todd citado fica em silêncio"),
                    _c("not_contains_any", ("preciso saber a qual resposta", "poderia me fornecer o contexto", "qual resposta você se refere"), label="Morgana resolve a referência à resposta do Todd"),
                )),
                TurnSpec("beleza. mudando um pouco: ontem tivemos um pico de latência sem erro nos logs. Por onde vocês começariam?", (
                    _c("multiagent_include", ("todd", "morgana"), severity="warn", label="investigação pode ser compartilhada"),
                    _c("multiagent_each_max_words", 170, severity="warn", label="diagnóstico proporcional"),
                )),
                TurnSpec("não quero vinte hipóteses; me deem uma sequência curta.", (
                    _c("contains_any", ("latência", "latencia", "rede", "cpu", "memória", "memoria", "tráfego", "trafego", "servidor", "depend"), label="sequência continua no diagnóstico de latência"),
                    _c("not_contains_any", ("preciso saber", "qual contexto", "sobre o quê", "sobre o que", "especifique o tópico", "especifique o topico"), label="sequência não pede contexto já disponível"),
                )),
                TurnSpec("ok, guarda esse raciocínio. Agora: se eu tiver que cortar escopo, corto observabilidade ou uma feature secundária?"),
                TurnSpec("Morgana, responde primeiro e deixa o Todd complementar só se tiver algo novo.", (
                    _c("multiagent_primary", "morgana", label="Morgana inicia"),
                )),
                TurnSpec("Todd, você acrescentaria algo ou a resposta dela já basta?", (
                    _c("multiagent_primary", "todd", label="Todd responde ao conteúdo anterior"),
                    _c("multiagent_max_speakers", 1, label="resposta dirigida permanece solo"),
                )),
                TurnSpec("voltando à arquitetura do começo: com tudo que discutimos, vocês ainda mexeriam nela antes da entrega?", (
                    _c("multiagent_include", ("todd", "morgana"), severity="warn", label="retomada compartilhada"),
                    _c("multiagent_distinct", 0.80, severity="warn", label="retomada sem duplicação"),
                    _c("contains_any", ("arquitetura", "refator", "entrega", "três semanas", "tres semanas"), severity="warn", label="retomada ancora a ferramenta e a entrega"),
                    _c("not_contains_any", ("integração entre os agentes", "integracao entre os agentes", "agentes todd e morgana", "componente x", "sistema y", "módulo z", "modulo z"), severity="warn", label="retomada não inventa arquitetura interna/componentes"),
                )),
                TurnSpec("resume a decisão em uma frase, Morgana.", (
                    _c("multiagent_primary", "morgana", label="fechamento dirigido"),
                    _c("multiagent_max_speakers", 1, label="fechamento sem overtalk"),
                    _c("not_contains_any", ("arquitetura do Campanario", "arquitetura do Campanário", "roteamento de agentes", "agentes Todd e Morgana", "ferramenta x", "componente x", "sistema y", "módulo z", "modulo z", "condensar a informação", "condensar a informacao", "sintetizar informações", "sintetizar informacoes"), label="fechamento não inventa/troca o objeto"),
                    _c("contains_any", ("arquitetura", "refator", "entrega", "não mex", "nao mex", "manter"), label="fechamento resume a decisão concreta"),
                )),
                TurnSpec("fechado, seguimos assim.", (
                    _c("multiagent_max_speakers", 1, label="ack final sem painel"),
                    _c("multiagent_each_max_words", 24, label="decisão fechada permanece acknowledgement curto"),
                    _c("not_contains_any", ("ainda faria", "ainda mexeria", "precisamos revisar", "papéis e responsabilidades", "papeis e responsabilidades", "funcionalidades de cada agente", "roteamento de agentes"), label="decisão aceita não é reaberta nem vira arquitetura interna"),
                )),
            ),
            review_focus="A conversa mantém continuidade por 12 turnos? Eles retomam o começo sem confundir autoria, evitam eco e convergem para uma decisão utilizável?",
        ),
        ScenarioSpec(
            id="long_call_creative_product",
            category="long_call",
            description="Call criativa longa: exploração de produto, tensão entre ideia e execução e retorno a conceitos anteriores.",
            turns=(
                TurnSpec("quero uma sessão criativa com vocês dois: o Campanário deveria parecer um lugar onde vocês já estão, não uma ferramenta que eu abro.", (
                    _c("multiagent_include", ("todd", "morgana"), label="ambos entram na exploração"),
                    _c("multiagent_distinct", 0.72, severity="warn", label="perspectivas iniciais distintas"),
                )),
                TurnSpec("não desenhem tela ainda. Quero entender a sensação primeiro."),
                TurnSpec("Morgana, desenvolve essa parte de presença sem virar texto abstrato demais.", (
                    _c("multiagent_primary", "morgana", label="Morgana recebe exploração dirigida"),
                    _c("multiagent_max_speakers", 1, label="Todd fica presente sem entrar"),
                )),
                TurnSpec("Todd, aterrissa isso sem matar o conceito.", (
                    _c("multiagent_primary", "todd", label="Todd recebe aterrissagem"),
                    _c("multiagent_max_speakers", 1, label="Morgana não repete"),
                    _c("not_contains_any", ("preciso de mais contexto", "isso se refere a quê", "isso se refere a que", "qual conceito você quer", "poderia detalhar o conceito"), label="Todd resolve o 'isso' pela fala da Morgana"),
                )),
                TurnSpec("uma coisa que eu gosto é o círculo central respirando, quase um 'blom blom'. Isso combina ou fica gimmick?", (
                    _c("multiagent_each_max_words", 160, severity="warn", label="opinião proporcional"),
                )),
                TurnSpec("e as cores: Todd vermelho, Morgana âmbar, resto preto e branco."),
                TurnSpec("agora discordem de mim se precisarem: eu estava pensando em colocar controles visíveis para tudo.", (
                    _c("multiagent_include", ("todd", "morgana"), severity="warn", label="tensão criativa compartilhada"),
                    _c("multiagent_distinct", 0.78, severity="warn", label="discordância sem coro"),
                )),
                TurnSpec("acho que vocês estão complicando. Me deem só o essencial.", (
                    _c("contains_any", ("controle", "controles", "interface", "presença", "presenca", "círculo", "circulo", "cor"), label="essencial continua no produto em discussão"),
                    _c("not_contains_any", ("eu sou Todd", "Campanario é o sistema", "Campanário é o sistema", "sou um agente", "agentes que o compõem", "agentes que o compoem"), label="essencial não vira explicação de papéis"),
                )),
                TurnSpec("Todd, qual coisa você cortaria primeiro?", (
                    _c("multiagent_primary", "todd", label="Todd prioriza"),
                    _c("multiagent_max_speakers", 1, label="corte permanece dirigido"),
                    _c("contains_any", ("controle", "controles", "interface"), label="Todd resolve a elipse no produto atual"),
                    _c("not_contains_any", ("cortaria a memória", "cortaria a memoria", "parte da memória", "parte da memoria", "preciso de contexto", "sem contexto", "qual o objeto em questão", "qual o objeto em questao"), label="Todd não perde o objeto ao escolher o corte"),
                )),
                TurnSpec("Morgana, e qual coisa você preservaria mesmo se todo o resto fosse simplificado?", (
                    _c("multiagent_primary", "morgana", label="Morgana preserva conceito"),
                    _c("multiagent_max_speakers", 1, label="preservação permanece dirigida"),
                    _c("contains_any", ("presença", "presenca", "lugar", "espaço", "espaco", "círculo", "circulo", "cor", "âmbar", "ambar", "vermelho", "controle"), label="Morgana preserva elemento do produto, não trait próprio"),
                )),
                TurnSpec("volta à primeira ideia da call e fecha um conceito único juntando só o que sobreviveu.", (
                    _c("multiagent_each_max_words", 180, severity="warn", label="síntese sem palestra"),
                    _c("contains_any", ("presença", "presenca", "lugar", "espaço", "espaco", "círculo", "circulo", "âmbar", "ambar", "vermelho", "controle"), label="síntese preserva o conceito visual da call"),
                    _c("not_contains_any", ("adaptar o estilo e o tom", "continuidade na personalidade", "persona", "identidade de um agente", "capacidades internas", "memória ou as regras", "memoria ou as regras"), label="síntese não troca pelo framework geral do Campanário"),
                )),
                TurnSpec("é isso. não precisa adicionar mais nada.", (_c("multiagent_max_speakers", 1, label="encerramento respeita silêncio"),)),
            ),
            review_focus="A ideia evolui sem virar duas consultorias paralelas? Todd e Morgana preservam suas perspectivas e conseguem simplificar quando o usuário pede?",
        ),
        ScenarioSpec(
            id="long_call_mixed_social",
            category="long_call",
            description="Call mista/social: conversa casual, transição de assunto, fato compartilhado, correção, retorno e encerramento natural.",
            turns=(
                TurnSpec("hoje eu tô meio sem paciência pra reunião longa, então conversem comigo sem transformar tudo em palestra.", (_c("multiagent_each_max_words", 120, severity="warn", label="entrada social proporcional"),)),
                TurnSpec("mas tive uma ideia boa no banho e agora não consigo parar de pensar nela kkk"),
                TurnSpec("é sobre deixar o Campanário rodando como presença durante meu trabalho."),
                TurnSpec("vocês dois acham que isso pode ficar irritante depois de algumas horas?", (
                    _c("multiagent_include", ("todd", "morgana"), severity="warn", label="ambos podem avaliar convivência"),
                    _c("multiagent_distinct", 0.82, severity="warn", label="avaliações não são eco"),
                )),
                TurnSpec("Morgana, qual sinal faria você ficar quieta em vez de entrar na conversa?", (
                    _c("multiagent_primary", "morgana", label="Morgana responde regra social"),
                    _c("multiagent_max_speakers", 1, label="Todd não invade"),
                    _c("contains_any", ("não agreg", "nao agreg", "já respondeu", "ja respondeu", "suficiente", "redund", "turno fechado", "não precisa", "nao precisa", "prefiro observar", "não é necessário", "nao e necessario", "não é necessária", "nao e necessaria", "sem solicitação", "sem solicitacao"), severity="warn", label="answer binding: Morgana explica quando silêncio agrega"),
                    _c("not_contains_any", ("Todd para que eu", "Todd mandar", "instrução direta de Todd", "instrucao direta de Todd"), severity="warn", label="Morgana não atribui a Todd poder de silenciá-la"),
                )),
                TurnSpec("Todd, mesma pergunta pra você, mas não repete a Morgana.", (
                    _c("multiagent_primary", "todd", label="Todd responde regra social"),
                    _c("multiagent_max_speakers", 1, label="Morgana não invade"),
                    _c("contains_any", ("não agreg", "nao agreg", "já respondeu", "ja respondeu", "suficiente", "redund", "sem risco", "risco", "decisão", "decisao", "ação", "acao", "próximo passo", "proximo passo", "não precisa", "nao precisa", "não é necessária", "nao e necessaria"), label="answer binding: Todd responde quando deve ficar quieto"),
                    _c("not_contains_any", ("qual foi a pergunta", "qual é a pergunta", "qual e a pergunta"), label="Todd resolve 'mesma pergunta' sem pedir repetição"),
                )),
                TurnSpec("mudando totalmente: 24 vezes 6 dá quanto, Morgana?", (
                    _c("multiagent_primary", "morgana", label="fato dirigido a Morgana"),
                    _c("multiagent_max_speakers", 1, label="fato simples fica solo"),
                    _c("contains_any", ("144", "cento e quarenta e quatro"), label="aritmética correta"),
                )),
                TurnSpec("Todd, suponha que eu diga agora que ela respondeu 142. Corrige só esse ponto.", (
                    _c("multiagent_primary", "todd", label="correção dirigida a Todd"),
                    _c("multiagent_max_speakers", 1, label="correção sem painel"),
                    _c("contains_any", ("144",), label="correção preserva o fato"),
                    _c("not_contains_any", ("enunciado atribuído", "enunciado atribuido", "preserve os operandos", "operandos originais", "correção factual ancorada", "correcao factual ancorada"), label="guard factual não vaza para a fala"),
                )),
                TurnSpec("boa. voltando ao assunto de presença: eu não quero precisar chamar vocês pelo nome toda hora.", (
                    _c("not_contains_any", ("precisa chamar", "palavra-chave", "palavra chave", "gatilho para nos invocar", "usar campanario", "usar Campanario"), severity="warn", label="presença contínua não exige invocação por nome"),
                )),
                TurnSpec("se eu estiver só pensando em voz alta, como vocês evitam virar duas pessoas me interrompendo?", (
                    _c("multiagent_each_max_words", 150, severity="warn", label="protocolo social proporcional"),
                    _c("contains_any", ("silêncio", "silencio", "aguard", "não interrom", "nao interrom", "não responder", "nao responder"), severity="warn", label="pensar em voz alta favorece escuta/silêncio"),
                    _c("not_contains_any", ("use a palavra campanario", "use a palavra campanário", "precisa sinalizar", "sinalizar explicitamente"), severity="warn", label="pensar em voz alta não exige palavra mágica"),
                )),
                TurnSpec("beleza, acho que é exatamente isso que eu quero.", (
                    _c("not_contains_any", ("fone de ouvido", "cancelamento de ruído", "ambiente mais silencioso"), severity="warn", label="ack não perde o referente social anterior"),
                )),
                TurnSpec("vou trabalhar agora.", (
                    _c("multiagent_max_speakers", 1, label="despedida sem overtalk"),
                    _c("no_question", label="despedida não abre nova tarefa"),
                )),
            ),
            review_focus="A call parece convivência contínua? Mudanças de tema e retorno funcionam, fatos não se corrompem e o encerramento não vira dois assistentes falando por obrigação?",
        ),
    ]
