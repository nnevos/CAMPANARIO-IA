# F5c.1 — Revisao de tools Windows

Objetivo: reduzir ruido operacional sem apagar evidencia/regressoes historicas.

## Mantidos em `tools/windows/`

| Tool | Motivo |
|---|---|
| `INICIAR_CAMPANARIO.bat` | launcher principal runtime + gateway + UI; agora preserva `voice-host` |
| `INICIAR_VOZ_HOST_F5C.bat` | cliente fisico de voz atual |
| `DIAGNOSTICO_VOZ_F5C.bat` | diagnostico STT/TTS/audio atual |
| `PAREAR_VOZ_HOST_F5C.bat` | trust/pairing explicito do host |
| `TESTAR_VOZ_F5C.bat` | gate automatizado F5c/F5b/F5/PF9 |
| `TESTAR_REALTIME_F5.bat` | presence/realtime atual |
| `TESTAR_LONG_CALL.bat` | regressao conversacional longa ainda obrigatoria |
| `INICIAR_RUNTIME_HEADLESS.bat` | ferramenta de desenvolvimento da fronteira runtime, nao uso de voz |
| `ABRIR_MANUAL.bat` | operacao |
| `CONSULTAR_ULTIMO_TESTE.bat` | operacao |
| `TROCAR_MODELO.bat` | operacao |
| `COMPARAR_MODELOS.bat` | avaliacao de provider/modelo |

## Movidos, nao removidos

### `tools/windows/regression/platform/`
PF1..PF9, F3, F4 e cliente mobile de prova. Esses gates ja foram concluidos; continuam disponiveis para regressao/auditoria.

### `tools/windows/regression/conversation/`
Suites antigas de comportamento, agentes, personalidade e conversa multiagente. Continuam importantes como regressao, mas nao precisam poluir a pasta operacional atual.

## Decisao

Nao apagar scripts de gate antigo enquanto F5 nao estiver congelada. Depois do freeze/Production Readiness pode haver uma segunda revisao para consolidar suites redundantes em um unico runner de regressao.
