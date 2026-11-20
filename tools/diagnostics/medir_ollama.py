"""Mede tempo de carregamento/primeiro texto/geracao no Ollama local.

Nao usa Campanario, memoria, prompts longos nem servicos remotos. Pode ajudar a
separar gargalo de GPU/Ollama de gargalo da orquestracao Campanario.
"""
from __future__ import annotations

import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def medir(modelo: str, pergunta: str) -> None:
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": pergunta}],
        "think": False,
        "stream": True,
        "keep_alive": "20m",
        "options": {"num_predict": 160, "num_ctx": 4096, "temperature": 0.55},
    }
    t0 = time.perf_counter()
    first = None
    parts = []
    result = {}
    try:
        request = Request("http://127.0.0.1:11434/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=180) as response:
            for line in response:
                if not line.strip():
                    continue
                event = json.loads(line)
                chunk = (event.get("message") or {}).get("content") or ""
                if chunk:
                    if first is None:
                        first = time.perf_counter()
                    parts.append(chunk)
                if event.get("done"):
                    result = event
                    break
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Erro ao chamar o Ollama local: {exc}")
        return
    elapsed = time.perf_counter() - t0
    print(f"\nModelo: {modelo}")
    print(f"Primeiro texto: {first - t0:.2f}s" if first else "Primeiro texto: nenhum")
    print(f"Tempo total: {elapsed:.2f}s")
    print(f"Tokens prompt: {result.get('prompt_eval_count', 'n/d')}")
    print(f"Tokens resposta: {result.get('eval_count', 'n/d')}")
    for field, label in (("load_duration", "Carregamento"), ("prompt_eval_duration", "Prompt"),
                         ("eval_duration", "Geracao")):
        if isinstance(result.get(field), int):
            print(f"{label} (reportado pelo Ollama): {result[field] / 1e9:.2f}s")
    print("Resposta:", "".join(parts)[:400] or "<vazia>")


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen3.5:9b"
    print("CAMPANARIO / diagnostico local (think=false, modelo aquecido entre testes)")
    medir(model, "Oi!")
    medir(model, "Que filme voce sugere pra uma noite tranquila? Responda em uma frase.")
