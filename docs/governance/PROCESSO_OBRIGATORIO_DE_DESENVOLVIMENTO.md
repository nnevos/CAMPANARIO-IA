# Processo obrigatório de continuidade — CAMPANÁRIO

**Checkpoint documental:** R2.8 · 23/11/2026.

Toda entrega que modifica código deve realizar a seguinte sequência, nesta ordem:

1. **Inventário comprovado:** ler código real, testes e documentação; identificar fase/gate, versão de base e quais dos três repositórios estão acessíveis; não confundir catálogo com executor.
2. **Decisão única:** selecionar a próxima pendência do ROADMAP canônico e da trilha V9, respeitando o FAILSAFE. Registrar objetivo, dependências, aceite e rollback; não começar vários tópicos aleatórios.
3. **Implementação conservadora:** manter compatibilidade e dados; autorização central > identidade do agente; sem criar Database/.venv paralelos; V9.1 e Dark Matter preservados.
4. **Testes reproduzíveis:** testes novos para cada comportamento e abuso, sintaxe, regressão, diferenciação de falha histórica; indicar ambiente real e o que não foi testado.
5. **Documentação ATÔMICA:** na MESMA revisão atualizar `docs/current/ROADMAP.md`, `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md`, `docs/operations/FAILSAFE_V9_CEREBROS.md`, `docs/governance/MANUAL_TECNICO_VIVO.md`, `CHANGELOG_Rxx.md`, `LEIA_PRIMEIRO_Rxx.md`, `docs/operations/RESULTADOS_TESTES_Rxx.md`. Descrever mudança, função/arquivo, limitações, testes, próxima etapa e recuperação no Explorador.
6. **Gate:** executar `python scripts/check_documentation_gate.py`; CI exige presença, checkpoint compartilhado, seções de manual e, em mudanças de código, diff dos quatro documentos canônicos (base SHA do evento); divergência bloqueia merge na CI. O script não prova que o texto é verdadeiro: revisar contra o código.
7. **Entrega:** ZIP incremental relativo a `CAMPANARIO-IA/` e completo igualmente; excluir `.env`, credenciais, `.venv`, SQLite, dados e cache; testar CRC/SHA256, documentar rollback. Atualização por extração/cópia no Windows, sem PowerShell obrigatório.
8. **Não promover fases sem aceite:** F5 físico, R1 sandbox, R10 integrada e demais gates só fecham depois de código/testes/host real correspondentes.

## Regras de severidade

Se o código e o manual discordarem, o comportamento real do código é a evidência técnica; a versão **não está pronta** até corrigir documentos/testes. Se falhar teste crítico novo, corrigir antes de empacotar. Se regressão geral falhar, documentar baseline e manter gate aberto. Na ausência de Python/Database externos, implementar apenas código isolado no IA, nunca inventar conteúdo externo.

## Responsabilidade da IA desenvolvedora

Começar cada nova tarefa por esta página + manual + dois ROADMAPs + FAILSAFE; narrar claramente já implementado versus intenção. Não alterar histórico para esconder falhas; acrescentar checkpoint rastreável. A confirmação humana é sempre externa à IA. Nunca conceder permissão por arquétipo, talento, cérebro ou persuasão do modelo.

## Checkpoint R2.9 — regra de engenharia factual

Toda mudança em `brains/`, `chat/canonical_answer.py`, `chat/service.py` ou `chat/grounded_expression.py` exige testes explícitos de ausência de novas afirmações, de fonte inexistente, de conflitos e de identidade de Morgana/Todd. O LLM não é fonte de evidências. Resposta de cérebro deve manter literal o corpo factual compilado ou recusar, sem paráfrase livre; política central continua obrigatória. **R2.9** mantém a regra documental anterior: atualizar os dois ROADMAPs, FAILSAFE, Manual Vivo, changelog, instruções e relatório, rodar gate em CI e documentar regressões. Nada disso autoriza promoção de R1/F5 ou habilitação dos seis cérebros não instalados.


## Checkpoint R2.10 — teste de roteamento e afirmações

