"""Carnet de notes : moyennes sur 20, rangs avec ex æquo, appréciation, remédiation (Python pur, testé).

Toutes les notes sont ramenées sur 20 (barème de l'épreuve), comme dans GESCOL et SCOLARIS. La moyenne d'une matière est la moyenne pondérée
(coefficient de l'épreuve) de ses épreuves ; la moyenne générale est la moyenne des matières notées."""
from __future__ import annotations

SEUIL = 10.0         # moyenne de passage sur 20
PERIODES = (("T1", "1er trimestre"), ("T2", "2e trimestre"), ("T3", "3e trimestre"))


def sur20(valeur, bareme) -> float | None:
    if valeur is None or not bareme:
        return None
    return round(float(valeur) * 20.0 / float(bareme), 2)


def moyenne_ponderee(couples: list[tuple[float, float]]) -> float | None:
    """couples = [(note sur 20, coefficient)]"""
    tot = sum(c for _, c in couples)
    return round(sum(n * c for n, c in couples) / tot, 2) if tot else None


def rangs(valeurs: dict) -> dict:
    """Rang avec ex æquo (1, 2, 2, 4) ; les valeurs None ne sont pas classées."""
    ok = sorted(((k, round(v, 2)) for k, v in valeurs.items() if v is not None), key=lambda x: -x[1])
    res, dernier, pos = {}, None, 0
    for i, (k, v) in enumerate(ok, start=1):
        if v != dernier:
            pos, dernier = i, v
        res[k] = pos
    return res


def appreciation(m) -> str:
    if m is None:
        return ""
    for seuil, lib in ((16, "Très bien"), (14, "Bien"), (12, "Assez bien"), (10, "Passable"), (7, "Insuffisant")):
        if m >= seuil:
            return lib
    return "Très insuffisant"


def resultats(eleves: list[dict], evals: list[dict], notes: dict, periode: str | None = None) -> dict:
    """eleves=[{id,nom,prenom}] ; evals=[{id,matiere,bareme,coef,periode}] ; notes={(eval_id, eleve_id): valeur}.
    Retourne {matieres:[...], lignes:[{eleve, par_matiere:{m:moyenne}, moyenne, rang, appreciation}], stats:{...}}."""
    ev = [e for e in evals if periode in (None, "", e["periode"])]
    matieres = sorted({e["matiere"] for e in ev})
    lignes = []
    for el in eleves:
        par = {}
        for m in matieres:
            c = [(sur20(notes.get((e["id"], el["id"])), e["bareme"]), e["coef"]) for e in ev if e["matiere"] == m]
            par[m] = moyenne_ponderee([(n, k) for n, k in c if n is not None])
        vals = [v for v in par.values() if v is not None]
        moy = round(sum(vals) / len(vals), 2) if vals else None
        lignes.append({"eleve": el, "par_matiere": par, "moyenne": moy, "appreciation": appreciation(moy)})
    rg = rangs({l["eleve"]["id"]: l["moyenne"] for l in lignes})
    for l in lignes:
        l["rang"] = rg.get(l["eleve"]["id"])
    notes_ok = [l["moyenne"] for l in lignes if l["moyenne"] is not None]
    stats = {"effectif": len(lignes), "classes": len(notes_ok),
             "moyenne": round(sum(notes_ok) / len(notes_ok), 2) if notes_ok else None,
             "max": max(notes_ok) if notes_ok else None, "min": min(notes_ok) if notes_ok else None,
             "taux_reussite": round(100 * sum(1 for x in notes_ok if x >= SEUIL) / len(notes_ok), 1) if notes_ok else None}
    return {"matieres": matieres, "lignes": lignes, "stats": stats}


def a_remedier(eleves: list[dict], ev: dict, notes: dict, seuil: float = SEUIL) -> list[dict]:
    """Élèves sous le seuil à une épreuve (note sur 20), du plus faible au moins faible."""
    out = []
    for el in eleves:
        n = sur20(notes.get((ev["id"], el["id"])), ev["bareme"])
        if n is not None and n < seuil:
            out.append({"eleve": el, "note20": n})
    return sorted(out, key=lambda x: x["note20"])


def bilan_presences(lignes: list[dict]) -> list[dict]:
    """lignes=[{eleve_id, statut, justifie}] → compte par élève."""
    res: dict = {}
    for l in lignes:
        r = res.setdefault(l["eleve_id"], {"P": 0, "A": 0, "R": 0, "A_nj": 0})
        r[l["statut"]] += 1
        if l["statut"] == "A" and not l.get("justifie"):
            r["A_nj"] += 1
    return [{"eleve_id": k, **v} for k, v in res.items()]


def decrocheurs(bilan: list[dict], seuil: int = 3) -> list[int]:
    return [b["eleve_id"] for b in bilan if b["A_nj"] >= seuil]
