import conftest  # noqa: F401
from werkzeug.security import generate_password_hash

from pedafiche import db
from test_web import APP, _connexion, _jeton, _amorcer


def test_enseignant_prend_sa_classe_seul():
    _amorcer()
    if not db.q("SELECT 1 FROM users WHERE identifiant='neuf'", un=True):
        db.ex("INSERT INTO users(identifiant, nom, prenom, role, mdp_hash) VALUES ('neuf','NOUVEAU','Test','enseignant',?)", (generate_password_hash("Secret2026"),))
    c = _connexion("neuf", "Secret2026")
    assert "Choisir ou créer ma classe" in c.get("/").get_data(as_text=True)
    j = _jeton(c, "/ma-classe")
    ce1 = db.q("SELECT id FROM classes WHERE nom='CE1 A'", un=True)["id"]
    cm2 = db.q("SELECT id FROM classes WHERE nom='CM2 A'", un=True)["id"]
    c.post("/ma-classe", data={"_csrf": j, "action": "prendre", "classe_id": ce1})          # classe d'une collègue : refusé
    assert c.get(f"/classe/{ce1}").status_code == 403
    r = c.post("/ma-classe", data={"_csrf": j, "action": "creer", "nom": "CP B", "cours": "CP", "ecole": "EPP Test"})
    assert r.status_code == 302
    cp = db.q("SELECT id FROM classes WHERE nom='CP B'", un=True)["id"]
    assert c.get(f"/classe/{cp}").status_code == 200 and c.get(f"/classe/{cm2}").status_code == 403
    c.post("/ma-classe", data={"_csrf": j, "action": "creer", "nom": "CP C", "cours": "CP"})  # déjà une classe : refusé
    assert db.q("SELECT 1 FROM classes WHERE nom='CP C'", un=True) is None
    c.post("/ma-classe", data={"_csrf": j, "action": "quitter", "classe_id": cp})             # change de classe
    assert c.get(f"/classe/{cp}").status_code == 403
    c.post("/ma-classe", data={"_csrf": j, "action": "prendre", "classe_id": cp})            # classe redevenue libre
    assert c.get(f"/classe/{cp}").status_code == 200
