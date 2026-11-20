# Hotfix de interface: horarios das mensagens

## Causa
`addTurn()` tentava alterar `stamp.textContent` quando `el.querySelector('.message-time')` retornava `null`. O template HTML de cada mensagem omitia a tag `<time>`.

## Alteracao
`src/campanario/web/index.html`: criado `<time class="message-time"></time>` dentro de `.message-meta` para usuario e agentes. Os horarios existentes sao exibidos em pt-BR e o atributo `dateTime` recebe ISO 8601.

## Verificacao
38 testes direcionados aprovados e sintaxe JS verificada via `node --check`. Sem validacao real no Windows/Neptune.

## Teste manual no Neptune
1. Backup da instalacao anterior e dos bancos; extrair o ZIP corrigido em pasta separada.
2. Iniciar pelo `CAMPANARIO.bat` e atualizar navegador com Ctrl+F5.
3. Enviar `oi`, depois `todd, quem e voce?`; confirmar que mensagens e horarios aparecem.
4. Abrir um episodio anterior no painel Sistema; verificar horario preservado e ausencia de erros.
5. Se houver outra falha, coletar o console F12 e log do terminal sem expor segredos.

O banco de memoria nao foi alterado.
