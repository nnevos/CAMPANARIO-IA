# LEIA PRIMEIRO — CAMPANARIO POS-REFACTOR FREEZE

> Leia este arquivo e `PROJECT_STATE.md` antes de qualquer alteracao. Considere o codigo como evidencia final. Continue somente do gate atual.

## Estado congelado

- Fundacao conversacional v1.6.1 congelada para comparacao de modelos.
- Refatoracao pre-agentes aplicada sem intencao de mudar comportamento.
- Modulos canonicos: `chat`, `response`, `model`, `storage`, `e2e`, `composition`.
- `campanario.llm.*` e compatibilidade temporaria; novo codigo nao deve depender dele.
- Todd/Morgana, RAG, internet, voz, tools e memoria cognitiva continuam BLOQUEADOS.

## Leia agora
1. `PROJECT_STATE.md`
2. `docs/current/BEHAVIORAL_REVIEW.md`
3. `docs/current/ARCHITECTURE.md`
4. `docs/current/MODEL_STRATEGY.md`
5. `docs/current/REFACTOR_MAP.md`
6. `docs/CAMPANARIO_SYSTEM_CONCEPT.md`
7. `docs/manual/README.md`

Historico integral pre-refactor: `docs/history/pre_refactor_v1_6_1/`.

## Validacao deste checkpoint

- Refatoracao offline: **225/225 testes**.
- `campanario.llm.*` mantido apenas como compatibility shim.
- Model bakeoff disponivel por `COMPARAR_MODELOS.bat`.

## Gate atual unico

**Validar a refatoracao e executar MODEL BAKEOFF com a mesma pipeline antes de qualquer novo tuning comportamental.**

1. Rodar `TESTAR_COMPORTAMENTO.bat` uma vez para confirmar que o baseline continua funcional.
2. Instalar/escolher candidatos locais que a maquina suporte (prioridade experimental: Qwen/Gemma; Llama atual como baseline).
3. Rodar `COMPARAR_MODELOS.bat` com o mesmo seed para todos.
4. Repetir a comparacao em pelo menos 3 seeds.
5. Escolher candidato por comportamento + latencia/recursos, nao apenas PASS bruto.
6. Depois executar standard e mega no vencedor.
7. Somente apos isso continuar a refatoracao final e liberar agentes.

## Regras de seguranca do projeto
- Nao hardcodar respostas para perguntas de benchmark.
- Nao misturar persona de saida com pragmatica de entrada.
- Nao preservar fontes conversacionais privadas; apenas abstracoes anonimizadas.
- Toda mudanca voltada ao usuario atualiza `docs/manual/`.
- Toda mudanca arquitetural exige ADR.
