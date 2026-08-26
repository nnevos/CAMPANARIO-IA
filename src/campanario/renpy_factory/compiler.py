from __future__ import annotations

import re
from pathlib import Path

from .models import RenPyGDD, ValidationReport


def _rpy(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\r", " ").replace("\n", " ")


def _safe_build_name(title: str) -> str:
    import unicodedata
    value = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return (value or "CAMPANARIO_RENPY_GAME")[:80]


def compile_script(gdd: RenPyGDD) -> str:
    lines = [
        "# -*- coding: utf-8 -*-",
        f"# Script educacional baseado no GDD aprovado - {_rpy(gdd.title)}",
        "",
        'define gui.accent_color = "#003c6e"',
        "",
        "# Personagens",
        "define nar = Character(None)",
        f'define p = Character("{_rpy(gdd.character.name)}", color="#ffffff")',
        'define j = Character("Jogador", color="#ffcc66")',
        "",
        "# Imagens",
        'image bg mainmenu = "main_menu.png"',
        'image bg CenarioInicial = "cenarioinicial.png"',
        'image bg Cenario = "cenarioinstrutor.png"',
        'image bg FinalIniciante = "Final_Iniciante.png"',
        'image bg FinalProficiente = "Final_Proficiente.png"',
        'image bg FinalMestre = "Final_Mestre.png"',
        "",
        "# Variáveis",
        "default score = 0",
        "default route = None",
        "",
        "# HUD",
        "screen hud():",
        "    frame:",
        "        align (0.95, 0.05)",
        "        xpadding 10",
        "        ypadding 5",
        '        text "Pontuação: [score]" size 22 color "#ffffff"',
        "",
        "screen fundo_fixo_screen():",
        '    add "cenarioinstrutor.png" xalign 0.5 yalign 0.5',
        "",
        "# TELA DE PERGUNTAS",
        "screen question_screen(question, choices):",
        "    modal True",
        '    key "dismiss" action NullAction()',
        '    add "cenarioinicial.png"',
        "",
        "    frame:",
        "        align (0.5, 0.5)",
        "        xsize 1400",
        "        ysize 700",
        '        background Solid("#003c6e")',
        "        padding (20, 20)",
        "",
        "        frame:",
        '            background Solid("#ffffff")',
        "            xfill True",
        "            yfill True",
        "            padding (40, 40)",
        "",
        "            vbox:",
        "                spacing 40",
        "                xalign 0.5",
        "                yalign 0.5",
        "",
        '                text "[question]":',
        "                    size 32",
        '                    color "#000000"',
        "                    xalign 0.5",
        "                    textalign 0.5",
        "",
        "                for c in choices:",
        "                    button:",
        "                        xsize 900",
        "                        xalign 0.5",
        "                        xpadding 24",
        "                        ypadding 16",
        '                        background Solid("#003c6e")',
        '                        hover_background Solid("#004f6e")',
        "                        action Return(c[1])",
        "",
        "                        text c[0]:",
        "                            size 26",
        '                            color "#ffffff"',
        "                            xalign 0.5",
        "                            textalign 0.5",
        "",
        "# INÍCIO",
        "label start:",
        "    scene bg CenarioInicial",
        "    with fade",
        "    $ _window_show()",
        "",
    ]
    for intro in gdd.intro_lines[:6]:
        lines.append(f'    nar "{_rpy(intro)}"')
    lines += [
        "    jump chamado",
        "",
        "label chamado:",
        "    show screen hud",
        "    show screen fundo_fixo_screen zorder -100",
        "",
    ]
    character_lines = gdd.character_intro_lines or [
        f"Olá! Sou {gdd.character.name}.",
        f"Estamos em {gdd.scenario.name} para {gdd.scenario.pedagogical_function.rstrip('.').casefold()}.",
        gdd.character.narrative_goal,
    ]
    for line in character_lines[:3]:
        lines.append(f'    p "{_rpy(line)}"')
    lines += [
        "    jump pp",
        "",
        "# PERGUNTA PRINCIPAL",
    ]
    _emit_main_question(lines, gdd)
    for code, route in (("A", gdd.route_a), ("B", gdd.route_b), ("C", gdd.route_c)):
        lines += ["", f"# ROTA {code}", f"label route_{code}:"]
        for idx, question in enumerate(route.questions, start=1):
            _emit_route_question(lines, idx, question)
        lines += ["    jump ending"]
    lines += [
        "",
        "# FINAL",
        "label ending:",
        "    hide screen hud",
        "    hide screen fundo_fixo_screen",
        "",
        "    if score <= 4:",
        "        scene bg FinalIniciante with dissolve",
        f'        p "{_rpy(gdd.finals.beginner)}"',
        "    elif score <= 8:",
        "        scene bg FinalProficiente with dissolve",
        f'        p "{_rpy(gdd.finals.proficient)}"',
        "    else:",
        "        scene bg FinalMestre with dissolve",
        f'        p "{_rpy(gdd.finals.master)}"',
        f'        p "{_rpy(gdd.final_message)}"',
        "",
        "    menu:",
        f'        p "{_rpy(gdd.replay_prompt)}"',
        '        "Sim":',
        "            $ score = 0",
        "            $ route = None",
        "            jump start",
        '        "Não":',
        "            return",
        "",
    ]
    return "\n".join(lines)


def _emit_main_question(lines: list[str], gdd: RenPyGDD) -> None:
    q = gdd.main_question
    letters = ["A", "B", "C"]
    lines += [
        "label pp:",
        "    $ route = None",
        "    $ _window_hide()",
        "",
        "    $ escolha_pp = renpy.call_screen(",
        '        "question_screen",',
        f'        question="{_rpy(q.prompt)}",',
        "        choices=[",
    ]
    for letter, choice in zip(letters, q.choices, strict=True):
        lines.append(f'            ("{_rpy(choice.text)}", "{letter}"),')
    lines += ["        ]", "    )", "", "    $ _window_show()", ""]
    for idx, (letter, choice) in enumerate(zip(letters, q.choices, strict=True)):
        if idx == 0:
            lines.append(f'    if escolha_pp == "{letter}":')
        elif idx == 1:
            lines.append(f'    elif escolha_pp == "{letter}":')
        else:
            lines.append("    else:")
        lines.append(f"        $ score += {choice.score}")
        lines.append(f'        $ route = "{letter}"')
        lines.append(f'        p "{_rpy(choice.justification)}"')
        lines.append(f'        p "{_rpy(choice.feedback)}"')
        lines.append(f"        jump route_{letter}")
        lines.append("")


def _emit_route_question(lines: list[str], idx: int, question) -> None:
    var = f"q{idx}"
    lines += [
        "    $ _window_hide()",
        f"    $ {var} = renpy.call_screen(",
        '        "question_screen",',
        f'        question="{_rpy(question.prompt)}",',
        "        choices=[",
    ]
    letters = ["A", "B"]
    for letter, choice in zip(letters, question.choices, strict=True):
        lines.append(f'            ("{_rpy(choice.text)}", "{letter}"),')
    lines += ["        ]", "    )", "    $ _window_show()", ""]
    first, second = question.choices
    lines += [
        f'    if {var} == "A":',
        f"        $ score += {first.score}",
        f'        p "{_rpy(first.feedback)}"',
        "    else:",
        f'        p "{_rpy(second.feedback)}"',
        "",
    ]


def validate_compiled_project(gdd: RenPyGDD, script_text: str, screens_text: str, options_text: str) -> list[str]:
    """Deterministic preflight for the minimal Ren'Py deliverable.

    This is intentionally provider-free: it verifies that code is a faithful
    compilation of the approved GDD and that the canonical template files still
    expose the expected Ren'Py anchors. It does not replace Ren'Py SDK lint.
    """
    issues: list[str] = []
    expected_script = compile_script(gdd)
    if script_text != expected_script:
        issues.append("script.rpy diverge da compilação determinística do GDD aprovado")

    required_labels = ("start", "chamado", "pp", "route_A", "route_B", "route_C", "ending")
    for label in required_labels:
        if f"label {label}:" not in script_text:
            issues.append(f"script.rpy sem label obrigatório: {label}")

    question_calls = script_text.count('renpy.call_screen(')
    if question_calls != 10:
        issues.append(f"script.rpy deve conter 10 chamadas de pergunta; encontrou {question_calls}")
    if script_text.count('question="') != 10:
        issues.append("script.rpy não contém exatamente 10 prompts de pergunta compilados")

    if "screen question_screen(question, choices):" not in script_text:
        issues.append("script.rpy sem question_screen esperado")
    if "screen hud():" not in script_text:
        issues.append("script.rpy sem HUD esperado")

    # screens.rpy is a canonical template: verify stable anchors instead of
    # regenerating or attempting to interpret the whole file.
    for anchor in ("screen main_menu():", "screen navigation():", "screen save():", "screen load():"):
        if anchor not in screens_text:
            issues.append(f"screens.rpy do template sem âncora esperada: {anchor}")

    expected_build_name = _safe_build_name(gdd.title)
    if f'define config.name = _("{gdd.title}")' not in options_text:
        issues.append("options.rpy não recebeu config.name do GDD")
    if f'define build.name = "{expected_build_name}"' not in options_text:
        issues.append("options.rpy não recebeu build.name seguro do GDD")
    if 'define config.version = "1.0"' not in options_text:
        issues.append("options.rpy alterou/perdeu a versão canônica 1.0")

    return issues


def render_code_compat_report(gdd: RenPyGDD, issues: list[str]) -> str:
    status = "APROVADO" if not issues else "REPROVADO"
    lines = [
        "# PREFLIGHT DE COMPATIBILIDADE REN'PY",
        "",
        f"Status: {status}",
        "",
        "Verificações determinísticas: fidelidade GDD -> script, labels obrigatórios, 10 perguntas,",
        "âncoras do screens.rpy canônico e campos mínimos do options.rpy.",
        "Este preflight não substitui o lint/build do Ren'Py SDK.",
        "",
    ]
    if issues:
        lines += ["## Problemas", *[f"- {item}" for item in issues], ""]
    else:
        lines += ["Nenhum problema estrutural encontrado no pacote mínimo.", ""]
    return "\n".join(lines)


def render_gdd_markdown(gdd: RenPyGDD) -> str:
    out = [
        "# GAME DESIGN DOCUMENT (GDD)",
        "## EDUCATIVO – REN’PY",
        "",
        "## 📦 1. RESUMO DO JOGO",
        "- Gênero: Jogo educativo narrativo",
        "- Plataforma: Ren’Py",
        f"- Tema: {gdd.theme}",
        f"- Objetivo educacional: {gdd.educational_objective}",
        "",
        "## 📚 2. BASE PEDAGÓGICA",
        "### Estrutura Pedagogicamente Encadeada",
        "- 1 Pergunta Principal: 3 alternativas conceituais (Adequada +3, Parcialmente Adequada +1, Inadequada 0).",
        "- 9 Perguntas Adicionais divididas em 3 Trilhas Derivadas: 2 alternativas por pergunta (Adequada +2, Inadequada 0).",
        "- Total do Banco de Questões: 10 perguntas e 21 alternativas semanticamente distintas.",
        "",
        "### Tabela Fixa de Pontuação",
        "| Tipo de Alternativa | Pontuação |",
        "|---|---:|",
        "| Principal – Adequada | +3 |",
        "| Principal – Parcialmente Adequada | +1 |",
        "| Principal – Inadequada | 0 |",
        "| Adicional – Adequada | +2 |",
        "| Adicional – Inadequada | 0 |",
        "",
        "### Regras Rígidas de Formulação",
        "- Evitar rótulos mecânicos como ‘Correto’, ‘Certo’, ‘Errado’ e ‘Incorreto’ no banco de questões.",
        "- Alternativas são frases conceituais completas sustentadas pelo e-book da unidade.",
        "- Cada alternativa contém pontuação, justificativa teórica, feedback pedagógico e evidência rastreável.",
        "",
        "## 👥 3. PERSONAGENS, CENÁRIOS E ENREDO",
        "### 3.1 Personagem",
        f"- Nome: {gdd.character.name}",
        f"- Papel clínico ou profissional: {gdd.character.role}",
        f"- Personalidade: {gdd.character.personality}",
        f"- Aparência: {gdd.character.appearance}",
        f"- Forma de fala: {gdd.character.speech_style}",
        f"- Objetivo narrativo-pedagógico: {gdd.character.narrative_goal}",
        "",
        "### 3.2 Cenários",
        f"- Nome: {gdd.scenario.name}",
        f"- Função pedagógica: {gdd.scenario.pedagogical_function}",
        f"- Descrição visual: {gdd.scenario.visual_description}",
        f"- Descrição sonora: {gdd.scenario.sound_description}",
        "",
        "### 3.3 Enredo",
        f"- Tema central: {gdd.central_theme}",
        f"- Conflito narrativo: {gdd.narrative_conflict}",
        "- Finais Narrativos:",
        f"  - Iniciante (0–4 pts): {gdd.finals.beginner}",
        f"  - Proficiente (5–8 pts): {gdd.finals.proficient}",
        f"  - Mestre (9+ pts): {gdd.finals.master}",
        f"- Mensagem final pedagógica: {gdd.final_message}",
        "",
        "## 🌳 4. ÁRVORE NARRATIVA COMPLETA",
        "```text",
        "        [PERGUNTA PRINCIPAL]",
        "          /      |      \\",
        "      [A +3]   [B +1]   [C 0]",
        "        |        |        |",
        "    TRILHA A  TRILHA B  TRILHA C",
        "      A1         B1         C1",
        "      ↓          ↓          ↓",
        "      A2         B2         C2",
        "      ↓          ↓          ↓",
        "      A3         B3         C3",
        "```",
        "",
        "## ❓ 5. MODELO PADRÃO – BANCO DE QUESTÕES (PREENCHIMENTO)",
    ]
    _md_question(out, "🔹 PERGUNTA PRINCIPAL", gdd.main_question)
    for code, route in (("A", gdd.route_a), ("B", gdd.route_b), ("C", gdd.route_c)):
        out += ["", f"### 🔸 TRILHA {code} – {route.title}"]
        for idx, q in enumerate(route.questions, start=1):
            _md_question(out, f"{code}{idx}", q)
    out += [
        "",
        "## 🏁 6. PONTUAÇÃO E FINAIS",
        "| Intervalo | Classificação | Resultado pedagógico |",
        "|---:|---|---|",
        f"| 0–4 | Iniciante | {gdd.finals.beginner} |",
        f"| 5–8 | Proficiente | {gdd.finals.proficient} |",
        f"| 9+ | Mestre | {gdd.finals.master} |",
        "",
        "## ⚙️ 7. IMPLEMENTAÇÃO TÉCNICA (REN’PY READY)",
        "O bloco abaixo é o mesmo conteúdo que será salvo como `script.rpy` na Etapa 2. Não há uma segunda geração de IA.",
        "",
        "```renpy",
        compile_script(gdd).rstrip(),
        "```",
        "",
        "## 📦 8. ENTREGA FINAL",
        "✓ 10 perguntas e 21 alternativas reais, contextualizadas e semanticamente distintas foram geradas.",
        "",
    ]
    return "\n".join(out)


def _md_question(out: list[str], title: str, question) -> None:
    out += ["", f"### {title}", question.prompt]
    for idx, c in enumerate(question.choices):
        label = chr(65 + idx)
        out += [
            f"- **{label})** {c.text}",
            f"  - ({c.score:+d} | Justificativa: {c.justification} | Feedback: {c.feedback})",
        ]


def render_gdd_docx(gdd: RenPyGDD, output_path: Path) -> Path:
    """Create a self-contained DOCX with stdlib only (no runtime dependency)."""
    from xml.sax.saxutils import escape
    import zipfile

    blocks: list[tuple[str, str]] = []
    def h(text: str, level: int = 1): blocks.append((f"Heading{level}", text))
    def p(text: str): blocks.append(("Normal", text))
    def b(label: str, value: str): blocks.append(("ListBullet", f"{label}: {value}"))

    blocks.append(("Title", "GAME DESIGN DOCUMENT (GDD)"))
    blocks.append(("Subtitle", "EDUCATIVO – REN’PY"))
    h("1. RESUMO DO JOGO")
    b("Gênero", "Jogo educativo narrativo")
    b("Plataforma", "Ren’Py")
    b("Tema", gdd.theme)
    b("Objetivo educacional", gdd.educational_objective)
    h("2. BASE PEDAGÓGICA")
    h("Estrutura Pedagogicamente Encadeada", 2)
    p("• 1 Pergunta Principal: 3 alternativas conceituais (Adequada +3, Parcialmente Adequada +1 e Inadequada 0).")
    p("• 9 Perguntas Adicionais divididas em 3 Trilhas Derivadas: cada pergunta possui 2 alternativas (Adequada +2 e Inadequada 0).")
    p("• Total do Banco de Questões: 10 perguntas e 21 alternativas semanticamente distintas.")
    h("Tabela Fixa de Pontuação", 2)
    for text in ("Principal – Adequada: +3", "Principal – Parcialmente Adequada: +1", "Principal – Inadequada: 0", "Adicional – Adequada: +2", "Adicional – Inadequada: 0"):
        p(text)
    h("Regras Rígidas de Formulação", 2)
    p("• Evitar rótulos mecânicos como 'Correto', 'Certo', 'Errado' e 'Incorreto' no banco de questões.")
    p("• Alternativas são frases conceituais completas sustentadas pelo e-book da unidade.")
    p("• Cada alternativa contém pontuação, justificativa teórica, feedback pedagógico e evidência rastreável.")
    h("3. PERSONAGENS, CENÁRIOS E ENREDO")
    h("3.1 Personagem", 2)
    for label, value in (("Nome", gdd.character.name), ("Papel clínico ou profissional", gdd.character.role), ("Personalidade", gdd.character.personality), ("Aparência", gdd.character.appearance), ("Forma de fala", gdd.character.speech_style), ("Objetivo narrativo-pedagógico", gdd.character.narrative_goal)):
        b(label, value)
    h("3.2 Cenários", 2)
    for label, value in (("Nome", gdd.scenario.name), ("Função pedagógica", gdd.scenario.pedagogical_function), ("Descrição visual", gdd.scenario.visual_description), ("Descrição sonora", gdd.scenario.sound_description)):
        b(label, value)
    h("3.3 Enredo", 2)
    b("Tema central", gdd.central_theme)
    b("Conflito narrativo", gdd.narrative_conflict)
    p("• Finais Narrativos:")
    p(f"  Iniciante (0–4 pts): {gdd.finals.beginner}")
    p(f"  Proficiente (5–8 pts): {gdd.finals.proficient}")
    p(f"  Mestre (9+ pts): {gdd.finals.master}")
    b("Mensagem final pedagógica", gdd.final_message)
    h("4. ÁRVORE NARRATIVA COMPLETA")
    p("[PERGUNTA PRINCIPAL]")
    p("A +3 → A1 → A2 → A3")
    p("B +1 → B1 → B2 → B3")
    p("C  0 → C1 → C2 → C3")
    h("5. MODELO PADRÃO – BANCO DE QUESTÕES (PREENCHIMENTO)")

    def q(label, question):
        h(label, 3)
        p(question.prompt)
        for idx, choice in enumerate(question.choices):
            letter = chr(65 + idx)
            p(f"{letter}) {choice.text}")
            p(f"({choice.score:+d} | Justificativa: {choice.justification} | Feedback: {choice.feedback})")

    q("PERGUNTA PRINCIPAL", gdd.main_question)
    for code, route in (("A", gdd.route_a), ("B", gdd.route_b), ("C", gdd.route_c)):
        h(f"TRILHA {code} – {route.title}", 2)
        for idx, question in enumerate(route.questions, start=1):
            q(f"{code}{idx}", question)
    h("6. PONTUAÇÃO E FINAIS")
    p(f"0–4 | Iniciante | {gdd.finals.beginner}")
    p(f"5–8 | Proficiente | {gdd.finals.proficient}")
    p(f"9–11 | Mestre | {gdd.finals.master}")
    h("7. IMPLEMENTAÇÃO TÉCNICA (REN’PY READY)")
    p("O código abaixo é exatamente o conteúdo que será salvo como script.rpy na Etapa 2; não há nova geração de IA.")
    for line in compile_script(gdd).splitlines():
        p(line if line else " ")
    h("8. ENTREGA FINAL")
    p("✓ 10 perguntas e 21 alternativas reais, contextualizadas e semanticamente distintas foram geradas.")

    def para(style: str, text: str) -> str:
        style_xml = f'<w:pStyle w:val="{style}"/>' if style else ''
        return f'<w:p><w:pPr>{style_xml}</w:pPr><w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'

    body = ''.join(para(style, text) for style, text in blocks)
    document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + \
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body + \
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/></w:sectPr></w:body></w:document>'
    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="21"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:jc w:val="center"/><w:spacing w:after="160"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:pPr><w:jc w:val="center"/><w:spacing w:after="300"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="240" w:after="100"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="180" w:after="80"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="23"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="120" w:after="60"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:sz w:val="21"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="360"/></w:pPr></w:style>
</w:styles>'''
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
    docrels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document)
        zf.writestr("word/styles.xml", styles)
        zf.writestr("word/_rels/document.xml.rels", docrels)
    return output_path

def render_evidence_report(gdd: RenPyGDD, report: ValidationReport) -> str:
    out = ["# EVIDENCE REPORT", "", f"Status: {'VALIDADO' if report.valid else 'REJEITADO'}", f"Evidências verificadas: {report.checked_evidence}", ""]
    if report.issues:
        out += ["## Ocorrências"] + [f"- [{i.severity.upper()}] {i.path}: {i.message}" for i in report.issues]
    else:
        out += ["Nenhuma violação de grounding detectada."]
    out += ["", "## Regra", "As evidências são selecionadas de um catálogo extraído do e-book; o modelo não redige as citações."]
    return "\n".join(out) + "\n"


def render_visual_prompts(gdd: RenPyGDD) -> str:
    return f'''CAPA
CRIE UMA CAPA DE INICIO DE JOGO COM O NOME “{gdd.title.upper()}” COM DETALHES RELACIONADOS AO TEMA “{gdd.theme}”, CENTRALIZADO EM 1920x1080 16:9. NÃO ADICIONE CONCEITOS PEDAGÓGICOS QUE NÃO ESTEJAM NO GDD VALIDADO.

CENARIO
crie uma imagem de um Nome: {gdd.scenario.name} Função pedagógica: {gdd.scenario.pedagogical_function} Descrição visual: {gdd.scenario.visual_description} realista, sem efeitos, sem texto no cenario, sem estilização, sem pessoas, em 1920x1080 16:9

PERSONAGEM
crie a imagem do personagem ficticio Nome: {gdd.character.name}

Papel: {gdd.character.role}

Personalidade: {gdd.character.personality}

Aparência: {gdd.character.appearance} de braços cruzados olhando para a câmera realista sem filtro sem fundo camera do quadril para cima sem fundo
'''


def render_options(title: str) -> str:
    template = Path(__file__).with_name("template") / "game" / "options.rpy"
    if not template.exists():
        raise FileNotFoundError("template/game/options.rpy ausente")
    text = template.read_text(encoding="utf-8-sig")
    build = _safe_build_name(title)
    text = re.sub(r'define config\.name = _\(".*?"\)', f'define config.name = _("{_rpy(title)}")', text, count=1)
    text = re.sub(r'define build\.name = ".*?"', f'define build.name = "{build}"', text, count=1)
    text = re.sub(r'define config\.save_directory = ".*?"', f'define config.save_directory = "{build}-1.0"', text, count=1)
    return text
