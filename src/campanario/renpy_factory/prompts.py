from __future__ import annotations

from .evidence import build_evidence_catalog, render_evidence_catalog
from .models import ExtractedEbook


SYSTEM_PROMPT = """Você é o compilador pedagógico da Fábrica Ren'Py do Campanário.
Sua única fonte factual é o EBOOK/CATÁLOGO DE EVIDÊNCIAS fornecido nesta requisição.
REGRA ABSOLUTA: não use conhecimento externo, memória, senso comum ou fatos não presentes na fonte fornecida.
A narrativa pode ser fictícia, mas qualquer afirmação pedagógica em pergunta, alternativa, justificativa ou feedback deve ser sustentada pelo evidence_id escolhido.
NUNCA invente evidence.quote. Para perguntas/rotas, escolha SOMENTE um evidence.source_hint no formato ev_XXXX presente no CATÁLOGO; use "USE_SOURCE_HINT" em evidence.quote. O Campanário substituirá deterministicamente pelo trecho literal.
Alternativas inadequadas podem ser falsas, mas devem ser uma distorção direta do conceito coberto pela evidência escolhida; não introduza entidades, leis, números, produtos, comandos ou fatos externos.
Não use as palavras 'Correto', 'Certo', 'Errado', 'Incorreto' nem emojis como rótulos mecânicos nos feedbacks. Faça feedback pedagógico natural, específico e explicativo.
QUALIDADE PEDAGÓGICA OBRIGATÓRIA:
- a alternativa de maior pontuação deve afirmar corretamente o conceito sustentado pela evidência escolhida;
- a alternativa parcialmente adequada deve conter um elemento verdadeiro, mas ser incompleta, limitada ou insuficiente — nunca pode ser apenas outra alternativa errada;
- a alternativa inadequada deve ser uma distorção direta e verificável do mesmo conceito;
- alternativa, justificativa e feedback nunca podem se contradizer;
- perguntas devem avaliar compreensão/aplicação, evitando enunciados vazios como 'de acordo com o texto' quando não agregarem contexto;
- feedback deve explicar a relação conceitual, não apenas julgar a escolha;
- não invente competência que o jogo não mede.
Retorne APENAS JSON válido, sem markdown. justification e feedback podem ter até 36 palavras quando necessário para manter precisão.
"""


def _source(ebook: ExtractedEbook) -> str:
    return "\n\n".join(f"[{s.source_id}]\n{s.text}" for s in ebook.segments)


def _structural_profile(ebook: ExtractedEbook) -> str:
    return f"""PERFIL ESTRUTURAL CONGELADO: legacy_un01_10x21
- Visual novel educativa Ren'Py.
- 1 pergunta principal com 3 alternativas e scores +3, +1, 0.
- A escolha principal abre rota A, B ou C.
- Cada rota possui exatamente 3 perguntas adicionais.
- Cada pergunta adicional possui exatamente 2 alternativas: +2 e 0.
- Total: 10 perguntas / 21 alternativas.
- Finais: 0-4 Iniciante; 5-8 Proficiente; 9+ Mestre.
- Um único personagem instrutor fictício e um único cenário-base.
- O personagem/cenário devem ser coerentes com o domínio do e-book, sem afirmar como reais organizações, pessoas ou acontecimentos fictícios.

Título sugerido extraído: {ebook.title_hint}
"""


def _base(ebook: ExtractedEbook) -> str:
    return _structural_profile(ebook) + f"""

EBOOK — ÚNICA FONTE FACTUAL:
{_source(ebook)}
"""


def _grounded_base(ebook: ExtractedEbook) -> str:
    catalog = build_evidence_catalog(ebook)
    return _structural_profile(ebook) + f"""

CATÁLOGO DE EVIDÊNCIAS — ÚNICA FONTE PEDAGÓGICA PARA ESTA ETAPA:
{render_evidence_catalog(catalog)}

REGRA DE EVIDÊNCIA:
- escolha somente IDs ev_XXXX existentes acima;
- em evidence.source_hint coloque exatamente esse ID;
- em evidence.quote coloque exatamente "USE_SOURCE_HINT";
- não escreva nem parafraseie a citação por conta própria;
- pergunta, alternativa, justificativa e feedback devem ser sustentáveis pelo trecho apontado.
"""


