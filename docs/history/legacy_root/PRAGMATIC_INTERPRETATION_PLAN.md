# Plano — Pragmatic Input Understanding

## Estado

**v1 integrada ao runtime** na Conversational v1.5, apos evidencia manual de que continuation apenas por prompt/listas nao era suficiente.

## Problema

Comunicacao humana informal nao e apenas escolha entre `social`, `factual` ou `continuation`. A mesma forma textual pode reagir, concordar, corrigir a anterior, encerrar assunto, pensar em voz alta, pedir opiniao ou combinar varias funcoes. Pontuacao e significado de dicionario nao bastam.

## Objetivo

Interpretar o que a mensagem esta fazendo na conversa antes da persona responder, sem:

- selecionar persona;
- decidir verdade/factualidade;
- imitar o estilo do usuario;
- criar memoria pessoal;
- ativar ferramentas;
- depender de uma lista de respostas prontas.

## Runtime v1

Arquivo: `src/campanario/chat/pragmatics.py`.

Contratos:
- `PragmaticAct`
- `PragmaticInterpretation`
- `PragmaticInterpreter`

Fluxo atual:

`entrada -> PragmaticInterpreter -> ConversationTurnInterpreter -> BehaviorContextManager -> modelo`

O interpretador e deterministico e nao adiciona chamada ao LLM. `TurnInterpretation` carrega os atos e a confianca; o boundary os expoe como sinal de compreensao de entrada.

## Precedencia inicial

- `close_topic`, `acknowledge` e `correct_previous` podem superar leitura literal;
- social pragmatica pode superar um `?` sintatico (`beleza?` nao e pergunta factual);
- tecnico/criativo/discussao/factual continuam classificando pedidos substantivos;
- `vent_or_share` orienta conversa social sem solucao automatica;
- `react` curto evita explicar risada/reacao;
- ambiguidades continuam sendo tratadas conservadoramente.

## Separacao de persona

Pragmatica diz **o que a entrada faz**. Persona dira **como responder**. Todd, Morgana e Campanario devem poder receber a mesma interpretacao pragmatica e expressa-la de formas diferentes no futuro.

## Privacidade

Materiais privados usados para descobrir padroes conversacionais sao insumo efemero. O projeto nao conserva copia, nome, hash, caminho, participantes ou identificadores da fonte. Apenas padroes generalizados, contratos e testes anonimizados permanecem.

## Proximo gate

Validar v1.5 no Windows/Ollama com frases novas e contextos variados. Se pragmatica melhorar a interpretacao mas o modelo continuar ignorando orientacoes de resposta, investigar policy/decoding/modelo em vez de adicionar frases especificas.

## Nao objetivos

- Todd/Morgana ativos;
- RAG/banco de livros;
- memoria cognitiva;
- perfil pessoal derivado de conversa privada;
- fine-tuning;
- copiar girias para a resposta.
