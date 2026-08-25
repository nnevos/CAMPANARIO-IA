# Modelos e portabilidade

## Objetivo

O Campanario nao deve depender de um modelo especifico para preservar comportamento, memoria, contexto,
testes ou futuras personas. O modelo e um **motor linguistico substituivel** atras do contrato `ModelProvider`.

Hoje o backend implementado e **Ollama**, mas o modelo dentro do Ollama pode ser trocado sem alterar codigo.
A arquitetura deixa a inclusao de outros backends para adapters futuros.

## Trocar o modelo sem editar codigo

No Windows, execute:

`TROCAR_MODELO.bat`

O script lista os modelos instalados, valida o nome escolhido e grava `CAMPANARIO_MODEL_NAME` no `.env`.
Reinicie o Campanario depois da troca.

Tambem e possivel editar `.env` manualmente:

```text
CAMPANARIO_MODEL_PROVIDER=ollama
CAMPANARIO_MODEL_NAME=qwen3:8b
```

Use exatamente um nome retornado por `ollama list`.

## O que nao muda ao trocar modelo

- banco SQLite e historico;
- Context Manager e proveniencia;
- interpretacao pragmatica;
- Response Contract Pipeline;
- truth/self-awareness/format contracts;
- Behavioral E2E e mega-teste;
- futuros agentes/personas, quando forem ativados.

O novo modelo pode produzir resultados melhores ou piores, por isso a troca exige **revalidacao**, nao
reimplementacao. Rode primeiro `TESTAR_COMPORTAMENTO.bat`; modelos candidatos importantes devem depois
passar pelo mega-teste.

## Configuracao generica

- `CAMPANARIO_MODEL_PROVIDER` - backend. Atualmente: `ollama`.
- `CAMPANARIO_MODEL_NAME` - modelo usado no chat e nos resumos.
- `CAMPANARIO_MODEL_BASE_URL` - endpoint do backend.
- `CAMPANARIO_MODEL_TIMEOUT_SECONDS` - timeout.
- `CAMPANARIO_MODEL_TEMPERATURE` - temperatura.

As antigas variaveis `CAMPANARIO_OLLAMA_*` continuam aceitas para compatibilidade com `.env` antigos,
mas novas configuracoes devem preferir `CAMPANARIO_MODEL_*`.

## Adicionar outro backend no futuro

Um backend novo deve implementar `ModelProvider` e ser registrado em `llm/runtime.py`. ChatService,
pragmatica, contratos, memoria e personas nao devem importar tipos do backend concreto.

Essa fronteira existe exatamente para evitar recomecar o Campanario do zero se Ollama, llama3 ou qualquer
modelo deixar de atender ao projeto.
