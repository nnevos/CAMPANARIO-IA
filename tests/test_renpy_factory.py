import json
from pathlib import Path

import pytest

from campanario.model.protocol import FakeModelProvider
from campanario.renpy_factory.compiler import compile_script, render_gdd_markdown, render_options, render_visual_prompts
from campanario.renpy_factory.extractor import extract_ebook
from campanario.renpy_factory.models import RenPyGDD
from campanario.renpy_factory.service import GroundingValidationError, RenPyFactoryService
from campanario.renpy_factory.validator import evidence_quote_present, validate_gdd


SOURCE = (
    "O sistema operacional atua como camada intermediária entre hardware e aplicações. "
    "O kernel gerencia processos, memória e dispositivos. "
    "A memória virtual amplia o espaço disponível para execução dos programas. "
    "Distribuições Linux podem priorizar estabilidade, facilidade de uso ou inovação. "
    "O terminal permite navegar pelo sistema de arquivos e executar comandos administrativos. "
    "O Linux teve origem em 1991 com o desenvolvimento iniciado por Linus Torvalds. "
    "O código-fonte aberto permite estudo, modificação e redistribuição. "
    "Servidores Linux são utilizados em ambientes corporativos e serviços digitais. "
    "Máquinas virtuais permitem praticar em ambiente isolado. "
    "Permissões e níveis de privilégio ajudam a proteger os recursos do sistema."
)

QUOTES = [
    "O sistema operacional atua como camada intermediária entre hardware e aplicações.",
    "O kernel gerencia processos, memória e dispositivos.",
    "A memória virtual amplia o espaço disponível para execução dos programas.",
    "Distribuições Linux podem priorizar estabilidade, facilidade de uso ou inovação.",
    "O terminal permite navegar pelo sistema de arquivos e executar comandos administrativos.",
    "O Linux teve origem em 1991 com o desenvolvimento iniciado por Linus Torvalds.",
    "O código-fonte aberto permite estudo, modificação e redistribuição.",
    "Servidores Linux são utilizados em ambientes corporativos e serviços digitais.",
    "Máquinas virtuais permitem praticar em ambiente isolado.",
    "Permissões e níveis de privilégio ajudam a proteger os recursos do sistema.",
]

QUOTE_TO_ID = {quote: f"ev_{idx:04d}" for idx, quote in enumerate(QUOTES, start=1)}


def choice(text, score, quote):
    return {"text": text, "score": score, "justification": "Derivada diretamente da evidência indicada.", "feedback": "Compare sua escolha com o conceito apresentado no material.", "evidence": {"quote": quote, "source_hint": QUOTE_TO_ID[quote]}}


def question(i, scores):
    quote = QUOTES[i % len(QUOTES)]
    return {"prompt": f"Questão pedagógica {i + 1}: qual interpretação é mais alinhada ao material?", "choices": [choice(f"Alternativa {i + 1}.{n + 1}", score, quote) for n, score in enumerate(scores)]}


def valid_payload():
    return {
        "title": "Linux em Prática",
        "theme": "Fundamentos do Linux",
        "educational_objective": "Integrar conceitos básicos de sistemas operacionais e Linux.",
        "character": {"name": "Dra. Helena", "role": "Instrutora de infraestrutura", "personality": "Analítica e didática", "appearance": "Profissional com tablet", "speech_style": "Técnica e clara", "narrative_goal": "Orientar decisões baseadas no material da unidade."},
        "scenario": {"name": "Laboratório Linux", "pedagogical_function": "Contextualizar decisões", "visual_description": "Laboratório de informática com estações de trabalho", "sound_description": "Ambiente discreto de laboratório"},
        "central_theme": "Uso fundamentado de Linux",
        "narrative_conflict": "Uma equipe precisa revisar conceitos para estabilizar seu ambiente fictício.",
        "finals": {
            "beginner": "Compreensão fragmentada; a equipe ainda toma decisões sem integrar os fundamentos da unidade.",
            "proficient": "Integração parcial; a equipe aplica parte dos conceitos, mas ainda mantém lacunas de decisão.",
            "master": "Integração conceitual consolidada; a equipe aplica os fundamentos da unidade de forma consistente.",
        },
        "final_message": "Você consolidou os conceitos centrais desta unidade.",
        "intro_lines": [
            "Bem-vindo ao simulador desta unidade.",
            "Você analisará situações construídas a partir dos conceitos do material.",
            "Cada decisão altera sua pontuação e direciona uma trilha de análise.",
            "Considere os fundamentos apresentados no e-book antes de escolher.",
            "Ao final, sua compreensão será classificada como Iniciante, Proficiente ou Mestre.",
        ],
        "character_intro_lines": [
            "Olá! Sou a Dra. Helena e vou acompanhar esta simulação.",
            "Estamos no Laboratório Linux para revisar decisões baseadas no material da unidade.",
            "Vamos começar pela situação principal.",
        ],
        "replay_prompt": "Deseja realizar uma nova simulação?",
        "main_question": question(0, [3, 1, 0]),
        "route_a": {"title": "Arquitetura", "questions": [question(1, [2, 0]), question(2, [2, 0]), question(3, [2, 0])]},
        "route_b": {"title": "Ecossistema", "questions": [question(4, [2, 0]), question(5, [2, 0]), question(6, [2, 0])]},
        "route_c": {"title": "Prática", "questions": [question(7, [2, 0]), question(8, [2, 0]), question(9, [2, 0])]},
    }




