# Limpeza controlada v0.8

Base: arquivo CAMPANARIO_UI_v0.7_PROJETO.zip recebido nesta conversa. Nao foi usada uma suposicao sobre o que havia no repositorio.

## Retirada do pacote ativo

162 arquivos originais, totalizando 22.207.741 bytes, foram separados em `CAMPANARIO_v0.8_LEGADO_ARQUIVADO.zip`. O inventario SHA256 individual esta em `REMOVIDOS_V08.json`. Esse total inclui os inicializadores originais que foram substituidos, e nao significa 162 funcionalidades removidas.

Saem a implementacao host de voz antiga, binarios locais Whisper/SAPI, o modulo Ren'Py, a pagina e launcher de fabrica, e testes exclusivos dos provedores/experimentos retirados. Os contratos genericos de audio, dispositivos, eventos e chamadas permanecem para a futura integracao.

O menu de entrada nao existe mais. Diagnosticos de desenvolvimento continuam em `tools/windows`, fora da abertura diaria. Remover um menu nao e motivo para apagar diagnosticos uteis ou testes de comportamento.

Manuais operacionais anteriores foram movidos para `docs/history/manual-v07`; os documentos da UI antiga para `docs/history/ui-v07`; ADRs Ren'Py para historico. `docs/manual/README.md` aponta para o guia atual. Os textos antigos continuam sendo historico, nao devem ser seguidos para iniciar voz ou usar a v0.8.

## Preservado

Nucleo de chat, identidades Morgana/Todd, protocolo social, memoria SQLite, RAG/indices suportados, autorizacoes, ferramentas e contratos realtime permanecem. Nenhum reset de dados pessoais, Ponto Zero ou modelo foi executado. A limpeza nao tenta decidir automaticamente quais memorias do usuario sao desnecessarias.

Testes de markup foram ajustados para ler os novos arquivos JS externos, a abertura em nova conversa e os metadados da release. Os testes comportamentais de memoria que falhavam continuaram ativos, sem serem marcados como aprovados ou removidos.

## Aplicacao

Use pasta nova. Sobrepor apenas arquivos nao remove os restos antigos. Nao extraia o ZIP de legado na pasta nova; ele existe para auditoria e eventual recuperacao dirigida, nao para reativacao automatica.
