# ADR-0016 — Private corpus derivation boundary

## Contexto

Materiais conversacionais privados podem ser uteis para descobrir padroes gerais de pragmatica, mas manter o arquivo original, seu nome, hash ou qualquer identificador dentro do projeto cria risco de privacidade sem beneficio para o runtime.

## Decisao

O Campanario adota derivacao com descarte da origem privada:

- a fonte privada e usada apenas durante a analise autorizada;
- nenhuma copia da fonte privada entra no repositorio ou pacote de release;
- nome, hash, caminho, participantes, relacoes e lore da fonte privada nao sao registrados nos manifests/failsafes;
- somente descobertas generalizaveis, contratos e testes anonimizados permanecem;
- a camada pragmatica nao cria perfil pessoal e nao usa a fonte privada em runtime.

## Consequencias

A reproducao da analise original exige novo fornecimento explicito da fonte pelo usuario. Essa perda deliberada de rastreabilidade e aceita em favor da privacidade. O estado do projeto continua auditavel pelo codigo, testes e documentos derivados.
