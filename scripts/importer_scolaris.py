"""Importe les données pédagogiques de SCOLARIS (corpus de fiches, progression annuelle,
emplois du temps, calendrier officiel, banque d'épreuves) vers le dépôt PédaFiche.

Usage :  python scripts/importer_scolaris.py chemin/vers/SCOLARIS-2.5.1
"""
from __future__ import annotations

import ast
import gzip
import json
import re
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DATA = RACINE / "pedafiche" / "data"
SEGMENTS = {"NIVEAUX", "NIVEAUX_LIB", "GROUPE_EDT", "JOURS", "MOIS_SCOLAIRES", "COLS_PLAN",
            "CLES_PLAN", "RECRE", "INTERCLASSE", "EDT_OFFICIELS", "PLANIFICATION_OFFICIELLE", "_edt"}


def ecrire_gz(chemin: Path, obj) -> int:
    with gzip.open(chemin, "wt", encoding="utf-8", compresslevel=9) as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    return chemin.stat().st_size


def constantes_synoptique(src: Path) -> dict:
    texte = (src / "m_synoptique.py").read_text(encoding="utf-8")
    arbre = ast.parse(texte)
    lignes = texte.split("\n")
    morceaux = []
    for n in arbre.body:
        nom = None
        if isinstance(n, ast.Assign):
            cibles = [t.id for t in n.targets if isinstance(t, ast.Name)]
            nom = cibles[0] if cibles else None
        elif isinstance(n, ast.FunctionDef):
            nom = n.name
        if nom in SEGMENTS:
            morceaux.append("\n".join(lignes[n.lineno - 1:n.end_lineno]))
    ns: dict = {}
    exec("\n\n".join(morceaux), ns)           # noqa: S102 — données de confiance, fournies par l'utilisateur
    return ns


def calendriers(src: Path) -> dict:
    texte = (src / "m_calendrier_officiel.py").read_text(encoding="utf-8")
    arbre = ast.parse(texte)
    ns: dict = {}
    for n in arbre.body:
        if isinstance(n, ast.Assign):
            cibles = [t.id for t in n.targets if isinstance(t, ast.Name)]
            if cibles and cibles[0] in ("REFERENCE_2026", "SOURCE_2026", "CALENDRIERS_OFFICIELS"):
                exec("\n".join(texte.split("\n")[n.lineno - 1:n.end_lineno]), ns)  # noqa: S102
    sortie = {}
    for annee, (ref, source, lignes) in ns["CALENDRIERS_OFFICIELS"].items():
        sortie[annee] = {"reference": ref, "source": source, "lignes": [
            dict(zip(["type", "libelle", "debut", "fin", "precision", "duree", "observations"], l))
            for l in lignes]}
    return sortie


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    DATA.mkdir(parents=True, exist_ok=True)
    corpus = json.loads(gzip.open(src / "static" / "pedafiche_corpus.json.gz").read())

    par_cours: dict[str, list] = {}
    for f in corpus["fiches"]:
        par_cours.setdefault(f["cours"], []).append(f)
    (DATA / "fiches").mkdir(exist_ok=True)
    for cours, fiches in par_cours.items():
        taille = ecrire_gz(DATA / "fiches" / f"{cours}.json.gz", fiches)
        print(f"fiches {cours:4} : {len(fiches):4} ({taille // 1024} Ko)")

    (DATA / "resumes").mkdir(exist_ok=True)
    res_par_cours: dict[str, list] = {}
    for r in corpus["resumes"]:
        res_par_cours.setdefault(r["cours"], []).append(r)
    for cours, lst in res_par_cours.items():
        taille = ecrire_gz(DATA / "resumes" / f"{cours}.json.gz", lst)
        print(f"résumés {cours:4} : {len(lst):4} ({taille // 1024} Ko)")

    ecrire_gz(DATA / "programmes.json.gz", {"cours": corpus["cours"], "matieres": corpus["matieres"],
                                            "programmes": corpus["programmes"]})
    ecrire_gz(DATA / "maternelle.json.gz", corpus["maternelle"])
    ns = constantes_synoptique(src)
    (DATA / "planification.json").write_text(
        json.dumps({"colonnes": [list(c) for c in ns["COLS_PLAN"]],
                    "planification": ns["PLANIFICATION_OFFICIELLE"]}, ensure_ascii=False), encoding="utf-8")
    (DATA / "edt.json").write_text(
        json.dumps({"groupes": ns["GROUPE_EDT"], "jours": ns["JOURS"], "edt": ns["EDT_OFFICIELS"]},
                   ensure_ascii=False), encoding="utf-8")
    (DATA / "calendrier.json").write_text(
        json.dumps(calendriers(src), ensure_ascii=False, indent=1), encoding="utf-8")
    for nom in ("banque_epreuves", "banque_dictees", "banque_ea_eps", "banque_taches", "banque_textes"):
        cible = RACINE / "pedafiche" / "banque" / f"{nom}.py"
        shutil.copy(src / f"{nom}.py", cible)
        code = cible.read_text(encoding="utf-8")
        code = re.sub(r"^import (banque_[a-z_]+) as", r"from pedafiche.banque import \1 as", code, flags=re.M)
        code = code.replace("import config  # noqa: E402", "from pedafiche import config  # noqa: E402")
        cible.write_text(code, encoding="utf-8")
    for ttf in (src / "static" / "fonts").iterdir():
        shutil.copy(ttf, RACINE / "pedafiche" / "fonts" / ttf.name)
    print("Import terminé.")


if __name__ == "__main__":
    main()