Além dos gates R2.9, todo release factual precisa provar: (a) conversa subjetiva não simula ferramenta desabilitada, (b) identidade e informação objetiva sem fonte não viram afirmações do LLM, (c) afirmação documental de cérebro exige trecho literal vinculado, (d) contradições/erros mantêm status e limitações honestos. Gate documental e atualização de 2 ROADMAPs, FAILSAFE e Manual Vivo seguem obrigatórios. Este checklist não comprova verdade semântica ou ausência completa de alucinações.


## Checkpoint R2.11 — teste do bloqueio G2 e benchmark factual

Qualquer futura mudanca em memoria, verificacao de fontes ou motor factual precisa testar os seguintes controles: (1) resposta pessoal nao aprovada nunca chega ao cliente nem ao historico; (2) aprovacoes de LLM sem citações originais nao valem; (3) fonte recuperada de assunto similar mas atributo nao solicitado nao confirma a pergunta; (4) conflito de fontes nao vira `verified`; (5) falha de uma dependencia do sistema nao vira evidencia inventada. Testar, registrar baseline com ZIP anterior para falhas conhecidas e atualizar 2 ROADMAPs, FAILSAFE, Manual, changelog, instrucoes e relatorio. Nao desbloquear executores perigosos sem PF6/sandbox.


## Checkpoint R2.12 — critérios objetivos para a próxima IA desenvolvedora

Antes de qualquer código: auditar repositório e três documentos canônicos, verificar qual versão realmente está no código; selecionar um único bloqueio do ROADMAP; registrar previsão de testes (incluindo negativas/abstenções) e rollback. Para toda alteração factual, medir pertinência da pergunta, vínculo de fonte, conflito, insuficiência e resistência a injeção; não trocar `grounded` por alegação de verdade. Teste com stub incompleto de sessão não pode forçar remoção da validação real: corrigir fixtures no R2.13. Depois da implementação, atualizar *juntos* ROADMAP, ROADMAP V9, FAILSAFE, MANUAL_TECNICO_VIVO, changelog, relatório e instruções. Executar `scripts/check_documentation_gate.py`, subset e regressão ampla; classificar falhas preexistentes com baseline verificável. Nunca distribuir `.env`, `.venv` externa ou Database.

## Checkpoint R2.13 — auditoria dos próprios testes

Futuros testes devem representar os contratos atuais: testes que passam com stubs desatualizados ou que exigem comportamento inseguro do LLM não demonstram funcionamento real. Sessão inexistente é erro prévio a pesquisa; proposta de memória sem verificação não é resposta autorizada; chunks podem ser coalescidos por segurança; documentação histórica ausente no ZIP não deve ser inventada para mascarar inconsistência. Todo benchmark deve indicar se testa evidência literal, conflito **já classificado**, verdade externa ou apenas roteamento, e não equiparar as categorias. A atualização documental sincronizada permanece obrigatória. **R2.13** ainda não homologou a suíte geral, Windows ou repositórios externos.


## Checkpoint R3.0 — marcos de capacidade em vez de microversões

É obrigatório planejar e entregar marcos agregados com critérios verificáveis. Não criar uma nova versão de release apenas para cada correção de teste, refatoração ou pequeno ajuste de documentação. Preferir uma entrega com código operacional, testes negativos, benchmark e atualização atômica de ROADMAP principal, ROADMAP V9, FAILSAFE e Manual Vivo. A expansão de cérebros exige executor registrado e realmente executado, autorização de leitura/escrita adequada, isolamento compatível, integração com `CanonicalAnswer` e testes. **Catálogo não é executor, métrica de testes não é prova de verdade, e release number não é promoção de gate.** R3.0 prova apenas a revisão numérica conservadora do caminho factual existente; os demais cérebros seguem pendentes.

