# Instalação rápida — Wikipédia offline (Fase 5 Inc.1)

**Este ZIP é um PATCH incremental, não o projeto completo.** Já deve existir `CAMPANARIO-IA`, `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE` funcionando.

**Não apague a pasta atual. Não altere `CAMPANARIO-PYTHON` nem `CAMPANARIO-DATABASE\dados`.**

## Sem PowerShell: copiar pelo Explorador

1. Feche o Campanario e salve cópias destes cinco arquivos da pasta atual:
   - `src\campanario\config.py`
   - `src\campanario\composition.py`
   - `src\campanario\chat\service.py`
   - `src\campanario\chat\fact_sheet.py`
   - `.env.example` (não confundir com o `.env` privado)
2. Abra o ZIP e entre na pasta `CAMPANARIO-IA`. **Copie as pastas/arquivos internos por cima da pasta `CAMPANARIO-IA` atual**, aceitando mesclar pastas e substituir os cinco arquivos listados. Os demais arquivos do patch são novos.
3. Siga as instruções em `docs\operations\WIKIPEDIA_OFFLINE_KIWIX.md` para baixar o Kiwix e o ZIM em `CAMPANARIO-DATABASE`, ligar o servidor com dois cliques e ativar a opção no `.env`.
4. Faça o diagnóstico com dois cliques em `TESTAR_WIKIPEDIA_OFFLINE.cmd`.
5. Teste no chat com `Todd, quem foi Ada Lovelace?`.

## Segurança e limitações

O arquivo `.env` privado nunca é enviado no patch. A funcionalidade começa desligada (`CAMPANARIO_ZIM_ENABLED=false`); nada muda até você ativar no `.env`. A busca é exclusivamente em `127.0.0.1`, com limite de tempo e tamanho; a fonte é um trecho literal com URL local. Não há downloads automáticos nem alterações dos bancos de memória.

Uma pergunta sem artigo correspondente continua com a política atual de abstenção. As vozes, personalidades e histórico não são alterados.
