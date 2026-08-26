# ADR 0085 — Ren'Py multiunit queue, audit UX e code preflight

Data: 2026-08-26

## Contexto

A Fábrica GDD-first já conseguia gerar, auditar, autorreparar e compilar uma unidade por vez. O próximo teste real precisa usar várias unidades na mesma sessão sem reintroduzir o pipeline antigo de imagem/build, e a auditoria precisava deixar evidente qual problema pertence a qual pergunta/unidade.

## Decisão

1. A UI aceita quantidade livre de e-books em seleção múltipla e os apresenta como UN01, UN02, UN03... na ordem local da fila.
2. A fila é processada sequencialmente. Cada upload continua transitório e cada unidade recebe um run independente; uma reprovação não interrompe as unidades seguintes.
3. A auditoria é apresentada por unidade e agrupada por path (pergunta principal, A1/B2/C3, metadata), usando itens estruturados retornados pelo serviço.
4. O autorreparo continua no menor escopo disponível: pergunta/choice antes de rota, até 3 tentativas por pergunta, sempre seguido de validação estrutural, grounding e reauditoria completa.
5. A compilação permanece determinística e ganha preflight local antes de liberar o pacote: fidelidade exata GDD -> script, labels obrigatórios, exatamente 10 call_screen de perguntas, âncoras do screens.rpy canônico e campos mínimos do options.rpy.
6. `CODE_COMPAT_REPORT.md` é gravado em cada run compilado. O preflight não substitui lint/build do SDK Ren'Py.
7. Imagens, Art Bible, workspace permanente e Web Build continuam fora deste checkpoint.

## Consequências

- A mesma sessão da Fábrica pode testar uma matéria com 1 ou N unidades sem obrigatoriedade de quatro.
- O usuário consegue comparar rapidamente quais unidades passaram, falharam ou ficaram parciais.
- Falhas de uma unidade não apagam nem bloqueiam as demais.
- O código não é liberado quando diverge do GDD ou perde contratos mínimos do template.
- E-books originais continuam não persistidos.

## Evidência

- `tests/test_renpy_factory.py`: 41/41 PASS.
- regressão completa: 484/484 PASS.
- `python -m compileall -q src tests`: PASS.
- JavaScript da nova UI: `node --check`: PASS.

## Gate global

Nenhuma mudança: F5 permanece pausado/aberto e F6 bloqueado.
