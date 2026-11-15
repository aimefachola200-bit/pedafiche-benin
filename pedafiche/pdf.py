"""PDF : fiche de préparation (A4 recto-verso), épreuves, tableaux (progression, EDT, calendrier).

Chaque page porte :
 * le nom du titulaire de la classe en filigrane (oblique, éclaté sur la page) ;
 * en bas, « Page x / y » et la mention « Conception : … » du concepteur.
Polices : Liberation Serif (licence OFL), équivalent métrique de Times New Roman.
"""
from __future__ import annotations

import io
import re
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

from . import config, corpus

_FONTS = {"Serif": "LiberationSerif-Regular.ttf", "Serif-Bold": "LiberationSerif-Bold.ttf",
          "Serif-Italic": "LiberationSerif-Italic.ttf", "Serif-BoldItalic": "LiberationSerif-BoldItalic.ttf"}
_ok = False


def _polices() -> None:
    global _ok
    if _ok:
        return
    for nom, fichier in _FONTS.items():
        pdfmetrics.registerFont(TTFont(nom, str(config.RACINE / "fonts" / fichier)))
    pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-Bold",
                                  italic="Serif-Italic", boldItalic="Serif-BoldItalic")
    _ok = True


def txt(s) -> str:
    """Texte → XML ReportLab : **gras**, retours à la ligne, puces conservées."""
    s = escape(str(s or ""))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s, flags=re.S).replace("**", "")
    return s.replace("\n", "<br/>")


class CanevasPeda(canvas.Canvas):
    """Canvas à deux passes : filigrane + « Page x / y » + mention du concepteur."""
    filigrane = ""
    paysage = False

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._pages: list = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for etat in self._pages:
            self.__dict__.update(etat)
            self._decor(total)
            super().showPage()
        super().save()

    def _decor(self, total: int) -> None:
        w, h = self._pagesize
        if self.filigrane:
            self.saveState()
            self.setFillColor(colors.HexColor("#1A3A6B"))
            self.setFillAlpha(0.07)
            self.setFont("Serif-BoldItalic", 26)
            for yy in range(-int(h), int(h) * 2, 190):
                for xx in range(-int(w), int(w) * 2, 330):
                    self.saveState()
                    self.translate(xx + (yy // 190 % 2) * 165, yy)
                    self.rotate(32)
                    self.drawString(0, 0, self.filigrane)
                    self.restoreState()
            self.restoreState()
        self.saveState()
        self.setFillColor(colors.HexColor("#6B7280"))
        self.setFont("Serif", 8.5)
        self.drawCentredString(w / 2, 9 * mm, f"Page {self._pageNumber} / {total}")
        self.setFillColor(colors.HexColor("#98A2B3"))
        self.setFont("Serif-Italic", 7.5)
        mention = f"Conception : {config.CONCEPTEUR}"
        if config.CONCEPTEUR_TEL:
            mention += f" — {config.CONCEPTEUR_TEL}"
        self.drawCentredString(w / 2, 5 * mm, mention)
        self.restoreState()


def _doc(buf, titulaire: str, paysage=False, marges=(14, 12, 14, 16)):
    _polices()
    taille = landscape(A4) if paysage else A4
    g, h, d, b = [m * mm for m in marges]
    doc = BaseDocTemplate(buf, pagesize=taille, leftMargin=g, topMargin=h, rightMargin=d,
                          bottomMargin=b + 6 * mm, title="PédaFiche Bénin", author=config.CONCEPTEUR)
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(g, b + 6 * mm, taille[0] - g - d,
                                                              taille[1] - h - b - 6 * mm,
                                                              leftPadding=0, rightPadding=0,
                                                              topPadding=0, bottomPadding=0)])])
    cls = type("C", (CanevasPeda,), {"filigrane": titulaire})
    return doc, cls, taille[0] - g - d


