# Review atual da fundacao conversacional

## Resultado consolidado

A fase de tuning baseada em `llama3:latest` foi encerrada. O Llama serviu como baseline adversarial, mas apresentou erros recorrentes de mecanismo factual, naturalidade e obediencia simultanea a varias invariantes.

O teste comparativo com `gemma3:12b`, usando a mesma pipeline do Campanario, mudou o diagnostico:

- standard informado pelo usuario: **11/11 cenarios, 64/64 checks**;
- mega informado pelo usuario: **75 PASS / 3 FAIL**, com as falhas concentradas em mecanismo factual/evaluator, nao em colapso geral de conversa;
- social, continuacoes, correcao, truth contract, self-awareness, creative->factual e diagnostico tecnico ficaram muito mais estaveis.

Conclusao: uma parte grande do problema anterior era capacidade/adequacao do modelo-base, nao falta de mais regras no prompt.

## O que esta comprovadamente funcionando

- persistencia local de sessoes e mensagens;
- Context Manager e resumo persistido;
- pragmatica de entrada separada da persona de saida;
- correcoes explicitas com estado atual;
- proveniencia que impede ficcao do assistant de virar evidencia factual;
- Response Contract Pipeline tipada;
- prompt leak guard;
- self-awareness sem fingir emocao humana;
- E2E seeded standard/full/mega;
- runtime de modelo substituivel;
- Gemma 3 12B como melhor candidato medido ate aqui.

## Problemas que continuam reais

1. **Factualidade aberta nao e garantida.** Um modelo melhor reduz muito os erros, mas nao substitui grounding/RAG/web quando essas fases forem liberadas.
2. **Evaluator deterministico nao e juiz absoluto.** PASS automatico continua exigindo leitura humana em releases importantes.
3. **Contratos acumulados precisam permanecer modulares.** Nao voltar a concentrar comportamento, evaluator e provider em arquivos gigantes.
4. **Naturalidade nao deve virar imitacao.** A IA entende linguagem informal, mas a futura persona continua responsavel pela voz.
5. **Agentes nao podem duplicar memoria/pipeline.** Todd e Morgana devem ser politicas/personas sobre o mesmo Campanario.

## Regra daqui para frente

Nao adicionar patches comportamentais para uma pergunta isolada. Primeiro testar se a falha e modelo, pipeline, contexto, evaluator ou conhecimento faltante.

## Agent Architecture v1.2

A foundation comportamental nao foi retunada. A mudanca e de coordenacao: Todd/Morgana deixam de ser selecoes exclusivas e passam a participantes persistentes com prioridade de fala + arbitragem conservadora para participacao secundaria.
