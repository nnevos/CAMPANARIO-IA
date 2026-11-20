# Arquitetura v0.8 - Base desktop e companion

## Limites da refatoracao

Campanario permanece como sistema. Morgana e Todd compartilham o runtime, contexto, memoria autorizada e ferramentas. A mudanca nao substitui o nucleo conversacional nem reinicia o banco pessoal.

```
Windows: atalho -> host pywebview -> API loopback -> runtime -> Ollama / SQLite
                                   |
                                   +-> listener HTTPS opcional -> API companion
                                                                  |
Android: host Java -> UI embarcada -> estado criptografado <-> sincronizacao
```

O telefone nao recebe acesso SQL, pasta do PC ou API administrativa. O servidor mobile e uma aplicacao FastAPI separada com superficie reduzida. O chat mobile passa pelo mesmo servico de conversa, sem reimplementar agentes.

## Modulos

- `app/desktop.py`: janela, servidor de propriedade do processo, splash, log e encerramento.
- `app/schema.py`: compara revisoes Alembic e faz backup antes de migrar.
- `app/security.py`: API administrativa restrita a loopback, Host e Origin locais.
- `app/status.py`: disponibilidade separada de processo, SQLite, modelo, voz e GPS. A presenca do modelo em `/api/tags` nao comprova a qualidade da inferencia.
- `app/remote.py`: listener TLS desligado por padrao, sem endpoints administrativos.
- `companion/store.py`: dispositivos, codigos/credenciais com hash, pacotes, notas, operacoes idempotentes e sessoes de cada aparelho.
- `companion/api.py`: pareamento, leitura do pacote, notas e chat expressamente autorizado.
- `web/static/`: separa shell, conversa, areas de trabalho, memoria e configuracoes antes embutidas no HTML.
- `apps/mobile/www`: UI e logica portable, sempre embarcadas no APK.
- `apps/mobile/android`: host Java, WebViewAssetLoader e armazenamento AES-GCM pelo Android Keystore.
- `modules/contracts.py`: interfaces futuras. TTS, STT e GPS novos estao **nao implementados**. Nao se reutiliza automaticamente o SAPI/Whisper antigo.

## Semantica da sincronizacao

Notas possuem `id`, `mutation_id`, `base_revision` e marca de exclusao. Cada mutacao e transacional e reutilizar uma identidade com outro conteudo e recusado. Uma edicao concorrente gera conflito; preservar ambas as versoes tem prioridade sobre conveniencia.

A publicacao de pacote e unilateral PC -> dispositivo e expressamente selecionada. Nao e sincronizacao bidirecional arbitraria da memoria. As notas do telefone sao visiveis no PC, mas nao sao aprendidas automaticamente pelos agentes. Revogar o aparelho impede novo acesso; nao destroi copias offline ja entregues.

Envios de chat usam identidade idempotente e estado `pending/done/error`. Nao ha promessa de exactly-once atraves de uma queda do processo: um registro pendente pode exigir verificacao humana. A regra e nao repetir automaticamente um efeito de resultado incerto.

## Componentes mantidos e futuros

Os contratos genericos de audio, eventos, dispositivos e chamadas foram mantidos por serem pontos de integracao e terem testes. O provedor fisico antigo foi retirado. O futuro TTS deve fornecer voz local, cancelamento e eventos reais de reproducao; uma animacao de sigilo nao equivale a audio sendo reproduzido.

O futuro GPS deve tratar consentimento, precisao, horario da ultima medida e perda de sinal. O contrato de posicao existe, mas nenhum acesso ao GPS foi habilitado. O host Android solicita somente INTERNET, nao microfone ou localizacao.

Nao ha IA on-device no telefone. Implementa-la exige selecionar modelo, runtime, tamanho de pacote, memoria/temperatura do aparelho e medir latencia. A independencia offline entregue e de dados e interface.

## Fronteiras conhecidas

A base nao inclui autenticacao multiusuario do PC, isolamento entre usuarios locais do mesmo sistema operacional, servidor publico de producao, fila duravel de ferramentas externas ou garantia de qualidade do raciocinio. A API loopback confia em aplicativos locais autorizados; ela nao protege contra malware com acesso ao usuario do Windows.

A UI ainda e parcialmente monolitica dentro de cada arquivo JS. A separacao realizada e por responsabilidade, nao uma migracao completa para React/Flutter. Historicos e testes comportamentais foram preservados; arquivos antigos nao foram apagados apenas por nao terem sido executados nesta auditoria.
