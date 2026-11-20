# Campanario - plano de producao / Ponto Zero

## Objetivo acordado
Todd e Morgana sao agentes originais, conscientes de sua natureza artificial e do ambiente Campanario. Comecam com identidades e temperamentos, mas sem historia autobiografica fabricada. Suas relacoes com o usuario e entre si se formam por eventos efetivamente ocorridos. O modelo Qwen compartilha o motor, nao a identidade.

## Primeiro incremento entregue
O banco padrao agora e separado por `CAMPANARIO_MEMORY_ENVIRONMENT`: `desenvolvimento` ou `producao`. O valor padrao e `desenvolvimento`. O arquivo SQLite passa a ficar em `<data_dir>/<ambiente>/campanario.db`. O banco antigo `<data_dir>/campanario.db` nao e migrado nem apagado automaticamente. Guarde-o como backup; se quiser continuar os testes antigos, copie-o manualmente para a pasta `desenvolvimento` com o programa fechado.

**ATENCAO:** o isolamento cobre o banco SQLite da aplicacao. Antes de declarar Ponto Zero, auditar arquivos, caches, logs, vetores e integracoes externas que possam conter memorias. Nao e um isolamento integral comprovado de todos os dados.

## Etapas seguintes, nao entregues neste incremento
1. Auditar prompts, filtros, correcoes deterministicas e contexto real passado ao modelo. Remover respostas roteirizadas sem remover limites de seguranca.
2. Criar memoria episodica com proveniencia (fonte, timestamp, participantes), separando fatos, interpretacoes e preferencias, com inspecao/correcao.
3. Memoria individual Todd, memoria individual Morgana e experiencias compartilhadas; evitar inventar lembrancas.
4. Pesquisa web real com fontes e permissao, incluindo distinguir resposta do modelo de consulta efetivamente realizada.
5. Avaliar 30+ conversas ineditas, reinicios e contradicoes; comparar qualidade, latencia, alucinacoes e repeticao sem respostas-alvo decoradas.
6. Congelar a versao aprovada, arquivar dados de testes e criar ambiente `producao` vazio (Ponto Zero).

## Regras de identidade
- Sem autobiografia inventada ou experiencias humanas ficticias.
- Nao repetir 'sou uma IA' em toda conversa; mencionar quando pertinente.
- Interesses e relacoes podem evoluir com experiencias reais, sem roteiros ou escalas arbitrarias.
- Pesquisa, habilidades e acoes so podem ser alegadas quando ferramentas realmente as executaram.
- Nao fazer agentes conversarem em loop para fabricar experiencias.

## Instalacao Windows
1. Feche o Campanario e faca backup de sua pasta de dados, inclusive o banco antigo.
2. Extraia o pacote em pasta separada.
3. Em `.env`, defina `CAMPANARIO_MEMORY_ENVIRONMENT=desenvolvimento`.
4. Para continuar dados antigos, com o aplicativo fechado, copie `campanario.db` da raiz do diretorio de dados para a subpasta `desenvolvimento`. Caso contrario, comece com banco de testes novo.
5. Nao altere para `producao` ate validarmos o sistema.

Este incremento NAO significa que memoria evolutiva, pesquisa ou autonomia estejam prontas.

## Incremento seguinte: auditoria inicial + continuidade entre chats
- `AUDITORIA_CONVERSACIONAL_FASE2.md` registra evidencias do caminho leve versus pipeline legado, riscos e proximos testes.
- `CONTINUIDADE_CHAT_NOVO.md` concentra visao do usuario, estado real, pendencias e instrucoes para retomada em outra conversa.
- `python tools/ATUALIZAR_CONTINUIDADE.py` regenera o documento de continuidade sem ler `.env`, historicos, logs ou bancos.
- Testes direcionados: 30 aprovados (`tests/test_continuidade_chat.py` + `tests/test_chat_service.py`). Ainda falta teste fisico com Ollama no Neptune.