A cada nova entrega: (a) escolher necessidade factual mensurável; (b) verificar fonte, autoridade, contrato, falha e recuperação; (c) manter voz fora do foco solicitado sem fechar F5; (d) realizar baseline Windows/Python/Database quando disponível, sem inventar acesso; (e) incluir changelog, relatório, instruções, ZIPs SHA/CRC e atualizar os quatro arquivos canônicos; (f) rodar `scripts/check_documentation_gate.py`.


## Checkpoint R3.1 — critérios obrigatórios para cérebros de investigação e estratégia

Adicionar/alterar cérebro exige: (1) registro real com health-check e indicação de indisponível sem DB; (2) chamada do subprocesso first-party e política central; (3) contrato `BrainResult` com fontes auditáveis e relatório reproduzível; (4) revisão canônica anterior ao agente e impossibilidade de reescrever fatos; (5) testes de dados presentes/ausentes, permissões, adulteração, timeout e colaboração; (6) relatório de testes honesto, incluindo condições não homologadas. Relatório de hipóteses é condicional: não conferir culpa, causalidade, verdade externa nem autorização. Atualizar ROADMAP principal, ROADMAP V9, FAILSAFE, Manual Vivo, processo, changelog, relatório e instruções na mesma entrega. Rollback sem tocar nos repositórios Python e Database. Não avançar Programação sem sandbox OS.


## Checkpoint R3.2 — desenvolvimento por marcos completos de uso

A partir do cenário didático Operação Eclipse, toda entrega de investigação deve avaliar o fluxo ponta a ponta: caso, original, integridade, fonte, evento (registrado versus proposto), hipóteses concorrentes, relatório, identidade do operador e rollback. Um simulador não comprova investigação real. Não lançar microversões para ajustes triviais; agrupar funcionalidades correlatas e seus testes num único marco. **Nenhuma API de escrita de casos pode surgir sem autenticação/autorizações PF6 e testes de abuso.** A documentação dos dois ROADMAPs, FAILSAFE, Manual, este processo, changelog, relatório e instruções continua atômica.

## Checkpoint R3.3 — proibição de ferramentas isoladas para capacidades do produto

Uma funcionalidade de usuário final do Campanário (como investigação de casos) só pode ser chamada de **integrada** quando utilizável pela interface nativa Dark Matter e pelas APIs apropriadas, sem outra aplicação, janela de terminal ou nova aba. Um BAT/CLI pode permanecer para manutenção, mas não pode ser o único caminho de operação. Sempre testar navegação, login/sessão, autorização granular, persistência exclusivamente no Database, evidências, operações reversíveis, prova de ausência de caminhos arbitrários, isolamento entre identidades e saída factual. **R3.3 integra a Central de Casos na UI, não ao chat dos agentes** — não ocultar essa pendência. Continuam obrigatórias as atualizações atômicas de ROADMAP principal, ROADMAP V9, FAILSAFE, Manual Vivo, Processo, Changelog, relatório de testes e instruções, com gate automatizado. Preferir um marco funcional abrangente a várias microversões.


## Checkpoint R3.4 — investigação conversacional sem falsos marcos

É obrigatório integrar capacidades de usuário final à interface e chat nativos, com autenticação por identidade e isolamento por caso. Testes de frontend precisam confirmar que dados de casos não são enviados a LLM por conveniência, não são interpolados como HTML, e não aparecem em histórico/memória sem consentimento. Um relatório lexical de casos **não é** prova de execução dos quatro cérebros sobre os documentos do cofre. Antes de abrir essa integração, testar seleção de fontes com hash, autorização do `BrainExecutor`, degradação segura, contrato canônico e rollback sem tocar em DATABASE. Atualizar conjuntamente ROADMAP, ROADMAP V9, FAILSAFE, Manual Vivo, processo, changelog, relatório e instruções, e rodar gate documental. Três repositórios independentes, `.venv` externa e dados pessoais no Database sem duplicação.


## Checkpoint R3.4 — priorizar funcionamento real na instalação pessoal

