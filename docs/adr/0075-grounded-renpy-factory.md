# ADR 0075 — Grounded Ren'Py Factory

## Status
Aceito como workstream de produção; não altera o gate F5/F6 do runtime pessoal.

## Contexto
A produção existente usa um fluxo e-book → GDD → código Ren'Py → template e prompts visuais. O processo manual dependia de duas gerações livres por LLM, criando risco de drift factual e de divergência entre GDD e `script.rpy`.

## Decisão
Criar `campanario.renpy_factory` e um menu web separado **Fábrica Ren'Py**.

O e-book é extraído localmente (DOCX/PDF/TXT/MD). A única chamada generativa produz um GDD JSON estruturado. Cada elemento pedagógico deve trazer `evidence.quote` literal do e-book. O validador fail-closed rejeita qualquer item cuja evidência não possa ser encontrada no corpus extraído.

Após validação, GDD → Ren'Py é determinístico: não há segunda chamada de LLM. O perfil inicial é `legacy_un01_10x21`, alinhado ao GDD UN01 de referência: 1 principal + 9 adicionais = 10 perguntas / 21 alternativas.

A saída contém GDD, JSON, relatório de evidências, prompts visuais e projeto Ren'Py com placeholders neutros.

## Consequências
- reduz invenção factual na conversão de material didático em jogo;
- preserva rastreabilidade por alternativa/feedback;
- mantém narrativa fictícia separada de fatos pedagógicos;
- inconsistências de evidência interrompem a geração;
- novos perfis estruturais devem ser adicionados explicitamente, sem alterar silenciosamente o perfil legado.
