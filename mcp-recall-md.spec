# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — produces a single mcp-recall-md.exe in dist/"""

a = Analysis(
    ["src/mcp_recall_md/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "chromadb",
        "chromadb.api",
        "chromadb.api.models",
        "chromadb.config",
        "chromadb.db",
        "chromadb.db.impl",
        "chromadb.db.impl.sqlite",
        "chromadb.segment",
        "chromadb.segment.impl",
        "chromadb.segment.impl.vector",
        "chromadb.telemetry",
        "chromadb.telemetry.product",
        "onnxruntime",
        "tokenizers",
        "tqdm",
        "huggingface_hub",
        "fastmcp",
        "mcp",
        "pydantic",
        "pydantic_settings",
        "anyio",
        "httpx",
        "watchdog",
        "watchdog.observers",
        "watchdog.events",
    ],
    excludes=["pytest", "IPython", "notebook", "matplotlib", "tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="mcp-recall-md",
    debug=False,
    strip=False,
    upx=True,
    console=True,
)
