# Revisão Behavioral E2E integrado — seed 1787664681

Modelo: `gemma3:12b` · suite: `agent_integrated`

Resultado: **3 PASS / 1 WARN / 0 FAIL**; **51 PASS / 2 WARN / 0 FAIL**.

## O que funcionou bem

- 5/7 turnos tiveram participação dos dois e 2/7 ficaram solo: presença compartilhada sem obrigatoriedade de dupla resposta.
- `integrated_creative_collaboration` passou com similaridade 0.094: Todd e Morgana contribuíram por ângulos diferentes.
- `integrated_useful_disagreement` passou com similaridade 0.100: discordância complementar, sem duplicação lexical relevante.
- `integrated_selective_silence` passou: pergunta factual direcionada ficou só com Morgana e `valeu` não virou painel de agentes.
- Não houve FAIL de prompt leak, encenação ou identidade.

## Problemas reais observados

### 1. Referência interpretada como convite

Nos turnos:
- `Morgana, pega o ponto do Todd...`
- `Todd, agora transforma a ressalva da Morgana...`

o segundo agente também recebeu `explicit_group_invitation`, gerando os 2 WARN de overtalk. O motivo era estrutural: `explicitly_invites_group()` considerava a presença dos dois nomes suficiente para convite de grupo.

Correção: endereçamento direto no início da frase vence a mera referência posterior ao outro nome. Convite de grupo exige marcador explícito (`os dois`, `vocês`, `Todd e Morgana`, etc.).

### 2. Simulação de speakers dentro da própria fala

Em `integrated_shared_decision` e `integrated_useful_disagreement`, Morgana gerou conteúdo como `Campanario:` / `Morgana:` e até reproduziu `Todd:` dentro da própria bubble. Isso viola speaker provenance e faz o modelo tentar encenar o painel que o sistema já controla.

Correção: Social Protocol v1 determina que cada saída contém somente a fala do speaker atual. O E2E integrado agora verifica automaticamente labels simulados.

## O que NÃO precisa mudar agora

- Não há evidência para recalibrar Personality Core.
- A complementaridade criativa e a discordância já apareceram de modo natural.
- O silêncio seletivo funcionou.
- A distribuição de participação não mostrou overtalk sistêmico fora do bug de referência/convite.

## Próxima validação

Reexecutar `TESTAR_CONVERSA_MULTIAGENTE.bat` com o Social Protocol v1. A bateria agora possui 6 cenários / 10 turnos e inclui explicitamente:
- referência ao outro sem convite;
- correção factual entre agentes sem disputa;
- ausência de labels simulados;
- não repetição/complemento;
- silêncio seletivo;
- colaboração e discordância úteis.
