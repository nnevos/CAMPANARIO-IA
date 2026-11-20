# CAMPANARIO-IA — Plano de execução aprovado somente após Fase 3

**Estado:** plano, NÃO execução. **Regra de transição:** Fase 2 (design) -> aprovação do usuário -> Fase 3 (benchmark BASELINE ANTES de mudanças) -> aprovação -> Fase 4 (alterações). É proibido mexer nos bancos reais, modelos, histórico de chat ou índices de produção durante protótipos.

## Método e critérios fixos

1. Todos os experimentos em **dados sintéticos ou cópias de leitura**; nenhum comando de `migration`, `ollama pull`, instalador Kiwix ou internet rodado automaticamente.
2. Uma alteração por passo, com **feature flag desativada por padrão durante transição** e rollback testado. Nunca deletar a rota antiga antes da nova vencer a avaliação.
3. A cada passo da Fase 4: rodar corpus fixo em `offline` **e** `online` quando ambiente permitir, e suíte geral; comparar com resultados de mesma máquina, Python/modelo/dados/versão. Se houver regressão no núcleo factual ou erro novo crítico, **interromper e reverter**. Falhas antigas são registradas com IDs e stacks, não ignoradas.
4. A meta `identidades inventadas = 0` vale para conjunto de avaliação; 1 caso novo de invenção, vazamento de dado, consulta externa sem autorização ou alteração de memória sem permissão **bloqueia** o passo. Recusas indevidas e inconsistências de fonte devem melhorar, não piorar. Latência é comparada como p50/p95 sem prometer valores antes de medir.
5. O estado de rede (`offline`, `online_autorizado`, `online_negado`, `network_error`) é parte do caso; testes reproduzíveis devem simular queda física/lógica e verificar **zero** requisições externas quando offline.

## Fase 3 — avaliação PRIMEIRO, sem alterar produção

- **3.1 Corpus `eval/v1`:** ~50 perguntas factuais (pessoas famosas/pouco conhecidas, 2+ homônimos, obras, conceitos, nomes inexistentes, paráfrases “quem foi”, “me fala sobre”, “conhece”, “qual a história”), ~20 de biblioteca com *citação exata de trecho/página*, cenários grupo/terceiro agente/sem agente/correção/rede caindo. Dados de ouro incluem coleção e snapshot de ZIM; sem instalar ZIM, marcar cenário `blocked_missing_corpus`, não inventar cobertura.
- **3.2 Dois modos obrigatórios:** `offline` (desativa tráfego externo mesmo com máquina conectada) e `online` (somente em ambiente de teste explicitamente autorizado). Guardar respostas e fontes brutas para auditoria. Não substituir ausência de conexão por resultado fabricado.
- **3.3 Grupo:** uma ficha de fatos; 1 vs 2 agentes; sem sintese salvo pedido; divergência de recomendação não é divergência factual; fala errada de A não pode contaminar B; Todd mantém empatia no cotidiano; nenhum repete duas recusas idênticas; medir latência e fontes.
- **3.4 Modos adicionais:** `system` direto sem persona, inclusão de terceiro perfil por **apenas arquivo**, troca entre perfis com os mesmos fatos e citações, permissão global de ferramenta prevalece, memória privada nunca vaza para outra persona.
- **3.5 Comparativo Qwen/Gemma:** fixar versões/tag/digest, quantização, `num_ctx`, hardware, modo thinking, temperatura, política de consulta A/B/C, corpus, fontes e permissão. Rodar sequencialmente, registrar VRAM, tokens, primeira resposta segura, duração total; escolher por evidência. **Sem modelo instalado não há baseline de geração.**
- **3.6 Baseline da suíte:** conservar registro de Fase 1 `655 passed / 30 failed` em Linux/Python 3.13.5 como referência histórica, **não** usar como comparação definitiva com Windows/Python 3.12. Gerar novo baseline antes de mudar código na máquina-alvo.

**Contrato do comando proposto, que NÃO existe ainda:**

```powershell
# Apenas depois de criar o runner na Fase 3 (NÃO executar agora):
python -m campanario.eval --dataset eval/v1 --mode offline --model qwen3.5:9b --report reports/baseline_qwen_offline.json
python -m campanario.eval --dataset eval/v1 --mode online --model qwen3.5:9b --report reports/baseline_qwen_online.json
```

## Fase 4 — alterações pequenas, em ordem reversível

