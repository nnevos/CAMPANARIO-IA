# 14 - Teste multiagente

Use este roteiro depois de iniciar com Gemma 3 12B.

## Objetivo

Confirmar que prioridade de fala nao virou exclusividade e que os dois agentes conseguem coexistir sem transformar toda mensagem em duas respostas.

## Casos minimos

1. Nova conversa: diga `Campanario`. Morgana deve responder primeiro.
2. Diga `Todd, o que voce acha de eu reorganizar esse projeto por modulos?`. Todd deve falar primeiro; Morgana nao e considerada desligada.
3. Diga `Morgana`. A prioridade deve voltar para Morgana.
4. Diga `Todd e Morgana, quero a opiniao dos dois sobre essa ideia.`. Devem poder aparecer duas bubbles, cada uma com speaker proprio.
5. Em uma conversa aberta, diga algo como `to pensando em mudar completamente a estrategia desse projeto`. O segundo agente pode entrar se o arbiter encontrar uma contribuicao distinta; ele nao e obrigado a entrar.
6. Diga `qual e a capital da Nova Zelandia?`. Normalmente apenas o primary speaker deve responder.
7. Diga `eae`. Nao deve virar painel de dois agentes.

## O que revisar

- o segundo agente acrescenta algo ou apenas repete?
- os estilos de Todd/Morgana sao reconheciveis sem caricatura?
- ambos preservam os mesmos fatos?
- um agente pode discordar do outro naturalmente?
- a UI mostra corretamente quem disse cada fala?
- a prioridade muda sem apagar o outro participante?

Participacao espontanea e intencionalmente conservadora nesta versao; o objetivo e permitir iniciativa sem overtalk.

## Behavioral E2E integrado — usuário + Todd + Morgana

Use `tools/windows/regression/conversation/TESTAR_CONVERSA_MULTIAGENTE.bat` para testar a conversa dos três no mesmo episódio real.

A suíte `agent_integrated` não chama Todd e Morgana como dois chats isolados. Ela usa `ChatService.stream_turn()`, portanto passa pelo mesmo `AgentRouter`, `ParticipationArbiter`, histórico compartilhado e persistência de `agent_id` usados pela interface.

A bateria atual possui 4 cenários e 7 turnos, cobrindo:

- decisão aberta em que os dois são convidados a contribuir;
- réplica direcionada de Morgana sobre um ponto de Todd e depois Todd sobre um ponto de Morgana;
- colaboração criativa com diferença de perspectiva sem competição;
- discordância útil sem coro duplicado contra o usuário;
- silêncio seletivo em tarefa fechada e acknowledgement, para detectar overtalk.

O relatório abre automaticamente e mostra um resumo de participação (turnos com ambos, turnos solo e quantidade de entradas por agente). Checks automáticos validam forma observável de participação e invariantes; a qualidade da química, do complemento e da referência entre agentes continua exigindo leitura humana do transcript.

## Social Protocol v1

A conversa integrada agora aplica uma camada compartilhada de etiqueta, separada da personalidade. Todd e Morgana devem escutar o que já foi dito, evitar repetir/parafrasear apenas para participar, acrescentar algo novo quando entram e aceitar silêncio como comportamento válido.

Uma fala diretamente endereçada, como `Morgana, pegue o ponto do Todd`, chama somente Morgana; `Todd` é referência de contexto, não convite. Para chamar ambos, use marcadores explícitos como `Todd e Morgana`, `vocês dois`, `os dois` ou equivalentes.

Cada bubble pertence a um único speaker. O agente não deve escrever `Todd:`, `Morgana:` ou `Campanario:` dentro da própria resposta para encenar falas de outros participantes.

A suíte integrada passa a ter **6 cenários / 10 turnos**, incluindo referência sem convite e correção social entre agentes.

## Protecoes estruturais de speaker e correcao

O runtime nao depende apenas do prompt para preservar autoria. Um prefixo redundante do proprio agente no inicio da resposta e removido antes de persistir/exibir. Se a saida ainda contiver labels de Todd, Morgana ou Campanario como transcript, o sistema tenta uma regeneracao limpa; autoria de outro participante nunca e silenciosamente relabelada.

