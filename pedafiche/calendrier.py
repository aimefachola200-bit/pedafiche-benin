"""Calendrier scolaire officiel et règles de calcul des jours de classe.

Règles (identiques à SCOLARIS) : un jour de classe est un jour du lundi au vendredi,
situé dans un trimestre et hors congés, vacances et jours fériés. Une période dont la
précision contient « après les cours » commence effectivement le lendemain de sa date de début.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from functools import lru_cache

from . import config

SANS_CLASSE = ("conges", "ferie", "vacances")
COULEURS = {"pre_rentree": "#FDE68A", "trimestre": "#D1FAE5", "conges": "#FECACA",
            "ferie": "#FCA5A5", "vacances": "#E9D5FF", "evenement": "#BFDBFE", "autre": "#E5E7EB"}
TYPES_LIB = {"pre_rentree": "Pré-rentrée", "trimestre": "Trimestre", "conges": "Congés",
             "ferie": "Jour férié", "vacances": "Grandes vacances", "evenement": "Événement",
             "autre": "Autre"}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


@lru_cache(maxsize=1)
def _brut() -> dict:
    return json.loads((config.DATA / "calendrier.json").read_text(encoding="utf-8"))


def annees() -> list[str]:
    return sorted(_brut())


def reference(annee: str) -> dict:
    d = _brut()[annee]
    return {"reference": d["reference"], "source": d["source"]}


def periodes(annee: str) -> list[dict]:
    out = []
    for l in _brut()[annee]["lignes"]:
        deb, fin = date.fromisoformat(l["debut"]), date.fromisoformat(l["fin"])
        eff = deb + timedelta(days=1) if "après les cours" in (l["precision"] or "").lower() \
            and l["type"] in SANS_CLASSE else deb
        out.append({**l, "debut_d": deb, "fin_d": fin, "debut_effectif": eff})
    return out


def _jours(p: dict):
    d = p["debut_effectif"]
    while d <= p["fin_d"]:
        yield d
        d += timedelta(days=1)


@lru_cache(maxsize=4)
def jours_de_classe(annee: str) -> frozenset:
    ps = periodes(annee)
    en_trimestre = {d for p in ps if p["type"] == "trimestre" for d in _jours(p)}
    bloques = {d for p in ps if p["type"] in SANS_CLASSE for d in _jours(p)}
    return frozenset(d for d in en_trimestre - bloques if d.weekday() < 5)


def est_jour_classe(d: date, annee: str = config.ANNEE) -> bool:
    return d in jours_de_classe(annee)


def trimestre_de(d: date, annee: str = config.ANNEE):
    for p in periodes(annee):
        if p["type"] == "trimestre" and p["debut_d"] <= d <= p["fin_d"]:
            return p["libelle"]
    return None


def semaines_de_classe(annee: str = config.ANNEE) -> list[date]:
    """Lundis des semaines comptant au moins un jour de classe."""
    return sorted({d - timedelta(days=d.weekday()) for d in jours_de_classe(annee)})


def resume(annee: str = config.ANNEE) -> dict:
    jc = jours_de_classe(annee)
    return {"jours_de_classe": len(jc), "semaines": len(semaines_de_classe(annee)),
            "rentree": min(jc), "fin_cours": max(jc)}


def evenements_du_jour(d: date, annee: str = config.ANNEE) -> list[dict]:
    return [p for p in periodes(annee) if p["type"] != "trimestre"
            and p["debut_effectif"] <= d <= p["fin_d"]]


def grille_mois(annee_civile: int, mois: int, annee: str = config.ANNEE) -> list[list[dict]]:
    """Semaines (lun→dim) d'un mois avec le type de chaque jour : classe, férié, congés…"""
    ps = periodes(annee)
    premier = date(annee_civile, mois, 1)
    d = premier - timedelta(days=premier.weekday())
    semaines = []
    while True:
        sem = []
        for k in range(7):
            j = d + timedelta(days=k)
            if j.month != mois:
                sem.append(None)
                continue
            if j in jours_de_classe(annee):
                t = "classe"
            elif j.weekday() >= 5:
                t = "weekend"
            else:
                t = next((p["type"] for p in ps if p["type"] != "trimestre"
                          and p["debut_effectif"] <= j <= p["fin_d"]), "hors")
            sem.append({"jour": j.day, "date": j, "type": t})
        semaines.append(sem)
        d += timedelta(days=7)
        if d.month != mois and d > premier:
            break
    return semaines
