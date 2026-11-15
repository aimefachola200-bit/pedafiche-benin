"""Génère le PDF « Cahiers de révisions et d'accompagnement — Volume 1 » (contenu original).

Usage : python scripts/generer_cahiers_revision.py [sortie.pdf]
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
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, Spacer, Table, TableStyle

from pedafiche import config, pdf
from pedafiche.pdf import _doc, _st, _tab, txt
from cahiers_contenu_dictees import DICTEES, NOTATION, RELECTURE
from cahiers_contenu_es_ea import BILANS, GRILLE_RECIT, LECONS, METHODE_RECIT, RECITS

BLEU, VERT, ROSE = "#1D4ED8", "#16315F", "#831843"
POINTILLES = "…" * 70


def bandeau(titre, sous, couleur, larg):
    t = Table([[Paragraph(txt(titre), _st(14, fontName="Serif-Bold", textColor=colors.white, leading=17)),
                Paragraph(txt(sous), _st(10, fontName="Serif-Italic", textColor=colors.white, alignment=2))]],
              colWidths=[larg * .68, larg * .32])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(couleur)),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


def boite(titre, texte, larg, fond="#EEF2F7", corps=10.5):
    t = Table([[Paragraph(f"<b>{txt(titre)}</b>", _st(corps)), Paragraph(txt(texte), _st(corps))]],
              colWidths=[larg * .16, larg * .84])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fond)),
                           ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#555555")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def ligne_reponse(corps=9):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    n = int(500 / stringWidth("…", "Serif", corps))          # remplit une ligne sans déborder
    return Paragraph("…" * n, _st(corps, textColor=colors.HexColor("#9CA3AF")))


def sommaire_page(larg):
    n, b = _st(11.5, leading=17), _st(12.5, fontName="Serif-Bold", leading=18, textColor=colors.HexColor(VERT))
    return [Paragraph("SOMMAIRE", _st(18, fontName="Serif-Bold", alignment=TA_CENTER, textColor=colors.HexColor(VERT))),
            Spacer(1, 12),
            Paragraph("Partie A — Français CE2 : cahier de dictées", b),
            Paragraph("13 dictées originales, avec exercices de préparation, notation, parcours de relecture, textes et corrigés (à détacher).", n),
            Spacer(1, 8),
            Paragraph("Partie B — ES / Éducation à la citoyenneté CM1 : cahier de révisions", b),
            Paragraph("10 leçons (« Je retiens », exercices), 2 situations d'intégration avec grille de correction, corrigés.", n),
            Spacer(1, 8),
            Paragraph("Partie C — Éducation artistique CI → CM2 : récitations", b),
            Paragraph("Méthode pour apprendre, grille d'évaluation sur 10, tableau d'accompagnement de 35 récitations (niveau, thème, mots à expliquer).", n),
            Spacer(1, 14),
            boite("Statut", "Documents originaux, rédigés pour SCOLARIS à partir des thèmes des supports fournis. Aucun texte, exercice ou illustration de ces supports n'est reproduit. À valider par le conseiller pédagogique avant diffusion.", larg, "#FFF7D6", 10)]


def cover(larg):
    icone = RACINE / "pedafiche" / "web" / "static" / "icons" / "icon-512.png"
    out = [Spacer(1, 40 * mm)]
    if icone.exists():
        out.append(Image(str(icone), 42 * mm, 42 * mm, hAlign="CENTER"))
    out += [Spacer(1, 10 * mm),
            Paragraph("CAHIERS DE RÉVISIONS", _st(30, fontName="Serif-Bold", alignment=TA_CENTER, leading=34, textColor=colors.HexColor(VERT))),
            Paragraph("ET D'ACCOMPAGNEMENT", _st(24, fontName="Serif-Bold", alignment=TA_CENTER, leading=28, textColor=colors.HexColor(VERT))),
            Spacer(1, 6 * mm),
            Paragraph("Volume 1 — Dictées CE2 · Civisme CM1 · Récitations CI-CM2", _st(14, alignment=TA_CENTER)),
            Spacer(1, 6 * mm),
            Paragraph("Collection SCOLARIS · Programme du Bénin · Approche par compétences", _st(11, fontName="Serif-Italic", alignment=TA_CENTER, textColor=colors.HexColor("#6B7280"))),
            Spacer(1, 40 * mm),
            Paragraph(f"Conception : {config.CONCEPTEUR}", _st(12, fontName="Serif-Bold", alignment=TA_CENTER)),
            Paragraph(config.CONCEPTEUR_TEL, _st(10, alignment=TA_CENTER))]
    return out


# ------------------------------------------------------------------------ partie A
def partie_a(larg):
    n, b = _st(10.5, leading=13), _st(10.5, fontName="Serif-Bold", leading=13)
    out = [PageBreak(), bandeau("Partie A — Cahier de dictées CE2", "Français · orthographe", BLEU, larg), Spacer(1, 8),
           Paragraph("Comment utiliser ce cahier ?", _st(13, fontName="Serif-Bold", textColor=colors.HexColor(BLEU))),
           Spacer(1, 3),
           Paragraph("• À chaque dictée correspond une page d'exercices. Tu peux faire la dictée <b>avant</b> les exercices pour te tester, ou <b>après</b> pour appliquer les règles.", n),
           Paragraph("• Les textes des dictées et tous les corrigés sont à la fin de la partie A (pages à détacher).", n),
           Paragraph("• La dictée n° 13 est la <b>dictée du champion</b> : elle mélange toutes les difficultés.", n),
           Spacer(1, 8), boite("La notation", NOTATION, larg, "#E0F2FE", 10),
           Spacer(1, 10), Paragraph("Pour une dictée sans faute — mon parcours de relecture", _st(13, fontName="Serif-Bold", textColor=colors.HexColor(BLEU))), Spacer(1, 3)]
    for i, e in enumerate(RELECTURE, 1):
        out.append(Paragraph(f"<b>{i}.</b> {txt(e)}", _st(11, leading=15)))
    out += [Spacer(1, 10), Paragraph("Pages d'écriture : dictée n° ____   Note : ____ / 20   Date : ____ / ____ / ________", _st(10.5))]
    for num, titre, notions, retiens, exos, mots, texte in DICTEES:
        out += [PageBreak(), bandeau(f"Dictée n° {num} — {titre}", "préparation", BLEU, larg), Spacer(1, 4),
                Paragraph(f"<b>Notions :</b> {txt(notions)}", n), Spacer(1, 4), boite("Je retiens", retiens, larg, "#FFF1E6", 10)]
        for k, (consigne, items) in enumerate(exos, 1):
            out += [Spacer(1, 7), Paragraph(f"<b>Exercice {k}.</b> {txt(consigne)}", n)]
            for q, _r in items:
                if q == "Réponse":
                    out.append(ligne_reponse())
                    continue
                out += [Paragraph("• " + txt(q), _st(10.5, leading=13, leftIndent=8)), ligne_reponse(8)]
        out += [Spacer(1, 8), boite("Mots à apprendre", mots, larg, "#E0F2FE", 10),
                Paragraph("Et maintenant, je fais ma dictée n° %d !" % num, _st(10.5, fontName="Serif-BoldItalic", alignment=2, textColor=colors.HexColor(BLEU)))]
    out += [PageBreak(), bandeau("À détacher — Textes des dictées et corrigés", "enseignant / parent", "#B91C1C", larg), Spacer(1, 4)]
    for num, titre, notions, retiens, exos, mots, texte in DICTEES:
        bloc = [Paragraph(f"<b>Dictée n° {num} — {txt(titre)}</b>", _st(11.5, leading=14, textColor=colors.HexColor(BLEU))),
                Paragraph("<i>Texte :</i> " + txt(texte), _st(10, leading=12.5))]
        reps = []
        for k, (consigne, items) in enumerate(exos, 1):
            reps.append(f"<b>Ex. {k}</b> — " + " ; ".join(txt(r) for _q, r in items))
        bloc.append(Paragraph("<br/>".join(reps), _st(9.5, leading=12, textColor=colors.HexColor("#1A5C38"))))
        bloc.append(Spacer(1, 6))
        out.append(KeepTogether(bloc))
    return out


# ------------------------------------------------------------------------ partie B
def partie_b(larg):
    n = _st(10.5, leading=13)
    out = [PageBreak(), bandeau("Partie B — ES : Éducation à la citoyenneté CM1", "cahier de révisions", ROSE, larg), Spacer(1, 8),
           Paragraph("Ce cahier reprend les grands thèmes du civisme au CM1 : vie démocratique, institutions, décentralisation, budget, sécurité routière, symboles de l'État et citoyenneté. Chaque leçon comporte un résumé (« Je retiens ») et des exercices ; les corrigés sont à la fin.", n),
           Spacer(1, 4), boite("Attention", "Les faits qui dépendent de l'actualité (nom du Président, nombre de députés, durée des mandats…) sont à compléter ou à vérifier d'après la Constitution et les textes en vigueur.", larg, "#FFF7D6", 10)]
    for i, (titre, retiens, qr, cles) in enumerate(LECONS, 1):
        out += [PageBreak(), bandeau(f"Leçon {i} — {titre}", "ES · civisme", ROSE, larg), Spacer(1, 6),
                boite("Je retiens", retiens, larg, "#FCE7F3", 10.5), Spacer(1, 8),
                Paragraph("Je m'exerce", _st(12, fontName="Serif-Bold", textColor=colors.HexColor(ROSE)))]
        for j, (q, _r) in enumerate(qr, 1):
            out += [Spacer(1, 5), Paragraph(f"<b>{chr(64 + j)}.</b> {txt(q)}", n), ligne_reponse(), ligne_reponse()]
        out += [Spacer(1, 8), boite("Mots-clés", cles, larg, "#E0F2FE", 10)]
    for titre, contexte, taches, crit, corr in BILANS:
        out += [PageBreak(), bandeau(titre, "situation d'intégration", ROSE, larg), Spacer(1, 6),
                boite("Situation", contexte, larg, "#FFF7D6", 10.5), Spacer(1, 6),
                Paragraph("<b>Tâche :</b> réponds aux questions suivantes.", n)]
        for t in taches:
            out += [Spacer(1, 6), Paragraph(txt(t), n), ligne_reponse(), ligne_reponse(), ligne_reponse()]
        lignes = [[Paragraph("<b>Critère</b>", _st(10)), Paragraph("<b>Indicateurs</b>", _st(10)), Paragraph("<b>Points</b>", _st(10))]]
        noms = ["C1 Pertinence", "C2 Outils de la discipline", "C3 Cohérence"]
        for nom, ind in zip(noms, crit):
            lignes.append([Paragraph(nom, _st(9.5)), Paragraph(txt(ind), _st(9.5)), Paragraph("/ 5", _st(9.5))])
        lignes.append([Paragraph("Perfectionnement", _st(9.5)), Paragraph("Soin, précision, exemple personnel (bonus)", _st(9.5)), Paragraph("+ 1", _st(9.5))])
        out += [Spacer(1, 10), Paragraph("Grille de correction (enseignant) — total / 15 + bonus, à ramener sur 20 selon le barème de l'école", _st(10, fontName="Serif-Bold")),
                Spacer(1, 3), _tab(lignes, [larg * .22, larg * .65, larg * .13], entete=True, couleur=ROSE, pad=2)]
    out += [PageBreak(), bandeau("Corrigés — Partie B", "enseignant", "#B91C1C", larg), Spacer(1, 4)]
    for i, (titre, retiens, qr, cles) in enumerate(LECONS, 1):
        bloc = [Paragraph(f"<b>Leçon {i} — {txt(titre)}</b>", _st(11, leading=14, textColor=colors.HexColor(ROSE)))]
        for j, (q, r) in enumerate(qr, 1):
            bloc.append(Paragraph(f"<b>{chr(64 + j)}.</b> {txt(r)}", _st(9.5, leading=11.5, leftIndent=6)))
        bloc.append(Spacer(1, 5))
        out.append(KeepTogether(bloc))
    for titre, _c, _t, _k, corr in BILANS:
        out.append(KeepTogether([Paragraph(f"<b>{txt(titre)}</b> — éléments de réponse", _st(11, leading=14, textColor=colors.HexColor(ROSE))),
                                 Paragraph(txt(corr), _st(9.5, leading=11.5)), Spacer(1, 5)]))
    return out


# ------------------------------------------------------------------------ partie C
def partie_c(larg):
    n = _st(10.5, leading=13)
    out = [PageBreak(), bandeau("Partie C — Éducation artistique : les récitations", "CI → CM2", "#BE185D", larg), Spacer(1, 8),
           Paragraph("Comment apprendre une récitation ?", _st(13, fontName="Serif-Bold", textColor=colors.HexColor("#BE185D"))), Spacer(1, 3)]
    for i, m in enumerate(METHODE_RECIT, 1):
        out.append(Paragraph(f"<b>{i}.</b> {txt(m)}", _st(11, leading=15)))
    lignes = [[Paragraph("<b>Critère</b>", _st(10)), Paragraph("<b>Points</b>", _st(10))]] + \
             [[Paragraph(txt(c), _st(10)), Paragraph(f"/ {p}", _st(10))] for c, p in GRILLE_RECIT] + \
             [[Paragraph("<b>Total</b>", _st(10)), Paragraph("<b>/ 10</b>", _st(10))]]
    out += [Spacer(1, 10), Paragraph("Grille d'évaluation de la récitation", _st(13, fontName="Serif-Bold", textColor=colors.HexColor("#BE185D"))), Spacer(1, 3),
            _tab(lignes, [larg * .82, larg * .18], entete=True, couleur="#BE185D", pad=3), Spacer(1, 8),
            boite("Conseil", "Les textes eux-mêmes ne figurent pas ici : utilise le recueil de ton école. Ce tableau sert à choisir la récitation adaptée au niveau, à préparer l'explication des mots et à vérifier la compréhension. Les auteurs sont indiqués tels qu'ils figurent dans le recueil source ; à vérifier avant publication.", larg, "#FFF7D6", 10)]
    en = [Paragraph("<b>Titre</b>", _st(9)), Paragraph("<b>Auteur (selon le recueil)</b>", _st(9)), Paragraph("<b>Niveau</b>", _st(9)),
          Paragraph("<b>Thème</b>", _st(9)), Paragraph("<b>Mots à expliquer</b>", _st(9))]
    corps = [en] + [[Paragraph(txt(c), _st(8.5, leading=10)) for c in r] for r in RECITS]
    out += [PageBreak(), Paragraph("Tableau d'accompagnement des récitations", _st(13, fontName="Serif-Bold", textColor=colors.HexColor("#BE185D"))), Spacer(1, 4),
            _tab(corps, [larg * .22, larg * .17, larg * .08, larg * .27, larg * .26], entete=True, couleur="#BE185D", pad=2)]
    out += [Spacer(1, 10), Paragraph("Pour aller plus loin : donne à chaque récitation une fiche d'exploitation (lecture, compréhension, vocabulaire, mémorisation par parties, restitution) en suivant la méthode ci-dessus.", n)]
    return out


def construire(sortie):
    buf = io.BytesIO()
    doc, cls, larg = _doc(buf, "")
    histoire = cover(larg) + [PageBreak()] + sommaire_page(larg) + partie_a(larg) + partie_b(larg) + partie_c(larg)
    doc.build(histoire, canvasmaker=cls)
    Path(sortie).write_bytes(buf.getvalue())
    return sortie


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "cahiers_revision_vol1.pdf"
    print(construire(out))