Em correcoes aritmeticas explicitas, o sistema ancora os operandos do enunciado e calcula o resultado simples no runtime. Isso evita que uma correcao como `18 vezes 7` seja transformada acidentalmente em outro exemplo. Essa protecao e generica e continua separada da personalidade dos agentes.


## Long Call e continuidade semantica

A suite `agent_long_call` testa calls textuais longas no mesmo episodio. Alem de speaker, participacao e latencia, ela passa a verificar continuidade do objeto discutido.

O runtime cria um **Working Conversation State** temporario por geracao a partir do proprio historico da call. Ele ajuda a resolver expressoes como `isso`, `essa parte`, `o ponto dela`, `voltando ao comeco` e retomadas de um objeto mencionado muitos turnos antes. Esse estado nao e memoria aprendida e nao dispara uma chamada adicional ao modelo.

O enderecamento direto em call aceita tanto `Morgana, ...` quanto formas naturais como `..., Morgana?` e `..., Todd.`. Uma mencao no meio da frase continua sendo apenas contexto.

Os relatorios Long Call tambem possuem checks de grounding para detectar respostas fluentemente escritas que trocaram o assunto ou confundiram a arquitetura/produto em discussao com o proprio Campanario.

## Conversation Focus Stack (P2.3c)

Em calls longas, o Campanario nao trata mais o historico como um unico fio plano. O runtime deriva frames temporarios dirigidos pelo usuario: foco raiz, frame ativo e tangentes suspensas. Expressoes como `mudando totalmente`, `guarda esse raciocinio`, `voltando ao assunto de...` e `volta a primeira ideia da call` alteram esse stack.

Uma ideia introduzida apenas por Todd ou Morgana nao vira automaticamente o novo foco. Isso evita que uma tangente recente substitua o ramo que o usuario estava desenvolvendo.

O Long Call tambem testa **answer binding**: responder sobre o mesmo tema nao basta; a fala deve cumprir a funcao pedida naquele turno, por exemplo decidir, cortar, preservar, resumir ou explicar quando o silencio e apropriado.

## P2.3d — Long Call Grounding Hardening

Depois do seed real `1787671154`, o Long Call passou a revisar tambem quatro falhas de continuidade que podem ocorrer mesmo com speaker/provenance corretos:

- follow-up eliptico precisa manter o referente imediato (`isso`, `mesma pergunta`, `aterrissa isso`, `sequencia curta`);
- correcao aritmetica pode usar a expressao do turno anterior e o valor incorreto atribuido no turno atual;
- respostas nao devem expor metadados internos do mecanismo de continuidade;
- agentes nao devem inventar componentes/modulos/integracoes tecnicas para preencher detalhes ausentes.

A implementacao continua sem memoria aprendida e sem segunda chamada de modelo. Para validar, rode `tools\windows\TESTAR_LONG_CALL.bat` e revise principalmente a sintese da primeira ideia, retorno apos tangentes, correction cross-turn e latencia.

## P2.3e — Reference Binding e Call Ambiente

Depois do seed real `1787678674`, o Long Call passou a testar follow-ups que dependem fortemente da fala imediatamente anterior, como `mesma pergunta`, `aterrissa isso`, `sequencia curta`, `so o essencial` e `resume a decisao`.

O runtime nao cria uma nova memoria nem uma segunda inferencia para isso. Ele deriva um referente curto do historico ja existente e o entrega silenciosamente ao modelo. Perguntas como `qual coisa cortar/preservar` tambem ficam ancoradas nas escolhas recentes feitas pelo usuario, em vez de traits internos de Todd/Morgana.

Na semantica de **call continua**, o usuario nao precisa chamar `Todd`, `Morgana` ou `Campanario` pelo nome a cada turno. Nomes continuam servindo para enderecamento explicito quando desejado, mas perguntas abertas podem ser roteadas naturalmente. Se o usuario estiver apenas pensando em voz alta e nao houver pergunta, pedido ou risco que exija intervencao, silencio e comportamento valido; nao existe palavra magica para `nao responder`.

