# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Thai ID Card Reader
Build command: pyinstaller build.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['thai_id_reader.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'smartcard',
        'smartcard.System',
        'smartcard.util',
        'smartcard.CardType',
        'smartcard.CardConnection',
        'smartcard.Exceptions',
        'flask',
        'flask_cors',
        'werkzeug',
        'jinja2',
        'markupsafe',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='ThaiIDReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI mode (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if sys.platform == 'win32' else None,
)