Uma capacidade de usuário destinada exclusivamente ao PC pessoal não deve exigir ativar subsistemas experimentais não relacionados para funcionar. **Casos** são serviço da plataforma; o modo localhost sem PF6 é suportado quando credenciais PF6 não estão configuradas. Não generalizar para endpoints de ferramentas perigosas, acesso remoto ou gravação fora de CAMPANARIO-DATABASE. Testar loopback, origem, modo autenticado legado, recuperação e a fronteira factual. A cada entrega atualizar ROADMAP (2), FAILSAFE, Manual Técnico Vivo e este processo, changelog, instruções, testes e rollback; documentar que o consentimento visual local não é segurança de API.

## Checkpoint R3.5 — gate obrigatório de conteúdo factual em casos

Todo novo marco deve comprovar que uma pergunta de caso lê apenas originais autorizados e preservados; que adulteração, evidência ausente, formato não suportado, prompt injection e contradição não viram fatos; que trechos citados correspondem literalmente às fontes; que arquivos privados permanecem no Database externo; e que personalidade não altera citações. Testar fluxo na UI atual e não entregar programa paralelo. Manter os quatro documentos canônicos atualizados conjuntamente, além deste processo, changelog, resultados reais, instruções e ZIPs verificáveis. O foco em desenvolvimento maior não permite declarar homologação sem testes Windows/Ollama/Database; R3.5 reforça a leitura documental, não conclui investigação autônoma.

## Checkpoint R3.6 — provas obrigatórias para capacidades semânticas e visuais

Cada atualização que afirme 'entender documentos', 'interpretar imagem' ou 'investigar automaticamente' deve provar (1) formatos realmente decodificados; (2) extração com localizador e hash; (3) caso de OCR errado/ausente; (4) indisponibilidade Ollama e não uso de rede remota; (5) hipóteses não promovidas a culpa/causa; (6) testes no host para alegações de produção e degradar sem falhar quando subsistema opcional não está presente. Registrar claramente o que usa modelos generativos/embeddings, quais bytes locais recebem e as limitações de modelos. Nunca chamar OCR de compreensão visual universal. ROADMAPs, FAILSAFE, Manual Vivo, Processo, changelog, resultados, instruções e ZIPs continuam atômicos; atualizar apenas IA com .venv única em PYTHON e dados no DATABASE.

Todo modelo visual deve retornar rótulo explícito de hipótese não verificada; não incorporar descrição gerativa ao cofre como prova. Testar ausência de modelo, impossibilidade de acesso remoto ao Ollama, hash alterado e não persistência automática.


## Checkpoint R3.7 — alegações de universalidade e autonomia

Não aceitar a palavra **universal** como critério de aprovação sem definir formatos, línguas, fontes, pressupostos, margem de erro e benchmark representativo. Toda investigação iterativa deve expor limite de rodadas e motivo de parada, provar que suporte a perguntas secundárias não confirma a principal, testar ausência de origem/hashes adulterados e impedir ações automáticas não autorizadas. Leitores de novos formatos precisam de limites de tamanho, de descompressão e testes com scripts/mídia hostil. Continuam obrigatórias a atualização conjunta dos dois ROADMAPs, FAILSAFE, Manual Vivo, Processo, changelog, resultados e instruções, e entrega de ZIP incremental/completo com verificação. Todo dado pessoal fica no DATABASE, `.venv` única no PYTHON e código no IA.


## Checkpoint R3.8 — gate para relações e planos investigativos

Uma alteração em Investigação ou Estratégia deve passar por testes de integridade, identificação de cada citação, deduplicação de consulta, ausência de causalidade inventada e diferenciação entre posições pró/contra **registradas** e evidências que semanticamente corroboram essas posições. O pipeline deve continuar só-leitura, limitado, auditável e integrado ao chat existente. É proibido promover resultados de follow-up para suporte da pergunta principal. Continua obrigatório revisar conjuntamente ROADMAP principal/V9, FAILSAFE, Manual Vivo e este Processo, mais changelog, teste, instrução e ZIPs. Não redistribuir dados, `.env` ou `.venv`, nem declarar homologação Windows/Database/Ollama sem executá-la.

## Checkpoint R3.9 — gate de proposições auditáveis

