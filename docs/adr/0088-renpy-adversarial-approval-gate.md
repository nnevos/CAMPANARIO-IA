# ADR 0088 — Ren'Py adversarial approval gate

Data: 2026-08-26

## Contexto

Testes multiunidade mostraram que o loop convergente já recuperava JSON e reparava perguntas, mas ainda podia produzir falso positivo de aprovação: uma alternativa +2 podia afirmar o oposto da própria justificativa/feedback (ex.: subdeterminação descrita como conclusão necessária; revisabilidade descrita como imutabilidade) e as auditorias amplas não detectarem.

## Decisão

Adicionar uma barreira final de aprovação em duas camadas, executada somente quando as auditorias normais consideram o GDD limpo:

1. auditoria adversarial por pergunta: 10 chamadas pequenas, uma para cada questão, confrontando texto da alternativa, score, justificativa, feedback e evidence.quote;
2. auditoria adversarial final do GDD completo, com instrução explícita para tentar provar que o documento não deve ser aprovado.

Qualquer issue volta ao mesmo reparo granular existente. Paths de choice são reduzidos à pergunta dona (ex.: `route_b.questions[2].choices[1]` -> B2), que é regenerada isoladamente e revalidada. O GDD só recebe `approved=true` quando estrutura, grounding, auditoria geral, auditoria das 21 alternativas, auditorias adversariais das 10 perguntas e auditoria adversarial final passam.

## Consequências

- aumenta o número de inferências por unidade, priorizando qualidade de produção sobre velocidade;
- reduz falso positivo de score/polaridade sem alterar o formato GDD 10x21;
- mantém source-first evidence, compilação determinística e e-book transitório;
- falhas reparáveis continuam no loop convergente; não voltam ao usuário como reprovação pedagógica.

## Validação

- `tests/test_renpy_factory.py`: 45/45 PASS;
- regressão completa: 488/488 PASS;
- `compileall`: PASS.
