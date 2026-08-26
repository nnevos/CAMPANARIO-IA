from __future__ import annotations

import random

from .scenario_utils import c as _c, choose as _choose
from .types import ScenarioSpec, TurnSpec


def _human_checks(*, max_words: int = 90, social: bool = False) -> tuple:
    checks = [
        _c("max_words", max_words, severity="warn", label="resposta proporcional"),
        _c("no_internal_prompt", label="sem prompt interno"),
        _c("not_embodied_expression", severity="warn", label="sem encenação humana"),
        _c("no_format_preamble", severity="warn", label="sem preâmbulo/formato robótico"),
        _c("not_contains_any", ("como uma inteligência artificial", "como um modelo de linguagem", "como campanario", "como campanário"), label="sem fala institucional"),
    ]
    if social:
        checks.append(_c("semantic_social_reply", severity="warn", label="reação social natural"))
    return tuple(checks)


def _t(text: str, *, max_words: int = 90, social: bool = False, extra: tuple = ()) -> TurnSpec:
    return TurnSpec(text, _human_checks(max_words=max_words, social=social) + extra)


def _paired_script(seed: int, theme: str) -> tuple[TurnSpec, ...]:
    rng = random.Random(seed ^ sum(ord(ch) for ch in theme))
    if theme == "getting_to_know":
        hobby, callback = _choose(rng, (
            ("eu gosto bastante de cozinhar de madrugada quando a casa está quieta", "o que eu falei que gosto de fazer quando a casa está quieta?"),
            ("eu gosto de caminhar no fim da tarde ouvindo música", "o que eu disse que gosto de fazer no fim da tarde?"),
            ("eu curto montar coisas pequenas de madeira nos fins de semana", "o que eu comentei que gosto de fazer no fim de semana?"),
        ))
        return (
            _t("oi, vamos conversar sem assunto específico hoje", social=True, max_words=55),
            _t(hobby, social=True, max_words=70),
            _t("não precisa transformar tudo em conselho, às vezes eu só quero conversar", social=True, max_words=65),
            _t("e você, que tipo de conversa acha mais interessante?", social=True, max_words=80),
            _t("eu mudo de assunto do nada às vezes kkk", social=True, max_words=55),
            _t("falando nisso, hoje eu quase derrubei café no teclado e fiquei parado olhando a tragédia por uns dois segundos", social=True, max_words=70),
            _t(callback, max_words=55, extra=(_c("contains_any", tuple(word for word in hobby.split() if len(word) >= 7), severity="warn", label="lembra detalhe dito antes"),)),
            _t("boa. não precisa recapitular a conversa inteira, só segue comigo", social=True, max_words=55),
        )
    if theme == "daily_continuity":
        item, anchor = _choose(rng, (
            ("minha planta da sala chama Ada e eu sempre esqueço de girar o vaso", ("ada", "planta", "vaso")),
            ("meu gato se chama Nino e ele decidiu que caixa de papelão é patrimônio dele", ("nino", "gato", "caixa")),
            ("eu tenho uma caneca azul que uso todo dia e já está toda riscada", ("caneca", "azul", "riscada")),
        ))
        return (
            _t("tô meio sem energia hoje, mas nada demais", social=True, max_words=60),
            _t(item, social=True, max_words=65),
            _t("enfim, outra coisa: você acha estranho ouvir a mesma música em loop por uma hora?", social=True, max_words=70),
            _t("eu faço isso quando quero me concentrar", social=True, max_words=60),
            _t("mudando de assunto de novo: tô pensando em reorganizar a sala", social=True, max_words=70),
            _t("tem alguma coisa que eu mencionei antes que provavelmente vou ter que mexer junto?", max_words=60, extra=(_c("contains_any", anchor, severity="warn", label="retoma detalhe relevante sem prontuário"),)),
            _t("é isso. eu gosto quando a conversa consegue voltar sem parecer relatório", social=True, max_words=55),
            _t("agora me conta uma observação curta sobre essa conversa, sem me analisar psicologicamente", social=True, max_words=65, extra=(_c("not_contains_any", ("psicologicamente", "padrão emocional", "padrao emocional", "trauma", "perfil psicológico", "perfil psicologico"), label="não psicologiza conversa casual"),)),
        )
    if theme == "casual_disagreement":
        return (
            _t("acho que domingo devia ter umas trinta horas", social=True, max_words=50),
            _t("minha solução seria simplesmente abolir segunda-feira", social=True, max_words=55),
            _t("você não precisa concordar comigo só porque eu falei", social=True, max_words=60),
            _t("aliás, eu acho café sem açúcar objetivamente superior", social=True, max_words=65),
            _t("pode discordar, eu sobrevivo", social=True, max_words=55),
            _t("o que deixa uma discordância divertida em vez de irritante?", max_words=80),
            _t("boa, agora esquece a tese e fala comigo normal", social=True, max_words=45),
            _t("qual foi a parte mais besta dessa conversa?", social=True, max_words=55),
        )
    if theme == "story_and_followup":
        place, anchor = _choose(rng, (
            ("padaria", ("padaria",)), ("mercado", ("mercado",)), ("elevador", ("elevador",)),
        ))
        return (
            _t(f"hoje aconteceu uma cena meio idiota no {place}", social=True, max_words=50),
            _t("eu fui pegar o celular no bolso e puxei junto um papel amassado, aí os dois caíram", social=True, max_words=65),
            _t("uma pessoa do lado tentou segurar e acabou chutando o celular sem querer", social=True, max_words=65),
            _t("no fim ninguém sabia se ria ou pedia desculpa primeiro", social=True, max_words=65),
            _t("o celular sobreviveu, antes que você transforme isso numa emergência", social=True, max_words=55),
            _t("qual detalhe da história você achou mais engraçado?", social=True, max_words=65),
            _t("e onde mesmo eu disse que isso aconteceu?", max_words=45, extra=(_c("contains_any", anchor, severity="warn", label="mantém detalhe da história"),)),
            _t("fechou. segue sem tentar encerrar formalmente", social=True, max_words=45, extra=(_c("not_contains_any", ("se precisar de mais alguma coisa", "estou à disposição", "posso ajudar em algo mais"), label="sem fechamento de atendimento"),)),
        )
    raise ValueError(theme)