def build_metadata_prompt(ebook: ExtractedEbook) -> str:
    return _base(ebook) + """

ETAPA 1/5 — METADADOS NARRATIVOS.
Retorne somente este objeto JSON:
{
  "title":"...",
  "theme":"...",
  "educational_objective":"...",
  "character":{"name":"...","role":"...","personality":"...","appearance":"...","speech_style":"...","narrative_goal":"..."},
  "scenario":{"name":"...","pedagogical_function":"...","visual_description":"...","sound_description":"..."},
  "central_theme":"...",
  "narrative_conflict":"...",
  "finals":{"beginner":"...","proficient":"...","master":"..."},
  "final_message":"...",
  "intro_lines":["...","...","...","...","..."],
  "character_intro_lines":["...","...","..."],
  "replay_prompt":"..."
}
REQUISITOS DE PRODUÇÃO:
- o personagem deve ser FICTÍCIO; não use o nome do autor, professor ou pessoa identificada no e-book como personagem;
- cenário e personagem podem ser ficcionais, mas devem servir ao conteúdo da unidade;
- intro_lines deve ter 5 ou 6 falas de narrador: contexto do simulador, objetivo, regra de decisões/pontuação, critério de análise e classificação final; evite frases promocionais genéricas como 'jornada fascinante';
- character_intro_lines deve ter 2 ou 3 falas naturais: apresentação, situação concreta no cenário e convite para a primeira decisão; não recite cargo/objetivo como campos de formulário;
- finais descrevem apenas o desempenho demonstrado NO JOGO. Não afirme que o estudante domina, configura, automatiza ou executa habilidades que as perguntas não mediram;
- replay_prompt deve combinar com o contexto narrativo (ex.: nova análise, nova simulação), sem inventar fato pedagógico.
Nesta etapa não gere perguntas nem alternativas.
"""


def build_main_question_prompt(ebook: ExtractedEbook) -> str:
    return _grounded_base(ebook) + """

ETAPA 2/5 — PERGUNTA PRINCIPAL.
Escolha um conceito central sustentado pelo catálogo e retorne somente:
{
  "prompt":"...",
  "choices":[
    {"text":"...","score":3,"justification":"...","feedback":"...","evidence":{"quote":"USE_SOURCE_HINT","source_hint":"ev_XXXX"}},
    {"text":"...","score":1,"justification":"...","feedback":"...","evidence":{"quote":"USE_SOURCE_HINT","source_hint":"ev_XXXX"}},
    {"text":"...","score":0,"justification":"...","feedback":"...","evidence":{"quote":"USE_SOURCE_HINT","source_hint":"ev_XXXX"}}
  ]
}
As três alternativas devem tratar o MESMO conceito e ser semanticamente distintas. A opção +3 deve ser diretamente sustentada pela evidência; a +1 deve ser genuinamente parcial; a 0 deve ser incompatível. Antes de responder, confira se nenhuma justificativa desmente a própria alternativa.
"""


def build_route_prompt(ebook: ExtractedEbook, route_code: str, excluded_prompts: list[str]) -> str:
    route_code = route_code.upper()
    excluded = "\n".join(f"- {item}" for item in excluded_prompts) or "- nenhuma"
    return _grounded_base(ebook) + f"""

ETAPA DE ROTA {route_code} — gere exatamente 3 perguntas adicionais.
NÃO repita nem parafraseie de perto estas perguntas já usadas:
{excluded}

Retorne somente:
{{
  "title":"título curto da trilha",
  "questions":[
    {{"prompt":"...","choices":[
      {{"text":"...","score":2,"justification":"...","feedback":"...","evidence":{{"quote":"USE_SOURCE_HINT","source_hint":"ev_XXXX"}}}},
      {{"text":"...","score":0,"justification":"...","feedback":"...","evidence":{{"quote":"USE_SOURCE_HINT","source_hint":"ev_XXXX"}}}}
    ]}},
    QUESTION,
    QUESTION
  ]
}}
Cada QUESTION deve ter exatamente 2 choices, na ordem score 2 e score 0. A opção +2 deve refletir diretamente a evidência escolhida e a opção 0 deve distorcer o mesmo conceito sem introduzir fatos externos.
As três perguntas devem formar uma trilha coerente, não três perguntas aleatórias. Use conceitos diferentes entre si e dos já listados; evite repetir virtualização, kernel ou qualquer tópico já usado em outra rota salvo se a nova pergunta avaliar um aspecto claramente diferente.
NÃO repita como conceito central uma expressão técnica já perguntada anteriormente (por exemplo, se uma pergunta já avaliou "falibilidade" ou "circularidade", outra rota deve escolher outro conceito do e-book). O título desta trilha também deve representar seu próprio eixo temático, não repetir literalmente o título das outras trilhas.
"""


