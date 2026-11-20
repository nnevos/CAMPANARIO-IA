# CAMPANÁRIO R2 — Instalação incremental sem PowerShell

Este pacote contém apenas código/documentação de **CAMPANARIO-IA**, partindo da **R1.1**. Não aplique o ZIP de arquivos isolados sobre V8/P0/R1 sem as etapas intermediárias; para uma instalação limpa do código IA use o ZIP completo, **sem apagar seus dados nem as outras duas pastas**.

1. Feche o Campanário, os serviços e o EXE que possam estar usando o código antigo.
2. Faça backup **privado** de `CAMPANARIO-IA` e `CAMPANARIO-DATABASE` em outro disco/local.
3. Extraia `CAMPANARIO_R2_ARQUIVOS_PARA_COPIAR.zip` numa pasta temporária fora do projeto.
4. Selecione o conteúdo **dentro** da pasta extraída, copie para `C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA` e **mescle** as pastas; substitua somente arquivos com o mesmo nome. Compare arquivos personalizados antes de confirmar.
5. Não copie `.env`, `.venv`, Python externo, SQLite, documentos, memórias, conversas, ZIM nem modelos. **Não apague a pasta IA inteira.**
6. Inicie pelo launcher habitual, confira a Central de Cérebros e teste um documento, um CSV e uma consulta combinada. `CAMPANARIO_BRAINS_V9_ENABLED=true` habilita a V9 experimental; `false` preserva o fluxo legado.

Não é necessário PowerShell **para atualizar o código**; comandos só podem ser necessários para instalar dependências, diagnosticar o ambiente ou executar migrações explicitamente aprovadas. A R2 parcial não adiciona migração/dependência. O manifesto SHA-256 identifica os arquivos, mas **cópia manual não verifica o arquivo instalado nem cria backup por você**.

**Limitações:** somente Conhecimento e Análise funcionam; a consulta combinada põe evidências/cálculos lado a lado, sem comparação semântica automatizada. `Campanario.exe` pré-compilado pode não usar o novo código. Python 3.12, Ollama, mobile e os repositórios externos não foram homologados.

Documentação: `docs/current/R2_PLANEJAMENTO_COLABORACAO_CEREBROS.md`, `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md` e `docs/operations/FAILSAFE_V9_CEREBROS.md`.
