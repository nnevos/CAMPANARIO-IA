# CAMPANARIO-IA — projeto enxuto

Campanario 0.8.0: assistente com Morgana e Todd, orquestracao de conversa, memoria, biblioteca local, Wikipedia ZIM e voz. **Esta pasta e o codigo.** O ambiente Python e as memorias pessoais ficam em duas pastas irmas.

## Estrutura ativa no Windows

```text
Documents/GitHub/
  CAMPANARIO-IA/             <- codigo, agentes, interfaces, testes, documentacao
  CAMPANARIO-PYTHON/.venv/   <- Python 3.12, Piper, Pocket TTS e PyTorch/CUDA
  CAMPANARIO-DATABASE/dados/ <- memorias e bancos SQLite pessoais
  CAMPANARIO-DATABASE/zim/   <- Wikipedia offline em arquivos ZIM (Kiwix local)
```

O `.env` fica localmente na raiz de `CAMPANARIO-IA` e aponta para as pastas externas. **Nao compartilhe o `.env`, bancos, pastas `.git`, ambientes `.venv` ou arquivos de voz pessoais.** Modelos Ollama continuam fora destas pastas.

## Abrir e testar

- Abrir: `CAMPANARIO.bat` ou `CAMPANARIO.vbs` no Windows (usa `../CAMPANARIO-PYTHON/.venv`).
- Diagnosticar: `DIAGNOSTICAR_CAMPANARIO.ps1`.
- Validar a instalacao de tres pastas: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\TESTAR_3_PASTAS.ps1 -ProjectRoot .`.
- Testar o roteamento de chamadas: `& "..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe" -m pytest tests/test_chamada_de_agente_sem_pesquisa.py -q`.
- Testes gerais: `& "..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe" -m pytest -q` (alguns testes historicos ja apresentam falhas conhecidas).

## Voz e pacote compartilhavel

Os arquivos `vozes/*.onnx` sao ativos locais grandes, nao entram no **ZIP leve de codigo**. Na troca de pasta, o instalador fornecido fora do projeto copia os modelos de voz, o `.env` e o historico `.git` diretamente da pasta anterior, sem colocar dados privados em arquivos compartilhados. A pasta antiga fica preservada ate a homologacao.

Se receber **somente** este codigo sem ter a pasta antiga, sera necessario fornecer localmente o `.env` e os modelos `.onnx` antes de usar voz. O instalador de troca se recusa a substituir um projeto sem poder preservar esses arquivos.

## Organizacao

- `src/campanario/`: codigo principal, agentes, chat, memoria, voz e UI.
- `tests/`: regressao e verificacoes de seguranca factual.
- `tools/`: diagnosticos, avaliadores e utilitarios.
- `docs/manual/`: guia de operacao.
- `docs/current/`: arquitetura atual e notas de evolucao.
- `docs/concept/`: conceitos originais de Campanario, Morgana e Todd.
- `apps/`: interfaces e prototipos, incluindo mobile.
- `eval/`: bases e criterios de avaliacao, sem relatarios gerados.

`ATIVAR_SEPARACAO.ps1` e `REVERTER_SEPARACAO.ps1` foram preservados para contingencia; **nao e necessario executar a migracao novamente** num computador ja homologado.

## Principios

- Conversas e identidades de Morgana e Todd sao preservadas.
- A verificacao factual e o cuidado com evidencias continuam ativos.
- A integracao Kiwix/ZIM e opcional, usando exclusivamente o servidor local.
- Com `CAMPANARIO_ZIM_ENABLED=true`, o desktop Windows inicia e encerra o Kiwix automaticamente, sem CMD; `INICIAR_WIKIPEDIA_OFFLINE.cmd` fica so para uso manual. Veja `LEIA_PRIMEIRO_KIWIX_AUTOMATICO.md`.
- Pesquisa web automatica e opcional e desligada por padrao. Quando autorizada, a prioridade pode ser web -> ZIM -> documentos.
- Para ativar/desativar a pesquisa online sem PowerShell, use ATIVAR_ONLINE_PRIMEIRO.cmd / DESATIVAR_PESQUISA_ONLINE.cmd.
- Para exportar codigo sem dados pessoais, use `tools/exportar_campanario.py` (ele exclui pesos, memorias e configuracoes privadas).

## Incremento CAMPANÁRIO V8 — conhecimento e análise

Foi adicionado um pipeline documental compatível com a biblioteca legada, com
metadados, seções/FTS5, OCR local opcional, DOCX/CSV/XLSX/JSON, recuperação de
evidências compartilhadas pelos agentes e análises numéricas locais. Não modifica
as pastas irmãs `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE` diretamente.

**Leia [`docs/current/V8_MOTOR_CONHECIMENTO.md`](docs/current/V8_MOTOR_CONHECIMENTO.md)**
antes da atualização. O documento explica comandos, backups, limitações,
instalação dos extras de análise e o teste fictício de Ordem Paranormal.

## Incremento CAMPANARIO V9.1 - expressao fundamentada

Sobre a base V8 foi introduzida uma resposta factual canonica **antes** da
reformulacao por Morgana/Todd, validacao conservadora de numeros, condicoes,
negacoes e referencias, alem de fallback extrativo e visor local de evidencias.
Reutiliza a infraestrutura de Ollama e as consultas documentais V8.

Veja [`docs/current/V91_EXPRESSAO_FUNDAMENTADA.md`](docs/current/V91_EXPRESSAO_FUNDAMENTADA.md)
e [`docs/current/RELATORIO_V91_ENTREGA.md`](docs/current/RELATORIO_V91_ENTREGA.md).
Este incremento nao inclui codigo externo dos cerebros V9 nem altera as pastas
`CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE`.

## V9 (cérebros) + V9.1 (expressão fundamentada)

O incremento de cérebros compartilhados e fichas heroicas preserva a arquitetura de chat e integra-se à validação factual V9.1. Ativação opt-in via `CAMPANARIO_BRAINS_V9_ENABLED=true`, após migração aditiva `0010` e backup do Database. Guia completo: [`docs/current/V9_BRAINS_ARQUETIPOS_TALENTOS.md`](docs/current/V9_BRAINS_ARQUETIPOS_TALENTOS.md) e [`LEIA_PRIMEIRO_V9_INTEGRADA.md`](LEIA_PRIMEIRO_V9_INTEGRADA.md).


## Roadmap de conclusão V9 — cérebros e failsafes

O incremento V9/V9.1 é uma base funcional, **não** o sistema de oito cérebros concluído. Conhecimento e Análise têm executores; os seis demais ainda estão indisponíveis. A sequência de integração, os gates P0/P1/P2, dependências das três pastas e os testes de aceite estão no [`roadmap completo V9`](docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md). Procedimentos para conter falhas, desativar a V9 pela flag, proteger evidências e recuperar a instalação estão em [`FAILSAFE V9`](docs/operations/FAILSAFE_V9_CEREBROS.md). Essas referências são planejamento/documentação e não introduzem novas capacidades no runtime.


## P0 — verificação integrada e atualização do código SEM PowerShell

A Central de Cérebros agora inclui uma verificação **somente leitura** da topologia das três pastas e do SQLite esperado, mesmo com a flag V9 desativada. Não move dados, não cria venv e não executa migrações. O executor bloqueia escopos ausentes e resultados com IDs de execução inválidos. Isso ainda **não** homologa as três pastas reais nem fornece sandbox com interrupção física.

**Atualização normal:** use o ZIP de arquivos alterados e copie pelo Explorador para dentro de `CAMPANARIO-IA` (depois de backup, com o aplicativo fechado). **Não precisa de PowerShell para substituir arquivos.** Comandos ficam reservados a dependências, migrações ou testes técnicos. Veja [`P0_TRES_PASTAS_SEM_POWERSHELL.md`](docs/current/P0_TRES_PASTAS_SEM_POWERSHELL.md), [`roadmap V9`](docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md) e [`FAILSAFE V9`](docs/operations/FAILSAFE_V9_CEREBROS.md).


**Exceção documentada:** `data/interaction_library_v2.sqlite` é uma biblioteca estática de exemplos, consultada em leitura, não o banco pessoal. O P0 prefere uma cópia em `CAMPANARIO-DATABASE/dados/reference/interaction_library_v2.sqlite`, mas preserva fallback legado. Não apague o original sem validar a cópia externa e o FAILSAFE.


## Checkpoint R1 — contenção de falhas dos cérebros (incremental, não homologado)

Os dois cérebros de leitura instalados (`knowledge`, `analysis`) usam subprocesso Python terminável ao exceder timeout/RSS. A leitura é autorizada por `PermissionPolicy` na composição canônica; a resposta factual V9.1 e a flag continuam preservadas. **Não é sandbox de segurança contra código hostil**, nem substitui autorização/isolamento das rotas de utilidades. Um `Campanario.exe` congelado pode precisar de Python sidecar; consulte [`R1_ISOLAMENTO_CEREBROS.md`](docs/current/R1_ISOLAMENTO_CEREBROS.md), [`ROADMAP`](docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md) e [`FAILSAFE`](docs/operations/FAILSAFE_V9_CEREBROS.md). Atualizações de código: copiar os arquivos do ZIP de overlay pelo Explorador, sem PowerShell.


## R1.1 — contenção de falhas do motor de cérebros

Sobre a base R1, o executor compartilha o timeout entre cérebros de um mesmo plano, interrompe a sequência quando o orçamento acaba e evita tempestades de workers após falhas repetidas. O worker de Conhecimento/Análise recebe ambiente reduzido e barreira Python para sockets; **isso não é firewall nem sandbox de segurança do Windows**. Não libera Programação ou ações arbitrárias. Veja [`LEIA_PRIMEIRO_R11.md`](LEIA_PRIMEIRO_R11.md), [`ROADMAP`](docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md) e [`FAILSAFE`](docs/operations/FAILSAFE_V9_CEREBROS.md). Atualização de arquivos é por cópia no Explorador, sem PowerShell. As pastas Python/Database permanecem separadas e intactas.