Toda implementação que diga "entender o que um documento afirma" exige (a) citação literal com evidência/linha/hash, (b) classificação separada de verdade externa, (c) testes de hipótese, negação e atribuição, (d) pares com negação explícita em fontes distintas, (e) contraexemplos que **não** devem produzir conflito, (f) integridade e ausência de chamada generativa para alterar fatos, (g) atualização conjunta de ROADMAP, ROADMAP V9, FAILSAFE, Manual Vivo e Processo, (h) changelog, teste, instruções e ZIPs conferidos. Testes de regras não demonstram semântica universal. Manter IA/PYTHON/.venv/DATABASE separados; nunca criar ambiente ou DB extra.



## Checkpoint R3.10 — revisão de semântica sem promoção a fato

Qualquer nova interpretação generativa exige citação literal rastreável e validação de esquema fechado; sugestões jamais viram conclusões sem comprovação independente e revisão. Proibir conteúdo livre do LLM em respostas factuais canônicas, persistência automática de inferências e acesso remoto a documentos privados. Testar casos com atribuição, modalidade, negação, sarcasmo/contexto ausente e injeção adversarial. Diferenciar teste offline com modelo simulado de teste real com Ollama/Windows. Consolidar etapas maiores de validação em vez de releases triviais, com documentação obrigatória, relatório, testes negativos e ZIPs. Preservar CAMPANARIO-IA, CAMPANARIO-PYTHON/.venv externa e CAMPANARIO-DATABASE isolados.


## Checkpoint R3.11 — proibição de ativação cega e de benchmark fictício

Se a próxima atualização tentar habilitar funcionalidades desativadas, deve verificar executáveis e modelos locais, manter `.env` privado com backup, nunca ligar automaticamente rede/ação/permissões/serviços ausentes e realizar teste real antes de declarar homologação. Avaliação em corpus sintético com rótulos idênticos aos esperados não mede acurácia de modelo. Exigir métricas por classe em execução Ollama real e contraexemplos humanos antes de liberar novos cérebros. Atualizar os quatro documentos canônicos, este processo, changelog, testes e instruções; preservar CAMPANARIO-IA, CAMPANARIO-PYTHON/.venv única e CAMPANARIO-DATABASE separado.


## Checkpoint R3.12 — aprovação factual exigindo modelo real e revisão humana

É vedado chamar qualquer execução de `score(gold, gold)` de homologação de modelo. Uma liberação factual requer modelo Ollama real em loopback, duas passagens completas, métricas por classe, zero falsos conflitos no conjunto de triagem, relatório identificável e avaliação independente por humanos. Um PASS sintético é só pré-requisito, nunca aprovação da plataforma ou dos cérebros pendentes. Erros ou ausência de modelo = BLOCKED/INCONCLUSIVE. Em cada alteração atualizar ROADMAP principal/V9, FAILSAFE, Manual Técnico Vivo, este Processo, changelog, testes, instruções e verificar o gate documental. Preservar os três repositórios, sem .venv, DB ou segredos no IA.


## Checkpoint R3.13 — upload de anexo na instalação pessoal local

Correções de usabilidade em modo pessoal devem usar exceções de capacidade delimitadas, não desativar a política V9 globalmente. Antes de entregar, validar ambos os caminhos (sem PF6 e com PF6), testes de origem remota e de sobrescrita, documento FAILSAFE e cache frontend; informar que upload no chat **só guarda o arquivo** na pasta de utilidades, não o indexa automaticamente. Preservar três repositórios, `.venv` externa e `.env` privado.


## Checkpoint R3.14 — prioridade de uso pessoal local

