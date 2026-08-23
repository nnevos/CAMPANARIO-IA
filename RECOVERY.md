# RECOVERY — Campanario

Estado atual:
- Fase 1 oficialmente concluída.
- Chat local, streaming, persistência e hardening básico validados no Windows real.
- Suíte de hardening: 8 testes.
- Ollama provisório: `llama3:latest`.
- Próximo trabalho: Fase 2 — Context Manager.

Ao retomar:
1. leia `PROJECT_STATE.md`;
2. inspecione `docs/ARCHITECTURE.md`, `docs/ROADMAP.md` e ADRs;
3. compare documentação com o código;
4. não reabra Fase 1 sem bug real;
5. implemente apenas Context Manager;
6. não antecipar memória, RAG, voz, personas ou agentes;
7. atualizar o handoff ao fim do incremento.
