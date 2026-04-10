def classify_intent(msg, llm=None):
    texto = msg.lower().strip()

    if any(x in texto for x in ["todd", "capuz", "red hood"]):
        if any(x in texto for x in ["tá", "ta", "está", "esta", "aí", "ai", "vem", "fala", "responde", "chama", "manda"]):
            return "CHAMADA_TODD"

    if any(x in texto for x in ["morgana", "oráculo", "oraculo"]):
        if any(x in texto for x in ["tá", "ta", "está", "esta", "aí", "ai", "vem", "fala", "responde", "chama", "manda"]):
            return "CHAMADA_MORGANA"

    if any(x in texto for x in ["tempo", "clima", "chuva", "sol", "nublado", "frio", "calor"]):
        return "CLIMA"

    if any(x in texto for x in ["como você", "como vai", "bom dia", "boa tarde", "boa noite", "oi", "olá", "ola"]):
        return "SAUDACAO"

    if any(x in texto for x in ["preciso", "me ajuda", "ajuda", "me explica", "como faço", "como fazer", "não sei", "nao sei", "duvida", "dúvida"]):
        return "AJUDA"

    if any(x in texto for x in ["estratégia", "estrategia", "plano", "risco", "foco", "organizar", "problema", "erro"]):
        return "ANALISE"

    if any(x in texto for x in ["tive", "aconteceu", "acontecendo", "hoje foi", "meu dia", "correria", "trabalho"]):
        return "CONVERSA"

    return "GERAL"


def get_routing_logic(intent):
    if intent == "CHAMADA_TODD":
        return {"agente": "Todd", "memoria_k": 5, "salvar": True}

    if intent == "CHAMADA_MORGANA":
        return {"agente": "Morgana", "memoria_k": 5, "salvar": True}

    if intent == "CLIMA":
        return {"agente": "Morgana", "memoria_k": 3, "salvar": False}

    if intent == "SAUDACAO":
        return {"agente": "Morgana", "memoria_k": 3, "salvar": False}

    if intent == "AJUDA":
        return {"agente": "Morgana", "memoria_k": 5, "salvar": True}

    if intent == "ANALISE":
        return {"agente": "Todd", "memoria_k": 5, "salvar": True}

    if intent == "CONVERSA":
        return {"agente": "Morgana", "memoria_k": 5, "salvar": True}

    return {"agente": "Morgana", "memoria_k": 5, "salvar": True}