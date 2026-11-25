"""Excel pour PédaFiche : mêmes modèles officiels EducMaster que GESCOL et SCOLARIS (liste des élèves, notes sur 20).
Les modèles officiels sont lus dans pedafiche/data/modeles/ s'ils y sont ; sinon un classeur de même présentation est fabriqué."""
from __future__ import annotations

import io
import os
import re
import unicodedata
from datetime import date, datetime

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "modeles")
ENTETES_CLASSE = ["Nom", "Prénom ( s )", "Sexe", "Date de naissance", "Lieu de naissance", "Téléphone de parents", "Nationalité", "Npi"]
MATIERES_COLONNES = {"maths": ["math"], "es": ["es"], "est": ["est"], "eps": ["eps"],
                     "ea": ["ea oral", "ea dessin couture", "ea dessin", "ea"],
                     "francais": ["dictee", "expresion ecrite", "expression ecrite", "comprehension de l ecrit"]}


def _n(t) -> str:
    s = unicodedata.normalize("NFD", str(t if t is not None else "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _charger(nom):
    import openpyxl
    p = os.path.join(DOSSIER, nom)
    return openpyxl.load_workbook(p) if os.path.exists(p) else None


def _octets(wb) -> bytes:
    buf = io.BytesIO()
    wb.save(buf)
    wb.close()
    return buf.getvalue()


def _date_fr(v) -> str:
    if isinstance(v, (datetime, date)):
        return v.strftime("%d/%m/%Y")
    s = str(v or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else s


def modele_eleves(cours, eleves) -> bytes:
    """Modèle officiel des élèves (feuille du cours) rempli avec la liste de la classe."""
    import openpyxl
    wb = _charger("educmaster_modele_classe.xlsx")
    ws = next((s for s in wb.worksheets if _n(s.title) == _n(cours)), None) if wb else None
    if ws is None:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = str(cours)[:30]
        for j, h in enumerate(ENTETES_CLASSE, 1):
            ws.cell(row=1, column=j, value=h)
    else:
        for s in list(wb.worksheets):
            if s is not ws:
                wb.remove(s)
    for i, e in enumerate(eleves, 2):
        vals = [e["nom"], e["prenom"], e["sexe"] or None, e["naissance"] or None, None, e["telephone"] or None, "Béninoise", e["matricule"] or None]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=i, column=j, value=v)
            if j in (6, 8):
                c.number_format = "@"
    return _octets(wb)


def lire_eleves(contenu: bytes, cours):
    """Lit le modèle des élèves rempli (feuille du cours, sinon première feuille). Retourne (liste, message d'erreur)."""
    import openpyxl
    try:
        wb = openpyxl.load_workbook(io.BytesIO(contenu), data_only=True, read_only=True)
    except Exception:  # noqa: BLE001
        return [], "Classeur illisible (fichier abîmé ou ce n'est pas un fichier Excel)."
    ws = next((s for s in wb.worksheets if _n(s.title) == _n(cours)), wb.worksheets[0])
    lignes = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    h = next((i for i, r in enumerate(lignes[:10]) if r and _n(r[0]).startswith("nom")), None)
    if h is None:
        return [], "En-têtes introuvables : la première colonne doit s'appeler « Nom »."
    col = {}
    for j, t in enumerate(lignes[h]):
        k = _n(t)
        for cle, motif in (("nom", "nom"), ("prenom", "prenom"), ("sexe", "sexe"), ("naissance", "date de naissance"), ("lieu", "lieu"),
                           ("telephone", "telephone"), ("npi", "npi"), ("npi", "nip"), ("matricule", "matricule")):
            if (k == motif or k.startswith(motif)) and cle not in col:
                col[cle] = j
    def val(r, cle):
        j = col.get(cle)
        return r[j] if j is not None and j < len(r) and r[j] is not None else ""
    out = []
    for r in lignes[h + 1:]:
        nom = str(val(r, "nom")).strip()
        if not nom:
            continue
        s = str(val(r, "sexe")).strip().upper()[:1]
        out.append({"nom": nom, "prenom": str(val(r, "prenom")).strip(), "sexe": "M" if s in ("M", "G") else ("F" if s == "F" else ""),
                    "naissance": _date_fr(val(r, "naissance")), "matricule": str(val(r, "matricule") or val(r, "npi")).strip(),
                    "tuteur": "", "telephone": str(val(r, "telephone")).strip()})
    return out, None


def modele_notes(eleves, ev, notes, libelle) -> bytes:
    """Feuille de notes dans la présentation du modèle officiel (matricule, nom, prénoms, note obtenue / note perf.)."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Notes"
    for j, t in enumerate(("Matricule", "Nom", "Prénoms", libelle), 1):
        ws.cell(row=1, column=j, value=t)
    ws.cell(row=2, column=4, value="Note obtenue")
    ws.cell(row=2, column=5, value="Note perf.")
    for i, e in enumerate(eleves, 3):
        v = notes.get(e["id"])
        for j, x in enumerate((e["matricule"] or None, e["nom"], e["prenom"], v, ev["bareme"] if v is not None else None), 1):
            ws.cell(row=i, column=j, value=int(x) if isinstance(x, float) and x.is_integer() else x)
    for lettre, l in (("A", 14), ("B", 24), ("C", 24), ("D", 16), ("E", 12)):
        ws.column_dimensions[lettre].width = l
    return _octets(wb)


def lire_notes(contenu: bytes, eleves, ev, matiere: str):
    """Retourne ({eleve_id: note}, [messages]). Accepte la feuille ci-dessus et le modèle officiel multi-matières."""
    import openpyxl
    try:
        wb = openpyxl.load_workbook(io.BytesIO(contenu), data_only=True, read_only=True)
    except Exception:  # noqa: BLE001
        return {}, ["Classeur illisible (fichier abîmé ou ce n'est pas un fichier Excel)."]
    ws = wb.worksheets[0]
    lignes = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    if len(lignes) < 3:
        return {}, ["Aucune ligne de données (modèle : en-têtes sur les lignes 1 et 2, élèves à partir de la ligne 3)."]
    h1, h2 = lignes[0], lignes[1]
    cols = []
    for j, t in enumerate(h2):
        if _n(t) == "note obtenue":
            k = j
            while k >= 0 and not _n(h1[k] if k < len(h1) else ""):
                k -= 1
            cols.append((j, _n(h1[k]) if k >= 0 and k < len(h1) else ""))
    if not cols:
        return {}, ["Colonne « Note obtenue » introuvable (ligne 2)."]
    if len(cols) == 1:
        choix = cols[0][0]
    else:
        cand = [(j, s) for j, s in cols if any(s == m or s.startswith(m + " ") for m in MATIERES_COLONNES.get(matiere, []))]
        if len(cand) > 1:
            titre = _n(ev["titre"])
            cand = [(j, s) for j, s in cand if s.split(" ")[0] in titre] or cand
        if len(cand) != 1:
            return {}, ["Plusieurs matières dans le fichier : mettez la matière (par exemple « Dictée ») dans le titre de l'évaluation, "
                        "ou supprimez les colonnes inutiles."]
        choix = cand[0][0]
    par_mat = {(e["matricule"] or "").strip(): e for e in eleves if (e["matricule"] or "").strip()}
    par_nom = {_n(f"{e['nom']} {e['prenom']}"): e for e in eleves}
    res, msg, inconnus = {}, [], []
    for i, r in enumerate(lignes[2:], 3):
        mat, nom, pre = (str(r[k]).strip() if k < len(r) and r[k] is not None else "" for k in range(3))
        if not (mat or nom or pre):
            continue
        e = par_mat.get(mat) or par_nom.get(_n(f"{nom} {pre}"))
        if not e:
            inconnus.append(f"{nom} {pre}".strip() or mat)
            continue
        v = r[choix] if choix < len(r) else None
        if v is None or (isinstance(v, str) and not v.strip()):
            continue
        try:
            x = float(v) if isinstance(v, (int, float)) else float(str(v).strip().replace(",", ".").replace(" ", ""))
        except ValueError:
            msg.append(f"ligne {i} ({nom}) : « {v} » n'est pas un nombre")
            continue
        if not 0 <= x <= ev["bareme"]:
            msg.append(f"ligne {i} ({nom}) : note hors de 0 à {ev['bareme']:g}")
            continue
        res[e["id"]] = round(x, 2)
    if inconnus:
        msg.append("élèves non reconnus (ignorés) : " + ", ".join(inconnus[:8]) + (" …" if len(inconnus) > 8 else ""))
    return res, msg
