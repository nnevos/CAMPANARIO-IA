# 23 — Mobile Readiness PF8

PF8 nao e o aplicativo Android/iOS final. E uma prova de que um cliente com identidade de celular pode usar o mesmo Campanario.

## O que ja funciona

- registrar um device mobile de teste;
- parear e obter uma credential PF6;
- reconnect autenticado;
- entrar na mesma `session_id` do PC/Web;
- enviar texto e receber eventos Todd/Morgana;
- reconectar sem criar outra sessao;
- anunciar um snapshot GPS de teste;
- disponibilizar esse snapshot como `location.current` no Capability Registry.

## Testar

No Windows:

```bat
tools\windows\regression\platform\TESTAR_RUNTIME_PF8.bat
```

Com Campanario ja iniciado localmente, o cliente de prova pode ser executado por:

```bat
tools\windows\RODAR_CLIENTE_MOBILE_PF8.bat
```

Na primeira execucao ele mostra uma credential de pairing. Ela e equivalente a um segredo do device e nao deve ser publicada.

## Importante

O servidor continua preso a `127.0.0.1`. Portanto um telefone fisico na rede ainda nao deve tentar conectar diretamente. PF8 prova arquitetura/protocolo; exposicao LAN/WAN exige uma etapa propria de transporte seguro (TLS, interface binding, pairing UX e revogacao).

A localizacao de PF8 e um snapshot deliberado de teste. Ela nao fica rastreando o usuario em background e e invalidada quando o device desconecta.
