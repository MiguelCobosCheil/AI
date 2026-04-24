# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['test_mouse.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pynput', 'pynput.mouse', 'pynput.keyboard'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='test_mouse_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='test_mouse_app',
)
app = BUNDLE(
    coll,
    name='test_mouse_app.app',
    icon=None,
    bundle_identifier=None,
)
