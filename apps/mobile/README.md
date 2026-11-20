# Campanario Mobile - Android companion

Host Android Java em `android/`, interface embarcada em `www/`. O app nao carrega a UI de um servidor remoto. Abrir `www/index.html` como arquivo nao equivale a executar o APK; modulos JS, origem segura e ponte nativa exigem o ambiente adequado.

Veja `../../LEIA-ME-V08.md` para compilacao, TLS, pareamento e limites offline. O Android ainda precisa de build e teste em aparelho. Nao ha iOS, modelo de IA mobile, TTS ou GPS nesta versao.

Testes logicos: `node --test tests/mobile/*.test.mjs`, a partir da raiz do projeto. A ponte Android deve ser validada separadamente: armazenamento criptografado, reinicio, atualizacao assinada preservando estado, certificados, teclado/insets e exclusao local.
