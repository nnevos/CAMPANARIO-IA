# Correcao: chamada curta dos agentes sem pesquisa factual

## Sintoma real observado no Windows

- Usuario: `oie` -> Morgana conversa normalmente.
- Usuario: `todd?` -> Todd foi selecionado, mas respondeu que a pesquisa estava desligada.

## Causa no codigo

`AgentRouter` ja reconhecia `todd?` como chamada ao agente. Entretanto,
`web_intent.direct_decision()` tambem classificava qualquer nome isolado
seguido de `?` como uma entidade externa que exigiria verificacao. O guard
factual prevalecia sobre a conversa mesmo quando a entidade era um agente
registrado na propria instalacao.

## Solucao localizada

- `agents/addressing.py`: `standalone_wake_target()` identifica apenas uma
  chamada completa (e cumprimentos simples) para o nome/id de agente
  registrado ou para Campanario como sistema. Nao usa catalogo de pessoas.
- `chat/service.py`: chamadas reconhecidas nao acionam biblioteca, busca web,
  planejamento ou ficha de fatos insuficiente. O agente responde pelo modelo
  com uma indicacao conversacional breve, sem alegar acesso a fontes.
- Perguntas factuais mais longas dirigidas a agentes, como `Todd, quem foi
  Ada Lovelace?`, NAO recebem isencao de evidencia. `/pesquisar Todd` tambem
  continua sendo comando de pesquisa.
- Nao ha alteracao de roteamento, identidade central, memoria ou SQLite.

## Limites e testes

Testes novos reproduzem o dialogo exato, chamadas com acentos/espacos, modo
web auto ligado, ausencia de consulta a SQLite, agente atual selecionado e
protecoes em perguntas factuais. Eles usam um provider simulado; a geracao
com Qwen real deve ser observada pelo usuario depois da instalacao.

Resultados no ambiente de desenvolvimento:
- 23/23 testes novos aprovados.
- Suite integral: 864 passed, 30 failed; as 30 falhas sao as mesmas do baseline
  historico antes do patch.

Nenhum dado pessoal nem modelo foi inspecionado ou modificado.
