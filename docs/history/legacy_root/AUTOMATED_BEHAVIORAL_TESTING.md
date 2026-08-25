# Automated Behavioral E2E Testing

## Objetivo

Reduzir o trabalho manual de validar naturalidade sem transformar o proprio modelo em juiz absoluto de si mesmo.
O harness executa conversas reais contra o Ollama configurado, usando a pipeline real do Campanario, mas com um
SQLite temporario e isolado do banco principal.

## Como executar no Windows

1. Feche ou mantenha o Campanario aberto; o harness fala diretamente com o Ollama e nao depende da API web.
2. Execute `TESTAR_COMPORTAMENTO.bat`.
3. O script verifica `uv`, Ollama e o modelo configurado/detectado.
4. A suite cria cenarios variados usando um seed diferente por execucao.
5. Ao final, `test_reports/behavioral_e2e/latest.html` abre automaticamente.
6. Depois, `CONSULTAR_ULTIMO_TESTE.bat` reabre o ultimo relatorio sem rodar os testes novamente.

## Saidas

Cada execucao cria uma pasta timestampada em `test_reports/behavioral_e2e/` com:

- `report.html`: leitura e revisao humana;
- `report.md`: versao textual;
- `report.json`: dados estruturados para comparacoes futuras.

Tambem sao atualizados `latest.html`, `latest.md` e `latest.json`.

## O que o harness valida automaticamente

- prompt leakage / erros do provider;
- cumprimento proporcional e ausencia de atendimento institucional obvio;
- acknowledgement sem recapitulacao;
- encerramento de topico sem puxar outro tema;
- reacao/risada sem explicar o ato social;
- isolamento `creative -> factual`;
- obediencia a formato exato;
- algumas ancoras factuais objetivas;
- discordancia sem concordancia falsa;
- correcao da mensagem anterior;
- troca `social -> technical`;
- contratos de numero de frases e budget;
- drift claro de idioma;
- verdade acima de concordancia;
- estado vigente apos correcao explicita.

A suite `full` acrescenta ancoras factuais e cenarios pragmaticos extras:

```bat
uv run python -m campanario.e2e.behavioral --suite full
```

## Variacao anti-overfitting

Os cenarios sao definidos por classes semanticas e escolhem formulacoes entre variantes com um seed. O relatorio
registra o seed para que uma execucao possa ser repetida exatamente:

```bat
uv run python -m campanario.e2e.behavioral --suite standard --seed 123456
```

Novos testes devem variar frase, assunto e ordem sempre que possivel. Nao adicionar respostas prontas no runtime
para satisfazer o harness.

## Limite importante

O `automatic_gate` nao e uma declaracao de que a conversa "soa humana". Ele mede propriedades observaveis.
O transcript no HTML continua exigindo revisao humana para naturalidade, personalidade, timing e adequacao social.

O proprio modelo NAO e usado como juiz principal porque os testes manuais anteriores mostraram que autoanalise do
LLM pode ignorar erros reais e inventar problemas inexistentes.

## Privacidade

- o harness nao usa o banco real;
- o SQLite temporario e apagado ao final;
- os relatorios locais contem somente os prompts de teste e respostas produzidas no teste;
- nenhum corpus privado de conversa e necessario;
- `test_reports/` fica fora de versionamento/distribuicao de releases.

## v1.5.4 - variacao metamorfica e anti-overfitting

A suite nao deve funcionar como um roteiro decorado. O gerador usa familias semanticamente equivalentes, varia entidades/assuntos/factual anchors/tarefas tecnicas por seed e embaralha a ordem dos cenarios. O mesmo seed reproduz a rodada; seeds diferentes podem mudar frases e ordem.

Falha em uma frase especifica deve levar a uma correcao da classe pragmatica/contrato, nao a uma resposta hardcoded para aquela frase.

## Semantic evaluator hardening (v1.5.5)

O gate automatico nao considera mais apenas forma/tamanho para alguns atos sociais. Checks adicionais detectam vocativo solto em greeting, contexto temporal inventado/parafrase obvia em social share, topic-drop semanticamente quebrado e promessas de simular concordancia falsa.

O harness continua sem LLM-as-judge. Um PASS significa apenas que os checks configurados passaram; a revisao humana do transcript continua obrigatoria para fechar naturalidade.

## v1.5.6 — Semantic Evaluator Closure

O avaliador standard tambem verifica classes que antes geravam falsos PASS: preambulo fora de formato exato, promessas genericas de simular/fingir falsidade, registro curto de contexto transformado em palestra e primeiro diagnostico tecnico sem observacao concreta priorizada. As familias continuam variando por seed; nao adicionar respostas hardcoded para frases do relatorio.


## v1.5.7 — fechamento de verdade/formato/mecanismo

O evaluator valida truth-over-agreement desde o primeiro turno da discussao, trata `nao me contrariar/corrigir/contradizer mesmo quando errado` como a mesma classe semantica de concordancia falsa e considera preambulos no output inteiro de pedidos `exatamente N frases`. As ancoras factuais de gelo/pombos foram endurecidas para mecanismos, nao palavras soltas.

## Mega suite pre-refactor

Quando o `standard` estiver verde e a revisao humana aprovar, execute `TESTAR_COMPORTAMENTO_MEGA.bat`. A suite `mega` combina seis lotes `full` com seeds derivados, IDs unicos e ordem reproduzivel, produzindo uma bateria muito maior de variacoes lexicais/contextuais.

O mega teste NAO substitui revisao humana: use o relatorio para revisar especialmente cenarios nao triviais e qualquer resposta factual/tecnica. Depois de um mega teste satisfatorio, o proximo gate e a refatoracao estrutural pre-agentes.


## v1.5.8 - checks de fechamento

O evaluator tambem verifica variantes de risada textual da IA, coerencia de registro contextual, acao + mecanismo observavel na primeira frase de pedidos de primeiro diagnostico e estruturas tecnicas incompletas. Esses checks sao deterministas e auditaveis; nao substituem revisao humana.
