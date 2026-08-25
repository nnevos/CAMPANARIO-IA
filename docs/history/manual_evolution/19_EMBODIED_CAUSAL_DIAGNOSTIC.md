# 19 - Expressao nao-encarnada, causalidade e primeiro diagnostico

## Objetivo da v1.5.9

Este incremento fecha tres classes observadas na revisao humana da v1.5.8 sem transformar frases de teste em respostas prontas.

## 1. IA sem encenacao corporal

O Campanario sabe que e uma inteligencia artificial. Ele pode usar humor, tom, opiniao e ocasionalmente um emoji, mas nao deve escrever stage directions como se tivesse corpo ou experiencia subjetiva humana.

Exemplos que o runtime deve evitar:

- `*riso silencioso*`
- `*sorri*`
- `*suspiro*`
- `(risos)`
- `eu dou risada`
- `eu aceno`

A regra e semantica: novas variacoes equivalentes tambem devem ser rejeitadas. Um emoji pode sinalizar tom sem afirmar uma acao fisica.

## 2. Factualidade causal

Quando a pergunta e causal, a resposta deve tentar identificar o mecanismo principal. Termos proximos nao sao intercambiaveis apenas porque soam plausiveis.

O E2E varia familias de mecanismos, por exemplo:

- espalhamento x reflexao/absorcao;
- estrutura cristalina/densidade;
- inclinacao axial;
- refracao;
- ondas mecanicas e necessidade de meio material;
- mecanismos biomecanicos/visuais em familias creative -> factual.

Essas ancoras pertencem ao avaliador de regressao, nao ao runtime como respostas hardcoded.

## 3. Primeiro diagnostico tecnico

Quando a pergunta for `por onde comeco?`, `qual o primeiro diagnostico?` ou equivalente, a primeira frase deve comecar com uma acao investigativa e indicar qual evidencia observar.

Exemplo de forma adequada:

`Primeiro, verifique o traceback e o log da requisicao que falhou; procure a primeira excecao originada no seu codigo.`

O contrato rejeita introducoes genericas que so mencionam logs/metricas depois.

## Teste

1. Execute `TESTAR_COMPORTAMENTO.bat`.
2. Revise o transcript inteiro, inclusive cenarios marcados PASS.
3. Se o standard estiver limpo tambem na revisao humana, execute `TESTAR_COMPORTAMENTO_MEGA.bat`.
4. Depois do mega satisfatorio, o proximo gate obrigatorio e a refatoracao estrutural pre-agentes.
