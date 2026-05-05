# FileSyncro.spec
block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'customtkinter',
        'zeroconf',
        'watchdog',
        'aiohttp',
        'asyncio',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='FileSyncro',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    onefile=True,
)
app = BUNDLE(
    exe,
    name='FileSyncro.app',
    bundle_identifier='de.filesyncro.app',
)
