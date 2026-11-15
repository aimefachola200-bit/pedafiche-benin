"""Évaluations : banque d'épreuves APC (organigramme INFRE) alimentée par la progression annuelle."""
from __future__ import annotations

from . import corpus, progression
from .banque import banque_epreuves as B

COURS_EVAL = B.COURS                       # CI → CM2


def mois_jusqua(per: str) -> list[int]:
    _c, _l, typ, m = B.PER[per]
    i = B.MOIS_SCO.index(m)
    if typ == "mensuelle":
        return [m]
    if typ == "trimestrielle":
        return B.MOIS_SCO[{12: 0, 3: 4, 6: 7}[m]:i + 1]
    return B.MOIS_SCO[:i + 1]


def progression_pour_epreuve(cours: str, per: str) -> dict:
    """Structure attendue par le générateur : {matière: {refs, sas, fiches par SA}}."""
    noms = {progression.MOIS_NOMS[m] for m in mois_jusqua(per)}
    lignes = [l for l in progression.progression_annuelle(cours) if l["mois"] in noms]
    titres = {}
    for p in corpus.programmes()["programmes"]:
        if p["cours"] == cours and p.get("type") == "sa" and p.get("num"):
            titres.setdefault((p["matiere"], p["num"]), p["titre"])
    out = {}
    for mat in progression.PLAN_COLS:
        texte = " ; ".join(l["matieres"][mat]["texte"] for l in lignes if l["matieres"][mat]["texte"])
        ids = [i for l in lignes for i in l["matieres"][mat]["fiches"]]
        par_sa: dict = {}
        for i in dict.fromkeys(ids):
            f = corpus.fiche(i)
            if f and f.get("sa"):
                par_sa.setdefault(f["sa"], []).append(f)
        refs = progression.references(texte)
        sas = [(n, titres.get((mat, n)) or (par_sa[n][0].get("intitule") if n in par_sa else f"SA {n}"))
               for n in sorted(set(refs["sa"]) | set(par_sa))]
        out[mat] = {"refs": texte[:300], "sas": sas, "fiches": par_sa}
    return out


def periodes(cours: str) -> list[tuple]:
    return B.periodes_du_cours(cours)


def epreuves_de_la_periode(cours: str, per: str) -> list[dict]:
    return B.jeu_complet(cours, per, progression_pour_epreuve(cours, per))


def epreuve(cours: str, per: str, code: str):
    return next((d for d in epreuves_de_la_periode(cours, per) if d["code"] == code), None)
