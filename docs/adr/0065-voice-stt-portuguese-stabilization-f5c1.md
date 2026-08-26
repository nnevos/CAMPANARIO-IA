# ADR 0065 — F5c.1 Voice STT / Portuguese stabilization checkpoint

Status: ACCEPTED (target-PC re-test pending; F5 remains open)

## Context

O primeiro E2E fisico provou microfone -> PCM -> whisper.cpp -> Conversation Runtime -> Morgana -> SAPI, mas mostrou transcricoes ruins em portugues e turnos fantasma como `[MÚSICA DE FUNDO]`. Ingles apresentou reconhecimento melhor. O codigo F5c ja passava `-l <language>` ao whisper.cpp, portanto a correcao nao deve assumir silenciosamente que o idioma nunca foi enviado.

## Decision

- manter `CAMPANARIO_VOICE_LANGUAGE=pt` explicito e torna-lo observavel no diagnostico;
- testar estruturalmente que o comando real do adapter inclui `-l pt`;
- adicionar prompt curto de dominio/pt-BR para nomes Campanario/Todd/Morgana;
- usar `--no-speech-thold` configuravel e `--no-timestamps`;
- rejeitar `ggml-*.en.bin` quando o idioma configurado nao for ingles;
- descartar somente transcricoes compostas integralmente por anotacoes de nao-fala (`[MÚSICA DE FUNDO]`, `[MUSIC]`, etc.);
- adicionar gate minimo de duracao de fala antes de chamar STT, reduzindo falsos turnos por picos de ruido;
- manter `ggml-base.bin` compativel, mas recomendar `ggml-small.bin` multilíngue caso a qualidade pt-BR continue insuficiente no host;
- nao alterar Conversation Runtime, Personality Core ou memoria.

## Tooling

`tools/windows/` passa a conter apenas operacao/F5 atual. Gates historicos foram movidos para `tools/windows/regression/{platform,conversation}` sem exclusao. `INICIAR_CAMPANARIO.bat` usa `uv sync --extra voice-host`, evitando remover `sounddevice` no boot.

## Gate

Repetir no PC alvo: uma frase em portugues deve gerar um unico `stt_final` correto; cinco segundos de silencio nao devem criar `voce:`; depois validar endereco Todd/Morgana e contexto compartilhado. F5 continua aberta ate o E2E fisico passar.
