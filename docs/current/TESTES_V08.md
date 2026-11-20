# Testes e limites da entrega v0.8

Data: 18/11/2026. Fonte auditada: CAMPANARIO_UI_v0.7_PROJETO.zip. Execucao em Linux, Python 3.13.5 e Node 22.16.0; o projeto continua declarando Python 3.12 como alvo. A execucao no ambiente alvo e uma validacao adicional obrigatoria.

## Resultados medidos

| Verificacao | Resultado |
|---|---|
| Suite integral da v0.7 recebida | 560 aprovados, 23 falhas, 583 casos |
| Suite integral da v0.8 | 547 aprovados, 14 falhas, 561 casos |
| Casos novos da fundacao (`test_v08_platform.py`) | 48 aprovados |
| Logica offline/mobile em Node | 16 aprovados |
| Gate da fundacao + API, UI segura e contratos preservados | 74 aprovados |
| Sintaxe Python e JavaScript | Verificada |
| UI isolada no Chromium com API/ponte simuladas | Sem erros JS nos fluxos exercitados |
| Servidor FastAPI local real, banco de teste e migracoes | Iniciou; `/health/live` confirmou runtime |
| Janela nativa Windows / WebView2 | Nao executada aqui |
| EXE PyInstaller / APK Android / Gradle / Java Android | Nao compilados aqui |
| Android Keystore, TLS em aparelho e atualizacao por APK | Nao testados em aparelho |
| IA Ollama com pesos reais, voz, GPS | Nao homologados nesta entrega |

As 14 falhas finais tem os mesmos identificadores de falhas presentes na execucao original. A reducao de totais nao representa ganho de cobertura: testes exclusivos dos legados retirados foram arquivados; novos testes de plataforma foram adicionados; expectativas antigas de markup/launcher foram atualizadas. Os testes comportamentais que falham continuam ativos.

A comparacao controlada desabilitou embeddings via variavel de ambiente para isolar servicos externos. Uma segunda execucao integral da v0.8 sem essa sobreposicao, preservando os defaults do projeto, tambem resultou em 547 aprovados/14 falhas. Nao se conclui por isso que o comportamento com um modelo real seja identico ao das fixtures.

## Falhas remanescentes

Onze casos em `test_g2_grounding_audit.py` tratam de extrapolacao de evidencias pessoais e reparacao de respostas. Tres casos em `test_g2_semantic_evidence_regression.py` tratam de recuperacao e resposta ancorada nas memorias recuperadas. Exemplo do problema: um registro "gosto de X" pode ser promovido indevidamente a "X e meu favorito". Isso exige correcao no nucleo de evidencia, nao uma troca de interface.

Os logs integrais estao em `evidencias/`. Nao foram usados `xfail`, exclusao desses testes ou respostas fixas para esconder o problema. A release de plataforma deve ser considerada base de desenvolvimento, nao memoria confiavel para decisoes criticas.

## O que os testes novos cobrem

Pareamento de uso unico, expiracao e concorrencia; hashes de segredos; revogacao; isolamento de pacotes por dispositivo; limites; idempotencia de notas; revisoes, conflitos e exclusoes; posse de sessoes; processamento de turnos com o ChatService real e provedor fake; repeticao do mesmo envio sem nova mensagem; recusa de reutilizacao do ID com outro texto; TLS/CORS, autenticao e limite de corpo; bloqueio de origens/proxies indevidos na API local; lock de instancia; backup SQLite; migracao somente quando necessaria; preservacao de banco desconhecido; versoes de releases; retirada dos imports antigos; modularizacao da UI.

O teste visual usa o HTML/CSS/JS do projeto com fetch e armazenamento nativo substituidos por fixtures em memoria. A politica do navegador deste ambiente bloqueou navegacao a localhost, portanto **nao e teste E2E da rede nem da janela nativa**. As capturas provam a renderizacao isolada, nao conexao com PC/celular real. Nenhuma politica do navegador foi desabilitada. O harness remove CSP apenas da copia isolada de teste para inserir fixtures; os arquivos entregues mantem a politica original.

Fluxos de UI exercitados: abertura de nova conversa, Configuracoes > Dispositivos, criar/gravar nota mobile, persistencia pela ponte simulada e rascunho offline sem envio. `tools/diagnostics/render_mock_ui.py` reproduz essa verificacao com Playwright/Chromium opcionais.

## Reproduzir

Use um diretorio de dados de teste, nunca o perfil pessoal. Na raiz do projeto e com as dependencias de desenvolvimento instaladas:

```sh
python -m pytest -q
python -m pytest -q tests/test_v08_platform.py
node --test tests/mobile/*.test.mjs
python -m compileall -q src
```

Os workflows GitHub repetem os testes em Python 3.12. O gate da fundacao e separado da suite integral, que permanece publicada como resultado de regressao e aviso quando falha. Os workflows estao escritos, mas nao foram executados em uma conta GitHub nesta entrega.

## Homologacao necessaria antes de uso principal

Validar Windows: instalacao nova, `.env` existente, WebView2, caminho com espacos/acentos, porta ocupada, duas aberturas, banco antigo e encerramento durante inferencia. Validar Android: build, assinatura permanente, teclado/insets, estado criptografado apos reinicio, erro de armazenamento sem sobrescrita, TLS, expiracao/revogacao, queda durante envio e atualizacao do APK preservando dados. Testar a busca com o backend de embeddings realmente usado no PC, sobretudo ao migrar entre Chroma e SQLite.
