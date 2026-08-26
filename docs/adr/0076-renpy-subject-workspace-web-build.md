# ADR 0076 — Ren'Py Subject Workspace + Variable Units + Web Build

## Contexto

O fluxo real de produção trabalha por matéria, com quantidade variável de unidades. A primeira unidade serve de referência visual para personagem/cenário; cada unidade possui e-book/GDD/código próprios. As artes são finalizadas manualmente no Photoshop e o build Web é feito depois pelo SDK Ren'Py local.

## Decisão

A Fábrica Ren'Py passa a suportar projetos de matéria com número livre de e-books. A UI cria uma matéria, processa os arquivos em ordem e registra `UN01..UNnn`. `UN01` congela uma `ArtBible` de personagem/cenário e unidades posteriores herdam apenas essa camada narrativa/visual. Grounding pedagógico continua isolado por e-book.

Os projetos editáveis são persistidos no workspace configurável, cujo padrão operacional é `C:\Users\Steam Deck\Desktop\Renpy`. O SDK é configurável e tem padrão `C:\renply\renpy-8.4.1-sdk`.

Antes de Web Build, seis PNGs principais devem existir em 1920x1080. O build usa `launcher web_build`, preserva o projeto-fonte, remove ícones padrão quando configurado e converte a capa para `web-presplash.jpg` no Windows. Upload para nuvem não é automatizado.

Projetos existentes não são sobrescritos silenciosamente: a pasta antiga recebe um nome de backup.

## Invariantes

- quantidade de unidades nunca é hardcoded em 4;
- perfil 10x21 vale por unidade, não por matéria;
- UN01 compartilha visual, nunca conteúdo factual;
- GDD -> script continua determinístico;
- falha de grounding continua fail-closed;
- upload/publicação permanece fora da Fábrica;
- não altera o gate F5/F6.
