# Limpeza do projeto — troca segura da pasta de codigo

A versao limpa e derivada do RAR fornecido em 19/11/2026, preservando os fontes atuais, personalidades, testes, manuais, ferramentas, interfaces, configuracoes de projeto, lockfile e lancadores Windows. A limpeza **nao altera o roteamento dos agentes, a memoria nem a sintese de voz**.

Excluidos do pacote de codigo: a `.venv` interna, `.git`, `.env`, backups `BACKUP_*`, caches Python, historicos de patch na raiz, ZIP/RAR, relatorios gerados e pesos `vozes/*.onnx`.

Os pesos de voz nao sao descartados na instalacao: sao copiados diretamente da pasta antiga para a nova pelo script `TROCAR_PROJETO_LIMPO.ps1` que acompanha o pacote de troca. O `.env` e `.git` sao copiados da mesma maneira, sem passar pelo ZIP. Nenhum banco de `CAMPANARIO-DATABASE` ou ambiente de `CAMPANARIO-PYTHON` e modificado.

A pasta anterior e renomeada para `CAMPANARIO-IA_ANTES_LIMPEZA_<data>` no diretorio irmao. **So considerar apaga-la manualmente depois de abrir o aplicativo, confirmar vozes e memorias e testar persistencia apos reiniciar**. O RAR que deu origem a versao limpa tambem deve ser guardado fora da pasta de codigo ate confirmar a homologacao.

Verifique especialmente configuracoes locais personalizadas que nao estejam no RAR enviado. A instalacao compara hashes dos fontes antigos para bloquear troca caso o codigo tenha sido editado depois da geracao do RAR.
