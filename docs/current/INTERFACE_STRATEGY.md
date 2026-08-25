# Interface Strategy — Browser-first, desktop-ready

## Decisao atual

A interface principal permanece **browser-first** sobre a API FastAPI local. Isso e suficiente para chat, agentes, configuracoes, memoria, RAG, biblioteca, relatorios, modelos, dashboards e grande parte das tools futuras.

A interface web nao e tratada como descartavel: ela deve ser o frontend reutilizavel por uma futura shell desktop.

## O que funciona muito bem no navegador

- chat e historico;
- selecao/visualizacao de agentes;
- configuracao de modelos;
- memoria e biblioteca/RAG;
- upload/organizacao de arquivos;
- dashboards, logs e testes;
- microfone/gravacao enquanto a pagina esta ativa;
- streaming de texto/voz;
- controls de tools executadas pelo backend local.

## Onde navegador puro fica limitado

- wake word sempre ativo com pagina fechada/minimizada;
- hotkey global;
- tray icon e startup nativo;
- captura de audio confiavel em background;
- notificacoes/overlays de sistema mais profundos;
- automacao de desktop que depende de privilegios/processos do SO.

## Direcao recomendada

Manter:

```text
FastAPI/Core do Campanario
        ^
        | HTTP/WebSocket/SSE
        v
Frontend web
```

E, quando voz/wake/tools de desktop justificarem, envolver o mesmo frontend em uma shell leve (preferencialmente Tauri ou tecnologia equivalente):

```text
Desktop Shell
  -> web UI reutilizada
  -> servico Campanario local
  -> wake/hotkeys/tray/audio nativos
```

Isso evita reescrever o sistema. O backend e os agentes permanecem os mesmos; muda apenas o host da interface.
