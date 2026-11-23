# LEIA PRIMEIRO — R3.19 projeto limpo

1. Feche Campanário, Android Studio e processos vinculados à pasta.
2. Na pasta `Documents\GitHub`, **renomeie** `CAMPANARIO-IA` atual para `CAMPANARIO-IA-BACKUP` (sem apagar dados).
3. Extraia o ZIP limpo **nessa pasta-pai**; deverá surgir uma pasta `CAMPANARIO-IA` nova.
4. Copie apenas `.env` da pasta antiga para a nova. Se usa pesos de voz `vozes/*.onnx` locais e caminhos relativos, copie a pasta de vozes da instalação antiga também ou ajuste a configuração.
5. Não mova nem altere `CAMPANARIO-PYTHON` nem `CAMPANARIO-DATABASE`; não copie `.venv` interna antiga.
6. Abra `CAMPANARIO.bat` **na raiz nova**, não dentro de `docs/operations`. Se ocorrer falha, feche, renomeie a nova pasta e restaure a anterior.
7. Para APK, abra `CAMPANARIO-IA\apps\mobile\android` no Android Studio, sincronize e use Build APK(s). O pacote não traz APK gerado.

GPS de baixa precisão não bloqueia pesquisa por endereço. Para "mais próximo", forneça coordenadas manuais se não houver localização. Guia ao vivo exige fix GPS confiável; serviços de roteamento/geocodificação precisam estar disponíveis.
