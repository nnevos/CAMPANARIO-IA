# CAMPANARIO — Kiwix automaticamente, sem janela preta

Este ZIP e um **patch incremental**. Nao apague a pasta `CAMPANARIO-IA` e nao
reinstale Python, Ollama, modelos de voz ou Wikipedia. Nenhum arquivo `.env`,
banco, memoria, executavel ou ZIM e incluido.

## Instalar so com o Explorador de Arquivos

1. Feche o Campanario. Se o Kiwix estiver aberto numa janela do CMD, **feche
   essa janela manualmente uma vez**. O Campanario nao encerra servidores que
   foram iniciados fora dele.
2. Por precaucao, guarde uma copia destes arquivos do seu projeto atual em
   uma pasta de backup *fora* de `CAMPANARIO-IA`:
   - `src\campanario\app\desktop.py`
   - `src\campanario\config.py`
   - `.env.example` (e apenas um exemplo; nao e seu `.env` privado)
   - `README.md`
3. Extraia o ZIP recebido e abra a pasta `CAMPANARIO-IA` que existe dentro
   dele. **Copie o conteudo** para `Documentos\GitHub\CAMPANARIO-IA` e
   escolha mesclar as pastas e substituir os arquivos com o mesmo nome.
   Nao remova a pasta inteira do projeto.
4. Verifique que seu `.env` existente ainda tem `CAMPANARIO_ZIM_ENABLED=true`.
   Nenhuma edicao adicional e necessaria: `CAMPANARIO_ZIM_AUTO_START` ja e
   `true` por padrao. Nao substitua o `.env` pelo `.env.example`.
5. Confirme que ja existem:
   - `CAMPANARIO-DATABASE\zim\wikipedia_pt*.zim`
   - `CAMPANARIO-DATABASE\kiwix\kiwix-serve.exe` (pode estar numa subpasta, com DLLs)
   - `CAMPANARIO-PYTHON\.venv` (ambiente atual, nao modificar)
6. Agora **abra somente `CAMPANARIO.bat`** (ou o atalho do aplicativo).
   O Kiwix sera iniciado invisivelmente em `127.0.0.1:8181`, se a porta
   estiver livre e os arquivos existirem. Nao precisa abrir o
   `INICIAR_WIKIPEDIA_OFFLINE.cmd`.
7. Com o Campanario aberto, teste no chat `Todd, quem foi Ada Lovelace?`.
   Se quiser diagnosticar, o `TESTAR_WIKIPEDIA_OFFLINE.cmd` continua servindo
   para testar a conexao, mas nao precisa ser executado diariamente.
8. Feche o Campanario normalmente. O processo Kiwix que ELE criou sera
   encerrado; servicos que voce iniciou manualmente nao serao encerrados.

## Comportamento seguro

- Funciona no aplicativo desktop Windows que usa `CAMPANARIO-PYTHON`.
- **Nao acessa internet** para iniciar Kiwix, nao baixa ZIM nem instala nada.
- Se o Kiwix nao estiver instalado, nao houver ZIM ou a porta ja estiver
  ocupada, o Campanario continua abrindo normalmente.
- O processo de outra pessoa/programa na porta 8181 nao sera derrubado.
- Se quiser voltar ao controle manual, coloque no `.env`:
  `CAMPANARIO_ZIM_AUTO_START=false` e reinicie o Campanario.
- Para desativar de vez a Wikipedia, use `CAMPANARIO_ZIM_ENABLED=false`.
- Kiwix e o proprio Campanario so escutam no computador local.
- Nao ha garantia para encerramento forçado via Gerenciador de Tarefas ou
  queda de energia; a rotina de desligamento normal encerra o processo criado.

**Atencao:** se houver um `Campanario.exe` precompilado antigo ao lado do
`CAMPANARIO.vbs`, esse iniciador prioriza o `.exe` e nao carrega alteracoes
recentes do Python. Na instalacao de codigo-fonte homologada (com Python
externo), use o `CAMPANARIO.bat` sem `Campanario.exe` antigo na pasta.

**Regressao:** a nova funcionalidade nao altera os agentes, a pesquisa web,
o sistema de PDFs, as vozes, nem as memorias. Os testes de Kiwix usam
processos falsos e nao substituem a validacao no seu Windows.
