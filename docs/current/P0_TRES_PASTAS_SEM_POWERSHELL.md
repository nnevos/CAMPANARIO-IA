# P0 — Integridade das três pastas e atualização sem PowerShell

**Revisão:** 19/11/2026 • **Escopo:** CAMPANARIO-IA V9 + V9.1 • **Estado:** verificações estruturais implementadas; homologação do computador de destino pendente.

## Arquitetura de pastas — contrato explícito

```text
C:\Users\Steam Deck\Documents\GitHub\
├── CAMPANARIO-IA\                     CODIGO, interface, .env local, docs, testes
│   ├── CAMPANARIO.vbs / CAMPANARIO.bat launcher Windows
│   ├── src\campanario\                agentes, chat, brains, runtime
│   └── migrations\                    Alembic (scripts, NAO dados)
├── CAMPANARIO-PYTHON\
│   └── .venv\Scripts\python.exe       interpretador Python 3.12 + dependencias
│       .venv\Scripts\pythonw.exe      interpretador sem console para o launcher
└── CAMPANARIO-DATABASE\
    ├── dados\
    │   ├── desenvolvimento\campanario.db    SQLite ambiente desenvolvimento
    │   └── producao\campanario.db           SQLite ambiente producao
    └── zim\                           acervos offline Kiwix, se instalados
```

**Conexão real verificada no código IA:** `CAMPANARIO.vbs` primeiro procura `Campanario.exe` na pasta IA; se não existe, tenta `..\CAMPANARIO-PYTHON\.venv\Scripts\pythonw.exe`; somente na ausência deste tenta `CAMPANARIO-IA\.venv\Scripts\pythonw.exe` (fallback legado). O `Campanario.exe`, quando existente, tem prioridade e deve ser verificado quanto à versão antes do aceite. `config.py` lê `.env` e determina `data_dir`, `zim_dir`, `memory_environment` e `database_path`. O backend usa SQLite em `<CAMPANARIO_DATA_DIR>\<CAMPANARIO_MEMORY_ENVIRONMENT>\campanario.db` (ou diretório legado de AppData caso `CAMPANARIO_DATA_DIR` não esteja configurado).

No `.env` **privado** na raiz IA, após migração confirmada, a configuração esperada é:

```dotenv
CAMPANARIO_DATA_DIR=C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-DATABASE\dados
CAMPANARIO_ZIM_DIR=C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-DATABASE\zim
CAMPANARIO_MEMORY_ENVIRONMENT=desenvolvimento
CAMPANARIO_BRAINS_V9_ENABLED=false
```

O ambiente `producao` deve ser selecionado apenas conscientemente. Não mudar a variável de dados sem conferir onde estão os SQLite, arquivos originais e backups; um caminho válido com banco vazio pode parecer perda de memórias, sem que elas tenham sido apagadas. **Não criar `.env` vazio sobre o existente.** ZIM é opcional e não é movido nem baixado por este pacote.

### Exceção herdada: Biblioteca Conversacional V2 (SQLite de referência)

A inspeção encontrou **um segundo arquivo SQLite legado dentro de `CAMPANARIO-IA/data/interaction_library_v2.sqlite`**. Ele armazena exemplos de comportamento revisados e é consultado **somente em leitura** por `agents/interaction_library.py`; **não** é o banco de memória pessoal `campanario.db`. Portanto seria incorreto declarar que *todos* os SQLite já foram separados.

