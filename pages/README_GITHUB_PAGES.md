# CAMPANÁRIO FIELD WEB — PUBLICAR EM GITHUB PAGES

## Publicação sem APK

### Opção simples: repositório exclusivo de site
1. Crie repositório público no GitHub chamado `campanario-field` (ou outro nome).
2. Coloque **somente o conteúdo** do ZIP `CAMPANARIO_FIELD_GITHUB_PAGES_R321.zip` na **raiz** desse repositório. Ele contém `index.html`, `map.html`, `app.mjs`, imagens e manifestos. Não envie `.env`, Database nem código servidor.
3. Em `Settings → Pages → Build and deployment`, selecione **Deploy from a branch** e depois `main / (root)`.
4. Abra `https://SEU_USUARIO.github.io/campanario-field/`, de preferência no Chrome do Android.
5. No navegador, use **Adicionar à tela inicial / Instalar app**. O aplicativo é um PWA; não existe APK nesse fluxo.

### Opção mantendo o CAMPANARIO-IA no GitHub
O projeto completo contém `.github/workflows/publicar-field-pages.yml`; vá a `Settings → Pages → Build and deployment → GitHub Actions`. O workflow publica **somente** a pasta `pages/` nas alterações em `main` / `master` ou por execução manual.

## O que funciona sem o PC
- Chat pode registrar rascunhos e histórico em cache; não há IA executada no GitHub.
- Notas offline no armazenamento **do próprio navegador** (IndexedDB); não criptografadas.
- Mapa online com OpenStreetMap, busca Nominatim, rotas OSRM de carro, GPS por permissão e origem manual. Sem sinal de GPS, informe a origem.
- O mapa-base não está disponível offline, nem a navegação contínua em segundo plano ou com tela apagada.
- Mapas e rotas dependem dos servidores públicos, sujeitos a limites e indisponibilidade. Não usar como navegador de segurança crítica.

## Usar Morgana / Todd e Database do PC
- O Github Pages **não executa Ollama, Python, SQLite ou o gateway**. Mantenha o Campanário PC funcionando separadamente.
- O gateway Companion do PC deve ser HTTPS válido e alcançável pelo telefone (por LAN, VPN privada ou túnel que você configure). **Não exponha Ollama, SQLite nem o servidor administrativo** na Internet.
- No `.env` LOCAL do PC, adicione `CAMPANARIO_FIELD_PAGES_ORIGIN=https://SEU_USUARIO.github.io` (somente o domínio, **sem** nome do repositório e **sem** barra final). Reinicie o servidor/Listener Companion. Esta variável habilita CORS apenas para a origem informada, e não equivale a autenticação. Pareamento por código temporário continua obrigatório.
- No Field Web → Conexão, informe endereço `https://...` do gateway e o código temporário gerado no PC. O token fica somente no `sessionStorage` (aba do navegador), **não protegido por Keystore**. Evite dispositivos de terceiros. Se fechar a aba, pode ser necessário parear novamente.
- TLS com certificado inválido ou IP não alcançável bloqueará a conexão. Github Pages não cria VPN, não contorna CGNAT nem fornece gateway do PC.

## Privacidade e limitações
- Site publicado é público. O conteúdo do repositório e do frontend pode ser visto por qualquer pessoa; **não inclua dados pessoais**.
- GPS é solicitado pelo navegador; localização não é enviada ao GitHub por nossa aplicação, mas coordenadas consultadas para mapa/rota podem chegar aos serviços públicos de mapas. Evite buscas sensíveis.
- A consulta ao Nominatim é feita mediante interação do usuário, com espera de 1,1 s por consulta dentro da aba; para uso público em escala, troque por um servidor autogerenciado ou provedor compatível com a política. Não há autocomplete automático.
- Trilha de localização só é mantida na sessão visível. Suspensões e economia de energia do sistema interrompem o GPS e a voz. O PWA não é um substituto de navegação homologada.

## Atualizar o site
Envie as alterações da pasta `pages/` ao mesmo repositório. O GitHub Pages atualizará o conteúdo conforme a configuração escolhida. O Service Worker usa política network-first e mantém o último conteúdo funcional para uso offline da interface; pode levar uma atualização da página para receber a nova versão.
