# -*- coding: utf-8 -*-
"""Prépare l'application Android autonome : recopie le paquet `pedafiche` et les bibliothèques Python pures
dans app/src/main/python (Pillow et lxml sont fournis par Chaquopy, voir app/build.gradle).
Utilisation : python3 packaging/android_autonome/preparer.py   (option --local : bibliothèques de cet ordinateur)"""
import glob
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.abspath(os.path.join(ICI, "..", ".."))
PY = os.path.join(ICI, "app", "src", "main", "python")
LIBS = [("flask", "flask"), ("werkzeug", "werkzeug"), ("jinja2", "jinja2"), ("markupsafe", "markupsafe"),
        ("itsdangerous", "itsdangerous"), ("click", "click"), ("blinker", "blinker"),
        ("reportlab", "reportlab"), ("charset-normalizer", "charset_normalizer"),
        ("pypdf", "pypdf"), ("python-docx", "docx"), ("typing-extensions", "typing_extensions"),
        ("openpyxl", "openpyxl"), ("et-xmlfile", "et_xmlfile")]
GARDER = {"pedafiche_android.py"}


def nettoyer():
    for nom in os.listdir(PY):
        if nom in GARDER:
            continue
        p = os.path.join(PY, nom)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)


def telecharger():
    tmp = tempfile.mkdtemp()
    subprocess.check_call([sys.executable, "-m", "pip", "download", "--no-deps", "--only-binary=:all:", "--dest", tmp,
                           "--python-version", "3.11", "--implementation", "cp", "--platform", "manylinux2014_x86_64",
                           "--platform", "manylinux_2_17_x86_64", "--platform", "any"] + [n for n, _ in LIBS])
    for whl in glob.glob(os.path.join(tmp, "*.whl")):
        with zipfile.ZipFile(whl) as z:
            z.extractall(PY)
    shutil.rmtree(tmp)


def copier_local():
    for _, mod in LIBS:
        spec = importlib.util.find_spec(mod)
        if spec is None:
            raise SystemExit(f"Bibliothèque absente : {mod}")
        if not spec.submodule_search_locations:      # module d'un seul fichier
            shutil.copy2(spec.origin, PY)
            continue
        shutil.copytree(list(spec.submodule_search_locations)[0], os.path.join(PY, mod),
                        ignore=shutil.ignore_patterns("__pycache__"))


def main():
    os.makedirs(PY, exist_ok=True)
    nettoyer()
    shutil.copytree(os.path.join(RACINE, "pedafiche"), os.path.join(PY, "pedafiche"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    copier_local() if "--local" in sys.argv else telecharger()
    for motif in ("**/*.so", "**/*.pyd", "**/*.dylib"):
        for f in glob.glob(os.path.join(PY, motif), recursive=True):
            os.remove(f)
    for p in glob.glob(os.path.join(PY, "**", "__pycache__"), recursive=True):
        shutil.rmtree(p, ignore_errors=True)
    print("Prêt :", sum(len(f) for _, _, f in os.walk(PY)), "fichiers dans", PY)


if __name__ == "__main__":
    main()
