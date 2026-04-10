from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests

API_URL = "http://127.0.0.1:8000/chat"

app = FastAPI(title="Morgana & Todd UI")


HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Morgana & Todd</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #0f1115;
      color: #e8e8e8;
      margin: 0;
      padding: 0;
    }
    .container {
      max-width: 820px;
      margin: 0 auto;
      padding: 20px;
    }
    h1 {
      font-size: 24px;
      margin-bottom: 16px;
    }
    .chat {
      background: #171a21;
      border: 1px solid #2a2f3a;
      border-radius: 12px;
      padding: 16px;
      min-height: 60vh;
      overflow-y: auto;
    }
    .msg {
      margin: 10px 0;
      line-height: 1.45;
      white-space: pre-wrap;
    }
    .user {
      color: #7dd3fc;
    }
    .bot {
      color: #c4b5fd;
    }
    .input-row {
      display: flex;
      gap: 10px;
      margin-top: 14px;
    }
    input {
      flex: 1;
      padding: 14px;
      border-radius: 10px;
      border: 1px solid #2a2f3a;
      background: #0b0d11;
      color: #fff;
      font-size: 16px;
      outline: none;
    }
    button {
      padding: 14px 18px;
      border: none;
      border-radius: 10px;
      background: #4f46e5;
      color: white;
      font-size: 15px;
      cursor: pointer;
    }
    button:hover {
      background: #4338ca;
    }
    .meta {
      font-size: 12px;
      opacity: 0.7;
      margin-bottom: 6px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Morgana & Todd</h1>
    <div id="chat" class="chat"></div>
    <div class="input-row">
      <input id="message" type="text" placeholder="Digite uma mensagem..." autocomplete="off" />
      <button onclick="sendMessage()">Enviar</button>
    </div>
  </div>

  <script>
    const chat = document.getElementById("chat");
    const input = document.getElementById("message");

    function addMessage(who, text) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + who;

  const label = who === "user" ? "User" : "Campanário IA";
  wrap.innerHTML = "<div class='meta'>" + label + "</div>" + text;

  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}

    async function sendMessage() {
      const text = input.value.trim();
      if (!text) return;

      addMessage("user", text);
      input.value = "";

      try {
        const resp = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text })
        });

        const data = await resp.json();
        addMessage("bot", "<b>" + data.agent + ":</b> " + data.response);
      } catch (err) {
        addMessage("bot", "Erro ao conectar com a API.");
      }
    }

    input.addEventListener("keydown", function(e) {
      if (e.key === "Enter") sendMessage();
    });
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(HTML_PAGE)