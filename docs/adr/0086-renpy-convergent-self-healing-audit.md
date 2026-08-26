# ADR 0086 — Ren'Py Factory convergent self-healing audit

## Contexto
A Fábrica já possuía reparo granular, mas ainda podia encerrar um GDD como reprovado depois de poucos retries locais ou de uma única rodada global. Em produção isso obrigava intervenção manual mesmo quando a própria auditoria já sabia identificar o path exato do problema.

## Decisão
- Erro pedagógico/estrutural reparável não é mais estado terminal.
- Cada etapa pequena pode tentar até 8 gerações automáticas antes de ser classificada como falha técnica.
- Perguntas com inconsistência podem receber até 8 reparos cirúrgicos, sempre no menor path possível.
- O GDD completo passa por até 12 ciclos globais de `validar -> reparar -> revalidar -> reauditar`.
- A auditoria geral e a auditoria focada das 21 alternativas continuam obrigatórias em cada convergência.
- Rotas que não fecham JSON continuam caindo para geração pergunta a pergunta; cada pergunta de fallback usa o retry ampliado.
- O resultado expõe `repair_history` e `repair_summary`, permitindo mostrar o que foi detectado, tentado e resolvido.
- A UI não usa mais linguagem de "reprovado" para defeitos reparáveis. Estado negativo final é reservado a falha técnica/não convergência dentro do teto de segurança.
- O e-book continua temporário e não é persistido.

## Segurança / limites
O loop não é infinito. O teto de segurança evita custo/latência sem fim quando o provider/modelo está indisponível ou incapaz de obedecer ao schema. Esse caso é apresentado como diagnóstico técnico, não como reprovação pedagógica.

## Evidência
- teste novo: a mesma pergunta permanece inválida por quatro reparos e converge na quinta tentativa;
- teste novo: fallback por pergunta recebe quatro JSONs inválidos e converge na quinta tentativa;
- testes focados da Fábrica: 43/43 PASS antes da regressão completa.
