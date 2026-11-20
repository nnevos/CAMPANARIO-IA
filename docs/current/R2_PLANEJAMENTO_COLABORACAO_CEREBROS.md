# CAMPANÁRIO R2 — Planejamento tipado e colaboração limitada

**Base:** R1.1 (V8 + V9 + V9.1) do repositório **CAMPANARIO-IA**. **Disponibilidade:** experimental, `CAMPANARIO_BRAINS_V9_ENABLED=true`; não equivale ao aceite dos gates R0/R1/R2 em Windows. Data: 19/11/2026.

## 1. O que executa de verdade

`agents/router.py` escolhe **quem fala** (Morgana ou Todd). `brains/router.py` (`CapabilityRouter`) escolhe **o que executar**. Um plano `BrainPlan` contém até três `BrainStep`s imutáveis, com IDs, objetivo, motivo, escopos, contrato de entrada/saída, consulta focal e dependências apenas para etapas anteriores. Ausência de evidência ou falha não ativa automaticamente outras capacidades.

Rotas determinísticas atuais:

| Pedido | Plano | Comportamento |
|---|---|---|
| Conversa cotidiana | vazio | Nenhuma execução de cérebro ou chamada adicional ao LLM |
| Consulta explícita a documento/biblioteca | `knowledge` | Recuperação V8 com trechos e referências reais |
| Planilha/cálculo explícito | `analysis` | Cálculo V8 em CSV/XLSX/JSON, sob subprocesso |
| Documento **e** planilha no mesmo pedido | `knowledge` → `analysis` | Consulta e cálculo **independentes**, sequenciais; resultados lado a lado, com fontes e limitações |

A segunda etapa recebe **somente identificadores de evidência** das etapas anteriores concluídas e com operações registradas. Isso permite rastrear procedência, **não** implica que o cálculo tenha consumido semanticamente o documento. Texto de documentos não se torna instrução de sistema. Os dois adaptadores continuam em subprocessos de leitura da R1/R1.1. Não foram implementados novos cérebros, gravação de dados, execução de código externo nem pesquisa web irrestrita.

## 2. Consolidação factual

`brains/collaboration.py` produz um `CollaborationSnapshot` com `TurnFactSheet` e `CanonicalAnswer` neutros, antes da expressão dos agentes. Para cada execução concluída, exige identificador da execução, operações observadas, fonte tipada compatível e registros já construídos pelos conversores V9.1. Nunca usa a saída de outro agente como evidência. O estado consolidado permanece `partially_verified` em consulta documental + cálculo: o número pode ser verificado programaticamente, mas o documento **afirma** algo, não prova sua verdade externa.

Se somente uma consulta tiver êxito, mostra apenas sua evidência e indica a outra como pendente. Se nenhuma fornecer fonte utilizável, informa que a comparação não pode ser feita. Na interface opcional de depuração, `semantic_comparison_performed=false` é literal: **não existe** análise interpretativa/causal automática entre fontes neste incremento.

Uma resposta exemplificativa **calculada nos testes com arquivos sintéticos importados**: documento `protocolo.md` afirma que uma entrega depende de aprovação formal; `vendas.csv` contém valores 100 e 200, somados pela ferramenta em **300**. O Campanário apresenta os resultados separadamente; não conclui que a aprovação determina o faturamento. Se o provedor simulado falar `999`, a resposta factual canônica não incorpora esse número.

## 3. Segurança e limites

- `AgentRouter`, `AgentProfile`, talentos, memórias e prompt base de Morgana/Todd **não foram substituídos**.
- A flag `false` mantém o caminho legado da V9.1. Como na R1.1, o runtime confere `PermissionPolicy` e `library:read` quando o executor está composto com a política; um pedido/etapa não concede novos escopos.
- Máximo de três etapas, dependências acíclicas e anteriores, e orçamento global de tempo. Nenhum retry automático com efeitos colaterais.
- `trace_id` e evidências produzidas são validados; IDs antecedentes só passam adiante se uma etapa **realmente** retornou `completed` com fonte e operação. Não há transferência de instruções/documentos completos entre etapas.
- Sem Ollama adicional para roteamento neste incremento. Classificação de ambiguidade por LLM, cache por hash/TTL, investigação semântica cruzada e execução de outros cérebros **pendentes**.
- A contenção R1.1 continua **sem sandbox de sistema operacional completo no Windows**, sem bloqueio de rede ao nível do kernel, e sem homologação de `Campanario.exe` congelado. Não executar código hostil.

## 4. Topologia das três pastas e atualização

```text
C:\Users\Steam Deck\Documents\GitHub\
  CAMPANARIO-IA\          # código, UI, config local (.env), docs, launcher
  CAMPANARIO-PYTHON\      # .venv\Scripts\python.exe (Python 3.12 e dependências)
  CAMPANARIO-DATABASE\    # dados\desenvolvimento\ e dados\producao\
                         # SQLite pessoal, documentos originais, acervo/zim
```

`CAMPANARIO_DATA_DIR` configura os dados externos; `CAMPANARIO_MEMORY_ENVIRONMENT` escolhe desenvolvimento/produção; `CAMPANARIO_ZIM_DIR` define o acervo offline. A referência `interaction_library_v2.sqlite` pode ainda ficar em fallback dentro do IA até ser **copiada** com backup para `CAMPANARIO-DATABASE\dados\reference\` (P0). Não mover bancos sem procedimento de backup e verificação.

**Atualização sem PowerShell:** fechar app e serviços, guardar backup privado de IA e Database, extrair `CAMPANARIO_R2_ARQUIVOS_PARA_COPIAR.zip` *fora* da pasta IA e copiar os **arquivos internos** para a raiz IA pelo Explorador, mesclando somente os homônimos, após comparar personalizações locais. Nunca apagar a pasta IA, substituir `.env`, a `.venv` externa, SQLite, ZIM ou documentos pessoais. Se `Campanario.exe` tiver precedência, pode continuar rodando código antigo; verificar o launcher na instalação real.

**Volta segura:** definir `CAMPANARIO_BRAINS_V9_ENABLED=false` no `.env` e reiniciar; para reverter também o código, restaurar os arquivos IA do backup com o app parado. A flag não reverte migrações nem desfaz efeitos. Nenhuma migração ou dependência nova nesta R2 parcial.

## 5. O que falta para aceitar R2

Plano para mais de duas capacidades ainda não faz uma integração semântica entre outputs; o roteador não usa Ollama para ambiguidade, não há cache por revisão de fonte e não existe cobertura física Windows/desktop/mobile/voz com os três repositórios. Os gates R0 e R1 continuam abertos; nenhum cérebro invasivo foi liberado. O status da suíte local consta em `docs/operations/RESULTADOS_TESTES_R2.md`. A versão usa Python 3.13 no ambiente de teste, **não** substitui homologação com Python 3.12 da `.venv` externa.