def _st(taille: float, **k) -> ParagraphStyle:
    return ParagraphStyle("x", fontName=k.pop("fontName", "Serif"), fontSize=taille,
                          leading=k.pop("leading", taille * 1.22), **k)


def _tab(data, widths, entete=None, couleur="#1D4ED8", fond_col0=True, pad=3):
    t = Table(data, colWidths=widths, repeatRows=1 if entete else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#444444")),
             ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), pad),
             ("BOTTOMPADDING", (0, 0), (-1, -1), pad), ("LEFTPADDING", (0, 0), (-1, -1), 4),
             ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if entete:
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(couleur))]
    elif fond_col0:
        style += [("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2F7"))]
    t.setStyle(TableStyle(style))
    return t


# --------------------------------------------------------------------------- fiche
def _histoire_fiche(f: dict, ctx: dict, corps: float, larg: float) -> list:
    couleur = corpus.COULEUR_MAT.get(f["matiere"], "#1A3A6B")
    n, b = _st(corps), _st(corps, fontName="Serif-Bold")
    petit = _st(corps - 0.5)
    blanc = _st(corps + 0.5, fontName="Serif-Bold", textColor=colors.white)

    def P(t, s=n):
        return Paragraph(txt(t), s)

    bandeau = Table([[Paragraph(txt(f"{corpus.LIB_MAT.get(f['matiere'], f['matiere'])} — "
                                    f"{f.get('sous_matiere') or ''}").rstrip(" —"), blanc),
                      Paragraph(txt(f"{f['cours']} · {f.get('duree') or ''}"),
                                _st(corps + 0.5, fontName="Serif-Bold", textColor=colors.white,
                                    alignment=2))]], colWidths=[larg * .7, larg * .3])
    bandeau.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(couleur)),
                                 ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    d = ctx.get("date")
    ident = _tab([[P("Enseignant(e)", b), P(ctx.get("enseignant", "")), P("École", b), P(ctx.get("ecole", ""))],
                  [P("Circonscription", b), P(ctx.get("circonscription", "")), P("Année", b), P(ctx.get("annee", ""))],
                  [P("Classe / effectif", b), P(f"{ctx.get('classe', f['cours'])} / {ctx.get('effectif', '')}"),
                   P("Date", b), P(d.strftime("%d/%m/%Y") if d else "…… / …… / ………")],
                  [P("Unité / SA / séance", b), P(f"{f.get('unite') or ''} — {f.get('intitule') or ''} — "
                                                 f"SA {f.get('sa') or '…'} / S{f.get('seance') or '…'}"), "", ""]],
                 [larg * .19, larg * .36, larg * .13, larg * .32], fond_col0=False)
    ident.setStyle(TableStyle([("SPAN", (1, 3), (3, 3)), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
                               ("BACKGROUND", (2, 0), (2, 2), colors.HexColor("#F2F2F2"))]))
    plan = [[P(k, b), P(f.get(c))] for k, c in (
        ("Compétence disciplinaire", "cd"), ("Compétences transversales", "ct"),
        ("Contenus / connaissances", "contenus"), ("Stratégies", "strategies"),
        ("Matériel / supports", "materiel"), ("Objectifs", "objectifs"))
            if f.get(c) and not str(f[c]).lower().startswith("confer")]
    out = [bandeau, Spacer(1, 4), ident, Spacer(1, 5),
           Paragraph(txt(f["titre"]), _st(corps + 2.5, fontName="Serif-Bold", alignment=TA_CENTER, leading=(corps + 2.5) * 1.2)),
           Spacer(1, 4), _tab(plan, [larg * .24, larg * .76])]
    if f.get("activite_preliminaire"):
        out += [Spacer(1, 4), _tab([[P("Activité préliminaire", b), P(f["activite_preliminaire"])]],
                                   [larg * .24, larg * .76])]
    out.append(PageBreak())                                        # ---- verso (page 2)
    lignes = [[P("Phases", blanc), P("Consignes (activités)", blanc), P("Résultats attendus", blanc)]]
    for r in f.get("deroulement") or []:
        r = list(r) + ["", ""]
        phase = re.sub(r"\*\*", "", str(r[0])).strip()
        lignes.append([Paragraph(txt(phase), _st(corps - 1.5, fontName="Serif-Bold")), P(r[1]), P(r[2], _st(corps - 0.5, fontName="Serif-Italic"))])
    out += [Paragraph("DÉROULEMENT DE LA SÉANCE", _st(corps + 1, fontName="Serif-Bold", alignment=TA_CENTER)),
            Spacer(1, 3), _tab(lignes, [larg * .19, larg * .58, larg * .23], entete=True, couleur=couleur)]
    fin = [[P(k, b), P(f.get(c))] for k, c in (("Évaluation", "evaluation"), ("Projection", "projection"))
           if f.get(c)]
    if fin:
        out += [Spacer(1, 4), _tab(fin, [larg * .15, larg * .85])]
    if f.get("je_retiens"):
        out += [Spacer(1, 4), _tab([[P("Je retiens", b), P(f["je_retiens"])]], [larg * .15, larg * .85])]
    if f.get("mention"):
        out += [Spacer(1, 3), Paragraph(txt(f["mention"]), _st(7.5, fontName="Serif-Italic", textColor=colors.HexColor("#6B7280")))]
    return out