def staged_part_from_request(request, payload=None):
    data = payload or valid_payload()
    prompt = request.messages[-1].content
    if "ETAPA 1/5" in prompt:
        keys = ["title", "theme", "educational_objective", "character", "scenario", "central_theme", "narrative_conflict", "finals", "final_message", "intro_lines", "character_intro_lines", "replay_prompt"]
        return {key: data[key] for key in keys}
    if "ETAPA 2/5" in prompt:
        return data["main_question"]
    if "ETAPA DE ROTA A" in prompt:
        return data["route_a"]
    if "ETAPA DE ROTA B" in prompt:
        return data["route_b"]
    if "ETAPA DE ROTA C" in prompt:
        return data["route_c"]
    for code, route_key in (("A", "route_a"), ("B", "route_b"), ("C", "route_c")):
        for idx in range(1, 4):
            if f"PERGUNTA {code}{idx}" in prompt:
                return data[route_key]["questions"][idx - 1]
    if "AUDITORIA PEDAGÓGICA FINAL" in prompt:
        return {"passed": True, "issues": []}
    if "AUDITORIA FOCADA DE CONSISTÊNCIA DAS ALTERNATIVAS" in prompt:
        return {"passed": True, "issues": []}
    if "AUDITORIA ADVERSARIAL POR PERGUNTA" in prompt:
        return {"passed": True, "issues": []}
    if "AUDITORIA ADVERSARIAL FINAL" in prompt:
        return {"passed": True, "issues": []}
    raise AssertionError("etapa desconhecida")


class StagedProvider:
    def __init__(self, payload=None):
        self.payload = payload or valid_payload()
        self.requests = []
    async def health(self):
        return True
    async def stream(self, request):
        from campanario.model.protocol import ModelChunk
        self.requests.append(request)
        yield ModelChunk(text=json.dumps(staged_part_from_request(request, self.payload), ensure_ascii=False))
        yield ModelChunk(text="", done=True)


def test_extract_plain_text_and_grounding_contract():
    ebook = extract_ebook("unidade.txt", SOURCE.encode())
    gdd = RenPyGDD.model_validate(valid_payload())
    report = validate_gdd(gdd, ebook.normalized_text)
    assert report.valid
    assert report.checked_evidence == 21


def test_grounding_rejects_quote_not_present_in_ebook():
    ebook = extract_ebook("unidade.txt", SOURCE.encode())
    payload = valid_payload()
    payload["route_c"]["questions"][2]["choices"][1]["evidence"]["quote"] = "Fato inventado que não existe no e-book."
    report = validate_gdd(RenPyGDD.model_validate(payload), ebook.normalized_text)
    assert not report.valid
    assert any("não foi localizada" in issue.message for issue in report.issues)


def test_compiler_is_deterministic_and_contains_10_question_structure():
    gdd = RenPyGDD.model_validate(valid_payload())
    script_a = compile_script(gdd)
    script_b = compile_script(gdd)
    assert script_a == script_b
    assert "label pp:" in script_a
    assert "label route_A:" in script_a and "label route_B:" in script_a and "label route_C:" in script_a
    assert script_a.count("renpy.call_screen(") == 10
    assert "Dra. Helena" in script_a




def test_gdd_contains_exact_compiled_script_for_one_to_one_review():
    gdd = RenPyGDD.model_validate(valid_payload())
    script = compile_script(gdd).rstrip()
    rendered = render_gdd_markdown(gdd)
    assert script in rendered
    assert "Evidência:" not in rendered  # audit stays in EVIDENCE_REPORT, not in the production GDD
    assert gdd.finals.beginner in rendered
    assert gdd.finals.proficient in rendered
    assert gdd.finals.master in rendered


def test_screens_is_canonical_template_and_options_changes_only_minimum_fields(tmp_path):
    template_game = Path("src/campanario/renpy_factory/template/game")
    reference_game = Path("/mnt/data/un01_ref/UN01/game")
    if reference_game.exists():
        assert (template_game / "screens.rpy").read_bytes() == (reference_game / "screens.rpy").read_bytes()
        assert (template_game / "options.rpy").read_bytes() == (reference_game / "options.rpy").read_bytes()
    original = (template_game / "options.rpy").read_text(encoding="utf-8-sig")
    rendered = render_options("Minha Unidade Teste")
    import re
    def normalize_mutable(text):
        text = re.sub(r'define config\.name = _\(".*?"\)', 'define config.name = _("<NAME>")', text, count=1)
        text = re.sub(r'define build\.name = ".*?"', 'define build.name = "<BUILD>"', text, count=1)
        text = re.sub(r'define config\.save_directory = ".*?"', 'define config.save_directory = "<SAVE>"', text, count=1)
        return text
    assert normalize_mutable(rendered) == normalize_mutable(original)
    assert 'define config.version = "1.0"' in rendered


def test_visual_prompts_preserve_user_direction_style():
    prompts = render_visual_prompts(RenPyGDD.model_validate(valid_payload()))
    assert "1920x1080 16:9" in prompts
    assert "sem texto no cenario" in prompts
    assert "sem fundo" in prompts
    assert "PERSONAGEM" in prompts


@pytest.mark.asyncio
async def test_factory_writes_auditable_zip(tmp_path):
    provider = StagedProvider()
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate("unidade.txt", SOURCE.encode())
    assert result["questions"] == 10
    assert result["alternatives"] == 21
    assert result["evidence_checked"] == 21
    assert len(provider.requests) == 18  # 5 etapas + 2 auditorias normais + 10 perguntas adversariais + auditoria adversarial final
    assert service.zip_path(result["run_id"]).exists()


def test_ui_has_dedicated_multiunit_gdd_first_factory_page():
    main_html = Path("src/campanario/web/index.html").read_text(encoding="utf-8")
    factory_html = Path("src/campanario/web/renpy_factory.html").read_text(encoding="utf-8")
    assert "Fábrica Ren'Py" in main_html
    assert "location.href='/renpy-factory'" in main_html
    assert 'id="books"' in factory_html
    assert 'multiple' in factory_html
    assert 'id="generateQueue"' in factory_html
    assert 'id="compileOne"' in factory_html
    assert 'id="compileAll"' in factory_html
    assert "/api/v1/renpy-factory/gdd" in factory_html
    assert "GDD.docx" in factory_html
    assert "screens.rpy" in factory_html
    assert "Auditoria por unidade" in factory_html
    assert 'id="gddPreview"' in factory_html
    assert "UN${String(i+1).padStart(2,'0')}" in factory_html
    assert 'href="/"' in factory_html


def test_factory_has_direct_windows_launcher():
    launcher = Path("tools/windows/ABRIR_FABRICA_RENPY.bat").read_text(encoding="utf-8")
    assert "/renpy-factory" in launcher
    assert "INICIAR_CAMPANARIO.bat" in launcher

