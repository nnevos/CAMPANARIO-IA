# F5c — Host Acceptance / Voice Ready Gate

Execute no PC Windows alvo. F5 só pode ser congelada quando todos os itens obrigatórios passarem.

## Preparação

- [ ] `uv sync --extra voice-host` concluído;
- [ ] `CAMPANARIO_VOICE_STT_BACKEND=whisper_cpp`;
- [ ] `CAMPANARIO_VOICE_TTS_BACKEND=windows_sapi`;
- [ ] `whisper-cli.exe` encontrado;
- [ ] modelo whisper.cpp encontrado;
- [ ] `DIAGNOSTICO_VOZ_F5C.bat` mostra STT/TTS/audio prontos;
- [ ] Campanario iniciado com o modelo conversacional normal.

## Aceitação obrigatória

- [ ] `PAREAR_VOZ_HOST_F5C.bat` conclui e a credencial é persistida;
- [ ] `INICIAR_VOZ_HOST_F5C.bat` abre uma Call sem criar outra sessão/persona;
- [ ] fala no microfone aparece como `stt_final` com conteúdo correto;
- [ ] Morgana responde audivelmente;
- [ ] Todd responde audivelmente quando diretamente chamado;
- [ ] Todd e Morgana são distinguíveis por voz configurada ou, no mínimo, por rate no baseline;
- [ ] falar durante TTS interrompe imediatamente a reprodução local;
- [ ] o runtime recebe `interrupt` e não continua tocando chunks antigos;
- [ ] uma nova fala após barge-in continua na mesma conversa;
- [ ] memória/contexto textual existente continuam disponíveis na Call;
- [ ] fechar e reabrir o host voice não cria outro Todd/Morgana ou banco de memória;
- [ ] latência `stt_final -> primeira reprodução` é registrada em pelo menos 10 turnos.

## Métricas para enviar de volta

Copie 10 valores impressos como:

```text
[latencia] stt_final -> primeira reproducao: 1234 ms
```

E anote:

- headset ou caixas de som;
- microfone usado;
- modelo whisper.cpp;
- nomes das vozes SAPI de Todd/Morgana;
- se houve falso barge-in por eco;
- qualquer transcrição errada perceptível.

## Gate

Se os itens físicos passarem, registrar ADR de freeze F5 Voice Ready. Se houver falso barge-in/latência ruim/transcrição insuficiente, corrigir dentro de F5 antes de F6.

## F5c.1 — estabilizacao de portugues

Antes do novo teste:

- [ ] diagnostico mostra `whisper.cpp language=pt`;
- [ ] diagnostico mostra modelo multilíngue (nao `*.en.bin`);
- [ ] launcher normal nao remove mais `sounddevice` (`uv sync --extra voice-host`);
- [ ] falar `Campanario, voces estao me ouvindo?` produz um unico `stt_final` coerente;
- [ ] ficar 5 segundos em silencio nao produz `[MÚSICA DE FUNDO]`/turno fantasma;
- [ ] se `ggml-base.bin` continuar fraco em pt-BR, testar `ggml-small.bin` multilíngue antes de mexer no runtime cognitivo.