def fiche_pdf(f: dict, ctx: dict) -> bytes:
    """Fiche sur une feuille recto-verso au plus : la police est réduite jusqu'à y tenir."""
    for corps in (12, 11, 10.5, 10, 9.5, 9, 8.5, 8):
        buf = io.BytesIO()
        doc, cls, larg = _doc(buf, ctx.get("filigrane", ""))
        doc.build(_histoire_fiche(f, ctx, corps, larg), canvasmaker=cls)
        n = buf.getvalue().count(b"/Type /Page\n") or len(re.findall(rb"/Type\s*/Page\b", buf.getvalue()))
        if n <= 2:
            break
    return buf.getvalue()


def lot_pdf(fiches: list[dict], ctx: dict) -> bytes:
    """Classeur : une fiche par feuille recto-verso, avec sommaire."""
    from pypdf import PdfReader, PdfWriter  # type: ignore
    w = PdfWriter()
    for f in fiches:
        for p in PdfReader(io.BytesIO(fiche_pdf(f, ctx))).pages:
            w.add_page(p)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


# ------------------------------------------------------------------------- épreuve
def epreuve_pdf(d: dict, ctx: dict, mode: str = "sujet") -> bytes:
    """mode : « sujet » (élève), « corrige » (réponses et note) ou « grille » (critères)."""
    buf = io.BytesIO()
    doc, cls, larg = _doc(buf, ctx.get("filigrane", ""))
    n, b = _st(11.5, leading=14.5), _st(11.5, fontName="Serif-Bold", leading=14.5)
    h1 = _st(14, fontName="Serif-Bold", alignment=TA_CENTER, leading=17)
    out = [Paragraph(txt("RÉPUBLIQUE DU BÉNIN"), _st(10, fontName="Serif-Bold", alignment=TA_CENTER)),
           Paragraph(txt(f"{ctx.get('circonscription', '')}  ·  {ctx.get('ecole', '')}".strip(" ·")),
                     _st(10, alignment=TA_CENTER)), Spacer(1, 4),
           Paragraph(txt(f"{d['type_lib'].upper()} — {d['periode_lib']}"), h1),
           Paragraph(txt(f"{d['discipline']} · {d['cours']}"), _st(12, fontName="Serif-Bold", alignment=TA_CENTER)),
           Spacer(1, 5),
           _tab([[Paragraph(txt(f"Classe : {ctx.get('classe', d['cours'])}"), n),
                  Paragraph(txt(f"Durée : {d['duree']}"), n), Paragraph(txt(f"Barème : /{d['bareme']}"), n),
                  Paragraph("Date : …/…/……", n)],
                 [Paragraph("Nom et prénoms :", n), "", "", Paragraph(f"Note : …… /{d['bareme']}", n)]],
                [larg * .3, larg * .25, larg * .2, larg * .25], fond_col0=False)]
    if mode == "corrige":
        out.insert(4, Paragraph("CORRIGÉ TYPE — RÉSERVÉ À L'ENSEIGNANT", _st(11, fontName="Serif-Bold", alignment=TA_CENTER, textColor=colors.HexColor("#B91C1C"))))
    if d.get("contexte"):
        out += [Spacer(1, 6), Paragraph("<b>Contexte :</b> " + txt(d["contexte"]), n)]
    if d.get("support_titre") or d.get("support"):
        out += [Spacer(1, 4), Paragraph(txt(d.get("support_titre") or "Support"), b),
                Paragraph(txt(d.get("support")), _st(11, fontName="Serif-Italic", leading=14))]
    if d.get("tache"):
        out += [Spacer(1, 4), Paragraph("<b>Tâche :</b> " + txt(d["tache"]), n)]
    if mode != "grille":
        for it in d.get("consignes") or []:
            out += [Spacer(1, 5), Paragraph(txt(it.get("titre") or ""), b)]
            for q in it.get("questions") or []:
                pts = f"  <i>({q['pts']:g} pt)</i>" if q.get("pts") else ""
                out.append(Paragraph(txt(q["q"]) + pts, n))
                if mode == "corrige" and q.get("r"):
                    out.append(Paragraph("<font color='#1A5C38'>→ " + txt(q["r"]) + "</font>", n))
                elif mode == "sujet":
                    out.append(Paragraph("…" * 60, _st(8, textColor=colors.HexColor("#999999"))))
    if mode in ("corrige", "grille"):
        if d.get("corrige_note"):
            out += [Spacer(1, 6), Paragraph("<b>Note au correcteur :</b> " + txt(d["corrige_note"]), n)]
        lignes = [[Paragraph("Critère", b), Paragraph("Indicateurs", b), Paragraph("Points", b)]]
        for g in d.get("grille") or []:
            lignes.append([Paragraph(txt(g.get("critere")), n),
                           Paragraph(txt("\n".join("☐ " + i for i in g.get("indicateurs", []))), n),
                           Paragraph(f"{g.get('points', '')}", n)])
        if len(lignes) > 1:
            out += [Spacer(1, 8), Paragraph("GRILLE DE CORRECTION", b), Spacer(1, 3),
                    _tab(lignes, [larg * .26, larg * .62, larg * .12], entete=True)]
    doc.build(out, canvasmaker=cls)
    return buf.getvalue()


