# ADR-0008 — Camada comportamental antes dos agentes completos

**Status:** Aceito em 2026-08-24.

## Contexto

A validação real do Context Manager source-aware passou: fatos antigos do USER foram recuperados corretamente após a janela recente e após reinício. O mesmo teste expôs um problema independente de memória: o modelo base produziu erros factuais, mistura de idiomas, perguntas de acompanhamento mecânicas e a frase artificial "Sua informação de fato é...".

Os exemplos de diálogo e backgrounds de Morgana/Todd já definem uma direção de personalidade, mas ativar dois agentes completos agora misturaria roteamento, personalidade, memória e factualidade numa única mudança difícil de medir.

## Decisão

Adicionar uma camada `BehaviorContextManager` que decora o `ContextManager` existente e injeta uma única instrução `system` de comportamento balanceado. Quando já existe uma mensagem `system` de contexto persistido, as duas instruções são combinadas em uma única mensagem para manter uma fronteira clara.

A camada define somente propriedades transversais:
- naturalidade e idioma consistente;
- uso natural do contexto persistido, sem expor campos internos;
- distinção entre fato, lembrança, inferência, opinião e criação;
- proibição de alegar ferramentas/ações não executadas;
- incerteza explícita quando faltar base;
- autonomia do usuário e iniciativa sem autoritarismo.

Morgana e Todd permanecem referências, não agentes ativos. Seus backgrounds completos ficam em `docs/reference/personas/`.

## Consequências

- a seleção/sumarização de histórico permanece intacta;
- não há migration;
- não há segunda chamada de modelo por resposta;
- a mudança é reversível removendo o decorator no bootstrap;
- factualidade ainda depende da capacidade do modelo local; este incremento reduz incentivo à invenção, mas não substitui RAG/web/validação futura.
