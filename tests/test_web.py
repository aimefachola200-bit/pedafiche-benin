import conftest  # noqa: F401
import re

from werkzeug.security import generate_password_hash

from pedafiche import db
from pedafiche.web import create_app

APP = create_app()


def _jeton(client, url="/connexion"):
    return re.search(r'name="_csrf" value="([0-9a-f]+)"', client.get(url).get_data(as_text=True)).group(1)


def _connexion(ident, mdp):
    c = APP.test_client()
    r = c.post("/connexion", data={"identifiant": ident, "mdp": mdp, "_csrf": _jeton(c)})
    assert r.status_code == 302
    return c


def _amorcer():
    if db.q("SELECT 1 FROM users WHERE identifiant='admin'", un=True):
        return
    ids = {}
    for ident, nom, role in (("admin", "ADMIN", "admin"), ("koffi", "ADJOVI", "enseignant"), ("awa", "SOGLO", "enseignant")):
        ids[ident] = db.ex("INSERT INTO users(identifiant, nom, prenom, role, mdp_hash) VALUES (?,?,?,?,?)",
                           (ident, nom, "Test", role, generate_password_hash("Secret2026")))
    cm2 = db.ex("INSERT INTO classes(nom, cours, ecole, circonscription, effectif, annee) VALUES ('CM2 A','CM2','EPP Pobè','CS Pobè',42,'2026-2027')")
    ce1 = db.ex("INSERT INTO classes(nom, cours, ecole, circonscription, effectif, annee) VALUES ('CE1 A','CE1','EPP Pobè','CS Pobè',38,'2026-2027')")
    db.ex("INSERT INTO affectations VALUES (?,?)", (ids["koffi"], cm2))
    db.ex("INSERT INTO affectations VALUES (?,?)", (ids["awa"], ce1))


def test_acces_par_classe():
    _amorcer()
    cm2 = db.q("SELECT id FROM classes WHERE nom='CM2 A'", un=True)["id"]
    ce1 = db.q("SELECT id FROM classes WHERE nom='CE1 A'", un=True)["id"]
    k = _connexion("koffi", "Secret2026")
    assert k.get(f"/classe/{cm2}").status_code == 200
    assert k.get(f"/classe/{ce1}").status_code == 403                 # pas sa classe
    assert k.get(f"/classe/{ce1}/fiches").status_code == 403
    assert k.get(f"/classe/{cm2}/progression").status_code == 200
    assert k.get("/admin").status_code == 403
    anon = APP.test_client()
    assert anon.get(f"/classe/{cm2}").status_code == 302


def test_fiche_pdf_filigrane_nom_du_titulaire():
    _amorcer()
    from pedafiche import corpus
    from test_core import texte
    cm2 = db.q("SELECT id FROM classes WHERE nom='CM2 A'", un=True)["id"]
    k = _connexion("koffi", "Secret2026")
    f = corpus.fiches("CM2", "francais")[3]
    r = k.get(f"/classe/{cm2}/fiche/{f['id']}.pdf")
    assert r.status_code == 200 and r.data[:4] == b"%PDF"
    t = texte(r.data)
    assert "Test ADJOVI" in t and "Conception :" in t
    ce1_fiche = corpus.fiches("CE1", "francais")[0]
    assert k.get(f"/classe/{cm2}/fiche/{ce1_fiche['id']}.pdf").status_code == 404   # autre cours


def test_pages_et_exports():
    _amorcer()
    cm2 = db.q("SELECT id FROM classes WHERE nom='CM2 A'", un=True)["id"]
    k = _connexion("koffi", "Secret2026")
    for url in (f"/classe/{cm2}/edt", f"/classe/{cm2}/edt.pdf", f"/classe/{cm2}/progression.pdf",
                f"/classe/{cm2}/evaluations?per=T1", f"/classe/{cm2}/evaluation/T1/math/corrige.pdf",
                f"/classe/{cm2}?jour=2026-10-12", f"/classe/{cm2}/semaine.pdf?jour=2026-10-12",
                "/calendrier", "/calendrier.pdf"):
        r = k.get(url)
        assert r.status_code == 200, (url, r.status_code)


def test_csrf_et_edt_personnalise():
    _amorcer()
    cm2 = db.q("SELECT id FROM classes WHERE nom='CM2 A'", un=True)["id"]
    k = _connexion("koffi", "Secret2026")
    assert k.post(f"/classe/{cm2}/edt", data={"n": 1}).status_code == 400          # sans jeton
    j = _jeton(k, f"/classe/{cm2}/edt")
    k.post(f"/classe/{cm2}/edt", data={"_csrf": j, "n": 1, "h0": "08h", "c0_lundi": "Français 45 min", "action": "enregistrer"})
    assert "Français 45 min" in db.edt_de_la_classe(cm2, "CM2")["lignes"][0]["lundi"]


def test_resumes_par_classe_et_pdf():
    _amorcer()
    from pedafiche import corpus
    from test_core import texte
    cm2 = db.q("SELECT id FROM classes WHERE nom='CM2 A'", un=True)["id"]
    ce1 = db.q("SELECT id FROM classes WHERE nom='CE1 A'", un=True)["id"]
    k = _connexion("koffi", "Secret2026")
    assert k.get(f"/classe/{cm2}/resumes").status_code == 200
    assert k.get(f"/classe/{ce1}/resumes").status_code == 403
    r = corpus.resumes("CM2", "maths")[0]
    rep = k.get(f"/classe/{cm2}/resume/{r['id']}.pdf")
    assert rep.status_code == 200 and "Test ADJOVI" in texte(rep.data) and "Conception :" in texte(rep.data)
    autre = corpus.resumes("CE1", "maths")[0]
    assert k.get(f"/classe/{cm2}/resume/{autre['id']}").status_code == 404
