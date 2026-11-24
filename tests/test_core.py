import conftest  # noqa: F401
from datetime import date

from pedafiche import calendrier, corpus, edt, epreuves, pdf, progression


def pages(contenu: bytes) -> int:
    from io import BytesIO
    from pypdf import PdfReader
    return len(PdfReader(BytesIO(contenu)).pages)


def texte(contenu: bytes) -> str:
    from io import BytesIO
    from pypdf import PdfReader
    return " ".join(p.extract_text() for p in PdfReader(BytesIO(contenu)).pages)


def test_corpus_complet():
    assert sum(len(corpus.fiches_du_cours(c)) for c in corpus.COURS) >= 4379
    assert all(isinstance(f["sa"], (int, type(None))) for f in corpus.fiches("CE1"))


def test_calendrier_officiel_2026_2027():
    r = calendrier.resume("2026-2027")
    assert r["rentree"] == date(2026, 9, 14) and r["fin_cours"] == date(2027, 6, 25)
    t1 = [d for d in calendrier.jours_de_classe("2026-2027") if calendrier.trimestre_de(d) == "Premier trimestre"]
    assert len(t1) == 70                                   # « 14 semaines de travail »
    assert calendrier.est_jour_classe(date(2026, 12, 18))  # congés « après les cours »
    assert not calendrier.est_jour_classe(date(2026, 12, 21))
    assert not calendrier.est_jour_classe(date(2027, 1, 7))   # jour férié
    assert calendrier.est_jour_classe(date(2027, 2, 19)) and not calendrier.est_jour_classe(date(2027, 2, 22))


def test_progression_et_semaine():
    for c in ("CI", "CP", "CE1", "CE2", "CM1", "CM2"):
        plan = progression.progression_annuelle(c)
        assert len(plan) == 10 and sum(len(m["matieres"]["francais"]["fiches"]) for m in plan) > 0
    s = progression.fiches_de_la_semaine("CM2", date(2026, 10, 12))
    assert s and all(f["cours"] == "CM2" for v in s.values() for f in v)


def test_edt_journee():
    e = edt.edt_defaut("CM2")
    j = edt.journee(e, "CM2", date(2026, 10, 14))
    assert any(c["fiche_id"] for c in j if c["matiere"]) and edt.journee(e, "CM2", date(2026, 10, 17)) == []


def test_evaluations_alimentees_par_la_progression():
    jeu = epreuves.epreuves_de_la_periode("CM2", "T1")
    assert len(jeu) == 8 and all(d["bareme"] for d in jeu)


def test_pdf_fiche_filigrane_et_concepteur():
    f = corpus.fiches("CM2", "maths")[5]
    ctx = dict(filigrane="Koffi ADJOVI", enseignant="Koffi ADJOVI", ecole="EPP Test", annee="2026-2027")
    p = pdf.fiche_pdf(f, ctx)
    assert pages(p) <= 2
    t = texte(p)
    assert "Koffi ADJOVI" in t and "Conception :" in t and "Page 1 / " in t


def test_pdf_epreuves():
    d = epreuves.epreuve("CM2", "T1", "math")
    ctx = dict(filigrane="X Y", ecole="EPP", classe="CM2 A")
    for mode in ("sujet", "corrige", "grille"):
        assert pages(pdf.epreuve_pdf(d, ctx, mode)) >= 1


def test_resumes_conjugaison_complementaires():
    nouveaux = [r for c in corpus.COURS for r in corpus.resumes_du_cours(c) if r["id"].startswith("rx-")]
    assert len(nouveaux) == 39 and len({r["id"] for r in nouveaux}) == 39
    assert {r["cours"] for r in nouveaux} == {"CI", "CP", "CE1", "CE2", "CM1", "CM2"}
    for r in nouveaux:
        assert r["regle"] and r["methode"] and r["exemple"] and len(r["exercices"]) >= 3
        assert all(e["q"] and e["r"] for e in r["exercices"])
        assert r["mois"] in ("Septembre", "Octobre", "Novembre", "Décembre", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin")
    assert corpus.resumes("CI", "francais", None, "verbe")        # les CI en ont enfin
