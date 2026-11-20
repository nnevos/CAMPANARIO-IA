# CAMPANÁRIO R2.1 — atualização manual sem PowerShell

**Pré-requisito:** `CAMPANARIO-IA` já atualizado para **R2**. Feche o Campanário e todos os serviços antes de copiar arquivos.

1. Faça backup de `CAMPANARIO-IA` e do `CAMPANARIO-DATABASE` (não envie dados privados).
2. Extraia `CAMPANARIO_R21_ARQUIVOS_PARA_COPIAR.zip` **fora** da pasta do repositório.
3. Copie o **conteúdo interno** do ZIP para `C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA`, mesclando diretórios e substituindo apenas arquivos homônimos **após comparar personalizações**.
4. Preserve `.env`, `CAMPANARIO-PYTHON\.venv`, todo o Database, ZIM e memórias.
5. Teste o launcher, a Central de Cérebros e uma consulta documental/planilha real. Um `Campanario.exe` antigo pode continuar usando seu código compilado — verifique qual caminho o launcher inicia.

**Não exige PowerShell, migração ou nova dependência.** A R2.1 adiciona dependências obrigatórias/opcionais verificáveis, validação de proveniência de resultados e exige autorização explícita para as ferramentas **via registro de capacidades** quando a flag V9 está ligada. A API web de Utilidades mantém a política antiga e continua pendente para R1.

Leia `docs/current/R21_DEPENDENCIAS_PROVENIENCIA_PERMISSOES.md`, `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md` e `docs/operations/FAILSAFE_V9_CEREBROS.md` antes de ativar recursos.
