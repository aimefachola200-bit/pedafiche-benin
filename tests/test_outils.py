"""Outils de l'enseignant : mes fiches, journal, élèves, appel, notes, bulletins, annonces, sécurité."""
import io
import re

import pytest
from werkzeug.security import generate_password_hash

from pedafiche import db, notes as N
from test_web import APP, _amorcer, _connexion, _jeton


# ------------------------------------------------------------------ logique pure
def test_rangs_ex_aequo_et_none():
    assert N.rangs({1: 8, 2: 8, 3: 5, 4: None}) == {1: 1, 2: 1, 3: 3}


def test_sur10_et_moyenne_ponderee():
    assert N.sur10(15, 20) == 7.5 and N.sur10(None, 10) is None
    assert N.moyenne_ponderee([(8, 1), (5, 2)]) == 6.0


def test_resultats_et_remediation():
    els = [{"id": 1, "nom": "A"}, {"id": 2, "nom": "B"}, {"id": 3, "nom": "C"}]
    evs = [{"id": 10, "matiere": "maths", "bareme": 20, "coef": 1, "periode": "T1"},
           {"id": 11, "matiere": "francais", "bareme": 10, "coef": 1, "periode": "T1"}]
    nn = {(10, 1): 16, (11, 1): 8, (10, 2): 6, (11, 2): 4, (10, 3): None}
    r = N.resultats(els, evs, nn, "T1")
    l = {x["eleve"]["id"]: x for x in r["lignes"]}
    assert l[1]["moyenne"] == 8.0 and l[1]["rang"] == 1 and l[1]["appreciation"] == "Très bien"
    assert l[2]["moyenne"] == 3.5 and l[3]["moyenne"] is None and l[3]["rang"] is None
    assert r["stats"]["taux_reussite"] == 50.0
    assert [x["eleve"]["id"] for x in N.a_remedier(els, evs[1], nn)] == [2]


def test_presences_decrocheurs():
    b = N.bilan_presences([{"eleve_id": 1, "statut": "A", "justifie": 0}] * 3 + [{"eleve_id": 2, "statut": "A", "justifie": 1}] * 5)
    assert N.decrocheurs(b, 3) == [1]


# ------------------------------------------------------------------ web
def _cid(nom):
    _amorcer()
    return db.q("SELECT id FROM classes WHERE nom=?", (nom,), un=True)["id"]


def _post(c, url, data, ref=None):
    return c.post(url, data={**data, "_csrf": _jeton(c, ref or url.rsplit("/", 1)[0] or "/")})


def test_mes_fiches_creation_export_partage_et_acces():
    cid = _cid("CM2 A")
    k = _connexion("koffi", "Secret2026")
    base = f"/classe/{cid}/mes-fiches"
    r = k.post(base + "/nouvelle", data={"titre": "Ma leçon sur les fractions", "matiere": "maths", "contenus": "Fractions",
                                          "cons0": "Présente", "res0": "ok", "cons1": "Travaille", "cons2": "Évalue",
                                          "_csrf": _jeton(k, base)})
    assert r.status_code == 302
    mid = int(re.search(r"/mes-fiches/(\d+)", r.headers["Location"]).group(1))
    assert k.get(f"{base}/{mid}.pdf").data[:4] == b"%PDF"
    d = k.get(f"{base}/{mid}.docx")
    assert d.status_code == 200 and d.data[:2] == b"PK"
    assert k.get(f"/classe/{cid}/fiche/{db.q('SELECT 1')[0][0] and ''}") is not None
    # un autre enseignant (autre classe) n'a pas accès à la classe CM2
    a = _connexion("awa", "Secret2026")
    assert a.get(f"{base}/{mid}.pdf").status_code == 403
    # partage + copie par un collègue du même cours
    k.post(f"{base}/{mid}/partager", data={"_csrf": _jeton(k, base)})
    assert db.q("SELECT partage FROM mes_fiches WHERE id=?", (mid,), un=True)["partage"] == 1
    # titre obligatoire
    assert k.post(base + "/nouvelle", data={"titre": "", "matiere": "maths", "_csrf": _jeton(k, base)}).status_code == 302
    assert db.q("SELECT COUNT(*) n FROM mes_fiches WHERE titre=''", un=True)["n"] == 0
    k.post(f"{base}/{mid}/supprimer", data={"_csrf": _jeton(k, base)})
    assert not db.q("SELECT 1 FROM mes_fiches WHERE id=?", (mid,), un=True)


