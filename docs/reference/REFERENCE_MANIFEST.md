# Manifesto de referências externas

Esses arquivos foram usados/considerados durante a análise arquitetural. Eles não precisam permanecer dentro do repositório Campanario, mas, se uma tarefa futura exigir análise/cópia/adaptação de código deles, use o snapshot correspondente e confira o SHA-256.

| Arquivo | SHA-256 | Papel |
|---|---|---|
| `row-bot-main.zip` | `996d0612828aceb6b30da8c9d40f406f3796cb12be5e6b110478a2907715b624` | memória, KG, agentes, tools, contexto |
| `Jarvis-main.zip` | `737c24fc9d482a408dd098996664b1c3366fa522ba9b2ed2ea91083c4d00cfc4` | voz, speaker/wake concepts, web fallback |
| `LocalMind-main.zip` | `4ff4a64c268694ad86e3717619949b29cc08a8aee8c6d1fc1d1f4b29e2875ffe` | local-first/PWA/UX/auditoria de memória |
| `khoj-master.zip` | `f429cfc4aa4c439d5d0eb16e5adab9f092724f79d291b5fc27fcd892cb3c9f3a` | RAG/retrieval; atenção à AGPL |
| `open-webui-main.zip` | `8849974f7eb67ffbf9cbdef58961ce0873f2f7033f4666b0b22e476ff3f2aff8` | UI/adapters/RAG/web; atenção à licença |
| `MemoryWebAssistant-main.zip` | `89ab45550df88476522ac5c69a82f678fba6ff807b18535bcbfdf193f419c9eb` | RAG/CAG didático; licença própria não encontrada |
| `local-ai-assistant-main.zip` | `a255f825eb94d358be3d1070d9e0dacf33034d0f64fbbdec1bf505a53a752e9c` | composição/deployment local |
| `Projeto_Campanario_v2.0_Documento_de_Conceito.docx` | `54ae3ac1de5891fc726861658cd9a26b07e97f541ca9ccd55c98cc2dbca5d044` | especificação conceitual principal |

## Política de licença lembrada

- Row-Bot/Thoth snapshot analisado: Apache-2.0.
- JARVIS: MIT.
- LocalMind: MIT.
- Khoj: AGPLv3 — preferir referência/reimplementação quando necessário.
- Open WebUI: licença própria/histórico; revisar antes de reutilizar.
- MemoryWebAssistant: não assumir direito de copiar sem licença explícita.

Sempre revalidar a licença do snapshot antes de reutilização concreta.