Antes de adicionar PF6, ACLs ou confirmações ao fluxo padrão, verificar se existe necessidade real para uso local por um único operador. O padrão R3.14 é `CAMPANARIO_LOCAL_PERSONAL_MODE=true`, sem login e sem autorização extra nos Casos/utilidades. Testar modo pessoal e restauração opcional do modo multiusuário, integridade e reabertura dos casos antigos. Limites de RAM/disco não são equivalentes a permissões de acesso e devem ser implementados por streaming quando viável. Preservar validação factual, nomes, caminhos, loopback e proibição de sobrescrita. Exigir atualização conjunta dos dois ROADMAPs, FAILSAFE, Manual Vivo, Processo, relatório, changelog e dois ZIPs comparados com base R3.13. Sem `.env` privado, `.venv`, DATABASE ou segredos no pacote.


## Checkpoint R3.15 — biblioteca realmente acessível e respostas ligadas ao documento

**Falha real reportada:** clipe do chat fazia apenas staging de arquivos, mas não invocava `library.import`; portanto, um arquivo presente em `CAMPANARIO-DATABASE/dados/.../utilidades/arquivos/` podia não existir em `documents` nem em `document_sections`, impossibilitando `search_document`. A UI não tornava essa distinção visível. Uma continuação com `qual` sem interrogação era classificada como conversa genérica, fazendo o modelo responder sem a fonte desejada.

**Correção integrada na UI:** chat passa `index=true` em `upload-stream`; o endpoint preserva o arquivo no workspace, importa por `UtilityService` no mesmo DATABASE externo e retorna `indexed`, `indexed_sections`, `index_state`, `document_id` ou `index_error` sem fingir êxito. Importação é feita em thread durante a requisição, nunca em background silencioso. PDF sem texto/OCR ausente e JSON inválido são marcados como não pesquisáveis. Arquivos antigos enviados somente ao staging: em Ferramentas → Arquivos, usar **Indexar**; documentos com erros: Ferramentas → Biblioteca → **Reindexar**. O original continua imutável, com SHA-256 validado antes da reindexação.

**Gerenciamento:** o Explorador e a Biblioteca têm paginação (100 itens/página e total real), nomes, estados, visualização do texto extraído, exclusão e renomeação. A Biblioteca tem `library.rename` (metadados apenas, preservando extensão/arquivo) e `library.reindex` (reextração do original validado e substituição transacional da indexação). Arquivos na pasta autorizada oferecem Indexar/Renomear/Mover/Lixeira. O conteúdo original preservado não é editado diretamente; nova versão deve ser importada conscientemente. Chat permanece na interface Dark Matter, sem nova aba/aplicativo de investigação.

**Intenção documental:** `document_request` reconhece “arquivo relacionado a ordem paranormal” e remove o sufixo “e me diga...” do nome sugerido. Perguntas de acompanhamento com “qual/quais/quem...” sem `?` mantêm a referência explícita recente ao documento; falta de citação continua exigindo abstenção factual. Nenhum nome de criatura da franquia foi codificado como resposta. Trecho recuperado mostra **o que a fonte diz**, não valida cânone externo.

**Verificação:** 90 testes direcionados PASS, incluindo regressões V8, PF6 pessoal, cérebros, casos e semântica; regressão geral: 33 PASS, 1 falha preexistente em `uv.lock` ausente. Compilação e JavaScript verificados. Não houve acesso ao acervo privado do operador nem homologação com Windows/Ollama reais. **Rollback:** fechar o Campanário, restaurar a cópia R3.14 do código e reiniciar; preservar o DATABASE. Metadados criados nesta versão são compatíveis com schema V8; cópia privada de segurança recomendada antes de reindexar ou excluir.


## Processo obrigatório — checkpoint R3.16 Maps V2

Antes de anunciar navegação pronta: executar testes unitários e de API com geometria real de fixtures, separar simulados de GPS de campo, verificar builds JavaScript e Android, documentação e ZIPs. Não usar dados de demonstração como rotas reais, não inventar coordenadas ou ETA, testar especificamente aba Chat versus Patrulha e retorno, e registrar indisponibilidade do OSRM/Nominatim/Overpass no ambiente. Os serviços autogerenciados e dados OSM exigem instalação consciente e backup, sem baixar conteúdo automaticamente para DATABASE. O cliente Android não tem ForegroundService nesta release; homologação de rota em segundo plano está aberta. Preservar personalidades dos agentes, V9.1 e três repositórios.


