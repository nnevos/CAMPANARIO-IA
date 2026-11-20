# CAMPANARIO P0 — atualizar codigo SEM PowerShell

**Base exigida:** CAMPANARIO-IA com V9 + V9.1 integradas e o roadmap/failsafe documental anterior. **Este pacote altera somente o repositorio IA.**

## Passo a passo no Explorador de Arquivos

1. Feche totalmente o Campanario e o servidor/voz local.
2. Faça um backup privado de `CAMPANARIO-IA` e `CAMPANARIO-DATABASE`. Preserve seu `.env` e suas vozes. NÃO apague o Python externo.
3. Extraia `CAMPANARIO_P0_ARQUIVOS_PARA_COPIAR.zip` em uma pasta temporaria fora do projeto, por exemplo `Downloads\P0_EXTRAIDO`.
4. Abra a pasta extraida, selecione o **conteudo interno** (README, `src`, `docs`, `tests`, `tools` etc.) e cole na raiz da pasta `CAMPANARIO-IA`. Ao perguntar, escolha **substituir os arquivos homonimos**. Nao exclua outros arquivos nem troque a pasta inteira.
5. Execute Campanario normalmente pelo atalho/`CAMPANARIO.vbs` e abra **Ferramentas > Central de Cerebros**. A verificacao das tres pastas aparece ate com V9 desligada.
6. Se houver `blocked`, siga `docs/current/P0_TRES_PASTAS_SEM_POWERSHELL.md` e `docs/operations/FAILSAFE_V9_CEREBROS.md` **antes** de qualquer migracao.

**Nao use PowerShell para copiar codigo.** Comandos so fazem sentido quando voce de fato precisa instalar/reparar `.venv`, instalar dependencias, aplicar migracoes ou rodar testes tecnicos. A atualizacao nao toca automaticamente `CAMPANARIO-PYTHON`, `CAMPANARIO-DATABASE`, `.env`, SQLite nem modelos Ollama.

**Cuidado com personalizacoes de codigo:** copiar via Explorador nao compara SHA-256 com versoes existentes. Se voce modificou arquivos do IA por conta propria, confira as diferencas e faça backup antes. `MANIFESTO_P0_SHA256.json` registra os hashes dos arquivos distribuidos, mas nao executa instalacao ou verificação no seu PC.

**Projeto completo:** o ZIP `CAMPANARIO_P0_IA_COMPLETO.zip` e uma **copia de referencia** do repositorio IA para inspeção/reinstalacao controlada, nao substitui as outras duas pastas. Atualizacoes comuns devem usar o ZIP menor de arquivos modificados.

**Status real do P0:** diagnostico e barreiras do executor implementados; homologacao Windows/venv/Database real, backup/restore e sandbox de processo permanecem pendentes. Consulte `docs/operations/P0_RELATORIO_EXECUCAO.md`.

**Exceção da Biblioteca V2:** o projeto original tem `IA/data/interaction_library_v2.sqlite` (referências estáticas, não memórias). O código prefere `DATABASE/dados/reference/interaction_library_v2.sqlite` quando existir. A cópia desse SQLite para a pasta separada é **manual e opcional nesta entrega**; não o apague antes de testar, conforme o guia P0.
