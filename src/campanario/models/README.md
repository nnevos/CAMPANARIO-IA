# Modelos de voz — armazenamento externo

Os pesos Whisper (`ggml-*.bin`) **nao fazem parte do pacote/repo do Campanario**. Eles podem ter centenas de MB e devem ser compartilhados entre versoes.

No Windows, `tools/windows/PREPARAR_VOZ_F5C.bat` instala por padrao em:

`%LOCALAPPDATA%\Campanario\models\ggml-small.bin`

Para usar outro disco/pasta, defina `CAMPANARIO_VOICE_MODELS_DIR` antes de iniciar o Campanario. Tambem e possivel apontar um arquivo exato com `CAMPANARIO_VOICE_WHISPER_MODEL_PATH`.

Compatibilidade: layouts antigos `models/`, `voice/models/` e `voice/ggml-*.bin` continuam aceitos, mas nao sao recomendados para handoff porque tornam o ZIP muito pesado.

Nao copie `ggml-small.bin`, `ggml-big.bin` ou outros pesos para o pacote que sera enviado. O codigo e os modelos devem viajar separadamente.
