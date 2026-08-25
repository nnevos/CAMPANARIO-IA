# ADR-0024 - Contract Enforcement + Context Provenance

## Status
Aceito - 2026-08-24

## Contexto
O E2E da v1.5.2 mostrou dois limites: retries podiam continuar quebrando contratos estruturais e conteudo criativo gerado pelo assistant podia reaparecer como explicacao factual posterior.

## Decisao
1. Contratos objetivamente verificaveis recebem enforcement deterministico apos um retry falho. O enforcement pode remover excesso e ajustar fronteiras de frases, mas nao inventa fatos.
2. Contexto recente recebe proveniencia interna. Saidas do assistant sao nao autoritativas; saidas originadas em `TurnMode.CREATIVE` sao `assistant_fiction_nonfactual`.
3. Em turnos `FACTUAL_SIMPLE` ou `TECHNICAL`, o texto bruto dessas saidas criativas e omitido do request ao modelo e substituido por marcador sem conteudo. O transcript persistido permanece intacto.
4. O E2E deve detectar falsos positivos do proprio avaliador e reutilizacao de termos inventados, sem hardcode de respostas no runtime.

## Consequencias
- criatividade continua livre no turno solicitado;
- diminui contaminacao ficcao -> fato;
- contratos de formato/budget passam a ser mais confiaveis;
- factualidade aberta ainda depende do modelo e das futuras camadas de grounding.
