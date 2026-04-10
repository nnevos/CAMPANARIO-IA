import sys
import json
import os
import re
from collections import deque

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama

import router_rules as router
from knowledge_search import buscar_conhecimento


ARQUIVO_ESTADO = "estado_conversa.json"
MODEL = "llama3"


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def load_txt(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


llm = Ollama(model=MODEL)
embeddings = OllamaEmbeddings(model=MODEL)
db = Chroma(persist_directory="memoria", embedding_function=embeddings)

personality_data = load_json("personality.json")
behavior_examples = load_json("behavior_examples.json")
style_rules = load_txt("style_rules.txt")

memoria_curto_prazo = deque(maxlen=20)
buffer_sessao = []

estado_conversa = {
    "destinatario_atual": None,
    "assunto_atual": None,
    "modo": "conversa",
    "ultima_intencao": None,
    "nivel_pressao": "normal",
    "ultima_entidade": None,
    "rodando_com": None
}


def salvar_estado():
    with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(estado_conversa, f, ensure_ascii=False, indent=2)


def carregar_estado():
    global estado_conversa
    if os.path.exists(ARQUIVO_ESTADO):
        try:
            with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
                estado = json.load(f)
                if isinstance(estado, dict):
                    estado_conversa.update(estado)
        except Exception:
            pass


def salvar_memoria(texto, tag="GERAL"):
    db.add_texts([f"[{tag}] {texto}"])


def buscar_memoria_dinamica(pergunta, k_resultados):
    resultados = db.similarity_search(pergunta, k=k_resultados)
    base = "\n".join([r.page_content for r in resultados])

    if any(x in pergunta.lower() for x in ["sobre mim", "meus", "quem sou"]):
        extras = db.similarity_search("[USUARIO]", k=5)
        base += "\n\nFatos Pessoais:\n" + "\n".join([r.page_content for r in extras])

    return base


def atualizar_contexto(u, r):
    memoria_curto_prazo.append(f"Usuário: {u}")
    memoria_curto_prazo.append(f"IA: {r}")
    buffer_sessao.append(f"U: {u} | IA: {r}")


def formatar_exemplos(nome_agente, exemplos):
    return "\n".join([f"U: {ex['input']} -> {nome_agente}: {ex['output']}" for ex in exemplos])


def detectar_destinatario(msg):
    texto = msg.lower().strip()

    padroes_todd = [
        r"^\s*todd\b",
        r"\btodd\b.*\b(tá|ta|está|esta|aí|ai|também|tambem|vem|fala|responde)\b",
        r"\bfala\s+com\s+o\s+todd\b",
        r"\bchama\s+o\s+todd\b",
        r"\bmanda\s+pro\s+todd\b",
        r"\bfala\s+com\s+o\s+capuz\b",
        r"\bchama\s+o\s+capuz\b"
    ]

    padroes_morgana = [
        r"^\s*morgana\b",
        r"\bmorgana\b.*\b(tá|ta|está|esta|aí|ai|também|tambem|vem|fala|responde)\b",
        r"\bfala\s+com\s+a\s+morgana\b",
        r"\bchama\s+a\s+morgana\b",
        r"\bmanda\s+pra\s+morgana\b",
        r"\bfala\s+com\s+a\s+oráculo\b",
        r"\bchama\s+a\s+oráculo\b"
    ]

    for p in padroes_todd:
        if re.search(p, texto):
            return "Todd"

    for p in padroes_morgana:
        if re.search(p, texto):
            return "Morgana"

    return None


def extrair_assunto(msg):
    texto = msg.lower().strip()

    if any(x in texto for x in ["todd", "capuz", "red hood"]):
        return "Todd"
    if any(x in texto for x in ["morgana", "oráculo", "oraculo"]):
        return "Morgana"
    if any(x in texto for x in ["tempo", "clima", "chuva", "sol", "nublado", "frio", "calor"]):
        return "clima"
    if any(x in texto for x in ["memória", "lembra", "recorda"]):
        return "memória"
    if any(x in texto for x in ["estratégia", "estrategia", "plano", "risco", "decidir", "foco"]):
        return "estratégia"
    if any(x in texto for x in ["saúde", "dor", "remédio", "febre"]):
        return "saúde"
    if any(x in texto for x in ["água", "agua", "abrigo", "comida", "fogo", "sobrevivência", "sobrevivencia", "primeiros socorros", "engenharia", "comunicação", "história", "historia"]):
        return "base_conhecimento"
    return None


def atualizar_estado(msg, destinatario=None, intent=None, assunto=None):
    texto = msg.lower().strip()

    if destinatario:
        estado_conversa["destinatario_atual"] = destinatario
        estado_conversa["rodando_com"] = destinatario

    if intent:
        estado_conversa["ultima_intencao"] = intent

    if assunto:
        estado_conversa["assunto_atual"] = assunto
        estado_conversa["ultima_entidade"] = assunto

    if any(x in texto for x in ["emergência", "emergencia", "socorro", "ajuda agora", "urgente"]):
        estado_conversa["modo"] = "emergencia"
        estado_conversa["nivel_pressao"] = "critico"
    elif any(x in texto for x in ["ajuda", "preciso", "como faço", "como fazer", "não sei", "nao sei"]):
        estado_conversa["modo"] = "ajuda"
        estado_conversa["nivel_pressao"] = "normal"
    elif any(x in texto for x in ["estratégia", "estrategia", "plano", "risco", "decidir", "foco"]):
        estado_conversa["modo"] = "analise"
        estado_conversa["nivel_pressao"] = "normal"
    else:
        estado_conversa["modo"] = "conversa"
        if estado_conversa["nivel_pressao"] != "critico":
            estado_conversa["nivel_pressao"] = "normal"

    salvar_estado()


def resumir_estado():
    return f"""
Destinatário atual: {estado_conversa['destinatario_atual']}
Assunto atual: {estado_conversa['assunto_atual']}
Modo: {estado_conversa['modo']}
Última intenção: {estado_conversa['ultima_intencao']}
Nível de pressão: {estado_conversa['nivel_pressao']}
Rodando com: {estado_conversa['rodando_com']}
""".strip()


def construir_prompt(msg, nome_agente, dados_persona, exemplos_str, memoria, contexto_base, config_router):
    historico = "\n".join(memoria_curto_prazo)
    diretrizes = "\n".join([f"- {d}" for d in dados_persona.get("diretrizes", [])])

    return f"""
Você é {dados_persona.get('nome', nome_agente)}.

Personalidade:
{dados_persona.get('perfil', '')}

História:
{dados_persona.get('backstory', '')}

Tom de voz:
{dados_persona.get('tom_de_voz', '')}

Diretrizes:
{diretrizes}

Regras gerais:
{style_rules}

Estado da conversa:
{resumir_estado()}

Contexto da base offline:
{contexto_base}

Regras absolutas:
- Você é uma IA, não uma humana.
- O outro personagem também é uma IA, não um humano.
- Cada um é independente, com voz própria, mas ambos fazem parte do mesmo sistema.
- Não finja biologia, emoções humanas literais ou experiências corporais.
- Não diga que é amigo humano, namorado, irmão, pessoa ou equivalente.
- Não associe os personagens a universos externos, fantasia, realeza, mitos ou lore não solicitado.
- Se o usuário perguntar sobre o outro personagem, responda sobre ele sem assumir a identidade dele.
- Se a informação não estiver no sistema atual, responda de forma simples e direta sem inventar.

Objetivo:
- Responder de forma natural, humana no tom, mas sem fingir ser humano.
- Não soar como assistente genérico.
- Não repetir estruturas prontas.
- Variar ritmo e tamanho da resposta.
- Se fizer sentido, puxar o assunto com uma pergunta curta ou comentário.
- Se o usuário falar casualmente, responda casualmente.
- Se pedir ajuda, ajude com clareza.
- Se não pedir ajuda, apenas converse de forma orgânica.
- Não use ações entre asteriscos como *sorrir*, *olha*, *respira fundo*.
- Não use linguagem mística, teatral, épica ou de fantasia.

Exemplos de diálogo:
{exemplos_str}

Histórico recente:
{historico}

Memória antiga:
{memoria}

Mensagem do usuário:
{msg}

Resposta de {nome_agente}:
""".strip()


def precisa_base_conhecimento(msg):
    texto = msg.lower()
    chaves = [
        "sobrevivência", "sobrevivencia", "água", "agua", "abrigo", "comida",
        "fogo", "primeiros socorros", "saúde", "saude", "engenharia",
        "comunicação", "comunicacao", "história", "historia", "estratégia", "estrategia"
    ]
    return any(k in texto for k in chaves)


def executar_agente(msg, nome_agente, config_router):
    chave = nome_agente.lower()
    dados_persona = personality_data.get(chave, {})
    exemplos = behavior_examples.get(chave, [])

    exemplos_str = formatar_exemplos(nome_agente, exemplos)
    memoria = buscar_memoria_dinamica(msg, config_router.get("memoria_k", 5))

    contexto_base = ""
    if precisa_base_conhecimento(msg):
        contexto_base = buscar_conhecimento(msg, k=4)

    prompt = construir_prompt(
        msg=msg,
        nome_agente=nome_agente,
        dados_persona=dados_persona,
        exemplos_str=exemplos_str,
        memoria=memoria,
        contexto_base=contexto_base,
        config_router=config_router
    )

    resposta = llm.invoke(prompt)
    atualizar_contexto(msg, resposta)

    if config_router.get("salvar", True):
        tag = "SOBREVIVENCIA" if chave == "todd" else "USUARIO"
        salvar_memoria(f"{msg} -> {resposta}", tag)

    return resposta


def orquestrador(msg):
    intent = router.classify_intent(msg, llm)
    config = router.get_routing_logic(intent)
    return config["agente"], executar_agente(msg, config["agente"], config)


def consolidar_sessao():
    if not buffer_sessao:
        return

    conversa = "\n".join(buffer_sessao)
    resumo = llm.invoke(
        f"Resuma os pontos mais importantes desta conversa em português, de forma curta e objetiva:\n{conversa}"
    )
    db.add_texts([f"[RESUMO_SESSAO] {resumo}"])


if __name__ == "__main__":
    carregar_estado()
    print("--- SISTEMA ONLINE (Padrão: Morgana) ---")
    try:
        while True:
            msg = input("\nVocê: ").strip()
            if not msg:
                continue

            if msg.lower() in ["sair", "exit"]:
                break

            destinatario = detectar_destinatario(msg)
            assunto = extrair_assunto(msg)

            if destinatario == "Todd":
                clean_msg = re.sub(r"\btodd\b", "", msg, flags=re.IGNORECASE).strip()
                atualizar_estado(clean_msg, destinatario="Todd", intent="CHAMADA_TODD", assunto=assunto)
                resp = executar_agente(clean_msg, "Todd", {"memoria_k": 5, "salvar": True})
                print(f"\nTodd: {resp}")

            elif destinatario == "Morgana":
                clean_msg = re.sub(r"\bmorgana\b", "", msg, flags=re.IGNORECASE).strip()
                atualizar_estado(clean_msg, destinatario="Morgana", intent="CHAMADA_MORGANA", assunto=assunto)
                resp = executar_agente(clean_msg, "Morgana", {"memoria_k": 5, "salvar": True})
                print(f"\nMorgana: {resp}")

            else:
                intent = router.classify_intent(msg, llm)
                config = router.get_routing_logic(intent)
                atualizar_estado(msg, destinatario=config["agente"], intent=intent, assunto=assunto)
                resp = executar_agente(msg, config["agente"], config)
                print(f"\n{config['agente']}: {resp}")

    except KeyboardInterrupt:
        pass
    finally:
        consolidar_sessao()
        salvar_estado()
        sys.exit(0)