# ------------------------------------------------------------------------- tableaux
def tableau_pdf(titre: str, sous_titre: str, entetes: list[str], lignes: list[list], largeurs: list[float],
                ctx: dict, taille: float = 8.5) -> bytes:
    buf = io.BytesIO()
    doc, cls, larg = _doc(buf, ctx.get("filigrane", ""), paysage=True, marges=(10, 10, 10, 12))
    n, b = _st(taille, leading=taille * 1.2), _st(taille, fontName="Serif-Bold", textColor=colors.white)
    data = [[Paragraph(txt(e), b) for e in entetes]] + [[Paragraph(txt(c), n) for c in l] for l in lignes]
    tot = sum(largeurs)
    out = [Paragraph(txt(titre), _st(14, fontName="Serif-Bold", alignment=TA_CENTER)),
           Paragraph(txt(sous_titre), _st(10, alignment=TA_CENTER)), Spacer(1, 6),
           _tab(data, [larg * x / tot for x in largeurs], entete=True, couleur="#16315F", pad=2)]
    doc.build(out, canvasmaker=cls)
    return buf.getvalue()


# -------------------------------------------------------------------------- résumé
def _histoire_resume(r: dict, ctx: dict, corps: float, larg: float, corrige: bool) -> list:
    couleur = corpus.COULEUR_MAT.get(r["matiere"], "#1A3A6B")
    n, b = _st(corps), _st(corps, fontName="Serif-Bold")
    blanc = _st(corps + 1, fontName="Serif-Bold", textColor=colors.white)

    def P(t, s=n):
        return Paragraph(txt(t), s)

    domaine = " — ".join(x for x in (r.get("collection"), r.get("domaine")) if x)
    bandeau = Table([[Paragraph(txt(f"RÉSUMÉ — {corpus.LIB_MAT.get(r['matiere'], r['matiere'])}"), blanc),
                      Paragraph(txt(f"{r['cours']} · {r.get('mois') or ''}"),
                                _st(corps + 1, fontName="Serif-Bold", textColor=colors.white, alignment=2))]],
                    colWidths=[larg * .7, larg * .3])
    bandeau.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(couleur)),
                                 ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    out = [bandeau, Spacer(1, 4),
           P(f"Élève : …………………………………………   Classe : {ctx.get('classe', r['cours'])}   Date : …… / …… / ………",
             _st(corps - 0.5)), Spacer(1, 5),
           Paragraph(txt(r["titre"]), _st(corps + 4, fontName="Serif-Bold", alignment=TA_CENTER,
                                          leading=(corps + 4) * 1.2)),
           Paragraph(txt(domaine), _st(corps - 1, fontName="Serif-Italic", alignment=TA_CENTER,
                                       textColor=colors.HexColor("#6B7280"))), Spacer(1, 6)]
    bloc = [("Je retiens", r.get("regle")), ("Ma méthode", r.get("methode")), ("Exemple", r.get("exemple"))]
    voc = r.get("vocabulaire")
    if voc:
        bloc.append(("Vocabulaire", ", ".join(map(str, voc)) if isinstance(voc, list) else voc))
    lignes = [[P(k, b), P(v)] for k, v in bloc if v]
    if lignes:
        out.append(_tab(lignes, [larg * .17, larg * .83]))
    exos = [e for e in (r.get("exercices") or []) if isinstance(e, dict)]
    if exos:
        out += [Spacer(1, 8), Paragraph("JE M'ENTRAÎNE", _st(corps + 1, fontName="Serif-Bold", textColor=colors.HexColor(couleur)))]
        for i, e in enumerate(exos, 1):
            out += [Spacer(1, 3), Paragraph(f"<b>{i}.</b> " + txt(e.get("q")), n),
                    Paragraph("…" * 58, _st(8, textColor=colors.HexColor("#999999")))]
        if corrige:
            rep = [[P(f"{i}.", b), P(e.get("r"))] for i, e in enumerate(exos, 1)]
            out += [Spacer(1, 6), P("Corrigé (enseignant)", _st(corps, fontName="Serif-BoldItalic",
                                                                textColor=colors.HexColor("#B91C1C"))),
                    _tab(rep, [larg * .07, larg * .93])]
    if r.get("mention"):
        out += [Spacer(1, 4), Paragraph(txt(r["mention"]), _st(7.5, fontName="Serif-Italic",
                                                               textColor=colors.HexColor("#6B7280")))]
    return out


def resume_pdf(r: dict, ctx: dict, corrige: bool = True) -> bytes:
    """Résumé sur une feuille ; avec `corrige`, les réponses figurent en bas (version enseignant)."""
    for corps in (13, 12, 11, 10, 9):
        buf = io.BytesIO()
        doc, cls, larg = _doc(buf, ctx.get("filigrane", ""))
        doc.build(_histoire_resume(r, ctx, corps, larg, corrige), canvasmaker=cls)
        if len(re.findall(rb"/Type\s*/Page\b", buf.getvalue())) <= 1:
            break
    return buf.getvalue()
