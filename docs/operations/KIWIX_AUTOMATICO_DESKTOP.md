# Kiwix automatico no desktop Windows — Fase 5

O Campanario controla um processo filho de `kiwix-serve.exe` durante a vida
normal da janela desktop. Esta integracao apenas automatiza o servidor local;
nao altera pesquisa, verificacao de evidencias ou respostas dos agentes.

**Gatilho:** `CAMPANARIO_ZIM_ENABLED=true` e
`CAMPANARIO_ZIM_AUTO_START=true` (novo padrao). `CAMPANARIO_ZIM_BASE_URL`
deve ser `http://127.0.0.1:PORTA` ou `http://localhost:PORTA` com porta
explicita. Nada inicia quando a integracao ZIM esta desligada.

**Descoberta:** seleciona o mesmo `wikipedia_pt*.zim` que o leitor de
artigos utiliza (arquivo de nome mais alto em ordenacao reversa). Procura
`kiwix-serve.exe` em `CAMPANARIO-DATABASE/kiwix`, inclusive subpastas.
DLLs devem permanecer junto ao executavel.

**Processo:** `subprocess.Popen` com lista de argumentos, `shell=False`,
`--address=127.0.0.1`, `--port`, `--blockexternal`, `cwd` do executavel e
`CREATE_NO_WINDOW`. Entrada e saidas encaminhadas a `DEVNULL`. Sem
alterar arquivos ZIM, sem downloads, sem console.

**Porta ocupada:** nao iniciar outro processo nem encerrar o existente.
**Saida normal:** terminar e esperar somente o filho criado pelo proprio
Campanario; forcar parada desse mesmo filho somente se nao encerrar em
prazo limitado. O app sempre tenta abrir mesmo quando Kiwix nao esta pronto.

**Diagnostico:** `CAMPANARIO-DATABASE/dados/<ambiente>/logs/desktop.log`;
`TESTAR_WIKIPEDIA_OFFLINE.cmd` consulta o servidor atual e nao precisa ser
aberto diariamente.

**Reversao:** restaurar `src/campanario/app/desktop.py` e
`src/campanario/config.py` do backup anterior ou adicionar
`CAMPANARIO_ZIM_AUTO_START=false` no `.env` e reiniciar.
