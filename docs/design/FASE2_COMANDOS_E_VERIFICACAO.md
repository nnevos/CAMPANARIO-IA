# Fase 2 — Verificação, comandos disponíveis e limites

**A Fase 2 é APENAS DESENHO.** Nenhum teste de implementação nova foi executado, porque nenhum código foi alterado. O baseline abaixo é da Fase 1, registrado em logs já entregues; não é resultado novo.

## Windows PowerShell — comandos existentes hoje

Preparar **somente uma cópia limpa** de `CAMPANARIO_IA_ETAPA3_CORRIGIDO_COMPLETO.zip`. Não substituir dados da instalação. Usar Python 3.12, não a versão 3.13 da auditoria.

```powershell
cd .\CAMPANARIO-IA
python --version
# Instalar/usar dependências de desenvolvimento já disponíveis conforme README do projeto.
$env:PYTHONDONTWRITEBYTECODE="1"
python -m pytest tests -q --tb=short -p no:cacheprovider
python -m pytest -q -p no:cacheprovider tests/test_utilities_offline.py tests/test_factual_quem_e.py tests/test_etapa3_grounding_naturalidade.py tests/test_agents.py tests/test_event_bus.py
```

## Inspeção de configuração e modelos — não altera modelos

```powershell
Get-Content .\.env.example
ollama list
ollama ps
nvidia-smi
```

Não rodar `ollama pull`, migrations, `web.save`, importações nem script de atualização sobre os dados reais nesta fase.

## Referência reproduzida na Fase 1

- Suíte completa: `655 passed, 30 failed, 14 warnings` (Linux, Python 3.13.5, incompatível com versão declarada).
- Recorte direcionado: `73 passed`.
- Evidências: `FASE1_AUDITORIA_CAMPANARIO.md`, `FASE1_EVIDENCIAS/pytest_suite_completa.log`, `provas_offline.txt`, `prova_runtime_sem_ollama.txt`, `prova_grupo_offline.txt` **no pacote anterior da Fase 1**, não duplicados neste ZIP.

## Checklist da próxima fase

- Versionar corpus sintético e fontes locais com hash/data, ~50+20 casos, offline/online e cenários multiagente.
- Criar comandos de um único runner reprodutível; registrar caso bloqueado quando Kiwix/modelo não disponíveis.
- Medir no hardware Windows alvo e confrontar 4096/8192 tokens e dois modelos quantizados.
- Registrar métricas de verdade/abstinência/citação/consistência/latência/VRAM antes de qualquer correção.
- Exigir aprovação explícita antes de iniciar a Fase 3 e novamente antes de implementar a Fase 4.
