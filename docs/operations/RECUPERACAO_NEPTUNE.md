# CAMPANARIO / Pacote Neptune — revisao de latencia e naturalidade

## O que muda

1. **Ollama Qwen3.5 9B**: `think=false` enviado no nivel correto da API `/api/chat`,
   `num_ctx=4096`, `num_predict=320`, `keep_alive=20m` (parametros ajustaveis).
   Respostas curtas nao pagam custo desnecessario de raciocinio. `keep_alive`
   nao impede carregamento lento na primeira mensagem ou apos ficar inativo.
2. **Resposta em streaming de verdade** no modo rapido. O texto chega a interface
   em partes, com pequena janela de retencao para inspecionar vazamento de prompts.
   O modo conservador anterior fica disponivel.
3. **Sem respostas sociais enlatadas no modo leve**. A antiga `ResponseContractPipeline`
   continua no codigo, mas nao substitui conversas por `Opa.`, `Certo.`, etc.
4. **Prompts menores e duas vozes distintas**. Todd e Morgana continuam IAs originais
   e nao personagens humanos ou representantes literais de herois de HQ.
5. **O arbitro de participacao por LLM foi desativado por padrao**: o segundo agente
   responde quando solicitado explicitamente; a participacao espontanea pode ser
   restaurada via configuracao, com custo de latencia.
6. **Resumo automatico sincronico desativado por padrao**. O contexto usa 12 mensagens
   recentes e a memoria experiencial do Campanario quando presente. Resumir grandes
   conversas com varias chamadas de LLM permanece opcional.
7. Diagnostico sem personalidade em `CAMPANARIO.bat > [12]` para separar hardware,
   carregamento, prompt e geracao.

## Windows 11 — instalar e iniciar

1. **Mantenha o ZIP original como backup**, descompacte esta versao em uma pasta NOVA,
   por exemplo `C:\Campanario-Neptune`. Nao sobreponha uma pasta em uso.
2. Ollama atual ja instalado: `ollama --version`, `ollama list`.
   Se necessario: `ollama pull qwen3.5:9b`.
3. Instale `uv` pelo site oficial https://docs.astral.sh/uv/ . Ele instala
   a versao de Python 3.12 requerida pelo projeto quando necessario.
4. Abra `CAMPANARIO.bat`. Opcao **12** mede duas perguntas fora do Campanario,
   com `think=false`. Observe diferenca entre primeira e segunda chamada.
5. Volte ao menu e use **1** para iniciar a interface. A primeira execucao
   cria `.env` a partir de `.env.example`. Acesse a URL mostrada pelo launcher.
6. Se voce ja tiver um `.env` antigo: **nao o copie sem revisar**. Ele pode apontar
   para `gemma3:12b` e pode substituir algumas opcoes novas. Edite apenas o arquivo
   local `.env` (nunca publique esse arquivo), usando o exemplo como guia.

## Configuracao essencial (.env)

```dotenv
CAMPANARIO_MODEL_NAME=qwen3.5:9b
CAMPANARIO_MODEL_THINK=false
CAMPANARIO_MODEL_CONTEXT_WINDOW=4096
CAMPANARIO_MODEL_MAX_OUTPUT_TOKENS=320
CAMPANARIO_MODEL_KEEP_ALIVE=20m
CAMPANARIO_LOW_LATENCY_MODE=true
CAMPANARIO_LIVE_STREAMING=true
CAMPANARIO_CONTEXT_MAX_MESSAGES=12
CAMPANARIO_CONTEXT_AUTO_SUMMARIZE=false
CAMPANARIO_PARTICIPATION_ARBITER_ENABLED=false
```

Reinicie o servidor do Campanario apos alterar o `.env`.

## Recursos e limitacoes honestas

- **Internet/pesquisa web**: nao foi acrescentado um navegador ou ferramenta de busca
  nesta revisao. Ter um agente que sabe conversar sobre internet nao significa que
  ele realmente navegou. A camada de permissoes existe, mas provedores de busca
  e suas credenciais/limites precisam ser implementados e testados separadamente.
- **Voz**: o subsistema STT/TTS antigo permanece intacto, mas NAO foi validado
  no Neptune. Nao ligue a voz antes de estabilizar texto. Este pacote nao promete
  ter corrigido erros de transcricao ou latencia de microfone.
- **Memoria**: memoria experiencial original persiste conforme configuracao e
  banco local existente. Desligar resumo sincronico evita chamadas LLM extras,
  mas reduz a janela literal do historico a 12 mensagens. Consulte o historico
  episodico pela interface quando necessario.
- **Seguranca**: streaming reduz a possibilidade de revisar a resposta completa
  antes de exibicao. Se quiser validacao e reparo completos antes da interface,
  desative `LOW_LATENCY_MODE` e `LIVE_STREAMING`.
- **Hardware**: modelos so foram verificados em testes sinteticos sem GPU aqui.
  Os tempos reais precisam ser medidos no Windows do Neptune.

## Checklist de qualidade anti-resposta decorada

Nao acrescente uma pergunta especifica no banco para 'fazer teste passar'. Em vez
isso, teste sempre cinco parafrases ineditas e pelo menos uma conversacao longa.
Criterios: se respondeu ao significado, se mantem voz de Todd/Morgana, se nao
inventa capacidade ou memoria, e quanto tempo demorou para primeira frase.

Algumas tarefas devem ser encaminhadas a ferramentas reais quando implementadas:
comandos no PC e buscas na web precisam de permissao/confirmacao e logs com
resultados. **Nunca trate uma resposta inventada pelo modelo como execucao.**

## Rollback

Configure `CAMPANARIO_LOW_LATENCY_MODE=false` e
`CAMPANARIO_LIVE_STREAMING=false` para retornar ao pipeline conversacional
anterior e ao modo bufferizado. Se precisar voltar ao modelo anterior, altere
`CAMPANARIO_MODEL_NAME` para um modelo instalado. O ZIP original e seu backup.

## G2 — embeddings locais (Fase 8)

Depois de iniciar o Ollama, escolha **14** no `CAMPANARIO.bat` para baixar/testar `embeddinggemma` (modelo local, ~622 MB). Para instalar manualmente: `ollama pull embeddinggemma`. Execute o diagnóstico real novamente via `uv run python tools/maintenance/DIAGNOSTICAR_BUSCA_SEMANTICA.py`. Sem o modelo, a recuperacao volta a lexical com aviso; isso **nao** comprova que G2 funcionou. O `data_dir` e `memory_environment` devem apontar para desenvolvimento, sem iniciar Ponto Zero.
