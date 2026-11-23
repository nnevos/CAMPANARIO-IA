# R3.21 — Field Web GitHub Pages
- Site PWA estático isolado em `pages/`, deploy GitHub Pages automatizado, instalação pela tela inicial.
- GPS via Geolocation API, mapa com tiles OpenStreetMap, busca Nominatim e rota OSRM público com origem GPS ou manual.
- App de notas e chat offline existentes preservados; emparelhamento pelo HTTPS Companion mediante origem CORS exata opcional.
- Token em sessionStorage (aba), nunca no repositório nem persistente em IndexedDB; notas IndexedDB permanecem locais.
- Android original e Python externos inalterados; sem APK, sem back-end na nuvem.
