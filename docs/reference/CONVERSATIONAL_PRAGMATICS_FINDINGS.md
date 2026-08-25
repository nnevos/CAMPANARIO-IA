# Descobertas de pragmatica conversacional

## Objetivo

Esta referencia registra descobertas generalizaveis obtidas a partir de um corpus real de conversa informal em portugues brasileiro. O objetivo e melhorar **como o Campanario interpreta a entrada humana**, nao copiar o jeito de falar de pessoas especificas nem construir perfis pessoais a partir do grupo analisado.

A fonte privada usada para derivar estas descobertas nao faz parte do projeto nem do runtime. O repositorio conserva apenas abstracoes generalizaveis e nao conserva copia, nome de arquivo, hash, identificador, participantes, relacoes ou lore da fonte privada.

## Separacao fundamental

A arquitetura deve manter tres camadas independentes:

1. **Pragmatica geral** — o que a mensagem esta fazendo na conversa.
2. **Adaptacao ao usuario** — futuramente, padroes realmente recorrentes de um usuario, com evidencia e possibilidade de correcao.
3. **Persona de resposta** — Campanario, Morgana, Todd ou outro agente decide como expressar a resposta.

Entender linguagem informal nao significa imitar o usuario.

## Descobertas generalizaveis

- Mensagens curtas podem carregar funcao social completa sem pedir nova informacao.
- Risada (`kkk`, keyboard smash e equivalentes) e um ato conversacional, nao apenas ruido textual.
- Palavroes e exageros precisam de contexto; nao significam automaticamente hostilidade ou literalidade.
- Mudancas de assunto podem ocorrer sem anuncio formal.
- Uma ideia pode ser fragmentada em varias mensagens consecutivas.
- Uma mensagem posterior pode corrigir a anterior (`personagem*`) em vez de criar uma nova afirmacao independente.
- `aham`, `pse`, `pois e`, `entendi`, `ok` e equivalentes podem cumprir funcoes diferentes conforme o contexto.
- Humor/ficcao de um turno nao autoriza resposta ficticia no turno factual seguinte.
- Pergunta nao e requisito para manter uma conversa natural.
- Conversa social valida pode nao ter objetivo produtivo.
- Uma mesma mensagem pode ter multiplos atos, por exemplo reacao + concordancia.
- Interpretacao e resposta sao problemas separados: a mesma entrada pode ser entendida igualmente por personas diferentes e respondida de formas distintas.

## Atos conversacionais candidatos

A fundacao de codigo representa, de forma nao exaustiva:

- acknowledge
- agree
- disagree
- react
- joke_or_play
- correct_previous
- continue_thought
- change_topic
- close_topic
- vent_or_share
- ask_info
- ask_opinion
- request_action
- plan
- clarify
- think_aloud

Uma mensagem pode receber mais de um ato. Esses rotulos sao **hints de interpretacao**, nao comandos de resposta e nao evidencias factuais.

## Regras de privacidade e generalizacao

- Nao transportar nomes, relacoes, preferencias ou lore do corpus para o nucleo comportamental.
- Nao inferir personalidade profunda, estado psicologico ou relacoes pessoais.
- Nao memorizar automaticamente conteudo sensivel porque apareceu numa conversa de grupo.
- Usar exemplos anonimizados/variados em testes, evitando otimizar o codigo para frases ou pessoas especificas.
- Nao registrar no repositorio nome, hash, caminho, identificador ou qualquer outro ponteiro para a fonte privada. Auditoria deve recair sobre as descobertas derivadas e seus testes, nao sobre a origem privada.

## Consequencia para o produto

O Campanario deve evoluir de classificacao de "tipo de pedido" para uma leitura pragmatica mais rica: **o que o usuario quis fazer socialmente com esta mensagem?** A persona entra apenas depois dessa interpretacao, preservando sua propria identidade e voz.
