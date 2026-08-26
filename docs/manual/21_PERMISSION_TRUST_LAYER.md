# Permission / Trust Layer

PF6 adiciona a fronteira de seguranca entre “o Campanario consegue fazer” e “o Campanario pode fazer”.

Um device pode existir no Device Registry sem ser confiavel. Pairing gera uma credencial secreta mostrada uma vez; o banco guarda apenas hash. Revogar invalida a credencial imediatamente.

As capabilities declaram permissoes. A policy pode permitir, negar, permitir somente durante sessao/call ou exigir confirmacao. Confirmacoes sao de uso unico e ligadas ao principal/dispositivo; `SCOPED_CONFIRM` tambem exige o mesmo escopo.

Endpoints locais PF6:
- `POST /api/v1/devices/{device_id}/pair`
- `POST /api/v1/devices/{device_id}/revoke`
- `GET /api/v1/security/audit`

O gateway continua localhost-only. Nao exponha a porta na LAN/Internet como se PF6 sozinho fosse um deployment remoto completo.
