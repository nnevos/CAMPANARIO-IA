# 11 - Funcoes do sistema

| Funcao | Estado | Uso |
|---|---|---|
| Chat local | ATIVO | `CAMPANARIO.bat` -> Iniciar |
| Interface web | ATIVO | `http://127.0.0.1:8000/` |
| Persistencia de sessoes/mensagens | ATIVO | automatica |
| Context Manager | ATIVO | automatico |
| Pragmatica de entrada | ATIVO / foundation validada | automatico + E2E |
| Response Contract Pipeline | ATIVO | automatico + E2E |
| Proveniencia creative->factual | ATIVO | automatico + E2E |
| Prompt leak guard | ATIVO | automatico |
| Self-awareness | ATIVO | automatico |
| Standard/Mega E2E | ATIVO | menu `CAMPANARIO.bat` |
| E2E de agentes | ATIVO | menu `CAMPANARIO.bat` |
| E2E de personalidade rapido/mega | ATIVO | mesmo prompt Todd/Morgana + multiplos seeds |
| Model bakeoff | ATIVO | menu `CAMPANARIO.bat` |
| Gemma 3 12B recomendado | ATIVO | configuracao, nao acoplamento |
| Morgana/Todd | ATIVO / baseline F2 congelada | participantes persistentes; Morgana fala primeiro por padrao |
| Runtime v2 PF1 | ATIVO | runtime client-independent + lifecycle/hosting process-local |
| Event Bus PF2 | ATIVO | contratos 1.0, ordem, provenance e replay process-local |
| Realtime/API Gateway PF3 | ATIVO LOCAL | `/api/v1` + `/ws/v1/events`; Web UI migrada; legado mantido |
| Device Registry PF4 | ATIVO LOCAL | devices persistentes + capabilities + `/ws/v1/devices`; trust/autorizacao ficam no PF6 |
| Experience/Learning Layer | PLANEJADO APOS PLATFORM FOUNDATION | nao disponivel |
| Memoria cognitiva | PLANEJADO | nao disponivel |
| RAG/livros | PLANEJADO | nao disponivel |
| Web/grounding | PLANEJADO | nao disponivel |
| Tools/computador | PLANEJADO | nao disponivel |
| Voz | PLANEJADO | nao disponivel |


## Platform Foundation atual

- Device Registry | ATIVO / PF4
- Capability / Tool Registry provider-independent | ATIVO / PF5
- Permission / Trust Layer | ATIVO / PF6
- Client-independent sessions | ATIVO / PF7
- Mobile Readiness | ATIVO / PF8
- Voice / Call Readiness (contratos) | PROXIMO GATE / PF9

PF8 prova um cliente mobile minimo autenticado sobre a mesma sessao/contexto, com reconnect e `location.current` de teste. `client_id`, `device_id` e `agent_id` continuam separados; nao existe app Android/iOS final nem exposicao LAN/WAN.

### PF9 — Voice / Call Readiness | ATIVO / contratos
Call semantica reutiliza a mesma sessao e Conversation Runtime. Wake/STT/TTS finais ainda nao sao funcionalidades de producao. Consulte `24_VOICE_CALL_READINESS.md`.

## Experience / Learning — ATIVO / F4

Memoria experiencial compartilhada, curiosidade proporcional, provenance/confidence/recency, correcao, esquecimento e continuidade entre reinicios estao ativos no ADR 0061. Personality Core continua congelada e separada.
