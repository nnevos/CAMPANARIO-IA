# CAMPANARIO-IA — Fase 3: comparação real do Qwen antes/depois da Etapa 3

**Data:** 19/11/2026. **Escopo:** somente análise de dois JSONs enviados pelo usuário; nenhuma alteração no núcleo, dados de usuário, banco SQLite ou modelos.  
**Fontes examinadas:** `baseline_offline_ollama_ANTES_ETAPA3.json` e `baseline_offline_ollama_qwen3.5_9b.json` (conservar originais).  
**Reprodutibilidade:** `tools/comparar_baselines_fase3.py`; saída `docs/evaluation/FASE3_COMPARACAO_POR_CASO.json`.

## FATO VERIFICADO — comparabilidade dos dois baselines

Ambos declaram: `mode=offline`, `engine=ollama`, `model=qwen3.5:9b`, `python=3.12.10`, plataforma Windows 11, `dataset_version=1.0.0` e `dataset_hash_sha256=dba8073d0f67423883ae45f549daf840a4194064c71f2487dd7308c4b921a886`. Ambos registram `internet_opt_in=false`, guarda de rede ativa, 74 casos e dados temporários isolados. As execuções ocorreram respectivamente às **13:46:04 UTC** e **14:43:15 UTC** do dia 19/11/2026.

Estas são evidências de **mesmo conjunto, modelo e modo declarados**, não de igualdade completa de configuração do Ollama (por exemplo, parâmetros de amostragem, cache, VRAM e temperatura não foram gravados).

## FATO VERIFICADO — métricas

| Indicador | Antes | Depois | Interpretação |
|---|---:|---:|---|
| Casos totais reportados | 74 | 74 | 50 factuais, 20 documentais, 4 cenários de grupo |
| Abstenções em 50 perguntas factuais | 25 | 48 | +23 recusas/abstenções |
| Factuais sem abstenção | 25 | 2 | Restaram apenas F038 e F041 |
| Casos factuais com resposta textual diferente | — | 24 | 23 transições a abstenção; F045 mudou o texto mantendo abstenção |
| Alegações com grounding confirmado pelo avaliador | 0 | 0 | **Não significa** que tudo esteja incorreto; não houve comprovação por fonte |
| Factuais com citação HTTP | 0 | 0 | Não havia web autorizada |
| Citações documentais verificadas | 0/20 | 0/20 | Lacuna sem melhoria |
| Respostas documentais idênticas entre baselines | — | 20/20 | Mesmo texto, comparado por SHA-256 registrado |
| Primeiro conteúdo, mediana global informada | 1.906,135 ms | 0,2 ms | Métrica dominada pelas recusas instantâneas depois |
| Primeiro conteúdo, p95 global informado | 5.634,47 ms | 3.634,01 ms | Não confundir com aceleração de inferência |
| Primeiro conteúdo entre factuais sem abstenção (mediana) | 4.225,22 ms (n=25) | 7.130,45 ms (n=2) | Amostras não equivalentes; **não** afirmar regressão causal de velocidade |
| Pico de VRAM | Não medido | Não medido | Pendente de medição no PC |

A amostra pós-Etapa 3 de geração factual contém somente F038 (9.661,47 ms) e F041 (4.599,43 ms). O texto e o SHA-256 de ambos permaneceram iguais ao resultado anterior; ainda **não há evidência/citação verificada** nesses dois casos. O aumento de abstenções não equivale a melhoria da capacidade de responder offline.

### IDs que passaram de resposta para abstenção

`F001, F002, F005, F006, F007, F010, F011, F012, F015, F016, F017, F020, F021, F022, F025, F026, F027, F030, F032, F035, F046, F047, F050`.

Caso adicional `F045`: o avaliador já marcava abstenção antes, em uma resposta cautelosa gerada pelo modelo; depois mudou para a mensagem determinística da pesquisa desativada. Por isso, há **24** mudanças de texto, mas **23** novas abstenções.

## FATO VERIFICADO — casos relevantes

