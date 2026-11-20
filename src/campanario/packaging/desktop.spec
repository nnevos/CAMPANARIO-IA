# Build on Windows with Python 3.12 and the desktop extra installed.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all
root = Path(SPECPATH).parent
web_data, web_binaries, web_imports = collect_all('webview')
data = collect_data_files('campanario') + web_data + [
    (str(root / 'migrations'), 'migrations'),
    (str(root / 'alembic.ini'), '.'),
]
a = Analysis([str(root / 'packaging/desktop_entry.py')],
    pathex=[str(root/'src')], binaries=web_binaries, datas=data,
    hiddenimports=collect_submodules('campanario') + collect_submodules('uvicorn') + web_imports,
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'tkinter', 'chromadb', 'sounddevice', 'pytest'],
    noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Campanario', debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False, console=False,
    icon=str(root/'packaging/campanario.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Campanario')
