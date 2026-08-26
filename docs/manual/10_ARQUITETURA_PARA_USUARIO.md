# 10 - Arquitetura para usuario

```text
Interface/API
  -> conversa/contexto/pragmatica
  -> behavior context
  -> response contract pipeline
  -> provider de modelo
  -> Ollama/modelo local
  -> resposta
```

Separacoes importantes:

- entender o usuario != imitar o usuario;
- persona != factualidade;
- naturalidade != fingir ser humano;
- modelo != Campanario;
- Campanario != agentes;
- agentes futuros compartilham memoria/capacidades do sistema.

Gemma 3 12B e apenas o motor recomendado atual; Qwen/Llama/outros podem ser trocados sem reconstruir o sistema.


## Runtime v2 — PF1 concluido

A partir do freeze F2, o Campanario possui um runtime independente da interface Web. PF1a separou o boundary logico; PF1b adicionou lifecycle explicito e um `RuntimeHost` que mantem um unico runtime ativo por processo. FastAPI e um host/adaptador, nao o dono da conversa.

Existe tambem um host headless de desenvolvimento (`uv run campanario-runtime`) para provar que o runtime pode permanecer ativo sem navegador/FastAPI. Ele ainda nao e um Windows service nem um servidor remoto. Ate o Realtime Gateway existir, nao execute host Web e headless esperando compartilhamento entre processos.


## Runtime v2 — PF2 Event Bus

O runtime agora possui um barramento interno de eventos. Conversa, selecao de speaker e respostas produzem eventos versionados com ordem e provenance. Isso ainda nao e WebSocket nem acesso remoto: e a fundacao interna que o futuro gateway realtime consumira. O replay atual e process-local/em memoria e nao substitui a persistencia SQLite das conversas.
