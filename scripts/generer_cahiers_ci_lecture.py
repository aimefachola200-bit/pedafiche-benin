"""Génère le PDF « Français CI — lecture-écriture, 42 leçons » (contenu original).

Usage : python scripts/generer_cahiers_ci_lecture.py [sortie.pdf]
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
from pedafiche.pdf import _doc, _st, txt
from generer_cahiers_revision import boite, ligne_reponse
from cahiers_ci_lecture import INTEGRATIONS, LECONS, decompte, syllabes, verifier

BLEU = "#1D4ED8"


def entete(titre, couleur, larg):
    from pedafiche.pdf import _tab  # noqa: F401
    from reportlab.platypus import Table, TableStyle
    t = Table([[Paragraph(txt(titre), _st(13, fontName="Serif-Bold", textColor=colors.white, leading=16))]], colWidths=[larg])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(couleur)), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def grand(texte, taille=17):
    return Paragraph(txt(texte), _st(taille, fontName="Serif-Bold", leading=taille * 1.5, textColor=colors.HexColor("#111827")))


def cover(larg):
    icone = RACINE / "pedafiche" / "web" / "static" / "icons" / "icon-512.png"
    out = [Spacer(1, 38 * mm)]
    if icone.exists():
        out.append(Image(str(icone), 40 * mm, 40 * mm, hAlign="CENTER"))
    out += [Spacer(1, 8 * mm),
            Paragraph("FRANÇAIS CI", _st(32, fontName="Serif-Bold", alignment=TA_CENTER, leading=36, textColor=colors.HexColor("#16315F"))),
            Paragraph("Lecture-écriture : 42 leçons", _st(20, fontName="Serif-Bold", alignment=TA_CENTER, leading=24, textColor=colors.HexColor("#16315F"))),
            Spacer(1, 6 * mm),
            Paragraph("Cahier de révisions et d'accompagnement — Volume 3", _st(13, alignment=TA_CENTER)),
            Spacer(1, 6 * mm),
            Paragraph("Collection SCOLARIS · Programme du Bénin · Approche par compétences", _st(11, fontName="Serif-Italic", alignment=TA_CENTER, textColor=colors.HexColor("#6B7280"))),
            Spacer(1, 30 * mm),
            Paragraph(f"Conception : {config.CONCEPTEUR}", _st(12, fontName="Serif-Bold", alignment=TA_CENTER)),
            Paragraph(config.CONCEPTEUR_TEL, _st(10, alignment=TA_CENTER)),
            PageBreak(),
            Paragraph("Comment utiliser ce cahier ?", _st(16, fontName="Serif-Bold", textColor=colors.HexColor(BLEU))), Spacer(1, 6),
            Paragraph("• Il suit l'ordre des lettres et des groupes de lettres du programme du CI : 42 leçons, de la lettre a au groupe om, avec 4 bilans d'intégration.", _st(11.5, leading=16)),
            Paragraph("• <b>Règle d'or de décodage</b> : chaque mot et chaque phrase à lire n'emploie que des lettres et des sons déjà étudiés. Cette règle est vérifiée automatiquement par le programme qui génère le cahier.", _st(11.5, leading=16)),
            Paragraph("• Chaque leçon propose : des syllabes à lire, des mots à lire, des phrases (à partir des mots outils), deux exercices.", _st(11.5, leading=16)),
            Paragraph("• Les réponses sont à la fin. Le maître lit d'abord à voix haute, l'enfant répète, puis lit seul.", _st(11.5, leading=16)),
            Spacer(1, 10),
            boite("Statut", "Document original rédigé pour SCOLARIS. Aucun texte ni exercice du cahier d'activités officiel n'est reproduit ; seul l'ordre des leçons a servi de plan. À valider par le conseiller pédagogique.", larg, "#FFF7D6", 10)]
    return out


def bloc_lecon(n, titre, mots, phrases, larg):
    sy = syllabes(n)
    out = [CondPageBreak(95 * mm), Spacer(1, 8), entete(f"Leçon {n} — {titre}", BLEU, larg), Spacer(1, 5)]
    if sy:
        out += [Paragraph("<b>Je lis les syllabes</b>", _st(10.5)), grand("   ".join(sy), 18)]
    if mots:
        out += [Paragraph("<b>Je lis les mots</b>", _st(10.5)), grand("   ".join(mots), 18)]
    if phrases:
        out += [Paragraph("<b>Je lis les phrases</b>", _st(10.5))] + [grand(p, 16) for p in phrases]
    out.append(Spacer(1, 4))
    new = next(t[2] for t in LECONS if t[0] == n)
    if new and mots:
        out += [Paragraph(f"<b>Exercice 1.</b> Entoure la lettre « {new} » dans chaque mot et écris combien de fois tu la vois.", _st(10.5)),
                Paragraph("  ·  ".join(mots[:5]), _st(11, textColor=colors.HexColor("#4B5563"))), ligne_reponse(8.5)]
    if mots:
        out += [Paragraph("<b>Exercice 2.</b> Écoute le maître et écris trois mots de la liste.", _st(10.5)), ligne_reponse(8.5)]
    else:
        out += [Paragraph("<b>Exercice.</b> Recopie une phrase de ton choix, avec la majuscule et le point.", _st(10.5)), ligne_reponse(8.5)]
    return out


def bloc_integration(n, titre, mots, phrases, larg):
    out = [PageBreak(), entete(titre, "#B45309", larg), Spacer(1, 8), Paragraph("<b>Je lis</b>", _st(11))]
    out += [grand("   ".join(mots), 20)] if mots else [grand(p, 18) for p in phrases]
    out += [Spacer(1, 10), Paragraph("<b>Je m'exerce</b>", _st(11)),
            Paragraph("A. Relie chaque mot ou chaque phrase à son image (le maître donne les images).", _st(11)), ligne_reponse(8.5),
            Paragraph("B. Écris sous la dictée du maître trois mots lus dans cette page.", _st(11)), ligne_reponse(8.5), ligne_reponse(8.5),
            Paragraph("C. Recopie ta phrase préférée, avec la majuscule et le point.", _st(11)), ligne_reponse(8.5), ligne_reponse(8.5),
            Spacer(1, 6), boite("Critères de réussite", "Je lis sans me tromper ; je respecte la majuscule et le point ; j'écris les lettres sur la ligne, de gauche à droite.", larg, "#E0F2FE", 10)]
    return out


def reponses(larg):
    out = [PageBreak(), entete("Réponses (enseignant)", "#B91C1C", larg), Spacer(1, 6),
           Paragraph("Exercice 1 de chaque leçon : nombre de fois que la nouvelle lettre apparaît dans chacun des 5 premiers mots.", _st(10))]
    for n, titre, new, mots, phrases in LECONS:
        if new and mots:
            rep = " ; ".join(f"{m} : {decompte(m, new)}" for m in mots[:5])
            out.append(Paragraph(f"<b>Leçon {n} ({new})</b> — {txt(rep)}", _st(9.5, leading=12)))
    out.append(Paragraph("Exercice 2 : dictée de trois mots pris dans la liste de la leçon (correction : le mot dicté).", _st(9.5, leading=12)))
    return out


def construire(sortie):
    err = verifier()
    if err:
        raise SystemExit("Contenu non conforme à la règle de décodage :\n" + "\n".join(err))
    buf = io.BytesIO()
    doc, cls, larg = _doc(buf, "")
    histoire = cover(larg)
    inter = {n: (t, m, p) for n, t, m, p in INTEGRATIONS}
    histoire += [PageBreak()]
    for n, titre, new, mots, phrases in LECONS:
        histoire += bloc_lecon(n, titre, mots, phrases, larg)
        if n in inter:
            t, m, p = inter[n]
            histoire += bloc_integration(n, t, m, p, larg) + [PageBreak()]
    histoire += reponses(larg)
    doc.build(histoire, canvasmaker=cls)
    Path(sortie).write_bytes(buf.getvalue())
    return sortie


if __name__ == "__main__":
    print(construire(sys.argv[1] if len(sys.argv) > 1 else "cahier_francais_CI_lecture.pdf"))
