# CAMPANÁRIO R3.19 — Limpeza verificável de projeto + Maps

Base: ZIP privado `CAMPANARIO-IA.zip` fornecido pelo operador. O pacote de origem tinha 8.238 entradas e ~267 MiB compactados. A nova pasta traz somente código, assets Android, ferramentas e documentação operacional. Removidos de distribuição (não apagados do PC): `.env`, `.git`, `.venv`, SQLite privado, backups, histórico MD, modelos ONNX redundantes e cópia recursiva do projeto dentro de `docs/operations`.

Funcionalidade: `navigation-v2.js` pesquisa endereço sem GPS, admite localização aproximada para pesquisa, usa origem manual para cálculo e mantém GPS preciso para guia vivo; `gps-map.js` abre tiles online por padrão e respeita desativação explícita. `CAMPANARIO.bat` utiliza `..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe` da raiz real.

Risco: ao trocar a pasta, preserve `.env`, vozes locais utilizadas e as duas pastas irmãs. Não execute preparadores automaticamente. APK e rotas reais no ambiente do usuário ainda não validados.
