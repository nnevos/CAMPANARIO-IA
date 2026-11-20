# Campanário — Integração da Biblioteca Conversacional V2

## Implementado

- Banco SQLite V2 preservado em `data/interaction_library_v2.sqlite` (186 cenários).
- Recuperador de referências em `src/campanario/agents/interaction_library.py`.
- Integração no fluxo de montagem de contexto de `src/campanario/chat/service.py`.
- Consulta somente leitura e somente cenários marcados `candidate` na tabela `scenario_metadata`.
- Os exemplos são **simulações**: não são fatos, memórias, experiências vividas ou instruções superiores.
- Seleção lexical por contexto, com no máximo dois exemplos curtos por resposta; sem dependências novas.
- Sem interferência no modo de baixa latência.
- Modo Patrulha excluído da consulta automática do chat comum; requer integração explícita futura com o estado operacional.
- Desativação: `CAMPANARIO_INTERACTION_EXAMPLES=0`.
- Caminho alternativo do banco: `CAMPANARIO_INTERACTION_DB=/caminho/arquivo.sqlite`.

## Verificação

`PYTHONPATH=src python -m pytest -q tests/test_interaction_library.py tests/test_personality_application.py`

Resultado local: **8 testes passaram**. Não foi executada uma sessão completa com Ollama, voz ou interface Windows.

## Próximas melhorias

- Ligar `patrol_mode` ao estado operacional real do Modo Patrulha.
- Avaliar relevância dos exemplos com testes de conversas reais; substituir busca lexical por busca semântica somente se houver ganho medido.
- Não gravar automaticamente preferências/experiências a partir de exemplos simulados.

## Privacidade do pacote

O `.env` e o diretório `.git` do ZIP original foram excluídos deste pacote para evitar compartilhar segredos e histórico de repositório. O arquivo `.env.example` foi mantido.
