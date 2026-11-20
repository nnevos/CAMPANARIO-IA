# Campanário — Preferências persistentes e revisáveis (V3)

## Alterações
- `src/campanario/agents/living_preferences.py`: identifica declarações explícitas de preferências em respostas finais dos próprios agentes e registra no repositório de experiências SQLite existente.
- `src/campanario/chat/service.py`: depois de salvar uma resposta do agente, observa possíveis preferências; antes de gerar a próxima resposta, recupera apenas preferências ativas do agente atual.
- `src/campanario/agents/morgana.py` e `todd.py`: contrato atualizado para permitir gostos persistentes e revisáveis sem impor gostos iniciais.
- `tests/test_living_preferences.py`: testes de extração, separação por agente, continuidade após reinício e revisão.

## Comportamento
- Exemplo: Morgana diz `Eu gosto de literatura de mistério.`; o sistema registra uma preferência de Morgana.
- Em sessões posteriores, ela pode usar essa preferência quando relevante; não precisa mencioná-la constantemente.
- Se depois disser `Não gosto de literatura de mistério.`, o registro anterior é marcado como `superseded` e um novo registro fica ativo.
- A origem é registrada como `agent_inference` com vínculo ao identificador da mensagem e da sessão; não se trata de um fato externo ou prova de consciência.
- A Bíblia de Identidade e o `PersonalityCore` continuam protegidos. O registro de desenvolvimento com aprovação manual continua disponível separadamente.

## Limites e próximos passos
- A detecção automática é conservadora e baseada em frases explícitas em português; não detecta todos os gostos implícitos e pode exigir refinamento para frases ambíguas.
- O mecanismo não cria preferências a partir dos diálogos simulados nem copia as preferências do usuário.
- A memória é persistida no banco de experiências configurado no runtime. O arquivo ZIP não contém as memórias pessoais do seu computador; elas permanecem no banco local existente.
- A interface de gerenciamento visual das preferências não foi adicionada nesta versão. Para uma versão futura, recomenda-se uma tela de inspeção, revisão e exclusão por agente.
- Não foi possível executar Ollama e a interface Windows aqui; a validação foi feita por testes automatizados Python.

## Testes
`PYTHONPATH=src pytest -q tests/test_living_preferences.py tests/test_fase4_inc3b_identidade_evolutiva.py`

Resultado: 20 testes aprovados.
