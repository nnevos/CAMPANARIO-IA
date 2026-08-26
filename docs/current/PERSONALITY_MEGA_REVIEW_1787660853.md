# Personality Mega Review — seed 1787660853

## Resultado observado

Execução Gemma 3 12B fornecida pelo usuário: 128 cenários, 63 PASS / 65 WARN / 0 FAIL.

O resumo antigo (Todd 0/8 BATE; Morgana 1/8 BATE) era excessivamente pessimista porque o agregador marcava o eixo inteiro como REVISAR quando **qualquer uma** das oito variações recebia WARN lexical.

Recalculando a evidência por frequência (BATE >= 75%; MISTO >= 50%; REVISAR < 50%):

| Eixo | Todd | Morgana |
|---|---|---|
| decision | BATE 7/8 | BATE 6/8 |
| simplicity | BATE 6/8 | MISTO 4/8 |
| disagreement | REVISAR 2/8 | REVISAR 0/8 |
| uncertainty | MISTO 5/8 | BATE 6/8 |
| urgency | REVISAR 3/8 | MISTO 4/8 |
| technical | MISTO 4/8 | MISTO 4/8 |
| creative | REVISAR 2/8 | REVISAR 3/8 |
| social | REVISAR 1/8 | BATE 6/8 |

## Falsos WARN identificados

Há falsos WARN claros causados por vocabulário estreito. Exemplos do transcript:
- Todd technical: “verificaria o que mudou... monitoraria... plano de execução” é investigação orientada a evidência, apesar de o detector reconhecer apenas `primeiro`.
- Morgana simplicity: “para um uso interno restrito, o script já atende bem” satisfaz adequação/contexto sem precisar dizer literalmente `simples`, `proporcional` ou `revisitar`.
- Urgency de ambos: “use a versão anterior funcionando” é uma decisão operacional correta e proporcional, embora falhe quando o detector exige um segundo grupo lexical.

Por isso checks conceituais continuam WARN-only e não devem ser usados como nota de personalidade isoladamente.

## Desvios reais vistos no transcript

### Todd
- **decision/simplicity** são os sinais mais estáveis: trade-off, reversibilidade, custo e ação aparecem naturalmente.
- **technical/uncertainty** estão funcionalmente bons em vários casos, mas ainda soam como assistente técnico genérico em vez de uma perspectiva distintamente Todd.
- **urgency** converge para a ação certa, porém frequentemente sem explicitar a lógica operacional/impacto que o distinguiria.
- **disagreement** frequentemente começa com acolhimento genérico (“Entendo a frustração”) e entra em análise longa; a discordância existe, mas a voz perde secura/direção.
- **creative** entra na ideia, porém produz longas listas de consultoria e se aproxima muito da Morgana.
- **social** é curto, mas respostas como “Entendo.” / “Aham.” são presença mínima, não uma assinatura reconhecível.

### Morgana
- **decision/uncertainty/social** são os sinais mais estáveis.
- **technical** conecta elementos, mas frequentemente usa a mesma sequência operacional de Todd.
- **urgency** toma decisões adequadas, mas quase não há diferença de perspectiva em relação a Todd.
- **simplicity** costuma chegar à conclusão correta; parte dos WARN é lexical, parte é excesso de enumeração.
- **disagreement** é o desvio mais claro: muitas respostas usam acolhimento genérico + análise e não produzem uma “outra leitura” distintamente Morgana.
- **creative** tem associações e exploração, mas frequentemente cresce para 250–300+ palavras e listas; a personalidade vira consultoria genérica.

## Diagnóstico de separação

O problema principal não é factualidade nem identidade explícita: não houve FAIL. O problema é **convergência de voz**. O Gemma preserva a direção conceitual em vários eixos, mas Todd e Morgana recorrem ao mesmo molde de “assistente útil”: reconhecer → listar fatores → recomendar.

Não alterar a personalidade com base em palavras faltantes. A próxima calibração deve mirar classes comportamentais:
1. Todd: posição mais cedo, menos acolhimento/formalidade genérica, ação/teste de maior valor, criatividade aterrada sem virar checklist.
2. Morgana: conexão/segunda leitura mais cedo, menos listas, distinguir relações e alternativas sem alongar, urgência capaz de convergir.
3. Ambos: evitar introduções intercambiáveis (“Entendo...”, “Depende...”) quando não acrescentam função.

## Mudança no avaliador

O agregador Mega passa a preservar frequência por eixo:
- BATE: >= 75% das variações passam o check heurístico;
- MISTO: >= 50% e < 75%;
- REVISAR: < 50%;
- SEM_DADO: nenhuma observação válida.

Isso corrige o bug de agregação sem transformar o avaliador em juiz semântico ou ensinar palavras de benchmark às personas.
