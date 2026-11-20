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