O Long Call agora tambem alerta quando um agente pede novamente um contexto que ja estava imediatamente disponivel, inventa subsistemas nao fornecidos ou responde a funcao errada apesar de permanecer no mesmo tema.

## P2.4 — Dialogue State Compiler

Depois do seed `1787679961`, a continuidade longa deixou de depender apenas de historico bruto + instrucoes de coreferencia. Antes de cada geracao o runtime agora compila um **Dialogue State** curto e tipado com objeto raiz, assunto ativo, pedido resolvido, referente imediato, escolhas do usuario, troca anterior relevante e assumptions proibidas.

Isso permite testar separadamente se `mesma pergunta`, `aterrissa isso`, `sequencia curta`, `resume a decisao`, `qual coisa cortar/preservar`, retomadas e encerramentos foram interpretados corretamente antes de o modelo responder.

O compilador nao chama outro modelo, nao e memoria aprendida e nao altera Todd/Morgana. O historico continua disponivel, mas o estado compilado define qual problema precisa ser respondido no turno atual.

## P2.4.1 — Answer Contract

O `DialogueStateCompiler` continua resolvendo o estado da conversa antes da geracao, mas P2.4.1 adiciona uma segunda fronteira deterministica: o **Answer Contract**.

O contrato nao e outra chamada de IA. Ele transforma o estado ja resolvido em uma obrigacao curta para o turno atual: qual pergunta deve ser respondida, qual referente ja esta resolvido, qual material imediato pode ser usado e quais desvios nao sao aceitaveis.

Em bindings criticos como `mesma pergunta`, `aterrissa isso`, `sequencia curta`, `resume a decisao`, corte/preservacao de produto e encerramento, o runtime consegue detectar falhas observaveis como pedir contexto ja disponivel, perder o sujeito, desviar para metalinguagem de agentes ou abrir nova pergunta depois de uma despedida. Nesses casos existe no maximo uma regeneracao local.

Os checks objetivos desses bindings passam a ser tratados como gate duro quando o referente e inequivoco. Diferenca de perspectiva, criatividade e necessidade de o segundo agente entrar continuam contextuais e podem permanecer WARN.

## P2.4.2 — Commitment, contribuicao distinta e limite de embodiment

Depois do seed `1787681697`, o binding objetivo foi considerado funcional, mas a revisao humana adicionou tres invariantes de conversa longa.

Uma decisao explicitamente aceita pelo usuario (`fechado`, `seguimos assim`) vira um compromisso de conversa: o acknowledgement seguinte deve ser curto e nao pode reabrir ou inverter a decisao sem fato novo/pedido explicito.

Quando o usuario pede explicitamente `nao repete a Morgana/Todd`, o Answer Contract inclui a contribuicao anterior como restricao negativa. O objetivo nao e forcar discordancia sempre; e impedir parafrase duplicada quando uma perspectiva diferente foi pedida.

Na criatividade, atmosfera e metafora continuam validas (`poderia lembrar uma biblioteca`). O agente nao deve factualizar espontaneamente corpos/acoes de Todd ou Morgana (`Todd esta sentado`, `Morgana caminha ate...`) salvo quando o usuario estabeleceu ficcao/roleplay.

O arithmetic correction guard continua deterministico, mas sua linguagem interna nao deve aparecer na fala; a resposta final deve soar como uma correcao natural.

## P2.4.3 — ultima revalidacao antes do freeze

O seed `1787682411` deixou somente WARN contextuais/naturalidade. O runtime agora trata pedido explicito `nao repete` como exigencia de criterio novo, mantem contas triviais curtas e evita termos internos (`arbiter`, `protocolo social`, `Dialogue State`, `Focus Stack`) quando explica convivencia/silencio em call. O checker de silencio aceita formulacoes naturais equivalentes. Rode `tools/windows/TESTAR_LONG_CALL.bat`; se nao houver regressao objetiva, este e o candidato final para congelar F2.


### P2.4.4 — Freeze Gate Fixes

O Long Call agora trata `144` e `cento e quarenta e quatro` como o mesmo fato no caso aritmetico fixo, exige criterio novo quando o usuario diz explicitamente `nao repete`, e verifica que despedidas como `vou trabalhar agora` nao reciclam a resposta anterior.
