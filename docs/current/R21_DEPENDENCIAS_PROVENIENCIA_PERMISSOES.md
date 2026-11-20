# CAMPANÁRIO R2.1 — Contratos de colaboração, proveniência e autorização

**Base:** R2 V9 + V9.1. **Escopo:** incremento experimental de segurança do `CAMPANARIO-IA`; não declara os gates R0/R1/R2 concluídos. **Data:** 19/11/2026.

## Fluxo realmente implementado

```text
ChatService → AgentRouter (quem fala)
            → CapabilityRouter (quais capacidades, até 3)
            → BrainPlan / BrainStep (escopos, contratos e dependências)
            → BrainExecutor (permissão da sessão, orçamento e circuit breaker)
            → KnowledgeBrain/AnalysisBrain (subprocessos de leitura)
            → validate_brain_result (traces, operações, evidências e guard)
            → consolidate_read_only (resposta canônica + limites)
            → Grounded Expression V9.1 (Morgana/Todd, validação e fallback)
```

**Contratos:** `BrainStep.dependency_policy` vale `optional` ou `required` (padrão `optional` para não quebrar a R2). Uma etapa `required` não executa se qualquer dependência não tiver leitura **concluída com evidência first-party validada**, retornando `dependency_not_met`. Uma dependência `optional` pode executar independentemente, recebendo `upstream_evidence_ids=[]` se a etapa anterior falhou. O plano gerado pelo roteador para documento + planilha permanece **opcional** porque o cálculo deve continuar utilizável quando o documento não existe; nunca afirma ter comparado semanticamente as fontes.

`input_contract` aceita `user_query` ou `user_query_plus_prior_evidence_metadata`, e `output_contract` apenas `brain_result_v9`; contratos desconhecidos são recusados. Para **planos compostos**, `trace_id` e `intent` da requisição devem coincidir com o plano antes do primeiro worker. Planos legados de um cérebro ainda preservam tolerância à divergência no `trace_id` por compatibilidade; unificar esse contrato depende da migração dos callsites antigos.

`result_validation.py` rejeita operação inválida, evidência duplicada, resultado `failed/unavailable` com fonte, `completed` sem operação e, nos dois cérebros locais, divergências entre IDs/títulos/trechos do `guard` original e `EvidenceRef`. A propagação de fontes entre etapas fica restrita a resultados completos **dos dois adaptadores first-party**; respostas de extensões/testes em processo não são automaticamente reconhecidas como evidência documental. Isso reduz citações falsas, mas não estabelece a verdade externa do documento.

**Política de execução:** quando `CAMPANARIO_BRAINS_V9_ENABLED=true`, a composição configura `CapabilityRegistry` para exigir um `AuthorizationContext` explícito antes de executar **ferramentas com permissões declaradas**. Ausência do contexto resulta em `PermissionDeniedError`, sem invocar o provider nem emitir evento de execução bem-sucedida. O `PermissionPolicy` já existente decide `ALLOW/DENY/CONFIRM` e rege tanto o registro de capacidades quanto o executor de cérebros vinculado pelo runtime. A flag `false` mantém a política legada do registro para compatibilidade.

**Não confundir:** esta proteção do `CapabilityRegistry` **NÃO** protege automaticamente `POST /api/v1/utilities/invoke`, que ainda chama `UtilityService` diretamente na interface humana. Esse endpoint é loopback-only e tem confirmação anterior, mas **não** é autenticado/pareado nem integrado à confirmação central. Gate R1 permanece bloqueado. Não habilitar ações externas/Programação com base neste incremento.

## Três pastas, venv e bancos separados

```text
C:\Users\Steam Deck\Documents\GitHub\
  CAMPANARIO-IA\
    src\campanario\     # runtime, interface Dark Matter, módulos cérebro
    .env                  # configuração LOCAL PRIVADA — preservar
  CAMPANARIO-PYTHON\
    .venv\Scripts\python.exe   # Python 3.12 e dependências; sem copiar para IA
  CAMPANARIO-DATABASE\
    dados\desenvolvimento\   # SQLite e recursos de desenvolvimento
    dados\producao\         # SQLite e recursos de produção
    dados\reference\         # SQLite de referência V2 (opcional)
    zim\                     # conteúdo offline conforme configuração
```

`CAMPANARIO_DATA_DIR` aponta aos dados externos; `CAMPANARIO_MEMORY_ENVIRONMENT` escolhe desenvolvimento/produção; `CAMPANARIO_ZIM_DIR` controla a fonte offline ZIM. **Não mover bancos ou conteúdo para IA.** Existe fallback legado `interaction_library_v2.sqlite` no IA até que a migração por cópia com backup esteja homologada (P0). O launcher pode dar prioridade a `Campanario.exe` compilado, o qual **não** se atualiza automaticamente ao substituir arquivos `.py`; validar o interpretador em uso no Windows antes de assumir que o incremento está ativo.

## Instalação sem PowerShell

1. Fechar Campanário, gateway, serviços e executável para liberar arquivos.
2. Fazer cópia de segurança privada de `CAMPANARIO-IA` e `CAMPANARIO-DATABASE`; confirmar que pode restaurá-la (não enviar dados pessoais).
3. Extrair **`CAMPANARIO_R21_ARQUIVOS_PARA_COPIAR.zip`** em Downloads, fora do repositório.
4. Pelo Explorador de Arquivos, copiar **o conteúdo da pasta extraída**, preservando subpastas, para a raiz de `CAMPANARIO-IA`. Comparar arquivos personalizados antes de substituir; **não apagar ou substituir a pasta IA inteira**.
5. Preservar `.env`, `.venv` externa, `CAMPANARIO-DATABASE`, documentos, modelos e ZIM. Não há dependência ou migração de banco nova nesta etapa.
6. Abrir pelo launcher Python atual, preferencialmente conferindo a Central de Cérebros; executar uma consulta conhecida e conferir `brain_run`, evidência, resultado e fallback. Para desfazer, desligar V9 no `.env` e reiniciar; para restaurar código, repor somente os arquivos do backup com aplicativo parado.

**PowerShell não é necessário para a atualização de código.** Terminal pode ser usado para instalar dependências, rodar testes ou migrações autorizadas, não para mesclar atualizações.

## Testes e bloqueios

Casos novos em `tests/test_r21_dependency_integrity.py`: contratos inválidos, dependência obrigatória/opcional, confirmação de execução real de documento + CSV, documento ausente, identidade de plano divergente, recusa de fonte forjada, ferramenta sem autorização e confirmação pendente. Resultados quantitativos em `docs/operations/RESULTADOS_TESTES_R21.md`. Testado em Linux/Python 3.13; **não houve** homologação Windows/Python 3.12 do usuário, Ollama real, repositórios Python/Database reais, restauração de backup nem execução física mobile.

**Gates abertos:** unificação da autenticação/confirmacão de `/api/v1/utilities`, isolamento de rede/arquivos por sistema operacional, Windows Job Object, migrações no host real, semântica cruzada entre cérebros, revisão de documentos por hash/TTL e todos os cérebros ainda não implementados.
