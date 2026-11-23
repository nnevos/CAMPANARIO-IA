# CAMPANÁRIO R3.21 — Field para GitHub Pages

- `pages/`: site PWA pronto para publicar, sem arquivos pessoais, chaves ou Python.
- `.github/workflows/publicar-field-pages.yml`: deploy GitHub Pages via GitHub Actions.
- `apps/mobile/android/`: projeto Android original **preservado**, mas não é necessário para usar o site.
- `src/campanario/app/remote.py`: origem exata `usuario.github.io` opcional para comunicação com servidor HTTPS pareado.
- `pages/map.html`: mapa online, localização do navegador, busca de endereços e roteamento de carro via serviços públicos OSM/OSRM; sem garantia de disponibilidade.

**Privacidade:** GitHub Pages é público. Nunca faça upload de `.env`, banco, credenciais ou mapas privados. O Field guarda notas localmente no navegador e token de pareamento apenas na sessão da aba, não criptografados. Para IA, configure `CAMPANARIO_FIELD_PAGES_ORIGIN=https://SEU_USUARIO.github.io` no `.env` local do PC; reinicie somente o listener Companion HTTPS. Não exponha o backend administrativo. Se o PC não estiver acessível por HTTPS, chat e sincronização ficam indisponíveis, mas notas e app continuam abrindo.

**Navegação:** GPS web funciona só com permissão HTTPS e enquanto a página permanece ativa. Voz de manobras e roteamento a pé offline, GPS com tela apagada e navegação homologada em campo não estão implementados.
