# 31 — Fábrica Ren'Py

A Fábrica Ren'Py trabalha no fluxo **GDD-first**: primeiro produz e audita o documento pedagógico; somente unidades aprovadas podem gerar `script.rpy`, `screens.rpy` e `options.rpy`.

## Trabalhar com uma ou várias unidades

1. Abra **Fábrica Ren'Py**.
2. Clique em **Adicionar e-books** ou arraste vários arquivos para a área de upload.
3. A fila vira `UN01`, `UN02`, `UN03`... na ordem escolhida. Não existe quantidade obrigatória; uma matéria pode ter uma, duas, quatro ou mais unidades.
4. Clique em **Gerar GDDs da fila**.
5. As unidades são processadas uma por vez. Se uma reprovar, as demais continuam.

Os e-books (`.docx`, `.pdf`, `.txt`, `.md`) são entradas temporárias e não são copiados para o projeto nem para os diagnósticos.

## Contrato pedagógico por unidade

O perfil atual permanece:

- 1 pergunta principal com scores `+3`, `+1`, `0`;
- 3 trilhas A/B/C;
- 3 perguntas adicionais por trilha;
- 2 alternativas por pergunta adicional com scores `+2`, `0`;
- total de 10 perguntas e 21 alternativas.

Perguntas, alternativas, justificativas e feedbacks usam grounding source-first: o modelo seleciona IDs de trechos já extraídos do e-book e não redige a citação de evidência.

## Auditoria e autorreparo

A aba **Auditoria** mostra a unidade selecionada e agrupa problemas pelo ponto exato do GDD, por exemplo `Pergunta principal`, `A1`, `B2`, `C3` ou `Narrativa / metadados`.

Antes de reprovar, a Fábrica tenta o menor reparo possível:

1. identifica o path exato do problema;
2. corrige a pergunta/alternativa antes de regenerar uma rota inteira;
3. permite até 3 tentativas cirúrgicas por pergunta;
4. revalida scores, cardinalidade, duplicidades e evidências;
5. executa novamente a auditoria pedagógica geral e a auditoria focada de consistência das 21 alternativas.

Se o reparo não resolver, o GDD reprovado/parcial continua visível e baixável para análise, mas o código permanece bloqueado.

## GDD como fonte canônica

Cada unidade expõe `GDD.docx`, `GDD.md`, `gdd.json`, `EVIDENCE_REPORT.md` e `AUDIT_REPORT.md` quando aplicável. A seção técnica do GDD contém o mesmo `script.rpy` que será gravado na compilação; não existe uma segunda geração de IA para transformar GDD em código.

## Código Ren'Py

Na aba **Código Ren'Py**, você pode compilar uma unidade aprovada ou todas as aprovadas da fila.

- `script.rpy` é compilado deterministicamente de `gdd.json`;
- `screens.rpy` é copiado do template canônico, sem geração por IA;
- `options.rpy` parte do template canônico e altera apenas os campos mínimos previstos;
- `CODE_COMPAT_REPORT.md` faz um preflight interno de fidelidade GDD -> script, labels obrigatórios, 10 chamadas de pergunta, âncoras do `screens.rpy` e campos mínimos do `options.rpy`.

O preflight interno não substitui o lint/build do SDK Ren'Py. Imagens, Art Bible, workspace permanente e Web Build continuam fora deste checkpoint enquanto GDD e código são testados em escala com mais unidades.

## Autocorreção convergente
A Auditoria não trata mais um problema reparável como resultado final. Quando identifica uma inconsistência, a Fábrica tenta corrigir o menor elemento possível, revalida o GDD inteiro e repete o processo até não restar bloqueio. A interface mostra o histórico de correções (o que foi detectado, quantas tentativas ocorreram e o que ficou resolvido). O estado negativo final fica reservado a falhas técnicas, material insuficiente ou não convergência dentro do limite de segurança. O e-book original continua temporário e não é salvo.
