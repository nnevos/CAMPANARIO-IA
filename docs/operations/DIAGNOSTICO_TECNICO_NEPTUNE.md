# Campanario / auditoria tecnica desta revisao

## Achados com respaldo no codigo do ZIP

- `src/campanario/model/adapters/ollama.py` nao enviava `think` na API;
  Qwen3.5 pode gerar tokens de raciocinio antes da resposta visivel.
- `src/campanario/chat/service.py` coletava a resposta completa antes de emitir
  um evento de texto; havia processamento de reparos apos a geracao.
- `response/pipeline.py` tem reparos fechados para saudacoes, reacoes e ack
  (`Opa.`, `Boa.`, `Certo.`), o que pode criar sensacao de resposta enlatada.
- `chat/context.py` pode executar duas chamadas de modelo para sumarizar
  mensagens antigas quando ultrapassa janela, somando latencia.
- `agents/participation.py` pode invocar outro prompt para decidir participacao
  do segundo agente e outra geracao para a propria fala.
- Prompt geral e de personalidade eram compostos por muitas secoes, acumulando
  instrucoes repetidas para cada interacao. Nao ha medicao antiga de tokens.
- `runtime/capabilities.py` e uma camada de registro; nao prova que uma busca web
  externa esteja realmente implementada e integrada aos agentes.

## Mudancas efetuadas

- `think=false` no nivel superior, `keep_alive`, limite de output e contexto.
- Modo conversacional leve com prompts compactos e no maximo um modelo
  solicitado por agente, exceto convites explicitos e reparos conservadores.
- Streaming validado em testes com fragments artificiais. Nao foi medido no
  Windows/Neptune nem houve inferencia real aqui.
- Arbitro semantico extra desligado por padrao; convite explicito aos dois segue.
- Resumo sincronico desligado por padrao (o sistema de memoria experiencial
  original continua em uso).
- O modo legado inteiro fica disponivel para rollback pelas flags.

## Resultado de validacao

- `pytest tests`: **487 PASS, 4 FAIL, 6 warnings** em Python 3.13 neste
  ambiente de auditoria (o projeto solicita 3.12). Falhas:
  * Teste `test_manual_docs`: lista permitida antiga omite guia experimental obsoleto.
  * Teste `test_project_layout`: lista permitida omite varios scripts ja presentes
    no ZIP e nosso novo diagnostico Qwen.
  * 2 testes da interface experimental antiga esperavam textos ausentes da UI atual.
  Estes resultados NAO foram alterados com respostas fixas nem testes removidos.
- `pytest tests/test_neptune_mode.py`: **5 PASS**, testes sinteticos de
  payload, identidade de agentes, streaming e ausencia de resposta enlatada.
- Nenhum teste de velocidade real de GPU foi executado neste ambiente.

## Riscos e compromissos

- Streaming publica texto antes de toda a resposta ser validada, inclusive
  possivel rotulo de speaker tardio; a guarda de marcadores internos opera
  incrementalmente e interrompe ao encontrar um marcador. Para segurança de
  publicacao/reparo completo, volte ao modo conservador.
- Janela de 12 mensagens sacrifica contexto literal antigo para reduzir custo;
  memoria e episodios antigos podem ser usados conforme infraestrutura local.
- Identidade precisa ser validada com usuarios reais; nao afirmamos que 5
  testes sintéticos comprovem naturalidade de longa duracao.
- STT/TTS foi mantido; os defeitos relatados de reconhecimento pt-BR nao
  foram corrigidos nem testados neste pacote.

## Referencias de API

Ollama /api/chat `think` no nivel superior: https://github.com/ollama/ollama/blob/main/docs/capabilities/thinking.mdx
Biblioteca Qwen3.5: https://ollama.com/library/qwen3.5
