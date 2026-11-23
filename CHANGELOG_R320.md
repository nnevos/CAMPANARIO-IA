# R3.20 — Maps automático e fallback público

**Base:** pacote limpo R3.19 fornecido no chat.

- Corrige mensagem de geocodificador local indisponível após pesquisar: fallback Nominatim / Overpass para buscas solicitadas, OSRM público somente para carro, preferindo serviços locais e sem resultados fabricados.
- Localização automática no Maps enquanto montado, com timestamp e precisão, autorização gerenciada por OS/navegador, origem manual mantida. Nenhum upload contínuo de GPS só por abrir Maps.
- Remove conflito dos handlers entre gps-map.js e navigation-v2.js. Atualiza mensagens e cache bust JS.
- Limita uso público via cache em memória (sem histórico), ritmo de até 1 solicitação por segundo por host, consultas explícitas e User-Agent próprio configurável.
- Limitação: serviços públicos best-effort, não garantidos; walk exige grafo pedestre. Provedores recebem consulta/coordenadas e estão habilitados por padrão porque operador solicitou Maps online.
- Testes e homologação: ver docs/operations/RESULTADOS_TESTES_R320.md. Não compilado em Android, nem homologado com GPS em aparelho real.