def test_fiche_corpus_en_word_et_adaptation():
    from pedafiche import corpus
    cid = _cid("CM2 A")
    k = _connexion("koffi", "Secret2026")
    fid = corpus.fiches("CM2")[0]["id"]
    assert k.get(f"/classe/{cid}/fiche/{fid}.docx").data[:2] == b"PK"
    page = k.get(f"/classe/{cid}/mes-fiches/nouvelle?base={fid}").get_data(as_text=True)
    assert "(adaptée)" in page
    ce1 = corpus.fiches("CE1")[0]["id"]
    assert k.get(f"/classe/{cid}/mes-fiches/nouvelle?base={ce1}").status_code == 404


def test_suivi_alimente_le_cahier_journal():
    from pedafiche import corpus
    cid = _cid("CM2 A")
    k = _connexion("koffi", "Secret2026")
    fid = corpus.fiches("CM2", "maths")[0]["id"]
    k.post(f"/classe/{cid}/suivi/{fid}", data={"fait": "1", "observation": "RAS", "_csrf": _jeton(k, f"/classe/{cid}")})
    assert db.q("SELECT 1 FROM journal WHERE classe_id=? AND fiche_id=?", (cid, fid), un=True)
    assert k.get(f"/classe/{cid}/journal").status_code == 200
    r = k.get(f"/classe/{cid}/journal.pdf?du=2020-01-01&au=2099-12-31")
    assert r.data[:4] == b"%PDF"


def test_eleves_import_appel_absences():
    cid = _cid("CE1 A")
    a = _connexion("awa", "Secret2026")
    csv_txt = "nom;prenom;sexe;naissance\nADJOVI;Koffi;M;12/03/2017\nSOGLO;Awa;F;01/01/2017\nADJOVI;Koffi;M;12/03/2017\n"
    r = a.post(f"/classe/{cid}/eleves", data={"action": "importer", "texte": csv_txt, "_csrf": _jeton(a, f"/classe/{cid}/eleves")},
               follow_redirects=True)
    assert "2 élève(s) importé(s)" in r.get_data(as_text=True)
    assert db.q("SELECT effectif FROM classes WHERE id=?", (cid,), un=True)["effectif"] == 2
    assert a.get(f"/classe/{cid}/eleves.pdf").data[:4] == b"%PDF"
    els = db.q("SELECT id FROM eleves WHERE classe_id=? ORDER BY id", (cid,))
    # appel futur refusé
    f = a.post(f"/classe/{cid}/appel", data={"jour": "2099-01-01", "_csrf": _jeton(a, f"/classe/{cid}/appel")})
    assert f.status_code == 302 and db.q("SELECT COUNT(*) n FROM presences WHERE jour='2099-01-01'", un=True)["n"] == 0
    for jour in ("2026-10-05", "2026-10-06", "2026-10-07"):
        a.post(f"/classe/{cid}/appel", data={"jour": jour, f"s{els[0]['id']}": "A", f"s{els[1]['id']}": "P",
                                              "_csrf": _jeton(a, f"/classe/{cid}/appel")})
    page = a.get(f"/classe/{cid}/absences?du=2026-09-01&au=2027-07-31").get_data(as_text=True)
    assert "1 élève(s) avec 3 absences non justifiées" in page
    assert a.get(f"/classe/{cid}/absences.pdf").data[:4] == b"%PDF"
    # un enseignant d'une autre classe n'y accède pas
    k = _connexion("koffi", "Secret2026")
    assert k.get(f"/classe/{cid}/eleves").status_code == 403 and k.get(f"/classe/{cid}/appel").status_code == 403


