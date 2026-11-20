# Fase 2 — auditoria inicial do caminho conversacional

## Evidencias do codigo
- `src/campanario/composition.py`: com `low_latency_mode=True`, o provider usa `safe_provider`, nao `BehaviorResponseGuardProvider`; assim o `ResponseContractPipeline` legado nao processa as falas desse perfil.
- `src/campanario/response/pipeline.py`: o caminho legado ainda contem `_closed_class_repair` com textos fixos `Opa.`, `Boa.`, `Certo.`, `Corrigido.`, `Fechado.` e pode solicitar regeneracoes extras. Nao foi removido para evitar quebrar compatibilidade sem regressao suficiente.
- `src/campanario/chat/service.py`: streaming so e ativado quando `live_streaming` E `low_latency_mode` sao verdadeiros. A composicao do contexto e do perfil ainda pode influenciar a rigidez da resposta.
- `src/campanario/config.py`: valores padrao do pacote incluem `model_think=False`, `low_latency_mode=True`, `live_streaming=True`, `context_auto_summarize=False`, `participation_arbiter_enabled=False`.

## Riscos e proximos testes
1. Testar com mensagens **ineditas**, nao apenas respostas esperadas fixas, que o caminho leve nao substitui cumprimentos ou identidades por frases programadas.
2. Inspecionar `agents/context.py`, `agents/profiles.py`, `agents/personality_application.py` e `chat/context.py` para detectar excesso de regras e historico irrelevante.
3. Confirmar a configuracao efetiva do `.env` no Windows; valores antigos podem reativar o pipeline legado.
4. Medir TTFT, tempo total, uso de GPU e qualidade real no Neptune; testes unitarios nao provam naturalidade.
5. Auditar camada `runtime/experience.py`: nao confundir existencia de memoria com qualidade de recuperacao ou aprendizagem.

## Regra de engenharia
Corrigir a origem de cada erro. Nao adicionar exemplos decorados, respostas-alvo ou autobiografia ficticia para melhorar pontuacao de testes.
