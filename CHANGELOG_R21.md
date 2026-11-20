# Changelog — R2.1: contratos, proveniência e autorização opt-in

Base: CAMPANÁRIO R2 IA. Incremento aditivo, sem migrações.

- `brains/router.py`: contrato de dependência `optional|required`, entradas e saídas permitidas; representação pública da política sem inventar resultados.
- `brains/result_validation.py` (novo): verificação determinística entre operações, fontes, resultados e guard first-party.
- `brains/executor.py`: bloqueio de dependência obrigatória, proveniência autorizada e consistência `plan.trace_id/intent` antes de plano composto; não propaga evidências de extensões não reconhecidas.
- `runtime/capabilities.py` e `composition.py`: registro geral requer `AuthorizationContext` explícito para ferramentas com permissões quando V9 está ativada, evitando fallback implícito ao principal interno; comportamento anterior preservado com flag desligada.
- `tests/test_r21_dependency_integrity.py` (novo): ensaios positivos/negativos, arquivos reais sintéticos e negação antes do provider.
- ROADMAP, FAILSAFE, relatório de testes e manual de três pastas/atualização atualizados.

**Não implementado:** unificação de confirmação em `/api/v1/utilities/invoke`, sandbox OS, 6 cérebros restantes, semântica multi-fonte, homologação Windows/Python 3.12/Ollama real. O resultado das ferramentas existentes nunca autoriza permissões adicionais.
