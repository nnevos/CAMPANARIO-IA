# Testes da R3.20 — Maps automático e fallback

**Escopo:** base limpa R3.19 extraída do pacote enviado, alterada na R3.20.

- Python direcionados ampliados: **71 aprovados**, 0 falhas (`test_r314_personal_mode`, `test_r315_file_index_and_management`, `test_r316_maps_v2`, `test_r317_native_field_contract`, `test_r320_maps_auto_public`, `test_r313_local_chat_upload`, `test_r33_cases_native`, `test_r34_case_conversation`).
- Python Maps V2 + R3.20: **27 aprovados**, 0 falhas.
- Node.js cliente mobile: **16 aprovados**, 0 falhas (suíte original). Não constitui homologação Android.
- `node --check` em `gps-map.js` e `navigation-v2.js`: aprovado.
- `compileall` na API Python e documentos sincronizados: aprovados.
- Casos de teste novos: falha Nominatim local -> resposta pública concreta; fallback desligado não usa rede pública; Overpass remoto só após falha local; OSRM público mantém geometria/manobras e recusa substituir perfil pedestre; localização automática e handlers únicos no frontend.
- Testes com provedores HTTP simulados por mocks; **não houve consultas externas reais nem GPS físico**. Não afirmar conectividade pública real, qualidade da rota, disponibilidade do Overpass, navegação segura em estrada, build de APK ou operação com Database real.
- Regressão integral de todos os módulos antigos não executada nesta entrega. Ambiente Windows e Android não disponíveis para homologação.

**Como homologar:** no Windows, confirmar acesso à internet, abrir Patrulha/Maps (permitir localização do dispositivo uma vez, se disponível), pesquisar destino por nome e por categoria próxima; escolher candidato e calcular rota. Se não houver GPS, pesquisar endereço sem localização ou preencher origem manual. Conferir `provider` no retorno de `/api/app/navigation/v2/route`. Em Android, validar permissões/GPS físico antes de usar na rua. O serviço público não possui SLA.
