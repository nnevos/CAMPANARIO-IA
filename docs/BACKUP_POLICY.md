# Política de backup do Campanario

## O que precisa ser protegido

1. Código e documentação do repositório.
2. `PROJECT_STATE.md` e ADRs.
3. SQLite/dados locais do Campanario.
4. Documentos de conhecimento no futuro.
5. Configuração sensível separadamente.

## O que não deve ser compartilhado automaticamente

- `.env`;
- chaves de API;
- tokens;
- credenciais;
- dados pessoais que futuramente existirem na memória do sistema.

## Backup rápido no Windows

Na raiz do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup_project.ps1
```

Por padrão cria um ZIP em:

`$HOME\Documents\CampanarioBackups`

O script copia o projeto e `%LOCALAPPDATA%\Campanario`, mas exclui `.env`, `.venv`, `.git` e caches.

## Frequência recomendada

- antes de migrations importantes;
- antes de trocar schema de memória/conhecimento;
- ao encerrar cada fase;
- antes de importar grandes bases/documentos;
- antes de experimentos destrutivos.
