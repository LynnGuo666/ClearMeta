# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('sponsor_qr.png', '.'),  # 包含赞助二维码
        ('README.md', '.'),       # 包含说明文档
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'pkg_resources.py2_warn',
        'pkg_resources.markers',
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
    [],
    exclude_binaries=True,
    name='ClearMeta',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClearMeta',
)

# macOS 应用包配置
app = BUNDLE(
    coll,
    name='ClearMeta.app',
    icon=None,  # 可以添加 .icns 图标文件
    bundle_identifier='com.clearmeta.app',
    info_plist={
        'CFBundleName': 'ClearMeta',
        'CFBundleDisplayName': 'ClearMeta',
        'CFBundleGetInfoString': "Image Metadata Cleaner by Lynn",
        'CFBundleIdentifier': "com.clearmeta.app",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHighResolutionCapable': 'True',
        'NSHumanReadableCopyright': "Copyright © 2025 Lynn",
        'LSApplicationCategoryType': 'public.app-category.photography',
    },
)
