# Fase 3 — Comandos, revisão e critérios de progresso

## Um comando para dois modos

Na raiz do projeto, com Python 3.12 e suas dependências:

```powershell
py -3.12 tools/eval_fase3.py --mode both --engine probe
```

**Probe** observa caminhos com stub; não mede precisão da IA. Use `--engine ollama --model qwen3.5:9b` (e depois `gemma3:12b`) para respostas reais. Ollama deve estar ativo e ter o modelo previamente instalado. O runner não instala nem faz download de nada.

## Acesso à internet

Padrão: web pública **desabilitada**, nos dois modos. O teste online real exige opt-in via `--allow-web`, sem afetar o modo offline. A ferramenta usa temporários próprios. Logs da tentativa de primeira falha e do baseline histórico vêm no ZIP.

## Registro humano (após o baseline real)

Preencha uma cópia do `MODELO_REVISAO_HUMANA_FASE3.csv`, não o original versionado. Para cada caso, registre fontes efetivamente lidas, excertos, identidade inventada (1/0), recusa indevida (1/0), citação correta (1/0), e consistência/ângulo para grupo. Ausência de informação deve contar como abstenção honesta, não como erro; não verificar nomes pelo conhecimento paramétrico do LLM. A meta de **zero identidades inventadas** só pode ser declarada após comparar as afirmações com as fontes; um `http` na resposta não comprova citação válida.

| Métrica | Definição | Critério proposto |
|---|---|---|
| Identidades inventadas | Identidades positivas não sustentadas por trecho | **0** no corpus revisado |
| Recusas indevidas | Abstenção apesar de evidência suficiente encontrada no acervo local disponível | Diminuir versus baseline no mesmo acervo |
| Cobertura offline | Consultas respondidas com citação verificável / consultas com fontes locais elegíveis | Crescente; não punir acervo ausente |
| Citações corretas | Afirmação vinculada a documento/URL local acessível + trecho realmente presente | **100% das afirmações factuais** |
| Consistência entre agentes | Mesmos `fact_id`/`source_id` das afirmações objetivas | **100%** |
| Distinção de ângulo | Dois analistas ofereceram raciocínio diferente sem mudar fatos | Revisão humana, sem exigir discordância teatral |
| Tempo até saída validada | `first_visible_ms` por turno, p50/p95 em máquina-alvo | Medir 1 vs 2 agentes com VRAM/quantização anotadas |
| Queda de internet | Resta fonte local; não inventa; sai do estado de busca | Teste de rede real controlado, ainda pendente |

A Fase 4 deve executar a avaliação em ambos os modos após **cada alteração** e comparar registros **da mesma máquina, modelo, acervo e configurações**. Resultados com corpus ou condições diferentes não são comparáveis diretamente.