| Passo | Mudança delimitada | Teste de aceitação | Como reverter sem perda de dados |
|---|---|---|---|
| **4.0 Segurança de rede** | Corrigir default web em `config.py`; `OfflinePolicy` central impede HTTP externo; logging de bloqueios | Offline não envia rede nem na ausência de `.env`; casos legado íntegros | Reverter flag/commit; manter default seguro |
| **4.1 Núcleo neutro** | `FactSheet` dataclass, `FactService` com status e citações; API neutra experimental **sem persona** e sem escrever dados | Com fonte retorna excerto/citação; sem fonte retorna `insufficient`; chat antigo não alterado | Desativar rota nova/flag |
| **4.2 Biblioteca** | Adaptar `library.search` já existente e acrescentar FTS5 em tabela/DB de **teste**, com fallback lexical e chunk/page offset | 20 docs com citações, remoção/reimportação e offline; não alterar SQLite real | Desativar FTS5 e retornar ao método anterior; tabela adicional não destrutiva |
| **4.3 Kiwix local** | Adaptador opcional `ZimKnowledgeSource`, aponta só a `127.0.0.1`/arquivo ZIM escolhido; não baixar conteúdo | Quem é X responde com ZIM instalado; Kiwix ausente degrada honestamente | Flag desliga adaptador; ZIM não é modificado |
| **4.4 Ficha única por turno** | Preflight de fontes local → memória → web opt-in; context snapshot compartilhado; persona não chama fonte separada | Grupo recebe mesmos fact_ids/source_ids; zero leitura web offline; correção invalida ficha | Flag mantém rota anterior em ambiente de teste |
| **4.5 Guardas G2 + evidência** | Auditoria por fact_ids, proveniência e extração; impedir persistir afirmação pessoal sem fonte | Fechar falhas de G2 relevantes; nenhum fato novo de resposta vira fonte | Reverter guardado novo isoladamente; manter failsafes anteriores |
| **4.6 Perfil declarativo e N agentes** | Loader JSON+validador, conversor dos perfis legados, roteamento genérico; suportar chat `system` sem agente | Terceiro só por JSON, sem mudar código; dois personagens padrão preservados; 0/1/N | Registry antigo atrás de flag até comparação |
| **4.7 Apresentação e dessacoplamento** | Remover persona de `chat/knowledge.py`, unificar neutral uncertainty e mover estilo para perfis; não gerar síntese automática | Mesmos fatos em Todd/Morgana/terceiro/neutro; empiria de ângulos, empatia e ausência de repetição | Flag antiga no período de transição |
| **4.8 Internet/caching consciente** | Web somente após insuficiência local ou pedido explícito; staging de `web.save` + confirmação | Queda de rede conserva locais, sem ingestão silenciosa; permissão revogável | Desligar web e staging; conteúdo local permanece |
| **4.9 Consolidação** | Retirar caminhos redundantes apenas após bateria e auditoria de chamadas; documentação e release | Suíte sem regressão crítica e baseline Fase 3 melhorado | Tag anterior + restore de backup se migration real ocorreu |

**Observações:** passos 4.6/4.7 requerem compatibilidade da UI/API, e devem ter testes de contrato; não quebrar `chat_sessions.primary_agent_id` nem `messages.agent_id`. Índices devem ficar em banco próprio ou em migração aditiva; não recriar memórias existentes. Revisar as 30 falhas da Fase 1 por severidade e ajustar a lista quando um teste for realmente obsoleto.

## Decisões de abandono da tentativa

- **Tool calling** será descartado como roteador principal se perder qualquer consulta factual do conjunto ou solicitar web sem opt-in, ainda que pareça mais natural.
- **FTS5** ficará opcional se a migração ou o índice piorar recall vs `substring` nos testes de documentos.
- **Kiwix-serve** pode ser trocado por libzim se interface local se mostrar instável no Windows; manter a API `KnowledgeSource` para evitar refatorar o resto.
- **Paralelismo de agentes** adiado até prova de VRAM livre e benefício em p95.
- **LLM como verificador factual universal** não é autoridade: precisa rastreabilidade por trecho e testes de invenção; com falha de confiança, o sistema deve abster.

## Critérios de saída para Fase 4 (medidos na Fase 3)

- Fonte neutra sem agente funcional offline com citação; ausência honesta sem busca web; grupo 2 e 3 agentes na mesma ficha; perfil adicional sem tocar código; 0 identidade inventada no corpus; 0 egress web offline; 0 regressão crítica em memória/permissão/contratos; nenhuma síntese não solicitada. Métricas quantitativas (recusa indevida, cobertura, p50/p95, VRAM) comparadas ao baseline na **mesma máquina**.

**Necessidades para execução futura, não pergunta/bloqueio desta fase:** Windows com Python 3.12, Ollama local e modelos previamente disponíveis, conjunto ZIM autorizado, backup dos bancos, dados de teste anonimizados. Sem esses recursos, a Fase 3 pode produzir benchmark estático e testes com stubs, mas **não** se declarar homologação física.
