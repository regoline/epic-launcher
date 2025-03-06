# launcher.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# List of additional files to include (e.g., media and config folders)
added_files = [
    ('media', 'media'),
    ('config', 'config')
]

# Main script and configuration
a = Analysis(
    ['launcher.py'],  # Your main script
    pathex=[],  # Additional paths to search for imports
    binaries=[],  # Additional binary files to include
    datas=added_files,  # Include additional files
    hiddenimports=[],  # Manually specify hidden imports (if needed)
    hookspath=[],  # Custom hooks (if needed)
    hooksconfig={},  # Custom hook configuration (if needed)
    runtime_hooks=[],  # Runtime hooks (if needed)
    excludes=[],  # Exclude unnecessary modules
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Exclude unnecessary PyQt5 modules
a.excludes += [
    'PyQt5.QtQml',  # Exclude QML modules
    'PyQt5.QtQuick',  # Exclude QML modules
    'PyQt5.QtWebEngine',  # Exclude WebEngine modules
    'PyQt5.QtWebEngineCore',  # Exclude WebEngineCore modules
    'PyQt5.QtWebChannel',  # Exclude WebChannel modules
    'PyQt5.Qt3D',  # Exclude 3D modules
    'PyQt5.QtMultimedia',  # Exclude multimedia modules
    'PyQt5.QtNetwork',  # Exclude network modules (if not used)
    'PyQt5.QtSql',  # Exclude SQL modules
    'PyQt5.QtTest',  # Exclude test modules
    'PyQt5.QtXml',  # Exclude XML modules
    'PyQt5.QtSvg',  # Exclude SVG modules (if not used)
    'PyQt5.QtPrintSupport',  # Exclude print support modules
    'PyQt5.QtOpenGL',  # Exclude OpenGL modules
    'PyQt5.QtBluetooth',  # Exclude Bluetooth modules
    'PyQt5.QtPositioning',  # Exclude positioning modules
    'PyQt5.QtSerialPort',  # Exclude serial port modules
    'PyQt5.QtWebSockets',  # Exclude WebSockets modules
    'PyQt5.QtXmlPatterns',  # Exclude XML patterns modules
    'PyQt5.QtWinExtras',  # Exclude Windows-specific modules
    'PyQt5.QtMacExtras',  # Exclude macOS-specific modules
    'PyQt5.QtX11Extras',  # Exclude X11-specific modules
    'PyQt5.QtDBus',  # Exclude DBus modules
    'PyQt5.QtNfc',  # Exclude NFC modules
    'PyQt5.QtSensors',  # Exclude sensors modules
    'PyQt5.QtWebView',  # Exclude WebView modules
    'PyQt5.QtLocation',  # Exclude location modules
    'PyQt5.QtTextToSpeech',  # Exclude text-to-speech modules
    'PyQt5.QtWebKit',  # Exclude WebKit modules
    'PyQt5.QtWebKitWidgets',  # Exclude WebKitWidgets modules
    'PyQt5.QtHelp',  # Exclude help modules
    'PyQt5.QtUiTools',  # Exclude UI tools modules
    'PyQt5.QtDesigner',  # Exclude designer modules
]

# Bundle into a single executable
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='epic_launcher',  # Name of the output executable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress the executable using UPX
    console=False,  # Set to True if you want a console window
)

# Collect additional files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='epic_launcher',  # Name of the output folder
)