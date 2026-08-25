# 01 - Primeiros passos

## Requisitos atuais (Windows)

1. Ollama instalado.
2. `gemma3:12b` recomendado (`ollama pull gemma3:12b`) ou outro modelo local compativel.
3. `uv` instalado e no PATH.
4. Projeto extraido em pasta com permissao de escrita.

## Primeira inicializacao

1. Extraia a release em uma pasta nova.
2. Execute `CAMPANARIO.bat`.
3. Escolha **Iniciar Campanario**.
4. Na primeira execucao, `.env` e criado a partir de `.env.example`.
5. O launcher sincroniza dependencias, aplica migrations e inicia a API.
6. O navegador abre `http://127.0.0.1:8000/`.

## Verificacao rapida

- Chat: `http://127.0.0.1:8000/`
- Swagger/API: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`
