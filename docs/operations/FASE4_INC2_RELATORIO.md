# CAMPANARIO-IA — Fase 4, Incremento 2: ficha factual neutra

Data: 19/11/2026. **Base:** Fase 4 Incremento 1 devidamente instalado e validado (13/13 testes no Windows do usuário).

## Escopo e princípio de evidência

**FATO VERIFICADO PELO CÓDIGO:** `chat/fact_sheet.py` contém `FactSource`, `FactClaim` e `TurnFactSheet`, dataclasses congeladas com campos imutáveis e validação de referências. `build_turn_fact_sheet` converte resultados já obtidos da biblioteca local ou da pesquisa web **sem consultar a rede, banco ou modelo**. Para toda chamada de `ChatService.stream_turn` uma ficha é construída antes de `_stream_turn_impl`, que seleciona a primeira persona. O objeto exato é entregue a todos os agentes e às contribuições grupais subsequentes.

- Ficha com status `supported` significa **trecho encontrado em fonte**, NÃO validação independente de fatos no mundo.
- Trechos de documentos importados têm nome, página, digest e referência. Os fatos são `source_assertion`, uma afirmação da fonte, não verdade comprovada.
- Resultados web carregam títulos, URLs e excertos com identificadores; pesquisa sem evidência legível não é promovida a fato.
- Em conflito, duas fontes ficam visíveis e a saída literal local pede ao usuário que escolha a referência, sem escolher unilateralmente.
- Perguntas sociais geram uma ficha `not_required` sem instruções extras, preservando o caminho conversacional anterior.
- Memória pessoal **não é** fonte factual externa. A recuperação pessoal existente permanece por agente e está fora da ficha nesse incremento.
- Ficha para documento não envia excertos potencialmente maliciosos ao modelo no prompt de geração; a resposta documental continua determinística, com citação literal, conforme Incremento 1.
- O chat não redige respostas sem agente neste incremento. Implementação de 0/1/N agentes e terceiro agente por arquivo permanecem pendentes.

## Isolamento factual no grupo

Para turnos com ficha factual ativa, o segundo agente recebe o histórico **anterior à primeira resposta** e a mesma ficha, mesmo que o usuário não use o sinalizador `independent_group_turn`. O texto livre do primeiro agente não é reenviado como evidência na instrução do segundo. Após a segunda contribuição, o turno factual não entra no ciclo automático de diálogo, evitando realimentar dados não verificados. Em conversa social comum, o fluxo anterior é preservado.

**Limite importante:** este isolamento elimina um caminho explícito de contaminação no contexto. Não comprova consistência semântica entre duas saídas de Ollama, que ainda requer teste real.

## Testes executados neste ambiente

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_fase4_inc1_biblioteca.py tests/test_fase4_inc2_ficha_neutra.py -q
```

**29 aprovados:** 13 do Incremento 1 e 16 do Incremento 2. Os testes adicionais cobrem construção sem I/O, imutabilidade, IDs de fontes, evidência web sem verdade presumida, falha/insuficiência, conflito, ausência de fontes, grupo com mesmo objeto por identidade, não propagação de um fato falso do agente 1, consulta SQLite única e banco não alterado.

Avaliação reproduzível sem modelo real:

```powershell
.\.venv\Scripts\python.exe tools/eval_fase4_inc2.py
```

**20/20** fichas neutras com trecho documental e nome da fonte corretos; **20/20** respostas documentais com trecho e fonte no fluxo integrado do chat; **0** gerações do modelo simulado para responder aos documentos. Banco temporário não foi modificado pela leitura da ficha. Os resultados são de documentos sintéticos. NÃO são taxa de acerto factual do Qwen.

Suíte integral na cópia Linux Python 3.13.5 (fora do requisito declarado `>=3.12,<3.13`): `695 passed, 30 failed, 14 warnings` em 16,13 segundos. Os **30 casos com falha são os mesmos** do relatório integral imediatamente anterior a esta última mudança; nenhum novo ID falhou. Referência Incremento 1: `679 passed, 30 failed`. Não afirmar que as 30 falhas sejam irrelevantes: incluem testes de fundamentação de memória, pesquisa web e conteúdo legado. Os logs ficam na entrega, não no projeto do usuário.

## Impacto e pendências

**Não há métricas novas com Qwen3.5:9b no Windows** para a ficha. A cobertura documental no conjunto sintético permaneceu 20/20; o ganho demonstrado neste incremento é estrutural (proveniência, imutabilidade e não contaminação interagentes), não crescimento de cobertura factual.

Ainda faltam: conexão enciclopédica Kiwix/ZIM, indexação escalável (FTS5), validação semântica de alegações, ficha agregando memória pessoal com status `USER_CLAIM`, 0/1/N agentes sem restrição por persona, terceira persona declarativa por arquivo, modo online autorizado realmente testado, teste real de grupo com Qwen/Gemma, avaliação de queda de rede e métricas de VRAM.

**Nenhum** SQLite do usuário, `.env` ativo, biblioteca real, modelo ou pasta Ollama foi lido/escrito por este incremento. Os testes utilizam somente bancos temporários e corpus sintético. Esta entrega **não autoriza** novos mecanismos de internet.

## Mudanças de código (somente Incremento 2)

- `src/campanario/chat/fact_sheet.py` — **novo**, data model e compilador neutro.
- `src/campanario/chat/service.py` — **modificado**, compila uma ficha por turno, a compartilha com os participantes, garante isolamento de resposta anterior nos turnos factuais.
- `tests/test_fase4_inc2_ficha_neutra.py` — **novo**, 16 testes.
- `tools/eval_fase4_inc2.py` — **novo**, verificação com corpus de 20 docs.

Os instaladores, o manifesto e esta documentação ficam fora da árvore de código funcional. Instalação e reversão exigem validação de SHA-256. O script de aplicação cria backup dos arquivos já existentes antes de trocar qualquer código.