- **F046 (Célia Vornacz, nome fictício do corpus):** antes, biografia detalhada sem fonte; depois, recusa. Redução de invenção nesse caso sintético.
- **F050 (O Eclipse de Pinavé, obra fictícia do corpus):** antes, autoria e enredo fabricados; depois, recusa. Redução de invenção nesse caso sintético.
- **F001 (Ada Lovelace), F002 (Alan Turing), F005 (Machado de Assis):** antes, respostas diretas sem fontes; depois, recusa por pesquisa desligada. Mais segurança formal, mas queda evidente de utilidade em perguntas sobre entidades existentes.
- **F038 (1984) e F041 (deriva continental):** continuam gerando texto sem citação/ficha factual validada, revelando que a proteção não cobre todos os formatos.
- **D001–D020 (documentos sintéticos do avaliador):** 20/20 com mesmo texto nas duas versões; 0/20 com citação e trecho exato verificados. D001, por exemplo, afirma por conta própria que o Projeto Faro usa serviços externos por padrão, sem recuperar a fonte correspondente.

**Cuidado de interpretação:** o total de identidades inventadas e de afirmações falsas não foi formalmente pontuado; os arquivos informam `known_inventions_confirmed=not_scored_requires_claim_source_annotation`. Os exemplos F046/F050 são demonstrações específicas, não uma taxa geral de alucinação.

## FATO VERIFICADO — agentes e grupo

Ambos os JSONs registram quatro cenários de grupo `G001`, `G002`, `G007`, `G006`. G001 e G002 contêm os speakers Morgana+Todd; G007 somente Morgana; G006 somente Todd. O status é `completed` antes e depois. Em todos, a distinção de perspectiva permanece `pending_manual_review` e a consistência factual `not_evaluable_without_shared_factsheet`. **Logo, grupo acessível não equivale a fatos compartilhados e validados.** Não é possível concluir que o novo código resolveu divergência entre personas.

## HIPÓTESES (a confirmar no código e em testes específicos)

1. O aumento de 25 para 48 abstenções decorre principalmente de `web_intent` ampliando a detecção factual, seguido por um fallback determinístico quando a pesquisa está desativada. É compatível com o probe do Windows (24/50 → 48/50), mas a confirmação causal exige rastrear o fluxo da chamada, não apenas resultados agregados.
2. Respostas documentais idênticas devem-se à biblioteca não integrada automaticamente ao prompt, conforme a prova estrutural anterior (`docs_source_in_model_context=0`), e não à incapacidade intrínseca do Qwen de ler os documentos.
3. Os tempos próximos de 0,2 ms refletem respostas por regras, não geração de tokens no Ollama; a amostra de dois casos restantes é insuficiente para comparar latência de geração de modelo.

## PROPOSTA — sequência de decisão para próxima implementação, sujeita a aprovação

1. **Congelar estes dois baselines**, o hash do dataset e a versão de código executada. Não sobrescrever as referências originais. Preservar os JSONs completos fora do Git se contiverem dados sensíveis; os casos usados aqui são sintéticos.
2. **Primeira correção reversível:** conectar a consulta local da biblioteca ao fluxo factual **antes** do fallback. Primeiro consulta local, depois memória elegível com proveniência, e somente então internet opcional autorizada. Não baixar enciclopédia ainda como pré-requisito.
3. **Contrato de fatos neutro:** produzir ficha factual única por turno, com proveniência de trecho/arquivo; retornos sem fonte ficam explicitamente sem evidência. A mesma ficha deve atender chat neutro e todos os agentes, sem passar falas não verificadas entre eles como novas fontes.
4. **Testes-gate:** repetir corpus antes/depois no Windows, exigir citações corretas nos 20 documentos sintéticos, zero identidades fabricadas nos casos fictícios e registrar número de recusas sobre entidades cobertas pela base local. Comparar latência só entre casos equivalentes, distinguindo fallback e inferência.
5. **Etapas pendentes da Fase 3:** testes de grupo com juízo semântico, correção e terceiro perfil configurável; internet realmente autorizada sob consentimento explícito; queda real de rede; comparação Gemma opcional; VRAM. Não marcar essas metas como realizadas.

## Situação

**Baseline OFFLINE real registrado e comparável: SIM.**  
**Fase 3 integralmente homologada (offline + online autorizado + semântica em grupo): NÃO.**  
**Fase 4 implementada: NÃO.**  

É defensável usar o baseline para planejar o **primeiro passo pequeno da Fase 4**, após aprovação do usuário, enquanto metas ainda não medidas permanecem abertas; não é defensável declarar o Campanario factual/offline já funcional.
