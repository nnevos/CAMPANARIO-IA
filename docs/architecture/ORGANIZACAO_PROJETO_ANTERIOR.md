# Organizacao do Campanario - fase 3

## Entrada
- `CAMPANARIO.bat`: launcher Windows, preservado.
- `README.md`: inicio rapido.
- `CONTINUIDADE_CHAT_NOVO.md`: retomada em novo chat.
- `ORGANIZACAO_PROJETO.md`: este mapa.

## Codigo e recursos
- `src/campanario/`: implementacao.
- `tests/`: testes automatizados.
- `tools/windows/`: launchers e diagnosticos Windows.
- `tools/ATUALIZAR_CONTINUIDADE.py`: regenera handoff sem ler memoria privada.
- `migrations/`: migracoes do banco.
- `voice/`: binarios legados de voz; preservados, pois os launchers ainda podem depender deles.
- `models/`: instrucoes para modelos.

## Documentacao
- `docs/project/`: planos, auditorias e registros recentes.
- `docs/manual/`: operacao.
- `docs/reference/personas/`: identidade original dos agentes.
- `docs/concept/`: concepcao futura.
- `docs/adr/`: decisoes tecnicas.
- `docs/history/`: legado historico.

## Compatibilidade e seguranca
- `RECOVER_FIRST.md`, `SAFEPOINT.md`, `PROJECT_STATE.md` ficam na raiz por referencias legadas.
- Nao excluir modulos, scripts ou recursos de voz sem rastrear dependencias e testar no Windows.
- Arquivos `.env`, bancos, caches e relatorios gerados nao devem entrar no ZIP.
- O manifesto em docs/project e historico; nao representa hashes do pacote reorganizado.
- Manter `CAMPANARIO_MEMORY_ENVIRONMENT=desenvolvimento` ate validar o Ponto Zero.

## Pendencias
- Inventario de dependencias e codigo morto; limpeza de codigo so apos testes completos.
- Revisar README legado e corrigir mencoes ao modelo gemma3:12b.
- Validacao real no Windows 11 e Ollama Qwen3.5.
