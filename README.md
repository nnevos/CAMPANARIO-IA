# CAMPANÁRIO — Projeto limpo para Windows e Android

Esta pasta contém **somente o código, o cliente Android, as ferramentas de desenvolvimento e a documentação operacional essencial**. Foi preparada a partir do ZIP enviado pelo proprietário, sem copiar ambientes virtuais, bancos, backups, históricos Git, modelos de voz duplicados ou `.env` privado.

## Estrutura

- `src/`: aplicação Python e interface Dark Matter.
- `apps/mobile/android/`: projeto Android (abra esta pasta no Android Studio para compilar).
- `apps/mobile/www/`: recursos web ainda usados pelo Field híbrido; não os remova.
- `tests/`: testes para evitar regressões.
- `tools/`, `scripts/`, `migrations/`, `config/`, `packaging/`: suporte de execução e manutenção.
- `docs/`: ROADMAPs, FAILSAFE, manuais técnico/de desenvolvimento e instalação de Maps/Field.
- `uv.lock`, `pyproject.toml`: versões de dependências.

## Iniciar no Windows

Coloque `CAMPANARIO-IA`, `CAMPANARIO-PYTHON` e `CAMPANARIO-DATABASE` **lado a lado**. Preserve a `.venv` já existente em `CAMPANARIO-PYTHON`. Dê dois cliques em `CAMPANARIO.bat`. O iniciador busca `..\CAMPANARIO-PYTHON\.venv\Scripts\python.exe`, sem executar o preparador.

**Antes de trocar pastas:** feche o app, renomeie sua `CAMPANARIO-IA` atual para um nome de backup, extraia esta pasta limpa no lugar e copie **somente** o seu `.env` original para a nova raiz. Não copie a `.venv` da pasta antiga. Modelos de voz locais (`vozes/*.onnx`) podem ser restaurados separadamente se você os usa e se não estiverem apontados pelo `.env` para outro caminho. Preserve `CAMPANARIO-DATABASE` sem alterações. Não mescle o projeto limpo sobre a pasta antiga: arquivos antigos continuariam lá.

## Maps

O mapa com internet começa ativo. A busca por endereço não exige GPS; busca pelo **mais próximo** precisa de uma origem informada ou localização autorizada. GPS aproximado pode apoiar a busca e o cálculo de rota, mas não substitui GPS confiável na navegação ao vivo. Roteamento depende de um provedor real disponível; a aplicação não inventa percursos.

## Android

Abra `apps/mobile/android` no Android Studio, sincronize Gradle e use **Build > Build APK(s)**. O ZIP não contém um APK pronto nem garante compilação em um SDK que não foi testado aqui. Alguns componentes móveis ainda são híbridos, embora a tela de navegação e o serviço de localização tenham implementação Android.

## Documentação

Consulte `docs/operations/INSTALACAO_MAPS_V2.md` e `docs/operations/ANDROID_FIELD_V1_BUILD_E_NAV.md` para infraestrutura de mapas e build. A documentação histórica de releases foi retirada deste pacote de trabalho. Não confunda remoção do ZIP com remoção das cópias de backup privadas.

## Maps R3.20

Ao abrir Modo Patrulha/Maps, o Campanário tenta obter sua localização automaticamente. O Windows/navegador pode pedir autorização uma vez; sem GPS, endereço e origem manual continuam disponíveis. Busca e rota de carro: provedores locais preferidos, fallback público por padrão para buscas/rotas solicitadas (Nominatim, Overpass e OSRM). Isso **compartilha a consulta e as coordenadas necessárias com provedores OSM externos**. Para impedir conexões externas, coloque `CAMPANARIO_MAPS_PUBLIC_FALLBACK=false` no `.env` e reinicie. Roteamento de caminhada ainda exige OSRM pedestre local; nenhum sistema de mapas garante disponibilidade ou precisão durante deslocamento.

## CAMPANÁRIO Field Web — GitHub Pages (R3.21)

Se não quiser compilar APK, o Field também possui uma versão web instalável (PWA) em `pages/`.

- Publicação de site com workflow GitHub Pages: `.github/workflows/publicar-field-pages.yml` (publique **somente** `pages/`).
- Instruções em `pages/README_GITHUB_PAGES.md` e `LEIA_PRIMEIRO_R321.md`.
- Mapa web com GPS do navegador, busca Nominatim e rotas públicas OSRM de **carro**; disponível sem PC mas depende de internet.
- Notas locais e rascunhos funcionam offline após carregar o site; chat e Database privados exigem gateway Companion HTTPS e pareamento com o PC.
- Para habilitar no listener Companion uma origem GitHub Pages exata, configure em seu `.env` privado no PC `CAMPANARIO_FIELD_PAGES_ORIGIN=https://SEU_USUARIO.github.io` e reinicie o listener. Não publique `.env` nem exponha o backend administrativo.
- O site não é navegador viário homologado: não fornece GPS com tela apagada, roteamento offline, tráfego em tempo real ou IA hospedada no GitHub.
