# -*- mode: python ; coding: utf-8 -*-
# PyInstaller : fabrique dist/PedaFiche/PedaFiche.exe  —  pyinstaller packaging/windows/pedafiche.spec --noconfirm
import os
from PyInstaller.utils.hooks import collect_submodules

RACINE = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
P = os.path.join(RACINE, "pedafiche")


def donnees(sous):
    return (os.path.join(P, sous), os.path.join("pedafiche", sous))


a = Analysis(
    [os.path.join(RACINE, "pedafiche_serveur.py")],
    pathex=[RACINE],
    datas=[donnees("web/templates"), donnees("web/static"), donnees("data"), donnees("fonts"), donnees("banque")],
    hiddenimports=collect_submodules("pedafiche") + ["waitress", "docx", "lxml", "lxml.etree", "pypdf", "tkinter"]
    + collect_submodules("reportlab.graphics.barcode") + collect_submodules("docx") + collect_submodules("waitress"),
    excludes=["pytest", "IPython", "matplotlib", "numpy"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="PedaFiche",
          icon=os.path.join(P, "web", "static", "icons", "pedafiche.ico"), console=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name="PedaFiche", upx=False)
