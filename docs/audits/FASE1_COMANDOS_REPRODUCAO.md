# Fase 1 — Como reproduzir no ambiente de desenvolvimento

**Precondicao:** extrair `CAMPANARIO_IA_ETAPA3_CORRIGIDO_COMPLETO.zip` em diretório separado, sem copiar bancos/`.env` de producao. **Nao executar sobre memórias reais sem backup.** Esta auditoria nao alterou o codigo.

## Windows / PowerShell — Python 3.12 recomendado

```powershell
cd .\CAMPANARIO-IA
python --version
# Preparar ambiente de desenvolvimento com dependencias ja baixadas ou ambiente de build isolado:
# uv sync --group dev
$env:PYTHONDONTWRITEBYTECODE="1"
python -m pytest tests -q --tb=short -p no:cacheprovider
python -m pytest -q -p no:cacheprovider tests/test_utilities_offline.py tests/test_factual_quem_e.py tests/test_etapa3_grounding_naturalidade.py tests/test_agents.py tests/test_event_bus.py
```

## Linux — replica do comando utilizado na auditoria (Python 3.13.5)

```bash
cd CAMPANARIO-IA
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests -q --tb=short -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_utilities_offline.py tests/test_factual_quem_e.py tests/test_etapa3_grounding_naturalidade.py tests/test_agents.py tests/test_event_bus.py
```

**Resultado obtido nesta maquina:** 655 passed / 30 failed / 14 warnings em 34,96 segundos no teste geral; 73 passed em 1,47 segundos no recorte. Resultados futuros podem diferir com Python 3.12, fixtures, dependencias e configuracao local.

## Inspecao estatica sem alterar codigo

```bash
# Linux
rg -n 'def (research_entity|research_topic|render_context)|library.search|_web_auto_search|def (resolve|decide)' src/campanario
rg -n -i 'todd|morgana|agent_id\s*(==|!=)' src/campanario/agents src/campanario/chat src/campanario/utilities
find . -iname '*.zim'
```

## Provas pontuais documentadas

`FASE1_EVIDENCIAS/provas_offline.txt`: biblioteca temporaria `prova.md` importada e pesquisada; contraste de `direct_decision` e `natural_uncertainty`.

`FASE1_EVIDENCIAS/prova_runtime_sem_ollama.txt`: chat construido em SQLite temporario e perguntas `quem foi Ada Lovelace?` (abstencao offline) e `Ola, tudo bem?` (falha do Ollama, que nao roda nesta maquina); teste de terceiro agente por perfil novo em memoria, sem tocar em arquivos do projeto.

`FASE1_EVIDENCIAS/prova_grupo_offline.txt`: chamada de grupo com Todd e Morgana e pesquisa auto desativada; dois speakers, duas abstencoes.

`FASE1_EVIDENCIAS/provas_entrada_grupo.txt`: cobertura de preflight para vocativos e lacunas do regex.

**Limitacoes nao reproduzidas:** Qwen/Gemma real, tempo ate primeiro token, latencia/VRAM, Windows 3.12, queda de internet durante geracao, Kiwix real. Nao converter simulacoes em homologacao.