from campanario.renpy_factory.service import _parse_json_payload


def test_factory_parser_accepts_fenced_and_wrapped_json():
    payload = valid_payload()
    raw = "Observação descartável\n```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```\nfim"
    parsed = _parse_json_payload(raw)
    assert parsed["title"] == payload["title"]


def test_factory_parser_repairs_trailing_commas():
    raw = '{"title":"x","items":[1,2,],}'
    parsed = _parse_json_payload(raw)
    assert parsed == {"title": "x", "items": [1, 2]}


@pytest.mark.asyncio
async def test_factory_requests_json_mode_and_retries_only_failed_stage(tmp_path):
    class CapturingProvider:
        def __init__(self):
            self.requests = []
            self.route_b_calls = 0
        async def health(self):
            return True
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "ETAPA DE ROTA B" in prompt:
                self.route_b_calls += 1
                if self.route_b_calls == 1:
                    yield ModelChunk(text='{"title":"truncado"')
                    yield ModelChunk(text="", done=True)
                    return
            yield ModelChunk(text=json.dumps(staged_part_from_request(request), ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = CapturingProvider()
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate("unidade.txt", SOURCE.encode())
    assert result["questions"] == 10
    assert provider.route_b_calls == 2
    assert len(provider.requests) == 19  # 5 etapas + 1 retry + 2 auditorias normais + 10 auditorias por pergunta + 1 adversarial final
    assert all(req.response_format == "json" for req in provider.requests)
    assert all(req.max_output_tokens == 8192 for req in provider.requests)
    assert all(req.context_window == 65536 for req in provider.requests)


@pytest.mark.asyncio
async def test_factory_route_json_failure_recovers_with_question_fallback(tmp_path):
    class BrokenRouteProvider(StagedProvider):
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            import re
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "ETAPA DE ROTA C" in prompt and "FALLBACK DE ROBUSTEZ" not in prompt:
                yield ModelChunk(text='{"broken":')
            elif "FALLBACK DE ROBUSTEZ — ROTA C" in prompt:
                idx = int(re.search(r"PERGUNTA C(\d)", prompt).group(1))
                yield ModelChunk(text=json.dumps(self.payload["route_c"]["questions"][idx - 1], ensure_ascii=False))
            else:
                yield ModelChunk(text=json.dumps(staged_part_from_request(request), ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = BrokenRouteProvider()
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["stage"] == "gdd_ready"
    assert len([r for r in provider.requests if "FALLBACK DE ROBUSTEZ — ROTA C" in r.messages[-1].content]) == 3


from campanario.renpy_factory.project import FactoryWorkspaceSettings, RenPyProjectManager


def _write_run(run_dir: Path, gdd: RenPyGDD):
    game = run_dir / "project" / "game"
    game.mkdir(parents=True)
    template = Path("src/campanario/renpy_factory/template/game")
    import shutil
    shutil.copytree(template, game, dirs_exist_ok=True)
    (run_dir / "gdd.json").write_text(gdd.model_dump_json(indent=2), encoding="utf-8")
    (run_dir / "GDD.md").write_text("stub", encoding="utf-8")
    (run_dir / "visual_prompts.txt").write_text("stub", encoding="utf-8")
    (game / "script.rpy").write_text(compile_script(gdd), encoding="utf-8")
    (game / "options.rpy").write_text("stub", encoding="utf-8")


def test_subject_accepts_variable_unit_count_and_reuses_first_art_bible(tmp_path):
    workspace = tmp_path / "workspace"
    manager = RenPyProjectManager(tmp_path / "state")
    state = manager.create_subject("Minha Materia", FactoryWorkspaceSettings(workspace_path=str(workspace), sdk_path=str(tmp_path / "sdk")))
    first = RenPyGDD.model_validate(valid_payload())
    run1 = tmp_path / "run1"; _write_run(run1, first)
    u1 = manager.register_unit(state.subject_id, run1, first, "un01.txt")
    second_payload = valid_payload()
    second_payload["title"] = "Unidade Dois"
    second_payload["character"]["name"] = "Outro Personagem"
    second_payload["scenario"]["name"] = "Outro Cenario"
    second = RenPyGDD.model_validate(second_payload)
    run2 = tmp_path / "run2"; _write_run(run2, second)
    u2 = manager.register_unit(state.subject_id, run2, second, "un02.txt")
    loaded = manager.load(state.subject_id)
    assert [u["code"] for u in loaded.units] == ["UN01", "UN02"]
    assert Path(u1["project_path"]).exists() and Path(u2["project_path"]).exists()
    rewritten = RenPyGDD.model_validate_json((run2 / "gdd.json").read_text(encoding="utf-8"))
    assert rewritten.character.name == first.character.name
    assert rewritten.scenario.name == first.scenario.name
    assert rewritten.title == "Unidade Dois"


def test_subject_generation_backs_up_existing_editable_unit(tmp_path):
    workspace = tmp_path / "workspace"
    manager = RenPyProjectManager(tmp_path / "state")
    state = manager.create_subject("Materia", FactoryWorkspaceSettings(workspace_path=str(workspace)))
    gdd = RenPyGDD.model_validate(valid_payload())
    run = tmp_path / "run"; _write_run(run, gdd)
    unit_path = workspace / "Materia" / "UN01"
    unit_path.mkdir(parents=True)
    (unit_path / "arte_manual.txt").write_text("preservar", encoding="utf-8")
    manager.register_unit(state.subject_id, run, gdd, "u.txt")
    backups = list((workspace / "Materia").glob("UN01_backup_*"))
    assert len(backups) == 1
    assert (backups[0] / "arte_manual.txt").read_text(encoding="utf-8") == "preservar"


def test_ui_factory_pauses_images_multiunit_and_web_until_core_is_approved():
    html = Path("src/campanario/web/index.html").read_text(encoding="utf-8")
    assert "Imagens, matéria multiunidade e build Web ficam pausados" in html
    assert "1. Produzir e auditar o GDD" in html
    assert "2. Revisar e compilar" in html


def test_evidence_matching_ignores_only_editorial_punctuation():
    ebook = "O kernel — núcleo do sistema — gerencia processos, memória e dispositivos."
    assert evidence_quote_present("O kernel, núcleo do sistema, gerencia processos memória e dispositivos", ebook)
    assert not evidence_quote_present("O kernel controla diretamente todos os programas do sistema", ebook)


@pytest.mark.asyncio
async def test_factory_retries_stage_when_json_is_valid_but_evidence_is_not_verbatim(tmp_path):
    class EvidenceRepairProvider:
        def __init__(self):
            self.requests = []
            self.main_calls = 0
        async def health(self):
            return True
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            part = staged_part_from_request(request)
            if "ETAPA 2/5" in request.messages[-1].content:
                self.main_calls += 1
                if self.main_calls == 1:
                    part = json.loads(json.dumps(part, ensure_ascii=False))
                    part["choices"][0]["evidence"]["source_hint"] = "ev_9999"
            yield ModelChunk(text=json.dumps(part, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = EvidenceRepairProvider()
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate("unidade.txt", SOURCE.encode())
    assert result["evidence_checked"] == 21
    assert provider.main_calls == 2
    retry_prompt = [r.messages[-1].content for r in provider.requests if "ETAPA 2/5" in r.messages[-1].content][-1]
    assert "selecione apenas um evidence.source_hint ev_XXXX" in retry_prompt


def test_evidence_catalog_is_source_first_and_verbatim():
    from campanario.renpy_factory.evidence import build_evidence_catalog
    ebook = extract_ebook("unidade.txt", SOURCE.encode())
    catalog = build_evidence_catalog(ebook)
    assert len(catalog) >= 10
    assert catalog[0].evidence_id == "ev_0001"
    assert catalog[0].quote == QUOTES[0]
    assert all(item.quote in SOURCE for item in catalog)


@pytest.mark.asyncio
async def test_factory_hydrates_quote_from_selected_evidence_id(tmp_path):
    class PlaceholderProvider(StagedProvider):
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            part = json.loads(json.dumps(staged_part_from_request(request), ensure_ascii=False))
            def replace(node):
                if isinstance(node, dict):
                    if isinstance(node.get("evidence"), dict):
                        node["evidence"]["quote"] = "USE_SOURCE_HINT"
                    for value in node.values():
                        replace(value)
                elif isinstance(node, list):
                    for value in node:
                        replace(value)
            replace(part)
            yield ModelChunk(text=json.dumps(part, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    service = RenPyFactoryService(PlaceholderProvider(), "fake", tmp_path)
    result = await service.generate("unidade.txt", SOURCE.encode())
    gdd = RenPyGDD.model_validate(result["gdd"])
    assert gdd.main_question.choices[0].evidence.quote == QUOTES[0]
    assert gdd.main_question.choices[0].evidence.source_hint.startswith("ev_0001 |")


@pytest.mark.asyncio
async def test_failure_diagnostic_does_not_persist_upload_or_model_response(tmp_path):
    class BrokenProvider:
        async def health(self):
            return True
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            yield ModelChunk(text='{"broken":')
            yield ModelChunk(text="", done=True)

    service = RenPyFactoryService(BrokenProvider(), "fake", tmp_path)
    with pytest.raises(Exception):
        await service.generate("SEGREDO_EBOOK.txt", SOURCE.encode())
    failure_files = list((tmp_path / "failed").rglob("*"))
    assert failure_files
    combined = "\n".join(p.read_text(encoding="utf-8") for p in failure_files if p.is_file())
    assert "SEGREDO_EBOOK" not in combined
    assert SOURCE not in combined
    assert not any(p.name.startswith("model_response") for p in failure_files)


def test_compiler_uses_narrative_intro_from_approved_gdd():
    gdd = RenPyGDD.model_validate(valid_payload())
    script = compile_script(gdd)
    assert 'p "Olá! Sou a Dra. Helena e vou acompanhar esta simulação."' in script
    assert 'p "Instrutora de infraestrutura."' not in script
    assert 'p "Deseja realizar uma nova simulação?"' in script
    assert script.count('nar "') >= 5


@pytest.mark.asyncio
async def test_quality_audit_repairs_only_rejected_stage(tmp_path):
    class QualityRepairProvider(StagedProvider):
        def __init__(self):
            super().__init__()
            self.audit_calls = 0
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "AUDITORIA PEDAGÓGICA FINAL" in prompt:
                self.audit_calls += 1
                payload = (
                    {"passed": False, "issues": [{"path": "main_question.choices[1]", "message": "alternativa adequada contradiz a evidência"}]}
                    if self.audit_calls == 1 else {"passed": True, "issues": []}
                )
            else:
                payload = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(payload, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = QualityRepairProvider()
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    prompts = [request.messages[-1].content for request in provider.requests]
    assert result["quality_audit"] == "approved"
    assert provider.audit_calls == 2
    assert sum("REVISÃO OBRIGATÓRIA APÓS AUDITORIA" in prompt for prompt in prompts) == 1
    assert any("ETAPA 2/5" in prompt and "REVISÃO OBRIGATÓRIA" in prompt for prompt in prompts)

@pytest.mark.asyncio
async def test_factory_retries_stage_when_scores_are_structurally_invalid(tmp_path):
    class BadScoresProvider(StagedProvider):
        def __init__(self):
            super().__init__()
            self.main_calls = 0
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            payload = json.loads(json.dumps(staged_part_from_request(request, self.payload), ensure_ascii=False))
            if "ETAPA 2/5" in request.messages[-1].content:
                self.main_calls += 1
                if self.main_calls == 1:
                    payload["choices"][0]["score"] = 2
            yield ModelChunk(text=json.dumps(payload, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = BadScoresProvider()
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["stage"] == "gdd_ready"
    assert provider.main_calls == 2


@pytest.mark.asyncio
async def test_factory_repairs_cross_route_duplicate_before_rejecting_gdd(tmp_path):
    class DuplicateRepairProvider(StagedProvider):
        def __init__(self):
            super().__init__()
            self.route_b_calls = 0
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            payload = json.loads(json.dumps(staged_part_from_request(request, self.payload), ensure_ascii=False))
            prompt = request.messages[-1].content
            if "ETAPA DE ROTA B" in prompt:
                self.route_b_calls += 1
                if self.route_b_calls == 1:
                    payload["questions"][0]["prompt"] = self.payload["route_a"]["questions"][0]["prompt"]
            yield ModelChunk(text=json.dumps(payload, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = DuplicateRepairProvider()
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["stage"] == "gdd_ready"
    assert provider.route_b_calls == 1
    assert any("PERGUNTA B1" in r.messages[-1].content and "auto-reparo granular" in r.messages[-1].content for r in provider.requests)


def test_grounding_validation_error_reports_real_reason_not_generic_evidence_message():
    ebook = extract_ebook("unidade.txt", SOURCE.encode())
    payload = valid_payload()
    payload["route_b"]["questions"][0]["prompt"] = payload["route_a"]["questions"][0]["prompt"]
    report = validate_gdd(RenPyGDD.model_validate(payload), ebook.normalized_text)
    error = GroundingValidationError(report)
    assert "Pergunta duplicada" in str(error)
    assert "conteúdo sem evidência literal" not in str(error)

@pytest.mark.asyncio
async def test_rejected_quality_gdd_is_preserved_for_review_and_compile_is_blocked(tmp_path):
    class AlwaysRejectAuditProvider(StagedProvider):
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "AUDITORIA PEDAGÓGICA FINAL" in prompt:
                payload = {"passed": False, "issues": [{"path": "route_b.questions[0]", "message": "feedback genérico"}]}
            else:
                payload = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(payload, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    service = RenPyFactoryService(AlwaysRejectAuditProvider(), "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["approved"] is False
    assert result["stage"] == "gdd_rejected"
    assert result["issues"]
    run_dir = Path(result["run_dir"])
    assert (run_dir / "GDD.docx").exists()
    assert (run_dir / "GDD.md").exists()
    assert (run_dir / "AUDIT_REPORT.md").exists()
    assert "NÃO CONCLUÍDO AUTOMATICAMENTE" in (run_dir / "AUDIT_REPORT.md").read_text(encoding="utf-8")
    with pytest.raises(Exception, match="autocorreção"):
        service.compile_run(result["run_id"])


def test_factory_ui_exposes_repair_history_and_technical_diagnostics():
    html = Path("src/campanario/web/renpy_factory.html").read_text(encoding="utf-8")
    assert "AUDIT_REPORT.md" in html
    assert "Histórico de autocorreção" in html
    assert "Corrigido e aprovado" in html
    assert "falha técnica" in html
    assert "repair_history" in html

@pytest.mark.asyncio
async def test_route_block_invalid_json_falls_back_to_one_question_at_a_time(tmp_path):
    class RouteFallbackProvider(StagedProvider):
        def __init__(self):
            super().__init__()
            self.route_b_block_calls = 0
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "ETAPA DE ROTA B" in prompt and "FALLBACK DE ROBUSTEZ" not in prompt:
                self.route_b_block_calls += 1
                yield ModelChunk(text='{"title":"quebrado","questions":[')
                yield ModelChunk(text="", done=True)
                return
            if "FALLBACK DE ROBUSTEZ — ROTA B" in prompt:
                import re
                idx = int(re.search(r"PERGUNTA B(\d)", prompt).group(1))
                payload = self.payload["route_b"]["questions"][idx - 1]
            else:
                payload = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(payload, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = RouteFallbackProvider()
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["stage"] == "gdd_ready"
    assert provider.route_b_block_calls == 2
    fallback_prompts = [r.messages[-1].content for r in provider.requests if "FALLBACK DE ROBUSTEZ — ROTA B" in r.messages[-1].content]
    assert len(fallback_prompts) == 3


@pytest.mark.asyncio
async def test_route_fallback_failure_preserves_partial_gdd_for_review(tmp_path):
    class PartialProvider(StagedProvider):
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "ETAPA DE ROTA B" in prompt and "FALLBACK DE ROBUSTEZ" not in prompt:
                yield ModelChunk(text='{"broken":')
                yield ModelChunk(text="", done=True)
                return
            if "FALLBACK DE ROBUSTEZ — ROTA B, PERGUNTA B2" in prompt:
                yield ModelChunk(text='{"broken":')
                yield ModelChunk(text="", done=True)
                return
            if "FALLBACK DE ROBUSTEZ — ROTA B, PERGUNTA B1" in prompt:
                payload = self.payload["route_b"]["questions"][0]
            else:
                payload = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(payload, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    service = RenPyFactoryService(PartialProvider(), "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["stage"] == "technical_incomplete"
    assert result["approved"] is False
    run_dir = Path(result["run_dir"])
    assert (run_dir / "PARTIAL_GDD.md").exists()
    text = (run_dir / "PARTIAL_GDD.md").read_text(encoding="utf-8")
    assert "TRILHA A" in text
    assert "TRILHA B — INCOMPLETA" in text
    assert "B1" in text
    assert "B2" not in text
    assert not any(p.suffix.lower() in {".docx", ".pdf"} for p in run_dir.iterdir())


def test_factory_ui_supports_incomplete_gdd_preview_without_rejected_language():
    html = Path("src/campanario/web/renpy_factory.html").read_text(encoding="utf-8")
    assert "technical_incomplete" in html
    assert "falha técnica" in html
    assert "gdd_md_url" in html
    assert "O GDD da unidade selecionada aparecerá aqui assim que houver conteúdo recuperável." in html

@pytest.mark.asyncio
async def test_duplicate_route_titles_are_auto_repaired_and_do_not_block(tmp_path):
    payload = valid_payload()
    payload["route_a"]["title"] = "Lógica e Argumentação Jurídica"
    payload["route_b"]["title"] = "Lógica e Argumentação Jurídica"
    payload["route_c"]["title"] = "Lógica e Argumentação Jurídica"
    service = RenPyFactoryService(StagedProvider(payload), "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["approved"] is True
    gdd = RenPyGDD.model_validate(result["gdd"])
    assert len({gdd.route_a.title, gdd.route_b.title, gdd.route_c.title}) == 3
    assert gdd.route_a.title.endswith("Eixo A")
    assert gdd.route_b.title.endswith("Eixo B")
    assert gdd.route_c.title.endswith("Eixo C")


def test_validator_flags_repeated_explicit_concept_in_later_route():
    ebook = extract_ebook("unidade.txt", SOURCE.encode())
    payload = valid_payload()
    payload["route_a"]["questions"][2]["prompt"] = "Qual a importância da 'falibilidade' para revisar um raciocínio?"
    payload["route_b"]["questions"][2]["prompt"] = "Como a 'falibilidade' influencia a revisão de uma conclusão?"
    report = validate_gdd(RenPyGDD.model_validate(payload), ebook.normalized_text)
    assert not report.valid
    assert any(issue.path.startswith("route_b.questions[3]") and "Conceito repetido" in issue.message for issue in report.issues)

@pytest.mark.asyncio
async def test_duplicate_concept_is_repaired_at_single_question_level_with_forbidden_concepts(tmp_path):
    payload = valid_payload()
    payload["route_b"]["questions"][2]["prompt"] = "Qual a importância da 'falibilidade' para revisar uma conclusão?"
    payload["route_c"]["questions"][2]["prompt"] = "Como a 'falibilidade' influencia a revisão do raciocínio?"

    class SurgicalRepairProvider(StagedProvider):
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "CONCEITOS CENTRAIS JÁ AVALIADOS" in prompt and "PERGUNTA C3" in prompt:
                repaired = json.loads(json.dumps(self.payload["route_c"]["questions"][2], ensure_ascii=False))
                repaired["prompt"] = "Qual a importância das 'permissões' para proteger recursos do sistema?"
                repaired["choices"] = [
                    choice("Permissões limitam acessos e ajudam a proteger recursos.", 2, QUOTES[9]),
                    choice("Permissões existem apenas para acelerar tarefas administrativas.", 0, QUOTES[9]),
                ]
                payload_out = repaired
            else:
                payload_out = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(payload_out, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = SurgicalRepairProvider(payload)
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["approved"] is True
    gdd = RenPyGDD.model_validate(result["gdd"])
    assert "permissões" in gdd.route_c.questions[2].prompt
    assert "falibilidade" not in gdd.route_c.questions[2].prompt.casefold()
    repair_prompts = [r.messages[-1].content for r in provider.requests if "CONCEITOS CENTRAIS JÁ AVALIADOS" in r.messages[-1].content]
    assert repair_prompts
    assert "falibilidade" in repair_prompts[-1].casefold()
    # The surgical repair must not regenerate the whole C route.
    assert sum("ETAPA DE ROTA C" in r.messages[-1].content for r in provider.requests) == 1


@pytest.mark.asyncio
async def test_granular_repair_retries_same_question_until_validator_accepts(tmp_path):
    payload = valid_payload()
    payload["route_b"]["questions"][2]["prompt"] = "Qual a importância da 'falibilidade' para revisar uma conclusão?"
    payload["route_c"]["questions"][2]["prompt"] = "Como a 'falibilidade' influencia a revisão do raciocínio?"

    class TwoStepSurgicalProvider(StagedProvider):
        def __init__(self, payload):
            super().__init__(payload)
            self.c3_repairs = 0

        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "PERGUNTA C3" in prompt and "auto-reparo granular" in prompt:
                self.c3_repairs += 1
                repaired = json.loads(json.dumps(self.payload["route_c"]["questions"][2], ensure_ascii=False))
                if self.c3_repairs == 1:
                    # First repair is still wrong. The service must detect this by
                    # revalidating and retry C3 only.
                    repaired["prompt"] = "Por que a 'falibilidade' exige abertura para revisão?"
                else:
                    repaired["prompt"] = "Como a 'circularidade' compromete a sustentação de um argumento?"
                    repaired["choices"] = [
                        choice("A circularidade usa a própria conclusão como suporte e não acrescenta fundamento independente.", 2, QUOTES[8]),
                        choice("A circularidade fortalece o argumento ao repetir a conclusão várias vezes.", 0, QUOTES[8]),
                    ]
                payload_out = repaired
            else:
                payload_out = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(payload_out, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = TwoStepSurgicalProvider(payload)
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["approved"] is True
    gdd = RenPyGDD.model_validate(result["gdd"])
    assert "circularidade" in gdd.route_c.questions[2].prompt.casefold()
    assert provider.c3_repairs == 2
    # Only the exact C3 question was surgically retried; route C was generated once.
    assert sum("ETAPA DE ROTA C" in r.messages[-1].content for r in provider.requests) == 1



@pytest.mark.asyncio
async def test_self_heal_can_retry_same_question_beyond_three_attempts(tmp_path):
    payload = valid_payload()
    payload["route_b"]["questions"][2]["prompt"] = "Qual a importância da 'falibilidade' para revisar uma conclusão?"
    payload["route_c"]["questions"][2]["prompt"] = "Como a 'falibilidade' influencia a revisão do raciocínio?"

    class PersistentRepairProvider(StagedProvider):
        def __init__(self, payload):
            super().__init__(payload)
            self.c3_repairs = 0

        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "PERGUNTA C3" in prompt and "auto-reparo granular" in prompt:
                self.c3_repairs += 1
                repaired = json.loads(json.dumps(self.payload["route_c"]["questions"][2], ensure_ascii=False))
                if self.c3_repairs < 5:
                    repaired["prompt"] = "Por que a 'falibilidade' exige abertura para revisão?"
                else:
                    repaired["prompt"] = "Como a 'circularidade' compromete a sustentação de um argumento?"
                    repaired["choices"] = [
                        choice("A circularidade usa a própria conclusão como suporte e não acrescenta fundamento independente.", 2, QUOTES[8]),
                        choice("A circularidade fortalece o argumento ao repetir a conclusão várias vezes.", 0, QUOTES[8]),
                    ]
                out = repaired
            else:
                out = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(out, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = PersistentRepairProvider(payload)
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["approved"] is True
    assert provider.c3_repairs == 5
    assert any(e["status"] == "fixed" and "questions[3]" in e["scope"] for e in result["repair_history"])



@pytest.mark.asyncio
async def test_surgical_json_repair_uses_convergent_retry_budget(tmp_path):
    payload = valid_payload()
    payload["route_b"]["questions"][2]["prompt"] = "Qual a importância da 'falibilidade' para revisar uma conclusão?"
    payload["route_c"]["questions"][2]["prompt"] = "Como a 'falibilidade' influencia a revisão do raciocínio?"

    class SurgicalJsonRecoveryProvider(StagedProvider):
        def __init__(self, payload):
            super().__init__(payload)
            self.surgical_calls = 0

        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "PERGUNTA C3" in prompt and "auto-reparo granular" in prompt:
                self.surgical_calls += 1
                if self.surgical_calls < 5:
                    yield ModelChunk(text='{"broken":')
                    yield ModelChunk(text="", done=True)
                    return
                out = json.loads(json.dumps(self.payload["route_c"]["questions"][2], ensure_ascii=False))
                out["prompt"] = "Como a 'circularidade' compromete a sustentação de um argumento?"
                out["choices"] = [
                    choice("A circularidade usa a própria conclusão como suporte e não acrescenta fundamento independente.", 2, QUOTES[8]),
                    choice("A circularidade fortalece o argumento ao repetir a conclusão várias vezes.", 0, QUOTES[8]),
                ]
            else:
                out = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(out, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = SurgicalJsonRecoveryProvider(payload)
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["approved"] is True
    assert provider.surgical_calls == 5
    assert any(
        e["status"] == "fixed" and "surgical_repair" in e["scope"]
        for e in result["repair_history"]
    )

@pytest.mark.asyncio
async def test_stage_fallback_retries_question_beyond_two_attempts_and_reports_recovery(tmp_path):
    class RecoveringFallbackProvider(StagedProvider):
        def __init__(self):
            super().__init__()
            self.b1_calls = 0

        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "ETAPA DE ROTA B" in prompt and "FALLBACK DE ROBUSTEZ" not in prompt:
                yield ModelChunk(text='{"broken":')
                yield ModelChunk(text="", done=True)
                return
            if "FALLBACK DE ROBUSTEZ — ROTA B, PERGUNTA B1" in prompt:
                self.b1_calls += 1
                if self.b1_calls < 5:
                    yield ModelChunk(text='{"broken":')
                    yield ModelChunk(text="", done=True)
                    return
                out = self.payload["route_b"]["questions"][0]
            elif "FALLBACK DE ROBUSTEZ — ROTA B" in prompt:
                import re
                idx = int(re.search(r"PERGUNTA B(\d)", prompt).group(1))
                out = self.payload["route_b"]["questions"][idx - 1]
            else:
                out = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(out, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = RecoveringFallbackProvider()
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["approved"] is True
    assert provider.b1_calls == 5
    assert any(e["scope"] == "route_b_q1" and e["status"] == "fixed" for e in result["repair_history"])

def test_validator_flags_incorrect_intro_scoring_claim():
    ebook = extract_ebook("unidade.txt", SOURCE.encode())
    payload = valid_payload()
    payload["intro_lines"][2] = "Cada resposta correta vale +3 pontos durante toda a simulação."
    report = validate_gdd(RenPyGDD.model_validate(payload), ebook.normalized_text)
    assert any(
        issue.path == "intro_lines" and "pontuação de forma incorreta" in issue.message
        for issue in report.issues
    )


@pytest.mark.asyncio
async def test_choice_consistency_audit_repairs_only_b2(tmp_path):
    payload = valid_payload()
    bad = payload["route_b"]["questions"][1]
    bad["choices"][0]["text"] = "A análise deve ser descartada quando faltam informações."
    bad["choices"][0]["justification"] = "A incompletude não invalida a análise; ela exige cautela e indicação das lacunas."
    bad["choices"][0]["feedback"] = "A análise continua útil, desde que seus limites sejam reconhecidos."

    class ConsistencyRepairProvider(StagedProvider):
        def __init__(self, payload):
            super().__init__(payload)
            self.consistency_calls = 0
            self.b2_repairs = 0

        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "AUDITORIA PEDAGÓGICA FINAL" in prompt:
                out = {"passed": True, "issues": []}
            elif "AUDITORIA FOCADA DE CONSISTÊNCIA DAS ALTERNATIVAS" in prompt:
                self.consistency_calls += 1
                out = (
                    {"passed": False, "issues": [{
                        "path": "route_b.questions[2].choices[1]",
                        "message": "A alternativa +2 contradiz sua justificativa e feedback.",
                    }]}
                    if self.consistency_calls == 1
                    else {"passed": True, "issues": []}
                )
            elif "PERGUNTA B2" in prompt and "auto-reparo granular de qualidade" in prompt:
                self.b2_repairs += 1
                out = json.loads(json.dumps(self.payload["route_b"]["questions"][1], ensure_ascii=False))
                out["choices"][0]["text"] = "A análise deve reconhecer as lacunas e permanecer aberta a informações relevantes adicionais."
                out["choices"][0]["justification"] = "A incompletude limita o alcance da conclusão, mas não invalida automaticamente a análise."
                out["choices"][0]["feedback"] = "Reconhecer as lacunas permite delimitar a conclusão e buscar dados relevantes sem descartar toda a análise."
            else:
                out = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(out, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = ConsistencyRepairProvider(payload)
    service = RenPyFactoryService(provider, "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())

    assert result["quality_audit"] == "approved"
    assert provider.b2_repairs == 1
    assert provider.consistency_calls == 2
    repair_prompts = [r.messages[-1].content for r in provider.requests if "auto-reparo granular de qualidade" in r.messages[-1].content]
    assert len(repair_prompts) == 1
    assert "PERGUNTA B2" in repair_prompts[0]


def test_compiler_preflight_accepts_canonical_minimal_project():
    from campanario.renpy_factory.compiler import compile_script, render_options, validate_compiled_project
    gdd = RenPyGDD.model_validate(valid_payload())
    script = compile_script(gdd)
    screens = Path("src/campanario/renpy_factory/template/game/screens.rpy").read_text(encoding="utf-8-sig")
    options = render_options(gdd.title)
    assert validate_compiled_project(gdd, script, screens, options) == []


def test_compiler_preflight_rejects_script_divergence():
    from campanario.renpy_factory.compiler import compile_script, render_options, validate_compiled_project
    gdd = RenPyGDD.model_validate(valid_payload())
    script = compile_script(gdd).replace("label route_C:", "label route_X:")
    screens = Path("src/campanario/renpy_factory/template/game/screens.rpy").read_text(encoding="utf-8-sig")
    issues = validate_compiled_project(gdd, script, screens, render_options(gdd.title))
    assert any("diverge" in item for item in issues)
    assert any("route_C" in item for item in issues)


@pytest.mark.asyncio
async def test_gdd_result_exposes_structured_audit_for_ui(tmp_path):
    service = RenPyFactoryService(StagedProvider(), "fake", tmp_path)
    result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    assert result["approved"] is True
    assert "audit_items" in result
    assert "audit_counts" in result
    assert result["auto_repair"]["question_attempts"] == 8
    assert result["auto_repair"]["global_cycles"] == 12
    assert "repair_history" in result


@pytest.mark.asyncio
async def test_compile_run_writes_compatibility_report(tmp_path):
    service = RenPyFactoryService(StagedProvider(), "fake", tmp_path)
    gdd_result = await service.generate_gdd("unidade.txt", SOURCE.encode())
    result = service.compile_run(gdd_result["run_id"])
    assert result["compatibility"] == "passed"
    assert result["compat_report_url"].endswith("CODE_COMPAT_REPORT.md")
    report = Path(gdd_result["run_dir"]) / "CODE_COMPAT_REPORT.md"
    assert "Status: APROVADO" in report.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_adversarial_gate_catches_score_polarity_false_positive_and_repairs_b2_b3(tmp_path):
    payload = valid_payload()
    payload["route_b"]["questions"][1]["choices"][0]["text"] = "A conclusão decorre necessariamente das premissas, sem margem para interpretações alternativas."
    payload["route_b"]["questions"][1]["choices"][0]["justification"] = "A subdeterminação ocorre quando as premissas são insuficientes para escolher uma única conclusão."
    payload["route_b"]["questions"][1]["choices"][0]["feedback"] = "As informações permitem múltiplas interpretações, portanto a conclusão não é necessária."
    payload["route_b"]["questions"][2]["choices"][0]["text"] = "A revisabilidade garante conclusões imutáveis e irrevogáveis."
    payload["route_b"]["questions"][2]["choices"][0]["justification"] = "Revisabilidade significa abertura para corrigir conclusões diante de novas razões."
    payload["route_b"]["questions"][2]["choices"][0]["feedback"] = "Uma conclusão revisável pode ser alterada quando surgem novas informações."

    class AdversarialRepairProvider(StagedProvider):
        def __init__(self, payload):
            super().__init__(payload)
            self.flagged = set()
            self.repairs = []
        async def stream(self, request):
            from campanario.model.protocol import ModelChunk
            self.requests.append(request)
            prompt = request.messages[-1].content
            if "AUDITORIA PEDAGÓGICA FINAL" in prompt or "AUDITORIA FOCADA DE CONSISTÊNCIA DAS ALTERNATIVAS" in prompt:
                out = {"passed": True, "issues": []}
            elif "AUDITORIA ADVERSARIAL POR PERGUNTA" in prompt and "PATH CANÔNICO: route_b.questions[2]" in prompt and "route_b.questions[2]" not in self.flagged:
                self.flagged.add("route_b.questions[2]")
                out = {"passed": False, "issues": [{"path":"route_b.questions[2].choices[1]","message":"A alternativa +2 afirma conclusão necessária, mas justificativa/feedback dizem que há múltiplas conclusões."}]}
            elif "AUDITORIA ADVERSARIAL POR PERGUNTA" in prompt and "PATH CANÔNICO: route_b.questions[3]" in prompt and "route_b.questions[3]" not in self.flagged:
                self.flagged.add("route_b.questions[3]")
                out = {"passed": False, "issues": [{"path":"route_b.questions[3].choices[1]","message":"A alternativa +2 diz imutável, mas justificativa/feedback definem revisabilidade como abertura à mudança."}]}
            elif "AUDITORIA ADVERSARIAL POR PERGUNTA" in prompt or "AUDITORIA ADVERSARIAL FINAL" in prompt:
                out = {"passed": True, "issues": []}
            elif "PERGUNTA B2" in prompt and "auto-reparo granular de qualidade" in prompt:
                self.repairs.append("B2")
                out = json.loads(json.dumps(self.payload["route_b"]["questions"][1], ensure_ascii=False))
                out["choices"][0]["text"] = "As premissas são insuficientes para impor uma única conclusão, permitindo interpretações alternativas."
                out["choices"][0]["justification"] = "A subdeterminação ocorre quando as premissas não selecionam uma única conclusão."
                out["choices"][0]["feedback"] = "Reconhecer a insuficiência das premissas explica por que mais de uma interpretação pode ser defensável."
            elif "PERGUNTA B3" in prompt and "auto-reparo granular de qualidade" in prompt:
                self.repairs.append("B3")
                out = json.loads(json.dumps(self.payload["route_b"]["questions"][2], ensure_ascii=False))
                out["choices"][0]["text"] = "A revisabilidade mantém conclusões abertas à correção diante de novas informações ou razões relevantes."
                out["choices"][0]["justification"] = "Revisabilidade é a disposição de corrigir uma conclusão quando surgem fundamentos novos."
                out["choices"][0]["feedback"] = "Uma análise revisável pode ser ajustada sem perder rigor quando novas razões justificam a mudança."
            else:
                out = staged_part_from_request(request, self.payload)
            yield ModelChunk(text=json.dumps(out, ensure_ascii=False))
            yield ModelChunk(text="", done=True)

    provider = AdversarialRepairProvider(payload)
    result = await RenPyFactoryService(provider, "fake", tmp_path).generate_gdd("unidade.txt", SOURCE.encode())
    assert result["approved"] is True
    assert "B2" in provider.repairs and "B3" in provider.repairs
    assert any(e["scope"] == "auditoria adversarial" and e["status"] == "retry" for e in result["repair_history"])
