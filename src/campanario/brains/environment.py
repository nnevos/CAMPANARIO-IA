"""Read-only R0 preflight for Campanario's three sibling repositories.

This module deliberately does *not* create directories, open SQLite in writable
mode, migrate files, inspect private content or install dependencies. Its checks
are observations, never proof that the actual Windows runtime was homologated.
"""
from __future__ import annotations

from pathlib import Path
import sys


def _inside(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def inspect_three_folders(
    *,
    project_root: Path,
    data_dir: Path,
    zim_dir: Path | None,
    python_executable: Path,
    memory_environment: str = 'desenvolvimento',
    packaged: bool = False,
) -> dict:
    """Evaluate paths and SQLite header without mutating local state.

    ``project_root`` is the IA repository, not the parent GitHub folder.
    The Python and Database repositories are expected to be its siblings.
    """
    ia = Path(project_root).resolve()
    base = ia.parent
    py = (base / 'CAMPANARIO-PYTHON').resolve()
    venv = py / '.venv'
    database = (base / 'CAMPANARIO-DATABASE').resolve()
    expected_data = database / 'dados'
    expected_zim = database / 'zim'
    active_data = Path(data_dir).resolve()
    active_python = Path(python_executable).absolute()
    expected_db = active_data / memory_environment / 'campanario.db'
    checks: list[dict] = []

    def mark(code: str, ok: bool, *, blocking: bool = False, details: str = ''):
        checks.append({'id': code, 'status': 'ok' if ok else ('blocking' if blocking else 'warning'),
                       'message': details})

    mark('project_root', ia.is_dir() and (ia / 'pyproject.toml').is_file()
         and (ia / 'src' / 'campanario').is_dir(), blocking=True,
         details='Codigo IA encontrado' if (ia / 'pyproject.toml').is_file()
         else 'Pasta IA nao contem pyproject.toml')
    mark('python_repository', py.is_dir(), blocking=True,
         details='CAMPANARIO-PYTHON presente' if py.is_dir() else 'CAMPANARIO-PYTHON ausente')
    candidates = [venv / 'Scripts' / 'python.exe', venv / 'Scripts' / 'pythonw.exe',
                  venv / 'bin' / 'python', venv / 'bin' / 'python3']
    venv_ok = venv.is_dir() and any(p.is_file() for p in candidates)
    mark('external_venv', venv_ok, blocking=True,
         details='Interpretador detectado na .venv externa' if venv_ok
         else 'Nao foi encontrado Python na CAMPANARIO-PYTHON/.venv')
    # A packaged .exe may legitimately run without sys.executable pointing into .venv.
    active_ok = packaged or _inside(active_python, venv)
    mark('runtime_python', active_ok, blocking=not packaged,
         details='Runtime empacotado' if packaged else
         ('Interpretador ativo usa a .venv externa' if active_ok
          else 'O processo atual nao utiliza a .venv externa'))
    mark('python_version', packaged or (sys.version_info[:2] == (3, 12)),
         details='Python 3.12 esperado para a .venv do Campanario; consulte o runtime efetivo',
         blocking=not packaged)
    mark('database_repository', database.is_dir(), blocking=True,
         details='CAMPANARIO-DATABASE presente' if database.is_dir()
         else 'CAMPANARIO-DATABASE ausente')
    isolated = _inside(active_data, expected_data)
    mark('data_dir_external', isolated, blocking=True,
         details='CAMPANARIO_DATA_DIR aponta para DATABASE/dados' if isolated
         else 'CAMPANARIO_DATA_DIR nao aponta para DATABASE/dados; nao migrar automaticamente')
    mark('data_dir_present', active_data.is_dir(), blocking=True,
         details='Diretorio de dados existente' if active_data.is_dir()
         else 'Diretorio de dados nao existe; nenhum diretorio foi criado por esta verificacao')
    if zim_dir is None:
        mark('zim_dir', True, details='ZIM opcional: nao configurado')
    else:
        active_zim = Path(zim_dir).resolve()
        mark('zim_dir', _inside(active_zim, expected_zim), blocking=True,
             details='CAMPANARIO_ZIM_DIR isolado em DATABASE/zim' if _inside(active_zim, expected_zim)
             else 'CAMPANARIO_ZIM_DIR aponta para fora de DATABASE/zim')
    # The authored Interaction Library V2 is a read-only reference SQLite. Legacy
    # versions bundled it in IA/data; highlight this explicit exception rather
    # than pretending all databases have already been moved.
    external_reference = active_data / 'reference' / 'interaction_library_v2.sqlite'
    legacy_reference = ia / 'data' / 'interaction_library_v2.sqlite'
    if external_reference.is_file():
        mark('interaction_library_reference', True,
             details='Biblioteca Conversacional V2 localizada em Database/dados/reference')
    elif legacy_reference.is_file():
        mark('interaction_library_reference', False,
             details='Biblioteca V2 usa fallback legado somente leitura em IA/data; copiar manualmente para Database/dados/reference quando homologado')
    else:
        mark('interaction_library_reference', False,
             details='Biblioteca Conversacional V2 nao encontrada nos caminhos esperados')
    # Only 16 bytes are read; this is neither a migration nor an integrity check.
    if expected_db.is_file():
        try:
            with expected_db.open('rb') as fh:
                header_ok = fh.read(16) == b'SQLite format 3\x00'
        except OSError:
            header_ok = False
        mark('sqlite_header', header_ok, blocking=True,
             details='Cabecalho SQLite reconhecido; integridade e revisao Alembic NAO verificadas'
             if header_ok else 'Arquivo existente nao tem cabecalho SQLite legivel')
    else:
        mark('sqlite_header', False, blocking=False,
             details='SQLite nao localizado; pode ser instalacao nova ou banco configurado em outro ambiente')
    blocked = [x['id'] for x in checks if x['status'] == 'blocking']
    warned = [x['id'] for x in checks if x['status'] == 'warning']
    return {
        'status': 'blocked' if blocked else ('partial' if warned else 'paths_ok'),
        'checked_without_changes': True,
        'host_homologated': False,
        'folders': {'ia': str(ia), 'python': str(py), 'venv': str(venv),
                    'database': str(database), 'data': str(active_data),
                    'sqlite': str(expected_db), 'zim': str(Path(zim_dir).resolve()) if zim_dir else None},
        'memory_environment': memory_environment,
        'runtime': {'python': str(active_python), 'packaged': packaged},
        'checks': checks, 'blocking': blocked, 'warnings': warned,
        'note': ('Verificacao estrutural somente leitura. Nao comprova backup/restauracao, '
                 'migracoes, permissao efetiva, Ollama, voz ou testes Windows/mobile.'),
    }


def inspect_current_environment(settings, *, project_root: Path | None = None) -> dict:
    return inspect_three_folders(
        project_root=project_root or Path(__file__).resolve().parents[3],
        data_dir=settings.data_dir,
        zim_dir=settings.zim_dir,
        python_executable=Path(sys.executable),
        memory_environment=settings.memory_environment,
        packaged=bool(getattr(sys, 'frozen', False)),
    )
