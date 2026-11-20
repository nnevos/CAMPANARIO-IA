"""Explicit consistent SQLite backup. Stop Campanario for a coherent multi-DB snapshot."""
import argparse
from datetime import datetime, UTC
from pathlib import Path
from campanario.app.schema import backup_sqlite
from campanario.config import get_settings

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True, type=Path)
    args=parser.parse_args()
    settings=get_settings()
    dest=args.destination / datetime.now(UTC).strftime('campanario-%Y%m%dT%H%M%S%fZ')
    found=[]
    for source in (settings.database_path, settings.database_path.parent/'companion.db'):
        if source.is_file():
            backup_sqlite(source,dest/source.name)
            found.append(source.name)
    if not found:
        parser.error('Nenhum banco encontrado no perfil configurado; nada foi criado.')
    print('Backup SQLite:',dest)
    print('Arquivos:',', '.join(found))
    print('Nao inclui .env, modelos, anexos, indices Chroma ou chaves. Preserve-os separadamente.')
if __name__=='__main__':main()
