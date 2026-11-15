"""Emplois du temps : modèles officiels (MEMP) par groupe de cours, personnalisables par classe."""
from __future__ import annotations

import json
import re
from datetime import date
from functools import lru_cache

from . import config, corpus, progression

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]
JOURS_LIB = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
_MATIERES = [(r"dict", "francais", "Dictée"), (r"fran|lecture|vocabulaire|expression", "francais", ""),
             (r"math|calcul", "maths", ""), (r"\bes\b|morale|civisme|histoire|g[ée]o", "es", ""),
             (r"\best\b", "est", ""), (r"\beps\b", "eps", ""),
             (r"\bea\b|po[ée]sie|chant|dessin|conte|couture|\btm\b|art", "ea", ""),
             (r"c[ée]r[ée]monial", "dg", "Cérémonial des couleurs")]


@lru_cache(maxsize=1)
def _brut() -> dict:
    return json.loads((config.DATA / "edt.json").read_text(encoding="utf-8"))


def edt_defaut(cours: str) -> dict:
    groupe = _brut()["groupes"].get(cours.lower() if cours != "MAT" else "maternelle1", "cm1_cm2")
    return json.loads(json.dumps(_brut()["edt"][groupe]))


def creneaux(cellule: str) -> list[dict]:
    out = []
    for ligne in str(cellule or "").split("\n"):
        ligne = ligne.strip()
        if not ligne:
            continue
        duree = re.search(r"(\d+)\s*(min|h)", ligne, re.I)
        mat = next((m for rx, m, _ in _MATIERES if re.search(rx, ligne, re.I)), None)
        out.append({"libelle": ligne, "matiere": mat, "duree": duree.group(0) if duree else ""})
    return out


def journee(edt: dict, cours: str, jour: date, suggestions: dict | None = None) -> list[dict]:
    """Créneaux d'une journée avec la fiche suggérée (rotation par matière sur la semaine)."""
    if jour.weekday() > 4:
        return []
    suggestions = progression.fiches_de_la_semaine(cours, jour) if suggestions is None else suggestions
    rang: dict = {}
    # les séances des jours précédents de la semaine consomment les premières fiches
    for k in range(jour.weekday()):
        for ligne in edt.get("lignes", []):
            for c in creneaux(ligne.get(JOURS[k])):
                if c["matiere"]:
                    rang[c["matiere"]] = rang.get(c["matiere"], 0) + 1
    out = []
    for ligne in edt.get("lignes", []):
        for c in creneaux(ligne.get(JOURS[jour.weekday()])):
            c["horaire"] = ligne.get("horaire", "")
            liste = suggestions.get(c["matiere"]) or []
            if c["matiere"] and liste:
                i = rang.get(c["matiere"], 0)
                f = liste[i % len(liste)]
                rang[c["matiere"]] = i + 1
                c["fiche_id"], c["fiche_titre"] = f["id"], f["titre"]
            out.append(c)
    return out