O P0 ajustou a consulta: ela prefere `CAMPANARIO-DATABASE/dados/reference/interaction_library_v2.sqlite` **se esse arquivo já existir**, e mantém fallback para `IA/data/interaction_library_v2.sqlite` para não quebrar a biblioteca. Para consolidar a separação, com o Campanário fechado, **copie** (não mova nem apague) o SQLite de referência pelo Explorador para a pasta `CAMPANARIO-DATABASE\dados\reference\` (crie `reference` se necessário) e confira a biblioteca no aplicativo. Guarde o original por segurança até homologação; a atualização **não copia nem remove esse arquivo**. O diagnóstico mostra a pendência `interaction_library_reference` enquanto usar o fallback legado.

A `CAMPANARIO-PYTHON/.venv` **não deve** ficar dentro do ZIP de código nem ser criada automaticamente a cada atualização. Dependências (Piper/Pocket TTS, PyTorch/CUDA, pandas, openpyxl, Python 3.12) são instaladas/verificadas somente quando exigido; comandos de preparação históricos permanecem disponíveis. O Ollama mantém seus modelos no local configurado pelo próprio Ollama (não mover para IA/Database automaticamente).

## Atualização do CÓDIGO pelo Explorador — sem PowerShell

Pacotes de atualização P0 fornecidos:

1. **`CAMPANARIO_P0_ARQUIVOS_PARA_COPIAR.zip`** contém **somente arquivos novos ou modificados** com caminhos relativos à raiz `CAMPANARIO-IA`. Para instalações que já têm a V9+V9.1 e o patch documental do roadmap, é a opção menos invasiva.
2. **`CAMPANARIO_P0_IA_COMPLETO.zip`** contém a pasta completa `CAMPANARIO-IA/` com o código atualizado e os recursos públicos disponíveis nesta cópia. Não traz dados pessoais, `.env`, `.venv` nem histórico `.git`.

Procedimento manual seguro:

1. Feche Campanário, desktop, servidor e quaisquer acessos simultâneos ao SQLite. Não atualize enquanto estiver escrevendo memórias.
2. Faça **backup separado** do `CAMPANARIO-IA` (incluindo `.env` local privado) e de `CAMPANARIO-DATABASE` **fora da árvore que será substituída**. Não compartilhe esses backups.
3. Extraia o ZIP de **arquivos para copiar** em uma pasta temporária fora do projeto, como `Downloads\P0_EXTRAIDO` (não extraia na pasta IA diretamente).
4. Abra essa pasta no Explorador, selecione as pastas e arquivos que estão dentro dela (`src`, `tests`, `docs`, `README.md` etc.) e **copie/cole na raiz existente `CAMPANARIO-IA`**. Aceite **substituir apenas os arquivos homônimos**, desde que não tenha modificações pessoais neles. Não escolha apagar a pasta IA nem excluir arquivos ausentes no ZIP. Mantenha a estrutura de subpastas.
5. Não copie sobre `CAMPANARIO-PYTHON`, `CAMPANARIO-DATABASE`, `.env`, `.venv`, voz privada ou arquivos pessoais: o ZIP de atualização não contém esses itens.
6. Abra o aplicativo normalmente por `CAMPANARIO.vbs`/atalho existente. Abra **Ferramentas → Central de Cérebros**. A verificação P0 das três pastas funciona **até com a flag V9 desligada**. Leia *todos* os itens `blocking` e `warning` antes de habilitar novos cérebros.
7. Se a instalação precisar de novas dependências ou migração Alembic, pare e siga o guia específico. **Somente essas ações operacionais**, ou testes opcionais, exigem comandos. A cópia do código em si não usa PowerShell.

O Windows Explorer não oferece comparação de hashes/mudanças de arquivos em nível de patch. **Se você modificou localmente algum arquivo de código, não faça substituição automática**: compare versões num editor ou Git antes. O `MANIFESTO_P0_SHA256.json` acompanha o ZIP de arquivos; validação automática de hash é opcional, não condição para copiar pelo Explorador. Não sobrescreva instalações antigas V7/V8 com o overlay P0: a base exigida é V9+V9.1 com roadmap atualizado. O pacote completo é referência de código, não um instalador que executa migrações.

## Diagnóstico de integração sem tocar no Database

**Ferramentas → Central de Cérebros → P0 · Diagnóstico das três pastas** chama `GET /api/v1/brains/environment` pela interface local (somente loopback). Exibe: IA, `.venv` esperada, Python de execução, Database, dados configurados, SQLite correspondente ao ambiente e ZIM (opcional).

O diagnóstico verifica existência/caminho e lê **somente os 16 bytes do cabeçalho SQLite**, sem executar SQL, criar arquivo, migrar, importar ou alterar `.env`. Um `paths_ok` **NÃO equivale a banco íntegro ou Windows homologado**; `blocked` exige investigação. Se detectar Python diferente, pode ser Python de testes, launcher de `Campanario.exe` ou um ambiente incorreto; interprete o resultado no contexto do aplicativo iniciado.

R0 **ainda depende** de comprovar no PC: integridade e restauração de uma cópia real do Database, revisão Alembic `0010`, Python 3.12 (ambiente externo), Ollama e voz, desempenho e UI mobile. Nenhuma dessas ações é feita automaticamente pelo diagnóstico. O script opcional `tools/verificar_3_pastas_p0.py` imprime JSON para suporte, usando o interpretador da venv externa, mas **não é necessário para atualizar arquivos**.

## FAILSAFE / recuperação

- **Erro apenas de código:** feche o app; restaure os arquivos IA do backup anterior. Mantenha intactos `CAMPANARIO-DATABASE`, `.env` e `.venv`; não faça downgrade Alembic por reflexo.
- **V9 causando erro:** coloque `CAMPANARIO_BRAINS_V9_ENABLED=false` no `.env` privado e reinicie. Isso desativa cérebros V9, mas não desfaz migrações e não mata uma thread antiga em execução.
- **Caminho do Database errado:** não mova ou remova banco por tentativa/erro; compare `CAMPANARIO_DATA_DIR` e `CAMPANARIO_MEMORY_ENVIRONMENT` com o estado previamente funcional e verifique backups.
- **`0010` ausente no banco:** planeje migração após backup confirmado; nunca aplique downgrade destrutivo no banco pessoal. `0010→0009` remove tabelas V9.
- **`.venv` externa ausente:** não copie a venv de outra máquina; execute os scripts de preparação do Python conforme `LEIA_PRIMEIRO_PYTHON_UNIFICADO.md`, só durante instalação/reparo.
- **Timeout dos cérebros:** o executor atual corta a espera, mas não interrompe fisicamente a thread. Não liberar execução arbitrária de código ou ações externas até R1.

Fontes internas: `src/campanario/config.py`, `CAMPANARIO.vbs`, `src/campanario/storage/database.py`, `src/campanario/brains/environment.py`, `docs/operations/FAILSAFE_V9_CEREBROS.md` e `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md`.


## Atualização de referência — R1 após P0

A observação anterior de que o timeout deixa uma **thread** continuar se refere ao executor do P0. No incremento R1, somente os dois adaptadores de leitura Conhecimento e Análise usam subprocesso que é encerrado em timeout/RSS. Não é sandbox OS com proibição de rede/diretórios; outros adapters ainda podem ser threads. O uso de `CAMPANARIO-PYTHON/.venv` é mantido e o Database segue externo, sem migração. Consulte [`R1_ISOLAMENTO_CEREBROS.md`](R1_ISOLAMENTO_CEREBROS.md) antes de habilitar V9.
