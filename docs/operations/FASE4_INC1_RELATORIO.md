# CAMPANARIO-IA — Fase 4, incremento 1: biblioteca local no chat

Data: 2026-11-19. Referência de código: **Etapa 3 acumulada**, verificada via SHA-256.

## FATO VERIFICADO

- `src/campanario/utilities/service.py` já guarda importações TXT/MD/PDF na tabela SQLite `documents` (metadados, hash e JSON por página); **não foi alterado**.
- O novo `ReadOnlyLocalLibrary` abre **o mesmo** `utilidades.sqlite3` no modo SQLite `mode=ro`, com `PRAGMA query_only=ON`, sem criar tabelas, importar, converter ou atualizar os arquivos dos usuários.
- A raiz do banco é a mesma de `utilities/integration.py`: `settings.data_dir / settings.memory_environment / utilidades / utilidades.sqlite3`. É injetada pela composição oficial de runtime (`build_chat_stack`). O chat criado manualmente sem injeção conserva o comportamento anterior.
- `ChatService.stream_turn()` agora tenta uma leitura local uma vez por turno **antes** de chegar à decisão de pesquisa web ou à recusa factual. Se houver um trecho suficientemente correspondente, usa uma ficha imutável `LocalFactSheet`, compartilhada com os agentes.
- O trecho apresentado é copiado literalmente da base importada e contém **nome de arquivo, página quando houver e prefixo SHA-256**. A extração não converte conteúdo do documento em instruções para modelos e não chama LLM para inventar uma paráfrase. Um trecho atribuído é evidência do conteúdo do documento, não verificação da verdade externa.
- Quando duas fontes diferentes dão respostas de correspondência comparável e conflitantes, o sistema mostra os dois trechos e pede que o usuário escolha; não decide arbitrariamente.
- Quando não há correspondência, os caminhos antigos permanecem; perguntas de identificação cobertas pelo guard ainda se abstêm se não houver evidências. **Não significa** que toda pergunta genérica sem fonte seja impedida de gerar texto.
- O padrão `Settings.web_auto_search` mudou de `True` para `False`. Se o `.env` real disser `CAMPANARIO_WEB_AUTO_SEARCH=true`, esse valor explícito **não é sobrescrito** e a pesquisa web opcional continua disponível na arquitetura legada.

## Evidências dos testes (Linux, Python 3.13.5; Python 3.12 do Windows pendente)

| Medição | Fase 3, Etapa 3 antes | Fase 4 incremento 1, teste sintético |
|---|---:|---:|
| 20 perguntas sobre 5 documentos importados | 0/20 citações verificadas no chat | **20/20 trechos literais e nomes de fonte** |
| Chamadas de LLM nas 20 respostas documentais | O modelo improvisava respostas | **0 (provedor simulado instrumentado)** |
| Consulta web durante benchmark novo | Não aplicável | **Nenhuma (socket externo bloqueado)** |
| Duas vozes com mesma evidência | Sem ficha neutra | **Mesma `LocalFactSheet` para o turno testado** |
| Testes novos | Não existem | **13 passaram** |
| Suíte completa pós-mudança | Fase 1: 655 passaram / 30 falharam | **679 passaram / 30 falharam**, 14 avisos |

**Controle de regressão:** os IDs das 30 falhas da suíte nova são exatamente os mesmos da Fase 1, após comparação ordenada dos logs. A diferença de 24 testes aprovados decorre de 11 testes do avaliador da Fase 3 sobrepostos e 13 novos testes da Fase 4. Os testes direcionados antigos tiveram 112 aprovações e 8 falhas tanto na cópia Etapa 3 quanto na cópia modificada; a cópia da Fase 4 adicionou 13 aprovações.

## Limitações / hipóteses (não afirmar como implementado)

- **NÃO há Kiwix/ZIM**; se o usuário não importou conteúdos sobre Ada Lovelace/Machado de Assis, a proteção factual ainda se recusa a responder. Não reportar melhoria de cobertura enciclopédica sem instalar ZIM.
- A consulta lexical tem teto de 300 documentos, 500 mil caracteres por documento e 4 milhões de caracteres por varredura. Não há FTS5, chunker semântico, índice incremental ou embeddings neste incremento; uma biblioteca grande requer Fase 4 incremento seguinte.
- A ficha factual é **local, de um excerto por pergunta (ou 2 em conflito)**, não é o `FactService` geral de múltiplas fontes, memória, Kiwix e web. A independência dos perfis e o modo 0 agentes **não** foram implementados neste incremento.
- A frase citada pode não responder exatamente ao aspecto implícito de perguntas vagas; inspeção humana continua necessária. Fontes contraditórias com escores muito diferentes podem não ser sinalizadas.
- A ausência de uma correspondência local em perguntas não identificadas pela guarda antiga não prova que a resposta do modelo será segura. Melhorias desse tipo exigem a etapa de factualidade geral, sem empilhar regex.
- Não foi testado no Windows com Python 3.12, Ollama real, SQLite de produção, CUDA/VRAM ou queda real de rede; não relatar falsos números de latência ou factualidade.
- `tools/eval_fase3.py` continua sendo o **baseline antigo** e cria o chat sem injetar a nova biblioteca. Para avaliar este incremento execute `tools/eval_fase4_inc1.py`, que cria a integração explicitamente e testa as 20 perguntas documentais.

## Próximo incremento proposto (não implementado)

Completar a ficha factual neutra de várias fontes, integrar livro/ZIM local, evoluir recuperação de trechos com índice FTS5 opcional, dar aos agentes interpretação distinta sob a mesma evidência e avaliar recusa e tempo em Qwen3.5:9b real no Windows. Iniciar somente após validação deste ZIP.
