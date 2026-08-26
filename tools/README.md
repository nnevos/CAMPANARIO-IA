# Tools

O diretorio Windows foi limpo na F5c.1 para separar uso atual de regressao historica.

## Uso atual — `tools/windows/`

- `INICIAR_CAMPANARIO.bat` — launcher normal: runtime + API/realtime + UI. Preserva `voice-host`.
- `INICIAR_VOZ_HOST_F5C.bat` — cliente fisico de microfone/alto-falante.
- `DIAGNOSTICO_VOZ_F5C.bat` — mostra STT/TTS/audio, idioma e modelo efetivos.
- `PAREAR_VOZ_HOST_F5C.bat` — pareamento explicito do PC de voz.
- `TESTAR_VOZ_F5C.bat` — gate automatizado F5c/F5b/F5/PF9.
- `TESTAR_REALTIME_F5.bat` — regressao de presence/realtime atual.
- `TESTAR_LONG_CALL.bat` — regressao conversacional longa ainda obrigatoria.
- `INICIAR_RUNTIME_HEADLESS.bat` — somente desenvolvimento; nao possui Gateway.
- `ABRIR_MANUAL.bat`, `CONSULTAR_ULTIMO_TESTE.bat`, `TROCAR_MODELO.bat`, `COMPARAR_MODELOS.bat` — utilitarios de operacao.

Para uso normal, prefira `CAMPANARIO.bat` na raiz.

## Regressao historica

Nada foi apagado. Scripts de gates ja concluidos foram movidos para reduzir ruido:

- `windows/regression/platform/` — PF1..PF9, F3, F4 e proof mobile;
- `windows/regression/conversation/` — suites antigas de comportamento, agentes, personalidade e multiagente.

Eles continuam disponiveis para auditoria/regressao, mas nao sao launchers de uso cotidiano.

## Manutencao

- `maintenance/` — backup e utilitarios de manutencao.
