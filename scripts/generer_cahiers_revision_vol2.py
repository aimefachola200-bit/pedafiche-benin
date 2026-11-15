"""Génère le PDF « Cahiers de révisions et d'accompagnement — Volume 2 » (contenu original).

Maths CI / CP / CM2 · Français CI / CP / CE1 / CM2 · Grammaire essentielle · Chants et poèmes.
Usage : python scripts/generer_cahiers_revision_vol2.py [sortie.pdf]
"""
import io
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import CondPageBreak, Image, KeepTogether, PageBreak, Paragraph, Spacer

from pedafiche import config
from pedafiche.pdf import _doc, _st, _tab, txt
from generer_cahiers_revision import bandeau, boite, ligne_reponse
from cahiers_contenu_vol2_francais import CHANTS, CONJ, FR_CE1, FR_CI, FR_CM2, FR_CP, GRAMMAIRE, POEMES
from cahiers_contenu_vol2_maths import MATHS_CI, MATHS_CM2, MATHS_CP

SECTIONS = [  # (code, titre, sous-titre, fiches, couleur)
    ("A", "Mathématiques CI", "initiation", MATHS_CI, "#1A5C38"),
    ("B", "Mathématiques CP", "cours préparatoire", MATHS_CP, "#1A5C38"),
    ("C", "Mathématiques CM2", "cours moyen 2e année", MATHS_CM2, "#1A5C38"),
    ("D", "Français CI", "initiation", FR_CI, "#1D4ED8"),
    ("E", "Français CP", "cours préparatoire", FR_CP, "#1D4ED8"),
    ("F", "Français CE1", "cours élémentaire 1re année", FR_CE1, "#1D4ED8"),
    ("G", "Français CM2", "cours moyen 2e année", FR_CM2, "#1D4ED8"),
    ("H", "Grammaire essentielle", "CE2 → CM2", GRAMMAIRE, "#4A1D96"),
]
VERT = "#16315F"


def cover(larg):
    icone = RACINE / "pedafiche" / "web" / "static" / "icons" / "icon-512.png"
    out = [Spacer(1, 40 * mm)]
    if icone.exists():
        out.append(Image(str(icone), 42 * mm, 42 * mm, hAlign="CENTER"))
    out += [Spacer(1, 10 * mm),
            Paragraph("CAHIERS DE RÉVISIONS", _st(30, fontName="Serif-Bold", alignment=TA_CENTER, leading=34, textColor=colors.HexColor(VERT))),
            Paragraph("ET D'ACCOMPAGNEMENT", _st(24, fontName="Serif-Bold", alignment=TA_CENTER, leading=28, textColor=colors.HexColor(VERT))),
            Spacer(1, 6 * mm),
            Paragraph("Volume 2 — Mathématiques · Français · Grammaire · Chants et poèmes", _st(14, alignment=TA_CENTER)),
            Spacer(1, 6 * mm),
            Paragraph("Collection SCOLARIS · Programme du Bénin · Approche par compétences", _st(11, fontName="Serif-Italic", alignment=TA_CENTER, textColor=colors.HexColor("#6B7280"))),
            Spacer(1, 40 * mm),
            Paragraph(f"Conception : {config.CONCEPTEUR}", _st(12, fontName="Serif-Bold", alignment=TA_CENTER)),
            Paragraph(config.CONCEPTEUR_TEL, _st(10, alignment=TA_CENTER))]
    return out


def sommaire(larg):
    b, n = _st(12.5, fontName="Serif-Bold", leading=18, textColor=colors.HexColor(VERT)), _st(11, leading=15)
    out = [Paragraph("SOMMAIRE", _st(18, fontName="Serif-Bold", alignment=TA_CENTER, textColor=colors.HexColor(VERT))), Spacer(1, 10)]
    for code, titre, sous, fiches, _c in SECTIONS:
        out.append(Paragraph(f"Partie {code} — {titre} ({len(fiches)} fiches)", b))
        out.append(Paragraph("Fiches « Je retiens + exercices » et corrigés.", n))
    out += [Paragraph("Partie I — Conjugaison : tableaux de référence", b), Paragraph("être, avoir, aller, faire, chanter : présent, imparfait, futur, passé composé.", n),
            Paragraph("Partie J — Chants et poèmes : tableau d'accompagnement", b), Paragraph(f"{len(POEMES)} poèmes et {len(CHANTS)} chants : niveau proposé, thème, lien avec les matières.", n),
            Spacer(1, 12),
            boite("Statut", "Documents originaux rédigés pour SCOLARIS. Les supports d'origine (cahiers d'activités, cahiers de la réussite, grammaire) n'ont pas été reproduits ; seuls leurs thèmes ont orienté le plan. À valider par le conseiller pédagogique avant diffusion.", larg, "#FFF7D6", 10)]
    return out