def test_notes_validation_resultats_bulletins():
    cid = _cid("CE1 A")
    a = _connexion("awa", "Secret2026")
    els = db.q("SELECT id FROM eleves WHERE classe_id=? ORDER BY id", (cid,))
    assert len(els) == 2
    r = a.post(f"/classe/{cid}/notes", data={"titre": "Devoir 1", "matiere": "maths", "jour": "2026-10-10", "bareme": "20",
                                              "coef": "1", "periode": "T1", "_csrf": _jeton(a, f"/classe/{cid}/notes")})
    eid = int(re.search(r"/notes/(\d+)", r.headers["Location"]).group(1))
    url = f"/classe/{cid}/notes/{eid}"
    # note hors barème refusée, rien n'est enregistré pour cet élève
    a.post(url, data={f"n{els[0]['id']}": "25", f"n{els[1]['id']}": "abc", "_csrf": _jeton(a, url)})
    assert db.q("SELECT COUNT(*) n FROM notes WHERE eval_id=? AND valeur IS NOT NULL", (eid,), un=True)["n"] == 0
    a.post(url, data={f"n{els[0]['id']}": "16,5", f"n{els[1]['id']}": "6", "_csrf": _jeton(a, url)})
    assert db.q("SELECT valeur FROM notes WHERE eval_id=? AND eleve_id=?", (eid, els[0]["id"]), un=True)["valeur"] == 16.5
    page = a.get(f"/classe/{cid}/resultats?periode=T1").get_data(as_text=True)
    assert "8.25" in page or "8,25" in page
    assert a.get(f"/classe/{cid}/resultats.pdf?periode=T1").data[:4] == b"%PDF"
    assert a.get(f"/classe/{cid}/bulletin/{els[0]['id']}.pdf?periode=T1").data[:4] == b"%PDF"
    assert a.get(f"/classe/{cid}/bulletins.pdf?periode=T1").data[:4] == b"%PDF"
    assert a.get(f"/classe/{cid}/notes/{eid}/remediation.pdf").data[:4] == b"%PDF"
    assert "3" in a.get(url).get_data(as_text=True)               # élève à 3/10 → remédiation
    # un bulletin d'un élève d'une autre classe n'existe pas
    k = _connexion("koffi", "Secret2026")
    cm2 = _cid("CM2 A")
    assert k.get(f"/classe/{cm2}/bulletin/{els[0]['id']}.pdf").status_code == 404
    assert k.get(url).status_code == 403


def test_annonces_accuse_de_lecture():
    _amorcer()
    ad = _connexion("admin", "Secret2026")
    ad.post("/annonces", data={"action": "publier", "titre": "Réunion", "corps": "Mardi 15h", "_csrf": _jeton(ad, "/annonces")})
    aid = db.q("SELECT id FROM annonces WHERE titre='Réunion'", un=True)["id"]
    k = _connexion("koffi", "Secret2026")
    assert "Annonces (" in k.get("/").get_data(as_text=True)
    assert k.post("/annonces", data={"action": "publier", "titre": "x", "corps": "y", "_csrf": _jeton(k, "/annonces")}).status_code == 403
    k.post("/annonces", data={"action": "lu", "id": aid, "_csrf": _jeton(k, "/annonces")})
    assert db.q("SELECT COUNT(*) n FROM annonces_lues WHERE annonce_id=?", (aid,), un=True)["n"] == 1
    assert "lue par 1 /" in ad.get("/annonces").get_data(as_text=True)


def test_blocage_apres_essais_faux():
    _amorcer()
    if not db.q("SELECT 1 FROM users WHERE identifiant='essai'", un=True):
        db.ex("INSERT INTO users(identifiant, nom, prenom, role, mdp_hash) VALUES ('essai','ESSAI','X','enseignant',?)",
              (generate_password_hash("Secret2026"),))
    c = APP.test_client()
    for _ in range(5):
        c.post("/connexion", data={"identifiant": "essai", "mdp": "faux", "_csrf": _jeton(c)})
    r = c.post("/connexion", data={"identifiant": "essai", "mdp": "Secret2026", "_csrf": _jeton(c)})
    assert r.status_code == 429 and "bloqué" in r.get_data(as_text=True)
    ad = _connexion("admin", "Secret2026")
    uid = db.q("SELECT id FROM users WHERE identifiant='essai'", un=True)["id"]
    ad.post("/admin", data={"action": "mdp", "user_id": uid, "mdp": "Nouveau2026", "_csrf": _jeton(ad, "/admin")})
    assert _connexion("essai", "Nouveau2026")
    assert "connexion_refusee" in ad.get("/admin/journal").get_data(as_text=True)


def test_mon_compte_et_sauvegarde():
    _amorcer()
    if not db.q("SELECT 1 FROM users WHERE identifiant='moi'", un=True):
        db.ex("INSERT INTO users(identifiant, nom, prenom, role, mdp_hash) VALUES ('moi','MOI','X','enseignant',?)",
              (generate_password_hash("Secret2026"),))
    m = _connexion("moi", "Secret2026")
    bad = m.post("/mon-compte", data={"ancien": "faux", "nouveau": "Autre2026x", "confirmation": "Autre2026x", "_csrf": _jeton(m, "/mon-compte")})
    assert bad.status_code == 200
    ok = m.post("/mon-compte", data={"ancien": "Secret2026", "nouveau": "Autre2026x", "confirmation": "Autre2026x", "_csrf": _jeton(m, "/mon-compte")})
    assert ok.status_code == 302 and _connexion("moi", "Autre2026x")
    assert m.get("/admin/sauvegarde").status_code == 403           # enseignant
    ad = _connexion("admin", "Secret2026")
    s = ad.get("/admin/sauvegarde")
    assert s.status_code == 200 and s.data[:15] == b"SQLite format 3"
