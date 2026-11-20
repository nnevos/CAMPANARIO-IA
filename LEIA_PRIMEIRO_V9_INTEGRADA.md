> **P0 após V9+V9.1:** a atualização habitual do código é por cópia dos arquivos pelo Explorador, não pelo PowerShell. Consulte [P0 — 3 pastas, venv e Database](docs/current/P0_TRES_PASTAS_SEM_POWERSHELL.md) e [FAILSAFE atualizado](docs/operations/FAILSAFE_V9_CEREBROS.md). Scripts só são necessários para instalação, reparo, testes ou migração.

# CAMPANÁRIO — V9 cérebros integrada com V9.1 expressão fundamentada

Esta atualização **não substitui** Morgana, Todd, o roteador de falantes ou a V9.1. Acrescenta um roteador de capacidades independente, dois cérebros operacionais (Conhecimento e Análise), fichas de agentes, oito arquétipos, seis talentos declarativos, persistência, APIs locais, Central de Cérebros, Forja e importação segura de `.campagent`.

A flag `CAMPANARIO_BRAINS_V9_ENABLED` fica **desativada por padrão**. Consulte **`docs/current/V9_BRAINS_ARQUETIPOS_TALENTOS.md`** para instalação segura e migração `0010`. Não aplique diretamente sobre V8: o patch verifica a V9.1 anterior. Não sobrescreva sua instalação sem backup externo do `CAMPANARIO-DATABASE`, `.env` e código personalizado.

O projeto completo inclui somente `CAMPANARIO-IA`. Os outros dois repositórios não foram enviados nem alterados. A execução dos testes foi local, não no Windows/Android da instalação final.