def build_route_question_prompt(ebook: ExtractedEbook, route_code: str, question_index: int, excluded_prompts: list[str], forbidden_concepts: list[str] | None = None) -> str:
    route_code = route_code.upper()
    excluded = "\n".join(f"- {item}" for item in excluded_prompts) or "- nenhuma"
    forbidden = "\n".join(f"- {item}" for item in (forbidden_concepts or [])) or "- nenhum"
    return _grounded_base(ebook) + f"""

FALLBACK DE ROBUSTEZ — ROTA {route_code}, PERGUNTA {route_code}{question_index} — REPARO CIRÚRGICO.
A rota completa não pôde ser validada como JSON. Gere SOMENTE UMA pergunta desta rota.
NÃO repita nem parafraseie de perto estas perguntas já usadas:
{excluded}

CONCEITOS CENTRAIS JÁ AVALIADOS — PROIBIDO reutilizá-los nesta pergunta:
{forbidden}

Escolha um conceito diferente, sustentado por outro trecho adequado do catálogo. Não troque apenas a redação: o objeto pedagógico avaliado precisa ser diferente.

Retorne SOMENTE este objeto JSON:
{{
  "prompt":"...",
  "choices":[
    {{"text":"...","score":2,"justification":"...","feedback":"...","evidence":{{"quote":"USE_SOURCE_HINT","source_hint":"ev_XXXX"}}}},
    {{"text":"...","score":0,"justification":"...","feedback":"...","evidence":{{"quote":"USE_SOURCE_HINT","source_hint":"ev_XXXX"}}}}
  ]
}}
A opção +2 deve refletir diretamente a evidência escolhida. A opção 0 deve distorcer o mesmo conceito sem introduzir fatos externos.
A pergunta deve contribuir para uma progressão coerente da rota {route_code}.
"""


# Compatibilidade com callers antigos/testes externos. O fluxo novo não usa geração monolítica.
def build_generation_prompt(ebook: ExtractedEbook) -> str:
    return _grounded_base(ebook) + "\nGere o GDD completo conforme o contrato legado 10x21."


def build_quality_audit_prompt(ebook: ExtractedEbook, gdd_json: str) -> str:
    return _grounded_base(ebook) + f"""

AUDITORIA PEDAGÓGICA FINAL — NÃO GERE UM NOVO GDD.
Analise o GDD candidato abaixo contra o catálogo e contra as próprias regras do GDD.

GDD CANDIDATO:
{gdd_json}

Reprove se houver QUALQUER um destes problemas:
1. alternativa de maior pontuação contradiz sua evidência, justificativa ou feedback;
2. alternativa +1 da principal é totalmente errada em vez de parcialmente adequada;
3. alternativa inadequada depende de fato externo em vez de distorcer o conceito da evidência;
4. feedback usa rótulo mecânico (Correto/Certo/Errado/Incorreto), emoji de julgamento ou não explica o conceito;
5. perguntas são duplicadas, quase duplicadas ou concentram excessivamente o jogo em poucos tópicos apesar de o e-book possuir eixos distintos;
6. trilha não possui coerência interna ou não oferece progressão/remediação coerente após a escolha principal;
7. personagem usa nome de autor/pessoa real identificada no material em vez de personagem fictício;
8. introdução parece propaganda genérica, formulário ou não explica a dinâmica do simulador;
9. final atribui ao estudante domínio/habilidade que as perguntas não mediram;
10. qualquer afirmação pedagógica não pode ser sustentada pela evidência selecionada.

Retorne SOMENTE:
{{"passed":true,"issues":[]}}
ou, se reprovado:
{{"passed":false,"issues":[{{"path":"main_question.choices[1]","message":"descrição objetiva do problema"}}]}}
Seja rigoroso. Não aprove apenas porque o JSON está válido.
"""



def build_choice_consistency_audit_prompt(ebook: ExtractedEbook, gdd_json: str) -> str:
    return _grounded_base(ebook) + f"""

AUDITORIA FOCADA DE CONSISTÊNCIA DAS ALTERNATIVAS — NÃO GERE UM NOVO GDD.
Analise SOMENTE as perguntas/alternativas do GDD candidato abaixo. Ignore estilo narrativo, títulos e cenário.

GDD CANDIDATO:
{gdd_json}

Para CADA alternativa, faça mentalmente estes checks antes de responder:
1. O texto da alternativa combina com o score?
   - score 3/2: deve estar correto e sustentado pela evidência.
   - score 1: deve ser parcialmente adequado, com parte verdadeira e limitação real.
   - score 0: deve ser incompatível/distorcido em relação à evidência.
2. A JUSTIFICATIVA sustenta a própria alternativa ou a contradiz?
3. O FEEDBACK explica a mesma avaliação implícita pelo score ou revela que a alternativa recebeu o score errado?
4. A evidência selecionada sustenta a avaliação atribuída?

EXEMPLO DE ERRO QUE DEVE SER REPROVADO:
- alternativa +2: "a análise deve ser descartada"
- justificativa/feedback: "a incompletude NÃO invalida a análise"
Isto é uma contradição interna e deve apontar para a pergunta/choice exata.

Retorne SOMENTE:
{{"passed":true,"issues":[]}}
ou
{{"passed":false,"issues":[{{"path":"route_b.questions[2].choices[1]","message":"A alternativa +2 contradiz a própria justificativa/feedback; o score e/ou texto devem ser corrigidos."}}]}}
Use paths exatos no formato main_question.choices[N] ou route_x.questions[N].choices[N].
Se uma pergunta contém qualquer alternativa internamente incoerente, reprove.
"""


