"""Progression annuelle : planification mensuelle officielle (SCOLARIS) → SA / unités → fiches."""
from __future__ import annotations

import json
import math
import re
from datetime import date, timedelta
from functools import lru_cache

from . import calendrier, config, corpus

PLAN_COLS = {"francais": ["francais"], "maths": ["maths"],
             "es": ["es_morale", "es_civisme", "es_histoire", "es_geographie"], "est": ["est"],
             "eps": ["eps"], "ea": ["ea_chant", "ea_poesie", "ea_conte", "ea_dessin", "ea_couture"]}
MOIS_NOMS = {9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre", 1: "Janvier",
             2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin"}
MOIS_ORDRE = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6]


@lru_cache(maxsize=1)
def _plan() -> dict:
    return json.loads((config.DATA / "planification.json").read_text(encoding="utf-8"))


def references(texte: str) -> dict:
    """« U1 semaine2 à U3 », « D1 SA1 Séq 8 à 15 », « SA2 Séq3 à SA3 » → numéros cités."""
    t = str(texte or "")
    sa: set = set()
    for m in re.finditer(r"SA\s*(\d+)((?:\s*(?:,|et|à|-)\s*\d+)*)", t, re.I):
        sa.add(int(m.group(1)))
        nums = [int(x) for x in re.findall(r"\d+", m.group(2) or "")]
        if re.search(r"à|-", m.group(2) or "") and nums:
            sa.update(range(int(m.group(1)), max(nums) + 1) if max(nums) - int(m.group(1)) < 12 else nums)
        else:
            sa.update(nums)
    u = {int(x) for x in re.findall(r"\bU\s*(\d+)", t)}
    d = {int(x) for x in re.findall(r"\bD\s*(\d+)", t)}
    for a, b in re.findall(r"\bU\s*(\d+)[^U]*?à\s*U\s*(\d+)", t):
        if 0 <= int(b) - int(a) < 12:
            u.update(range(int(a), int(b) + 1))
    return {"sa": sorted(sa), "u": sorted(u), "d": sorted(d)}


def correspondances(cours: str, matiere: str, refs: dict) -> list[dict]:
    if not (refs["sa"] or refs["u"] or refs["d"]):
        return []
    out = []
    for f in corpus.fiches(cours, matiere):
        nu = corpus.num_unite(f)
        if matiere == "francais" and refs["u"]:
            ok = nu in refs["u"]
        elif matiere == "maths" and refs["d"]:
            ok = nu in refs["d"]
        else:
            ok = bool(refs["sa"]) and f.get("sa") in refs["sa"]
        if ok:
            out.append(f)
    return out


def planification(cours: str) -> list[dict]:
    """Lignes mensuelles officielles du cours (CI → CM2). Vide pour la maternelle."""
    return [dict(l) for l in _plan()["planification"].get(cours, [])]


def progression_annuelle(cours: str) -> list[dict]:
    """Pour chaque mois : texte officiel par matière, références et fiches correspondantes.

    Quand la planification ne cite aucun numéro de SA / unité (ex. « Semaines 1-2 » au CI),
    les fiches de la matière sont réparties linéairement sur les mois (mode « lineaire »).
    """
    lignes = planification(cours)
    n_mois = max(1, len(lignes))
    out = []
    for i, ligne in enumerate(lignes):
        mats = {}
        for mat, cols in PLAN_COLS.items():
            texte = " ; ".join(str(ligne.get(c) or "").strip() for c in cols if str(ligne.get(c) or "").strip())
            refs = references(texte)
            fiches = correspondances(cours, mat, refs)
            mode = "officiel"
            if not fiches and texte and not re.fullmatch(r"(?i)[-\s;]*(initiation|[ée]valuation diagnostique)?[-\s;]*", texte):
                tout = corpus.fiches(cours, mat)
                a, b = round(i * len(tout) / n_mois), round((i + 1) * len(tout) / n_mois)
                fiches, mode = tout[a:b], "lineaire"
            mats[mat] = {"texte": texte, "refs": refs, "mode": mode, "fiches": [f["id"] for f in fiches]}
        out.append({"trimestre": ligne.get("trimestre"), "mois": ligne.get("mois"),
                    "observations": ligne.get("observations", ""), "matieres": mats})
    return out


def _ligne_du_mois(cours: str, jour: date):
    nom = MOIS_NOMS.get(jour.month)
    return next((p for p in progression_annuelle(cours) if p["mois"] == nom), None)


def fiches_de_la_semaine(cours: str, jour: date, annee: str = config.ANNEE) -> dict[str, list[dict]]:
    """Fiches à préparer la semaine de `jour`, par matière.

    Les fiches du mois (selon la planification officielle) sont réparties à parts égales sur
    les semaines de classe du mois ; la semaine courante reçoit sa tranche.
    """
    ligne = _ligne_du_mois(cours, jour)
    if not ligne:
        return {}
    semaines = [s for s in calendrier.semaines_de_classe(annee)
                if (s + timedelta(days=3)).month == jour.month]
    lundi = jour - timedelta(days=jour.weekday())
    rang = semaines.index(lundi) if lundi in semaines else 0
    n = max(1, len(semaines))
    res = {}
    for mat, info in ligne["matieres"].items():
        liste = [f for f in (corpus.fiche(i) for i in info["fiches"]) if f]
        if not liste:
            continue
        taille = math.ceil(len(liste) / n)
        res[mat] = liste[rang * taille:(rang + 1) * taille] or liste[-taille:]
    return res
