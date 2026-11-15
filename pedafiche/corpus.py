"""Accès au corpus de fiches (issu de SCOLARIS), chargé à la demande par cours."""
from __future__ import annotations

import gzip
import json
import re
import unicodedata
from functools import lru_cache

from . import config

COURS = ["MAT", "CI", "CP", "CE1", "CE2", "CM1", "CM2"]
LIB_COURS = {"MAT": "Maternelle", "CI": "CI", "CP": "CP", "CE1": "CE1", "CE2": "CE2",
             "CM1": "CM1", "CM2": "CM2"}
ORDRE_MAT = ["francais", "maths", "es", "est", "eps", "ea", "dg"]
LIB_MAT = {"francais": "Français", "maths": "Mathématiques", "es": "Éducation sociale",
           "est": "Éducation scientifique et technologique", "eps": "Éducation physique et sportive",
           "ea": "Éducation artistique", "dg": "Développement global"}
COULEUR_MAT = {"francais": "#1D4ED8", "maths": "#1A5C38", "es": "#831843", "est": "#4A1D96",
               "eps": "#92400E", "ea": "#BE185D", "dg": "#164E63"}


def sans_accent(t) -> str:
    return unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower()


def num_unite(f: dict):
    m = re.search(r"(\d+)", f.get("unite") or "")
    return int(m.group(1)) if m else None


def _entier(v) -> int:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return 0


def _cle_tri(f: dict):
    return (ORDRE_MAT.index(f["matiere"]) if f["matiere"] in ORDRE_MAT else 9,
            num_unite(f) or 0, _entier(f.get("sa")), _entier(f.get("seance")), str(f.get("titre") or ""))


_LEADER = re.compile(r"[.…·_]{6,}\s*(Fiche\s*(N°)?\s*:?\s*)?[.…·_]*", re.I)


def _nettoyer(f: dict) -> dict:
    """Retire les points de suite hérités des modèles papier (titres, activités…)."""
    for cle in ("sa", "seance"):                      # numéros parfois saisis en texte dans le corpus
        v = f.get(cle)
        f[cle] = int(v) if isinstance(v, str) and v.strip().isdigit() else (v if isinstance(v, int) else None)
    if re.match(r"(?i)\s*PREPARATION DE", f.get("sous_matiere") or ""):
        f["sous_matiere"] = ""
    for k, v in f.items():
        if isinstance(v, str):
            f[k] = _LEADER.sub("", v).strip()
        elif isinstance(v, list):
            f[k] = [[_LEADER.sub("", c).strip() if isinstance(c, str) else c for c in ligne]
                    if isinstance(ligne, list) else ligne for ligne in v]
    return f


@lru_cache(maxsize=8)
def fiches_du_cours(cours: str) -> tuple:
    chemin = config.DATA / "fiches" / f"{cours}.json.gz"
    if not chemin.exists():
        return ()
    with gzip.open(chemin, "rt", encoding="utf-8") as f:
        return tuple(sorted((_nettoyer(x) for x in json.load(f)), key=_cle_tri))


@lru_cache(maxsize=1)
def _index() -> dict:
    return {f["id"]: f for c in COURS for f in fiches_du_cours(c)}


def fiche(fiche_id: str):
    return _index().get(fiche_id)


def fiches(cours: str, matiere: str | None = None, texte: str | None = None) -> list[dict]:
    out = [f for f in fiches_du_cours(cours) if not matiere or f["matiere"] == matiere]
    if texte:
        mots = [sans_accent(m) for m in texte.split()]
        out = [f for f in out if all(m in sans_accent(" ".join(
            str(f.get(k) or "") for k in ("titre", "intitule", "sous_matiere", "contenus", "unite"))) for m in mots)]
    return out


def matieres_du_cours(cours: str) -> list[str]:
    vues = {f["matiere"] for f in fiches_du_cours(cours)}
    return [m for m in ORDRE_MAT if m in vues]


def unites(cours: str, matiere: str) -> list[dict]:
    """Regroupe les fiches (déjà ordonnées) par unité / SA, dans l'ordre de la progression."""
    groupes: dict = {}
    for f in fiches(cours, matiere):
        cle = (f.get("sous_matiere"), f.get("unite"), f.get("sa"), f.get("intitule"))
        groupes.setdefault(cle, []).append(f)
    return [{"sous_matiere": k[0], "unite": k[1], "sa": k[2], "intitule": k[3], "fiches": v}
            for k, v in groupes.items()]


@lru_cache(maxsize=1)
def programmes() -> dict:
    with gzip.open(config.DATA / "programmes.json.gz", "rt", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------------ résumés
def _complements(cours: str) -> list[dict]:
    """Résumés ajoutés au corpus SCOLARIS (collections originales, ex. « Conjugaison sans faute »)."""
    out = []
    for fichier in sorted((config.DATA / "resumes_complements").glob("*.json")):
        out += [r for r in json.loads(fichier.read_text(encoding="utf-8")) if r["cours"] == cours]
    return out


@lru_cache(maxsize=8)
def resumes_du_cours(cours: str) -> tuple:
    chemin = config.DATA / "resumes" / f"{cours}.json.gz"
    base = []
    if chemin.exists():
        with gzip.open(chemin, "rt", encoding="utf-8") as f:
            base = json.load(f)
    return tuple(_nettoyer(r) for r in base + _complements(cours))


@lru_cache(maxsize=1)
def _index_resumes() -> dict:
    return {r["id"]: r for c in COURS for r in resumes_du_cours(c)}


def resume(rid: str):
    return _index_resumes().get(rid)


def resumes(cours: str, matiere: str | None = None, mois: str | None = None,
            texte: str | None = None) -> list[dict]:
    out = [r for r in resumes_du_cours(cours)
           if (not matiere or r["matiere"] == matiere) and (not mois or r.get("mois") == mois)]
    if texte:
        mots = [sans_accent(m) for m in texte.split()]
        out = [r for r in out if all(m in sans_accent(" ".join(
            str(r.get(k) or "") for k in ("titre", "domaine", "regle", "collection"))) for m in mots)]
    return out


def resumes_de_la_fiche(f: dict) -> list[dict]:
    return [r for r in resumes_du_cours(f["cours"]) if f["id"] in (r.get("fiches") or [])]
