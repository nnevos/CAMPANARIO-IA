# F4 — Experience / Learning Layer Review

## Resultado
F4 implementa a primeira camada real de autoaprendizado por experiencia/memoria, sem fine-tuning automatico e sem alterar Personality Core.

## Balanca de curiosidade
- se faltar informacao do usuario que muda materialmente a resposta: perguntar uma coisa objetiva;
- se der para responder de forma geral/condicional: responder sem perguntar;
- nao perguntar apenas para preencher perfil;
- resposta explicita a uma pergunta necessaria pode virar memoria;
- segredos e marcadores sensiveis de alto risco nao sao persistidos automaticamente.

## Memoria
Cada item possui kind, subject, key, value, confidence, source/provenance, evidence, status, timestamps, recall_count e supersession lineage. Fatos, preferencias, planos, experiencias compartilhadas e inferencias sao distintos.

## Correcao / esquecimento
Nova evidencia explicita para a mesma chave supersede a anterior. `/api/v1/memory` permite inspecao, correcao e esquecimento. Pedido conversacional estreito de "esquece ..." tambem remove a memoria mais relevante.

## Anti-drift
Todd e Morgana consultam a mesma ExperienceLayer; perfis em `agents/profiles.py` nao sao reescritos. Inferencias permanecem hipotese e recebem confianca inferior.

## Gate
F4 concluida no ADR 0061. Proximo gate canonico: F5 Realtime Presence / Call / Multi-client.