## Checkpoint R3.17 — validação Android obrigatória antes de chamar APK pronto

Nenhum arquivo `.apk` pode ser anunciado sem compilação via Android SDK + Gradle, arquivo existente verificado, assinatura e instalação experimental documentadas. Distinguir testes Python/JS e inspeção Java de build Android/ensaio de sensor e direção em campo. O Field mantém três repositórios irmãos e a experiência integrada; nunca criar sistema de chat independente no telefone nem abrir serviços do PC na internet. Para próximas entregas: prova de GPS foreground, notificações Android 13+, suspensão, roteamento OSM real, permissão revogada, TTS em aparelho, OTA assinado e compatibilidade da API. Entrega R3.17: fonte e documentação, compilação Android pendente.

## Checkpoint R3.19 — protocolo de manutenção de projeto enxuto

A produção de pacotes para o proprietário requer: (1) inventário do ZIP real, (2) lista positiva de runtime e código Android, (3) exclusão de `.env`, bancos, pesos ONNX, `.venv`, `.git`, cachês e cópias antigas, (4) preserve `uv.lock`, `src`, `apps/mobile/android` + `apps/mobile/www`, (5) testes GPS com e sem origem, (6) CRC e SHA256, (7) instruções de troca por **renomeação de pasta**, nunca mescla em instalação poluída. Testes simulados não equivalem a navegação real ou APK assinado. Restaurar pasta antiga se a inicialização falhar sem tocar PYTHON/DATABASE.


## R3.20 — localização automática e busca/rota com fallback (23/11/2026)

- Ao abrir Maps no Dark Matter, o cliente tenta `navigator.geolocation.watchPosition` automaticamente, conforme a autorização do Windows/navegador. Mantém latitude, longitude, precisão e horário somente em memória de interface; não envia localização ao servidor durante a simples observação. Sem GPS, busca por endereço permanece disponível e a origem manual continua possível.
- A tela Maps usa somente `CampanarioNavigationV2` para os botões de busca/rota, evitando que o antigo `gps-map.js` sobrescreva os handlers.
- Busca por endereço: Nominatim local primeiro; se estiver indisponível, Nominatim público em consulta explícita. Categoria próxima: Overpass local e depois público; roteamento carro: OSRM local e, se estiver indisponível, servidor público de demonstração OSRM. Caminhada: somente grafo pedestre local (não inventar rota de carro).
- O fallback está **ativado por padrão para uso pessoal** e pode ser desativado com `CAMPANARIO_MAPS_PUBLIC_FALLBACK=false`. Serviços públicos recebem a busca e, em roteamento, as coordenadas. Nominatim público tem limitação de uso, identificação do aplicativo, cache em memória e espaçamento de 1,1 s por host; não usar autocomplete nem disparar varreduras. Não há GPS fictício.
- Pendente: teste de campo em Windows/Android; conectividade e política dos provedores públicos; precisão do GPS no PC; compilação APK e navegação Android em segundo plano. Não declarar homologação de campo.


## Checkpoint R3.21 — Field GitHub Pages (23/11/2026)
- Frontend PWA público estático, isolado em `pages/`, com GPS do navegador, mapa OSM e consulta de rotas públicas; não contém dados privados.
- Servidor Python/Ollama/Database continuam exclusivamente no PC; acesso opcional via listener Companion HTTPS autenticado e CORS para origem Pages explicitamente configurada.
- Compatibilidade e limitações: consulta cartográfica pública sujeita a quota, rota de carro somente, GPS em primeiro plano, sem APK nem homologação em campo; tela e notas offline, sem roteamento offline.
- Implantação reversível: excluir publicação Pages / desabilitar `CAMPANARIO_FIELD_PAGES_ORIGIN`; sem migração de dados e sem alterações nos três repositórios externos.
- Testes da alteração e pendências descritos em `docs/operations/RESULTADOS_TESTES_R321.md`. Não declarar homologado o acesso real a PC ou geolocalização do usuário.
