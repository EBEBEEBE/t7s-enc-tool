# PyInstaller build description. Documentation and license resources are
# intentionally included as external files because the About and Help pages
# load them at runtime.
from pathlib import Path

project = Path(SPECPATH)

a = Analysis(
    [str(project / "t7s_assetcrypt.py")],
    pathex=[str(project)],
    binaries=[],
    datas=[
        (str(project / "ABOUT.md"), "."),
        (str(project / "README.md"), "."),
        (str(project / "docs" / "QUICKSTART.md"), "docs"),
        (str(project / "LICENSE"), "."),
        (str(project / "THIRD_PARTY_NOTICES.md"), "."),
        (str(project / "DISCLAIMER.md"), "."),
        (str(project / "THIRD_PARTY_LICENSES"), "THIRD_PARTY_LICENSES"),
        (str(project / "assets" / "app_icon.png"), "assets"),
        (str(project / "assets" / "app_icon.ico"), "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# PySide6's hook collects the complete Qt installation.  These modules and
# plugins are not used by this application; filter their native payloads after
# collection while retaining QtCore/Gui/Widgets, Windows platform support, and
# the image formats used by Qt.
_unused_qt_files = {
    "pyside6\\qt6pdf.dll",
    "pyside6\\qt6qml.dll",
    "pyside6\\qt6qmlmeta.dll",
    "pyside6\\qt6qmlmodels.dll",
    "pyside6\\qt6qmlworkerscript.dll",
    "pyside6\\qt6quick.dll",
    "pyside6\\qt6svg.dll",
    "pyside6\\qt6virtualkeyboard.dll",
    "pyside6\\plugins\\iconengines\\qsvgicon.dll",
    "pyside6\\plugins\\imageformats\\qpdf.dll",
    "pyside6\\plugins\\imageformats\\qsvg.dll",
    "pyside6\\plugins\\platforminputcontexts\\qtvirtualkeyboardplugin.dll",
}
a.binaries = type(a.binaries)(
    entry for entry in a.binaries
    if str(entry[0]).lower() not in _unused_qt_files
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="t7s_enc_tool",
    icon=str(project / "assets" / "app_icon.ico"),
    console=True,
)
