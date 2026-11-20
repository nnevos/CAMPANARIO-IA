# Campanário R1.1 — proteção operacional e orçamento dos cérebros

**Estado:** implementação incremental sobre R1, com testes sintéticos; **não** é a conclusão do gate de segurança R1, nem autorização para executar código não confiável. Somente `CAMPANARIO-IA` disponível para edição. Não foram inspecionados os repositórios Python e Database reais.

## Fluxo operacional

```text
Chat/Prévia -> CapabilityRouter (até 3) -> PermissionPolicy (runtime)
       -> BrainExecutor (um orçamento TOTAL por plano; circuit breaker por cérebro)
       -> worker Python descartável (apenas knowledge/analysis)
       -> leitura SQLite/documentos e cálculo determinístico (V8)
       -> JSON com trace_id + referências verificáveis
       -> resposta factual canônica -> expressão V9.1 -> validação/fallback
```

O executor não substitui `AgentRouter`; identidade, personalidade e memória de Morgana/Todd continuam independentes. O plano não é automaticamente paralelo; continua sequencial. Um prazo de 8 segundos, por exemplo, limita **o conjunto de cérebros acionados**, não concede 8 segundos novos a cada um. Em caso de orçamento restante inferior a 100 ms, o executor devolve `turn_budget_exhausted` sem iniciar o próximo cérebro. O código registra duração e falha pelo mecanismo de auditoria existente; nenhum resultado de cérebro indisponível vira prova de consulta.

### Falhas em sequência

Três falhas de infraestrutura (`timeout`, `timeout_terminated`, `memory_limit_terminated`, `worker_failed`, `worker_start_failed`, `invalid_worker_payload`, `invalid_brain_result`, `worker_output_too_large`) em janela de 30 segundos abrem circuito por 20 segundos, **somente para o cérebro afetado**. Não há nova execução nesse período (`circuit_open`). Negação de permissão ou documento ausente não conta como incidente. Os valores são limites de código do incremento, não percentuais de precisão. O estado é **volátil, por instância do executor**; reiniciar o runtime reinicia os contadores. Não existe retry automático.

### Processo filho e segredo

`brains/isolation.py` agora passa um ambiente reduzido ao worker, evitando herdar `HTTP_PROXY`, `PYTHONPATH` de terceiros, tokens e variáveis privadas arbitrárias do chat. Mantém as variáveis necessárias para Windows e inicialização da `.venv`, sem instalar pacotes. `brains/worker.py` usa um guard de socket em nível Python enquanto adapta Conhecimento/Análise; ele recusa `connect`, `connect_ex`, `bind`, `listen`, `sendto`, `create_connection` e resolução via `getaddrinfo`. **Essa barreira é contornável por código hostil e bibliotecas nativas; NÃO é firewall ou sandbox de SO.** A proteção relevante é que esse worker aceita apenas os dois adaptadores first-party em leitura, com entrada JSON fixa, sem código fornecido pelo usuário ou shell. A validação de `trace_id` e a política de evidências permanecem no executor.

Ao cancelar uma tarefa, `execute_local_worker` executa a limpeza do processo no bloco `finally`. A presença de `psutil` (dependência já declarada) é verificada antes da criação do worker; sem monitoramento o executor falha fechado (`process_monitor_unavailable`) em vez de executar sem limite de RSS. Esse monitoramento é por amostragem e **não impede um pico instantâneo**. No Windows o subprocesso não possui Job Object/AppContainer, e o executável congelado sem interpretador sidecar ainda falha fechado. Códigos/ações de rede/escrita e o cérebro Programação **não estão habilitados** por este incremento.

## Topologia: três repositórios, um ambiente Python e dados externos

```text
C:\Users\Steam Deck\Documents\GitHub\
  CAMPANARIO-IA\                  codigo, interface, .env privado, docs
  CAMPANARIO-PYTHON\.venv\       Python 3.12, dependencias, psutil, voz
  CAMPANARIO-DATABASE\
    dados\desenvolvimento\campanario.db
    dados\producao\campanario.db
    dados\reference\interaction_library_v2.sqlite  (copia preferida, se existente)
    zim\                         acervo opcional
```

`CAMPANARIO_DATA_DIR` configura a raiz de dados; `CAMPANARIO_MEMORY_ENVIRONMENT` seleciona desenvolvimento/produção. `CAMPANARIO_ZIM_DIR` aponta para o acervo offline quando houver. O launcher `CAMPANARIO.vbs` pode preferir o antigo `Campanario.exe` empacotado antes de iniciar o Python da `.venv`. A Biblioteca V2 admite fallback legado de referência dentro do IA; não confundir com o SQLite pessoal. Esta atualização não lê nem migra automaticamente o banco real, não altera `.env`, `.venv`, modelos Ollama, voz ou o cliente mobile.

## Atualizar sem PowerShell

1. Feche Campanário, servidor e eventuais instâncias do EXE. Faça backup privado de `CAMPANARIO-IA` e `CAMPANARIO-DATABASE` (não distribua dados pessoais).
2. Extraia `CAMPANARIO_R11_ARQUIVOS_PARA_COPIAR.zip` em uma pasta temporária fora do projeto.
3. Pelo Explorador, **abra a pasta extraída e copie o conteúdo interno** para a raiz existente `CAMPANARIO-IA`, mesclando diretórios e substituindo apenas arquivos com o mesmo caminho. Compare antes os arquivos que personalizou. Não substitua a pasta inteira e não inclua o ZIP dentro do projeto como se fosse código.
4. Preserve `.env`, `CAMPANARIO-PYTHON\.venv` e todo o `CAMPANARIO-DATABASE`. Não há migração ou nova dependência para R1.1.
5. Inicie pelo launcher que já utiliza; verifique a Central de Cérebros e faça uma pergunta documental real. Se falhar, não atribua a informação ao documento; consulte o FAILSAFE e retorne apenas os arquivos IA anteriores a partir do backup.

PowerShell não é necessário para atualizar arquivos. Só faz sentido para instalar dependências, executar testes voluntários, manter a venv ou realizar migrações com backup validado.

## Testes e ressalvas

Foram executados os seis novos cenários de `tests/test_r11_brain_guardrails.py`, além de todos os testes direcionados da R1/V9/V9.1/V8/P0. Ver `docs/operations/RESULTADOS_TESTES_R11.md`. O ambiente foi Linux/Python 3.13.5 (fora do alvo Python 3.12/Windows). Não foram realizados testes com seu Ollama, EXE compilado, Windows Job Objects, restauração real do SQLite, network isolation nativa ou mobile físico.

**Próximo gate:** unificar `utilities/api.py` com o runtime de autorização e confirmação sem quebrar ações existentes; criar sandbox verdadeiro para qualquer futuro cérebro Programação; validar cancelamento, limites e worker com a `.venv` e EXE reais no Windows. Só depois considerar R1 encerrada e iniciar a composição R2 com autorização segura.
