# Manual do Campanario

Este diretorio contem apenas a documentacao operacional atual. Historico de versoes antigas fica em `docs/history/`.

## Uso diario

| Quero... | Abra |
|---|---|
| preparar pela primeira vez | `01_PRIMEIROS_PASSOS.md` |
| iniciar/encerrar | `02_INICIAR_E_ENCERRAR.md` |
| usar o chat | `03_USAR_O_CHAT.md` |
| rodar testes | `04_TESTES_COMPORTAMENTAIS.md` |
| ler relatorios | `05_RELATORIOS_DE_TESTE.md` |
| configurar/trocar modelo | `06_CONFIGURACOES.md` |
| entender memoria/contexto | `07_MEMORIA_E_CONTEXTO.md` |
| backup/recuperacao | `08_BACKUP_E_RECUPERACAO.md` |
| resolver falhas | `09_SOLUCAO_DE_PROBLEMAS.md` |
| entender arquitetura | `10_ARQUITETURA_PARA_USUARIO.md` |
| ver funcoes ativas/planejadas | `11_FUNCOES_DO_SISTEMA.md` |
| usar Todd/Morgana | `12_AGENTES.md` |
| entender navegador vs desktop | `13_INTERFACE_WEB_E_DESKTOP.md` |
| testar convivencia Todd/Morgana | `14_TESTE_MULTIAGENTE.md` |
| confirmar build/UI e diagnosticar launcher | `15_LAUNCHER_UI_E_BUILD.md` |
| testar personalidade/evolucao dos agentes | `16_PERSONALIDADE_E_EVOLUCAO_DOS_AGENTES.md` |
| entender eventos internos do runtime | `17_EVENTOS_DO_RUNTIME.md` |
| entender API v1 e eventos realtime | `18_REALTIME_API_GATEWAY.md` |
| entender dispositivos e capabilities anunciadas | `19_DEVICE_REGISTRY.md` |
| entender capabilities/tools e providers | `20_CAPABILITY_TOOL_REGISTRY.md` |

## Menu principal

No Windows, execute `CAMPANARIO.bat` na raiz. Ele substitui a antiga colecao de launchers espalhados.

Os scripts individuais continuam disponiveis em `tools/windows/` para diagnostico ou automacao.

- `21_PERMISSION_TRUST_LAYER.md` — pairing, trust, permissoes, confirmacao, revogacao e audit.

- `22_CLIENT_INDEPENDENT_SESSIONS.md` — como clientes diferentes compartilham a mesma sessao/contexto.

- `23_MOBILE_READINESS.md` — cliente mobile minimo, pairing, mesma sessao e location.current de teste.

- `24_VOICE_CALL_READINESS.md` — contratos de Call, wake/STT semantico, TTS directive e interruption signal-only.

25. `25_RUNTIME_TELEMETRY.md` — milestones de latencia/provenance do Runtime v2 e endpoint diagnostico.

26. `26_EXPERIENCE_LEARNING.md` — memoria experiencial, curiosidade proporcional, correcao e esquecimento.

- `30_CONVERSA_HUMANA_BASELINE.md` — bateria de conversa humana cotidiana, comparação cega Todd × Morgana e sala compartilhada.

27. `27_REALTIME_PRESENCE_F5.md` — Presence Realtime F5.
28. `28_VOICE_MEDIA_F5B.md` — mídia de voz F5b.
29. `29_HOST_VOICE_F5C.md` — Host Voice F5c.
