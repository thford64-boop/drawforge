# drawforge.spec
# PyInstaller spec file for DrawForge
# Run: pyinstaller drawforge.spec
#
# Generated for: DrawForge — Professional Drawing Studio
# Usage: pyinstaller drawforge.spec
#        (or see README for the full one-liner command)

import sys
from pathlib import Path

block_cipher = None

# Collect any data assets (icons, default images, etc.)
# Add tuples: ('source_path', 'dest_folder_in_bundle')
datas = [
    # ('assets/icon.ico', 'assets'),   # uncomment if you add icons
]

a = Analysis(
    ['main.py'],
    pathex=[str(Path('').resolve())],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # PIL/Pillow
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageTk',
        'PIL.ImageFilter',
        # numpy (used by warp tool)
        'numpy',
        'numpy.core._multiarray_umath',
        'numpy.core.multiarray',
        # tkinter
        'tkinter',
        'tkinter.ttk',
        'tkinter.colorchooser',
        'tkinter.filedialog',
        'tkinter.messagebox',
        # app modules
        'canvas_engine',
        'tool_engine',
        'app',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy'],   # exclude unused heavyweights
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DrawForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,               # compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
