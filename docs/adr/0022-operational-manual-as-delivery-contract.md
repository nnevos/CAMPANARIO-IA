# ADR-0022 - Manual operacional como contrato de entrega

## Status
Aceito em 2026-08-24.

## Contexto
O projeto passou a ter launchers, configuracoes, testes E2E, relatorios, memoria/contexto e varias fases futuras. Depender do historico da conversa para lembrar como usar cada funcao criaria risco operacional e de continuidade.

## Decisao
- `docs/manual/` e a area oficial de documentacao para uso/operacao do Campanario.
- Failsafes continuam separados e servem a retomada de desenvolvimento.
- Toda funcionalidade voltada ao usuario so e considerada entregue quando o manual registra: estado, uso, configuracao, teste, limitacoes e troubleshooting aplicavel.
- `ABRIR_MANUAL.bat` fornece acesso local simples ao indice.

## Consequencias
- Novas releases devem atualizar `docs/manual/11_FUNCOES_DO_SISTEMA.md` e os guias afetados.
- O manual distingue explicitamente recursos ATIVOS, EM VALIDACAO e PLANEJADOS para evitar confundir referencia conceitual com capacidade de runtime.
