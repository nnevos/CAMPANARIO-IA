# Long Call Review — seed 1787670418

## Resultado

- suite: `agent_long_call`
- modelo: `gemma3:12b`
- cenarios: 1 PASS / 2 WARN / 0 FAIL
- checks: 230 PASS / 5 WARN / 0 FAIL
- 36 turnos; 9 multiagente; 27 solo

## O que melhorou

P2.3b eliminou os FAILs objetivos do seed anterior: vocativo final funcionou, aritmetica dirigida/correcao permaneceu correta, reference-vs-invitation continuou estavel e a call nao trocou a arquitetura da ferramenta pela arquitetura interna do Campanario.

A latencia tambem melhorou: TTFR p95 caiu para 8.781s e max para 11.110s; turno multiagente medio ficou em 9.828s.

## Problema remanescente

O historico e o Working Conversation State lembram informacao suficiente, mas ainda faltava uma nocao explicita de **foco dominante**. A ultima fala de agente podia introduzir uma tangente e o modelo a tratava como se fosse o novo assunto do usuario.

Exemplos observados:

- Todd respondeu a uma decisao de arquitetura com pesquisa de usuarios, mantendo tema amplo mas perdendo a funcao especifica da pergunta;
- na call criativa, Morgana introduziu memoria como tangente e Todd depois escolheu cortar memoria, embora o ramo do usuario fosse controles visiveis/UI;
- a sintese final criativa abandonou presenca/lugar/orb/cores e virou a capacidade abstrata de Morgana de conectar informacoes;
- no social, Morgana sugeriu que uma ordem de Todd para ela sair seria motivo para silencio; agentes nao devem possuir autoridade social um sobre o outro;
- Todd nao respondeu diretamente a pergunta sobre quando deveria ficar quieto;
- apos retornar de uma tangente aritmetica, a correcao anterior ainda vazou para a retomada de presenca.

## Decisao P2.3c

Implementar `Conversation Focus Stack` deterministico e temporario, dirigido pelos movimentos discursivos do usuario:

- frame raiz;
- frame ativo;
- frames suspensos/tangentes;
- `mudando...` abre novo frame;
- `guarda esse raciocinio` preserva o frame sem mante-lo dominante;
- `voltando...` reativa frame correspondente;
- restricoes/decisoes do usuario permanecem no frame ativo;
- falas de agente nao promovem tangentes a foco automaticamente;
- `answer binding`: responder a funcao exata do pedido, nao apenas ao tema geral;
- frame suspenso nao vaza sem referencia explicita.

O mecanismo nao chama outro modelo, nao e memoria aprendida e nao altera Personality Core.