def build_question_adversarial_audit_prompt(question_path: str, question_json: str) -> str:
    return f"""
AUDITORIA ADVERSARIAL POR PERGUNTA — TENTE PROVAR QUE ESTA PERGUNTA ESTÁ ERRADA.
Não gere conteúdo novo. Analise somente a pergunta abaixo e seja especialmente desconfiado de inversão de score.

PATH CANÔNICO: {question_path}
PERGUNTA:
{question_json}

Para CADA alternativa, confronte literalmente:
- texto da alternativa;
- score;
- justificativa;
- feedback;
- evidence.quote já injetada pelo Campanário.

REGRAS:
- score 3/2 só pode aparecer em uma afirmação sustentada pela evidência;
- score 1 deve ser parcialmente adequada, nunca o oposto da justificativa;
- score 0 deve ser incompatível com a evidência;
- se justificativa ou feedback explicam o OPOSTO do texto da alternativa, isso é erro grave de polaridade;
- não aceite uma alternativa positiva apenas porque sua justificativa está correta: o TEXTO da alternativa também precisa estar correto;
- procure negações invertidas, imutável vs revisável, suficiente vs insuficiente, única conclusão vs múltiplas conclusões, válida vs inválida, descartar vs manter com ressalvas e equivalentes semânticos.

Retorne SOMENTE:
{{"passed":true,"issues":[]}}
ou
{{"passed":false,"issues":[{{"path":"{question_path}.choices[1]","message":"A alternativa pontuada contradiz justificativa/feedback/evidência; há inversão de polaridade."}}]}}
Use sempre o PATH CANÔNICO fornecido, com choices em índice 1-based.
"""


def build_final_adversarial_audit_prompt(ebook: ExtractedEbook, gdd_json: str) -> str:
    return _grounded_base(ebook) + f"""

AUDITORIA ADVERSARIAL FINAL — TENTE PROVAR QUE ESTE GDD NÃO DEVE SER APROVADO.
Você é a última barreira antes da compilação Ren'Py. Não gere um novo GDD. Procure defeitos concretos que auditorias anteriores possam ter deixado passar.

GDD CANDIDATO:
{gdd_json}

Procure especificamente:
1. alternativa pontuada positivamente cujo texto diga o oposto da justificativa, feedback ou evidência;
2. score 0 que na verdade descreva corretamente a evidência;
3. +1 principal totalmente correta ou totalmente errada em vez de parcial;
4. conceitos repetidos com redação diferente;
5. feedback mecânico com Correto/Certo/Errado/Incorreto ou emoji;
6. títulos-placeholder como apenas 'Trilha B', 'Trilha C', 'Eixo A' sem descrição temática;
7. introdução explicando pontuação incorretamente;
8. finais que alegam domínio completo/excepcional ou habilidades não medidas;
9. afirmações pedagógicas não sustentadas pela evidência escolhida;
10. qualquer contradição interna que torne uma resposta marcada como adequada pedagogicamente inadequada.

Não invente problemas. Aponte apenas defeitos verificáveis no próprio GDD/evidência. Use paths exatos e 1-based para questions/choices.
Retorne SOMENTE:
{{"passed":true,"issues":[]}}
ou
{{"passed":false,"issues":[{{"path":"route_b.questions[2].choices[1]","message":"descrição objetiva e verificável do defeito"}}]}}
"""

def append_quality_feedback(prompt: str, issues: list[str]) -> str:
    feedback = "\n".join(f"- {item}" for item in issues)
    return prompt + f"""

REVISÃO OBRIGATÓRIA APÓS AUDITORIA:
A versão anterior foi reprovada pelos seguintes motivos:
{feedback}
Corrija esses problemas nesta etapa sem alterar a estrutura, sem introduzir conhecimento externo e mantendo evidence.source_hint válido.
"""
