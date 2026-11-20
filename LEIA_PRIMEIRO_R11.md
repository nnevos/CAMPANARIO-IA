# Campanário R1.1 — Próximo incremento de segurança dos cérebros

Este ZIP é uma **atualização incremental para quem já possui o código R1**. Não aplique sobre V7/V8/P0 isoladamente. Instale **copiando arquivos pelo Explorador**, sem PowerShell.

1. Feche Campanário e faça backup do IA e Database em local privado.
2. Extraia `CAMPANARIO_R11_ARQUIVOS_PARA_COPIAR.zip` em outra pasta.
3. Copie **todos os arquivos e subpastas internos do ZIP** para `C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA`; mescle e substitua somente homônimos. Se o código local foi personalizado, compare antes de substituir.
4. **Não remova** sua pasta IA. **Não substitua** `.env`, `CAMPANARIO-PYTHON`, `.venv`, `CAMPANARIO-DATABASE`, memórias, chats nem SQLite.
5. Abra pelo launcher habitual. Se ele prioriza `Campanario.exe`, ele pode estar usando código compilado antigo; consulte o FAILSAFE antes de concluir que o novo worker está ativo.

**O que mudou:** orçamento compartilhado entre cérebros, contenção de falhas por circuit breaker, ambiente do worker menos exposto a segredos, bloqueio aplicativo de chamadas de rede Python, e testes de encerramento por cancelamento.

**O que NÃO mudou:** P0, R1, V9/V9.1, memória e perfis, Ollama, dados externos e a `.venv`. Não foram criadas migrações nem dependências. **Não é sandbox OS ou liberação para executar scripts hostis.**

Documentos: [`R11_PROTECOES_EXECUTOR_CEREBROS.md`](docs/current/R11_PROTECOES_EXECUTOR_CEREBROS.md), [`ROADMAP`](docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md), [`FAILSAFE`](docs/operations/FAILSAFE_V9_CEREBROS.md), [`TESTES`](docs/operations/RESULTADOS_TESTES_R11.md).
