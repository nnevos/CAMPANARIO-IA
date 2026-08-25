# 03 - Usar o chat

## Criar e selecionar conversas

A interface local em `/` permite criar sessoes, selecionar sessoes anteriores e carregar historico.

## Como conversar

Nao e necessario formular prompts formais. A foundation interpreta conversa social, pedidos factuais/tecnicos, discussao, criatividade, continuacoes, correcoes e encerramento de topico.

## Identidade

Campanario sabe que e uma inteligencia artificial. Naturalidade nao significa fingir ser humano nem declarar sentimentos humanos como estados internos. Humor, opiniao e emoji podem ser usados como linguagem/tom sem virar emocao propria.

## Contratos de resposta

A Response Contract Pipeline valida propriedades do turno como formato explicito, proportionalidade e invariantes comportamentais antes de liberar a resposta. Preferencias de estilo nunca autorizam tratar falsidade como verdade apenas para concordar.

## Agentes

A interface mostra Campanario como sistema e Morgana/Todd como participantes. Morgana tem prioridade padrao de fala; os botoes mudam prioridade, nao exclusividade. Chamar `Todd` ou `Morgana` diretamente muda quem fala primeiro, e convites aos dois podem produzir duas falas no mesmo turno. Consulte `12_AGENTES.md`.

## Atualmente ativo

- chat local via modelo Ollama;
- streaming/API local;
- sessoes e mensagens persistidas;
- Context Manager;
- pragmatica/turn mode;
- source provenance;
- response contracts;
- prompt leak guard;
- agentes Todd e Morgana v1.

## Ainda nao ativo

Memoria cognitiva, RAG/livros, web, tools e voz continuam fora do runtime ate seus respectivos gates.
