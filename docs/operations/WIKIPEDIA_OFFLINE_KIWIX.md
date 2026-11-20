# CAMPANARIO — Fase 5, incremento 1: Wikipédia offline por Kiwix/ZIM

## O que este incremento FAZ

- Consulta **apenas** `127.0.0.1:8181`, via `kiwix-serve` executando na mesma máquina.
- Detecta arquivos `wikipedia_pt*.zim` em `CAMPANARIO-DATABASE\zim`, sem copiá-los, indexá-los ou lê-los diretamente em Python.
- Usa o índice de títulos (`/suggest`) e **lê a página real** (`/raw`), em vez de confiar apenas em um resultado de pesquisa.
- Dá prioridade aos documentos já importados no Campanario; depois consulta o ZIM, **antes** de considerar a web ou a abstenção.
- Integra o trecho literal com a **Ficha Factual Neutra e Imutável** por turno, igualmente para Morgana e Todd, identificando o arquivo ZIM e link local.
- Evita extrapolação: títulos ambíguos, evidência insuficiente ou Kiwix indisponível não geram fatos inventados.
- Está **desligado por padrão**, não instala Python, não altera bancos, não toca em personalidades, voz ou `.env` privado.

## Limites conhecidos

- **Não há ZIM nem `kiwix-serve.exe` neste patch.** São downloads oficiais separados; não existe Wikipédia offline sem o conteúdo.
- A primeira entrega prioriza perguntas que identifiquem **um artigo pelo título**, como `Todd, quem foi Ada Lovelace?` e `O que é Python?`; perguntas relacionais ou vagas sem artigo único podem se abster.
- O serviço Kiwix deve ser iniciado pelo `.cmd` antes do Campanario; este incremento **não cria processos em segundo plano**.
- `kiwix-serve` disponibiliza o conteúdo só para consulta no localhost. Desative qualquer opção de proxy externo e mantenha `--blockexternal`.
- Kiwix `/suggest` é uma API privada e pode mudar; o artigo é obtido da API pública `/raw` e a integração falha de modo seguro se o formato de sugestões mudar.
- Os arquivos ZIM são snapshots da Wikipédia. Podem ser antigos ou conter erros; trecho de artigo não é verdade independente.
- A demonstração automatizada utiliza um servidor HTTP falso e texto sintético. **Não foi homologada contra seu ZIM real no Windows**.

## Instalação sem PowerShell

1. Faça backup manual dos arquivos atuais listados no arquivo `LEIA_PRIMEIRO_WIKIPEDIA_OFFLINE.md`.
2. Extraia o ZIP incremental, abra a pasta `CAMPANARIO-IA` interna e arraste seu conteúdo para `Documentos\GitHub\CAMPANARIO-IA`, **mesclando as pastas** e substituindo apenas os arquivos listados. **Nunca apague a pasta CAMPANARIO-IA antes de copiar.**
3. Baixe `kiwix-tools` para Windows x64 do site oficial: https://download.kiwix.org/release/kiwix-tools/ (um pacote `kiwix-tools_win-x86_64-*.zip`). Extraia todo o conteúdo para `Documents\GitHub\CAMPANARIO-DATABASE\kiwix`; preserve as DLLs ao lado do executável.
4. Baixe a Wikipédia em português no catálogo oficial: https://library.kiwix.org/ — procure `wikipedia_pt_all_nopic` (artigos completos sem imagens) ou `wikipedia_pt_all_mini` (introduções). Guarde o arquivo `.zim` em `Documents\GitHub\CAMPANARIO-DATABASE\zim`. **Não descompacte o ZIM**.
5. Dê dois cliques em `INICIAR_WIKIPEDIA_OFFLINE.cmd`, na pasta do código, e mantenha a janela aberta. Verifique no navegador o endereço `http://127.0.0.1:8181`.
6. Abra seu `.env` (arquivo privado, que **não vem no ZIP**) no Bloco de Notas, acrescente **apenas** `CAMPANARIO_ZIM_ENABLED=true`. As configurações ativadas anteriormente `CAMPANARIO_DATA_DIR` e `CAMPANARIO_ZIM_DIR` devem continuar iguais.
7. Dê dois cliques em `TESTAR_WIKIPEDIA_OFFLINE.cmd`; o diagnóstico deve mostrar `Status: grounded_local_zim` e `OK`.
8. Reinicie o Campanario e teste `todd?`, depois `Todd, quem foi Ada Lovelace?`. Resposta com citação de `wikipedia_pt...zim` indica integração funcionando.

## Reverter somente este incremento

Feche o Campanario e Kiwix. Restaure os arquivos de código sobrescritos do backup manual. Remova `CAMPANARIO_ZIM_ENABLED=true` ou altere para `false` no `.env` e reinicie. O ZIM e o executável Kiwix podem permanecer em `CAMPANARIO-DATABASE` sem interferência; os bancos não foram modificados.

## Verificação automatizada

No Python externo existente, `python -m pytest tests/test_wikipedia_zim_offline.py -q`.

Este incremento deliberadamente não altera downloads, memória pessoal, arquivos ZIM nem vozes.
