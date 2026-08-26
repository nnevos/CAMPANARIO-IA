# Long Call E2E Review — seed 1787669291

## Resultado real recebido

- suite: `agent_long_call`
- modelo: `gemma3:12b`
- 36 turnos em 3 episodios longos;
- cenarios: 0 PASS / 1 WARN / 2 FAIL;
- checks: 222 PASS / 2 WARN / 2 FAIL.

## Leitura do resultado

Os dois FAILs objetivos vieram do mesmo bug de roteamento: vocativo ao final da frase nao era reconhecido (`..., Morgana?` / `..., Morgana.`), fazendo Todd responder por ser o primary persistido.

O transcript revelou um problema mais importante que os checks anteriores nao capturavam: perda de **binding semantico de longo contexto**. O modelo mantinha historico textual, mas em alguns turnos deixava de saber qual objeto estava sendo discutido.

Exemplos observados:

- arquitetura da ferramenta local virou arquitetura interna do Campanario;
- `nao quero vinte hipoteses; me deem uma sequencia curta` perdeu o referente do pico de latencia do turno anterior;
- `qual coisa voce cortaria primeiro?` deixou de apontar para controles/interface e virou uma resposta abstrata;
- uma sintese da call criativa trocou o conceito visual/presenca por um conceito geral de personalidade/estilo;
- `isso que eu quero` na call social foi reinterpretado como ruido/ambiente fisico, produzindo sugestao de fones de ouvido.

Isso e diferente de memoria de longo prazo: trata-se de **estado de trabalho da conversa atual**.

## Correcao P2.3b

### 1. Vocativo natural em call

O roteamento agora reconhece endereco direto no inicio ou no fim:

- `Morgana, responde...`
- `responde..., Morgana?`
- `resume em uma frase, Morgana.`

Nomes no meio da frase continuam sendo referencia, nao convite/endereco.

### 2. Working Conversation State

Foi adicionado `src/campanario/chat/working_context.py`.

A cada geracao ele deriva deterministicamente, do historico completo do episodio:

- ancora de abertura da call;
- ultimos turnos do usuario;
- ancoras anteriores relacionadas lexicalmente ao pedido atual;
- ultima fala de agente;
- pedido atual;
- regras de resolucao de elipse/retomada.

Nao existe segunda chamada de modelo e o estado nao e persistido como memoria aprendida.

### 3. Entity anchoring

O prompt de trabalho explicita que termos como `arquitetura`, `sistema`, `ferramenta` e `produto` devem permanecer ligados ao objeto que o usuario introduziu. Eles nao devem virar automaticamente a arquitetura interna do Campanario.

### 4. Retomada e referencia

Expressoes como `isso`, `essa parte`, `o ponto dela`, `voltando`, `do comeco` e `a primeira ideia` passam a receber ancoras estruturadas do episodio.

### 5. Autoidentificacao em call

`Todd aqui.` / `Morgana aqui.` no inicio da propria fala sao normalizados como ruido estrutural estreito. Isso nao remove referencias ao outro participante.

### 6. E2E fortalecido

O Long Call agora inclui checks WARN para detectar:

- troca da arquitetura da ferramenta pela arquitetura interna do Campanario;
- perda do referente do diagnostico de latencia;
- elipse de controles/interface;
- sintese criativa que abandona presenca/UI;
- ack social que responde a outro problema.

## Latencia observada no seed

- TTFR media: 4.918s;
- TTFR p95: 12.484s;
- TTFR max: 17.969s;
- solo medio: 4.37s;
- multiagente medio: 11.198s;
- gap medio ate segundo agente: 4.205s.

A correcao P2.3b nao adiciona inferencia extra para working state, portanto nao deve aumentar a latencia por uma segunda chamada de LLM.

## Proximo gate

Reexecutar `tools/windows/TESTAR_LONG_CALL.bat` com Gemma 3 12B e revisar especialmente os novos checks de continuidade semantica. Nao alterar Personality Core antes dessa evidencia.
