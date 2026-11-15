"""Export Word (.docx) des fiches de préparation : même contenu que le PDF, modifiable (Word, WPS, Google Docs)."""
from __future__ import annotations

import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from . import config, corpus


def _t(s) -> str:
    return re.sub(r"\*\*", "", str(s or "")).strip()


def _cellule(cell, texte, gras=False, taille=10):
    cell.text = ""
    p = cell.paragraphs[0]
    for i, ligne in enumerate(_t(texte).split("\n")):
        if i:
            p = cell.add_paragraph()
        r = p.add_run(ligne)
        r.bold = gras
        r.font.size = Pt(taille)
        r.font.name = "Times New Roman"


def fiche_docx(f: dict, ctx: dict) -> bytes:
    d = Document()
    st = d.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(11)
    sec = d.sections[0]
    sec.header.paragraphs[0].text = f"Enseignant(e) : {ctx.get('filigrane') or ctx.get('enseignant', '')}"
    sec.footer.paragraphs[0].text = (f"Conception : {config.CONCEPTEUR}"
                                     + (f" — {config.CONCEPTEUR_TEL}" if config.CONCEPTEUR_TEL else ""))
    sec.footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    h = d.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = h.add_run(f"FICHE DE PRÉPARATION — {corpus.LIB_MAT.get(f['matiere'], f['matiere'])}")
    r.bold, r.font.size = True, Pt(14)
    t = d.add_table(rows=0, cols=4)
    t.style = "Table Grid"
    dt = ctx.get("date")
    for a, b, c, e in (("Enseignant(e)", ctx.get("enseignant", ""), "École", ctx.get("ecole", "")),
                       ("Circonscription", ctx.get("circonscription", ""), "Année", ctx.get("annee", "")),
                       ("Classe / effectif", f"{ctx.get('classe', f['cours'])} / {ctx.get('effectif', '')}",
                        "Date", dt.strftime("%d/%m/%Y") if dt else "…… / …… / ………"),
                       ("Unité / SA / séance", f"{f.get('unite') or ''} {f.get('intitule') or ''} — SA {f.get('sa') or '…'} "
                        f"/ S{f.get('seance') or '…'}", "Durée", f.get("duree") or "")):
        c4 = t.add_row().cells
        for cell, v, g in zip(c4, (a, b, c, e), (True, False, True, False)):
            _cellule(cell, v, g)
    d.add_paragraph()
    tt = d.add_paragraph()
    tt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = tt.add_run(_t(f.get("titre")))
    r.bold, r.font.size = True, Pt(13)
    t = d.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    for lib, cle in (("Compétence disciplinaire", "cd"), ("Compétences transversales", "ct"),
                     ("Contenus / connaissances", "contenus"), ("Stratégies", "strategies"),
                     ("Matériel / supports", "materiel"), ("Objectifs", "objectifs"),
                     ("Activité préliminaire", "activite_preliminaire")):
        if f.get(cle):
            c2 = t.add_row().cells
            _cellule(c2[0], lib, True)
            _cellule(c2[1], f[cle])
    d.add_paragraph()
    p = d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("DÉROULEMENT DE LA SÉANCE").bold = True
    t = d.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    for cell, v in zip(t.rows[0].cells, ("Phases", "Consignes (activités)", "Résultats attendus")):
        _cellule(cell, v, True)
    for lg in f.get("deroulement") or []:
        lg = list(lg) + ["", ""]
        c3 = t.add_row().cells
        _cellule(c3[0], lg[0], True, 9)
        _cellule(c3[1], lg[1])
        _cellule(c3[2], lg[2], False, 9)
    d.add_paragraph()
    t = d.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    for lib, cle in (("Évaluation", "evaluation"), ("Projection", "projection"), ("Je retiens", "je_retiens")):
        if f.get(cle):
            c2 = t.add_row().cells
            _cellule(c2[0], lib, True)
            _cellule(c2[1], f[cle])
    if f.get("mention"):
        m = d.add_paragraph()
        r = m.add_run(_t(f["mention"]))
        r.italic, r.font.size = True, Pt(8)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()
