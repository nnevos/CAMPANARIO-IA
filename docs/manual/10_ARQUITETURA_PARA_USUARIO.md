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
