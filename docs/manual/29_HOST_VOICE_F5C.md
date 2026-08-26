# 29 — Voz no PC (F5c)

F5c conecta o microfone e o alto-falante do Windows à mesma Call do Campanario. Não cria outro Todd, outra Morgana, outra memória ou outro ChatService.

## Componentes escolhidos

- STT: whisper.cpp local;
- TTS: Windows SAPI local;
- áudio físico: sounddevice/PortAudio;
- transporte: `/ws/v1/call` já existente.

## Preparação

Instale o extra de áudio:

```bat
uv sync --extra voice-host
```

Coloque `whisper-cli.exe` e um modelo whisper.cpp local no PC. Configure no `.env`:

```env
CAMPANARIO_VOICE_STT_BACKEND=whisper_cpp
CAMPANARIO_VOICE_TTS_BACKEND=windows_sapi
CAMPANARIO_VOICE_WHISPER_CPP_PATH=C:\caminho\whisper-cli.exe
CAMPANARIO_VOICE_WHISPER_MODEL_PATH=C:\caminho\ggml-small.bin
CAMPANARIO_VOICE_LANGUAGE=pt
```

Opcionalmente informe vozes SAPI distintas:

```env
CAMPANARIO_VOICE_TODD_VOICE=Nome exato da voz
CAMPANARIO_VOICE_MORGANA_VOICE=Nome exato da outra voz
```

Se os nomes ficarem vazios, o SAPI usa a voz padrão e F5c aplica rates diferentes por agente. Para a aceitação final, prefira duas vozes instaladas de fato.

## Teste

Use nesta ordem:

```text
tools/windows/DIAGNOSTICO_VOZ_F5C.bat
tools/windows/PAREAR_VOZ_HOST_F5C.bat
tools/windows/INICIAR_VOZ_HOST_F5C.bat
```

O pareamento é feito uma vez. A credencial é armazenada no diretório local de dados do Campanario.

Durante a Call, fale normalmente. O cliente mostra a transcrição, o agente que respondeu e a latência entre `stt_final` e a primeira reprodução. Se você falar enquanto Todd/Morgana estiverem tocando, o host tenta cortar o áudio e envia barge-in ao runtime.

## Limite atual

F5c não inclui cancelamento acústico/echo cancellation. Headset é recomendado para o primeiro teste de barge-in. A fase só pode ser considerada `voice ready` depois do teste físico no PC alvo.

Checklist de aceite: `docs/current/F5C_HOST_ACCEPTANCE_CHECKLIST.md`.

## Recovery / checkpoint F5c.4

The physical pipeline has been proven on the Windows target, but Portuguese recognition is not yet accepted. A real phrase `Campanario, voce esta ai?` was transcribed as `O Brasil e o maior.`. If this happens, do not change Todd/Morgana or the conversation runtime: first verify the actual multilingual Whisper model and Portuguese language configuration.

If local voice assets were deleted or the PC was reformatted, restore the whisper.cpp executable/DLLs under `voice/` and a multilingual model under a supported `models/` layout, then run `tools/windows/PREPARAR_VOZ_F5C.bat` before Host Voice. Pairing credentials are machine-local and may need to be recreated; do not ship them inside recovery media.

## F5c.5 — estabilização física pt-BR

O caminho físico agora preserva um pequeno **pré-roll** antes do primeiro frame classificado como fala e, depois que a fala começa, mantém também sílabas/pausas de baixa energia até o hangover final. O VAD decide apenas as bordas da utterance; ele não remove mais frames internos antes de o Whisper receber o WAV.

Quando houver mais de um modelo multilingue no diretório externo, o F5 físico usa preferência de **qualidade**: `large-v3/large/big/medium` antes de `small/base`. Para priorizar latência em vez de acurácia, configure `CAMPANARIO_VOICE_WHISPER_PREFER_ACCURACY=false`.

Defaults do gate físico: `CAMPANARIO_VOICE_LANGUAGE=pt`, `CAMPANARIO_VOICE_PREROLL_FRAMES=6`, `CAMPANARIO_VOICE_SILENCE_FRAMES_TO_FINALIZE=45` e `CAMPANARIO_VOICE_MIN_SPEECH_MS=300`. O hangover de 45 frames (~1,8 s no frame atual) prioriza manter pausas naturais dentro do mesmo turno; nova fala confirmada substitui uma resposta ainda em voo e chunks de correlacao antiga nao voltam como TTS. Durante TTS local, PCM de microfone nao e enviado ao STT salvo quando barge-in humano e confirmado, evitando eco do alto-falante como turno do usuario. Nenhuma correção semântica é feita depois do STT; Todd/Morgana recebem exatamente a transcrição aceita pela fronteira de voz.

## Enderecamento e probes de presenca no F5c.6

O Host Voice aceita `Campanario` e `Campanário` como o mesmo wake. Perguntas curtas de presenca como `Campanário, me escuta?` e `Campanário, ta ai?` devem receber uma confirmacao curta, sem virar uma pergunta aberta sobre o que o usuario quer que seja ouvido.

Quando a fala nomeia explicitamente `Todd e Morgana`, os dois recebem a mesma fala original do usuario. A resposta de Todd nao deve ser reinterpretada por Morgana como um novo pedido, nem o inverso. Esse isolamento vale para o enderecamento explicito no Host Voice; conversas textuais multiagente continuam usando a coordenacao normal do ParticipationArbiter.

## F5c.9 — velocidade do TTS ajustável

A velocidade do Windows SAPI é configurável sem alterar conteúdo, personalidade ou roteamento. O default físico agora é mais ágil: `CAMPANARIO_VOICE_TODD_RATE=4` e `CAMPANARIO_VOICE_MORGANA_RATE=3`, numa escala SAPI de `-10` (muito lenta) a `+10` (muito rápida).

No Windows, execute `tools\windows\AJUSTAR_VELOCIDADE_VOZ.bat` para escolher um preset de **Calma**, **Natural**, **Rápida**, **Muito rápida** ou **Turbo**. O script persiste os valores no ambiente do usuário para as próximas execuções do Campanario. Feche qualquer runtime já aberto e inicie novamente para aplicar.

Para ajuste fino manual, defina `CAMPANARIO_VOICE_TODD_RATE` e `CAMPANARIO_VOICE_MORGANA_RATE` diretamente entre `-10` e `+10`.

## F5c.10 — fragmentos, fala contínua e interrupção natural

- Frases completas continuam sendo despachadas normalmente.
- Fragmentos com forte sinal de continuação ficam pendentes por até ~1,2 s.
- Se você continuar falando, o Campanario junta o PCM original e executa Whisper novamente sobre a fala consolidada; ele não cola textos STT possivelmente errados.
- Enquanto Todd/Morgana falam, você pode interromper: barge-in confirmado corta o áudio e cancela o turno antigo antes de sua nova fala ganhar prioridade.
- Ajustes opcionais: `CAMPANARIO_VOICE_FRAGMENT_HOLD_MS`, `CAMPANARIO_VOICE_BARGE_IN_THRESHOLD`, `CAMPANARIO_VOICE_BARGE_IN_FRAMES`, `CAMPANARIO_VOICE_BARGE_IN_PREROLL_FRAMES`.
- O modo de voz pede respostas mais curtas e conversacionais; isso é apenas entrega do canal, não treinamento nem mudança de Personality Core.