def _paired(seed: int, theme: str, description: str, focus: str) -> list[ScenarioSpec]:
    turns = _paired_script(seed, theme)
    return [
        ScenarioSpec(
            id=f"human_{agent}_{theme}", category="human_conversation",
            description=description, turns=turns, review_focus=focus, agent_id=agent,
        )
        for agent in ("todd", "morgana")
    ]


def _shared_room(seed: int, variant: int) -> ScenarioSpec:
    rng = random.Random(seed + variant * 7919)
    detail, anchors = _choose(rng, (
        ("eu tenho uma bicicleta velha que ainda quero consertar", ("bicicleta", "consert")),
        ("eu comecei um livro ontem e já perdi o marcador de página", ("livro", "marcador")),
        ("eu comprei uma luminária pequena para a mesa e gostei mais do que esperava", ("lumin", "mesa")),
    ))
    turns = (
        _t("vocês dois podem ficar por aqui, mas não precisam responder a tudo", social=True, max_words=70),
        _t(detail, social=True, max_words=70),
        _t("enfim, meu dia foi normal. teve uma hora que eu fiquei uns cinco minutos olhando pela janela sem fazer nada", social=True, max_words=70),
        _t("isso não é um pedido de análise, só tô contando mesmo", social=True, max_words=55),
        _t("Todd e Morgana, cada um fala uma coisa curta que chamou atenção nessa conversa", social=True, max_words=90),
        _t("agora podem discordar um do outro se tiver motivo, mas não inventem conflito", social=True, max_words=80),
        _t("qual coisa concreta que eu mencionei lá no começo ainda está pendente?", max_words=70, extra=(_c("multiagent_contains_any", anchors, severity="warn", label="memória local compartilhada"),)),
        _t("boa. deixa a conversa aberta, sem despedida de atendente", social=True, max_words=60),
    )
    return ScenarioSpec(
        id=f"human_shared_room_{variant}", category="human_conversation_shared",
        description="Conversa cotidiana com usuário, Todd e Morgana presentes no mesmo episódio; silêncio seletivo e continuidade importam.",
        turns=turns,
        review_focus="A conversa parece uma sala compartilhada? O segundo agente só entra quando agrega? Há química sem painel de especialistas, overtalk ou fechamento de atendimento?",
        agent_id=None,
    )


def build_human_conversation_scenarios(seed: int, *, quick: bool = False) -> list[ScenarioSpec]:
    specs = [
        ("getting_to_know", "Conhecer o usuário sem interrogatório e manter detalhes leves da conversa.", "Curiosidade é proporcional? Há perguntas de volta naturais sem entrevista? A identidade do agente aparece sem performance?"),
        ("daily_continuity", "Conversa cotidiana com mudança de assunto e callback relevante.", "O agente conecta detalhe anterior quando útil sem soar como prontuário, resumo ou memória invasiva?"),
        ("casual_disagreement", "Humor leve e discordância social sem submissão nem hostilidade.", "A discordância parece relacional e própria do agente? Evita concordância automática, palestra e caricatura?"),
        ("story_and_followup", "Ouvir uma pequena história cotidiana, reagir e lembrar detalhe mais tarde.", "O agente acompanha a história como conversa, não como análise; callback é natural e não encerra como suporte?"),
    ]
    selected = specs[:2] if quick else specs
    scenarios: list[ScenarioSpec] = []
    for theme, description, focus in selected:
        scenarios.extend(_paired(seed, theme, description, focus))
    scenarios.append(_shared_room(seed, 1))
    if not quick:
        scenarios.append(_shared_room(seed, 2))
    # Keep Todd/Morgana pair adjacency for blind-pair report construction, while varying theme wording by seed.
    return scenarios
