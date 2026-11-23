# Testes Campanário R3.21 — GitHub Pages

Procedimento: `python -m pytest -q tests/test_r321_pages.py`, `node --check` dos módulos JS da pasta `pages`, inspeção do workflow de deploy e integridade ZIP.

**Não houve teste com telefone GPS físico, servidor Ollama, gateway HTTPS com certificado real, publicação GitHub Pages autenticada ou serviços OSM públicos ao vivo neste ambiente.** Testes com HTTP simulado ou servidor local não substituem esses cenários. Sujeito a disponibilidade de bibliotecas.

Critérios: servidor remoto só autoriza origem Pages explicitamente configurada; origem `appassets` continua válida; conteúdo estático não inclui dados privados; mapa não usa coordenadas fictícias; navegador exige autorização; fallback de origem manual disponível; notas locais em IndexedDB; token efêmero na aba; ZIP full preserva código de PC e Android. 

Execução neste ambiente: **4/4 testes de contrato R3.21, 31/31 testes direcionados Python (incluindo aqueles 4), 19/19 JavaScript mobile**. Verificação de sintaxe Node para os módulos web, compilação Python e gate documental: PASS. A validação visual no Chromium em modo headless não pôde ser concluída porque a execução travou ao tentar carregar tiles externos; isso não foi contado como teste aprovado.