def section(code, titre, sous, fiches, couleur, larg):
    n = _st(10.5, leading=13)
    out = [PageBreak(), bandeau(f"Partie {code} — {titre}", sous, couleur, larg), Spacer(1, 6)]
    for i, (t, retiens, qr, cles) in enumerate(fiches, 1):
        out += [CondPageBreak(120 * mm), Spacer(1, 10), Paragraph(f"<b>Fiche {code}{i} — {txt(t)}</b>", _st(12.5, fontName="Serif-Bold", leading=15, textColor=colors.HexColor(couleur))),
                Spacer(1, 3), boite("Je retiens", retiens, larg, "#EEF2F7", 10.5), Spacer(1, 5), Paragraph("Je m'exerce", _st(11.5, fontName="Serif-Bold"))]
        for j, (q, _r) in enumerate(qr, 1):
            out += [Spacer(1, 3), Paragraph(f"<b>{chr(64 + j)}.</b> {txt(q)}", n), ligne_reponse(8.5)]
        out += [Spacer(1, 4), Paragraph("<i>Mots-clés :</i> " + txt(cles), _st(9.5, textColor=colors.HexColor("#4B5563")))]
    out += [PageBreak(), bandeau(f"Corrigés — Partie {code} ({titre})", "enseignant", "#B91C1C", larg), Spacer(1, 4)]
    for i, (t, retiens, qr, cles) in enumerate(fiches, 1):
        bloc = [Paragraph(f"<b>Fiche {code}{i} — {txt(t)}</b>", _st(11, leading=14, textColor=colors.HexColor(couleur)))]
        for j, (q, r) in enumerate(qr, 1):
            bloc.append(Paragraph(f"<b>{chr(64 + j)}.</b> {txt(r)}", _st(9.5, leading=11.5, leftIndent=6)))
        bloc.append(Spacer(1, 4))
        out.append(KeepTogether(bloc))
    return out


def conjugaison(larg):
    out = [PageBreak(), bandeau("Partie I — Conjugaison : tableaux de référence", "indicatif", "#4A1D96", larg), Spacer(1, 6)]
    en = [Paragraph(f"<b>{h}</b>", _st(9, textColor=colors.white)) for h in ("Temps", "je", "tu", "il / elle", "nous", "vous", "ils / elles")]
    for verbe, temps in CONJ.items():
        lignes = [en]
        for nom, formes in temps:
            f = [x.strip() for x in formes.split(",")]
            lignes.append([Paragraph(f"<b>{nom}</b>", _st(9))] + [Paragraph(txt(x), _st(8.5, leading=10)) for x in f])
        out += [Paragraph(f"<b>{verbe}</b>", _st(12, fontName="Serif-Bold", textColor=colors.HexColor("#4A1D96"))), Spacer(1, 2),
                _tab(lignes, [larg * .14] + [larg * .143] * 6, entete=True, couleur="#4A1D96", pad=2), Spacer(1, 7)]
    out.append(boite("Astuce", "Pour le passé composé, je choisis l'auxiliaire : avoir pour la plupart des verbes, être pour aller, venir, arriver, partir, tomber, naître, mourir et les verbes pronominaux.", larg, "#FFF7D6", 10))
    return out


def chants_poemes(larg):
    en = lambda *h: [Paragraph(f"<b>{x}</b>", _st(9)) for x in h]
    c = lambda t: Paragraph(txt(t), _st(8.5, leading=10))
    out = [PageBreak(), bandeau("Partie J — Chants et poèmes", "éducation artistique", "#BE185D", larg), Spacer(1, 6),
           boite("Mode d'emploi", "Les textes ne sont pas reproduits : utilisez le recueil de votre école. Les niveaux et les thèmes sont des propositions déduites des titres, à confirmer après lecture. Les auteurs ne sont indiqués que lorsqu'ils figuraient dans le recueil source ; « non vérifié » signifie qu'ils restent à confirmer. Pour apprendre, évaluer et exploiter une récitation, reprenez la méthode et la grille du Volume 1 (partie C).", larg, "#FFF7D6", 10),
           Spacer(1, 8), Paragraph("Poèmes", _st(13, fontName="Serif-Bold", textColor=colors.HexColor("#BE185D"))), Spacer(1, 3),
           _tab([en("Titre", "Type", "Auteur", "Niveau proposé", "Thème et usage")] + [[c(x) for x in r] for r in POEMES],
                [larg * .20, larg * .10, larg * .17, larg * .11, larg * .42], entete=True, couleur="#BE185D", pad=2),
           CondPageBreak(90 * mm), Spacer(1, 10), Paragraph("Chants", _st(13, fontName="Serif-Bold", textColor=colors.HexColor("#BE185D"))), Spacer(1, 3),
           _tab([en("Titre", "Type", "Niveau proposé", "Thème et usage")] + [[c(x) for x in r] for r in CHANTS],
                [larg * .30, larg * .10, larg * .18, larg * .42], entete=True, couleur="#BE185D", pad=2)]
    return out


def construire(sortie):
    buf = io.BytesIO()
    doc, cls, larg = _doc(buf, "")
    histoire = cover(larg) + [PageBreak()] + sommaire(larg)
    for code, titre, sous, fiches, couleur in SECTIONS:
        histoire += section(code, titre, sous, fiches, couleur, larg)
    histoire += conjugaison(larg) + chants_poemes(larg)
    doc.build(histoire, canvasmaker=cls)
    Path(sortie).write_bytes(buf.getvalue())
    return sortie


if __name__ == "__main__":
    print(construire(sys.argv[1] if len(sys.argv) > 1 else "cahiers_revision_vol2.pdf"))
