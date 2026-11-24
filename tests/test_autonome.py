"""Application autonome (PC, téléphone, tablette) : le premier utilisateur crée son compte, une seule fois."""
import os
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = r'''
import re, sys
from pedafiche.web import create_app
app = create_app(); app.config["TESTING"] = True
c = app.test_client()
r = c.get("/connexion"); assert r.status_code == 302 and "premiere-installation" in r.headers["Location"], r.headers
h = c.get("/premiere-installation").get_data(as_text=True)
jeton = re.search(r'name="_csrf" value="([^"]+)"', h).group(1)
r = c.post("/premiere-installation", data={"_csrf": jeton, "nom": "KANLISSOU", "identifiant": "Dom", "mdp": "court", "mdp2": "court"})
assert r.status_code == 200 and "8 caract" in r.get_data(as_text=True)
r = c.post("/premiere-installation", data={"_csrf": jeton, "nom": "KANLISSOU", "prenom": "Dominique", "identifiant": "Dom", "mdp": "motdepasse1", "mdp2": "motdepasse1"})
assert r.status_code == 302
r = c.get("/premiere-installation"); assert r.status_code == 302 and "connexion" in r.headers["Location"]
assert c.get("/connexion").status_code == 200
print("OK")
'''


def _lancer(autonome):
    env = dict(os.environ, PEDAFICHE_DB=os.path.join(tempfile.mkdtemp(), "p.db"))
    env.pop("PEDAFICHE_AUTONOME", None)
    if autonome:
        env["PEDAFICHE_AUTONOME"] = "1"
    return subprocess.run([sys.executable, "-c", SCRIPT if autonome else "from pedafiche.web import create_app\napp=create_app();c=app.test_client()\nr=c.get('/premiere-installation')\nassert r.status_code==302 and 'connexion' in r.headers['Location']\nprint('OK')"],
                          cwd=RACINE, env=env, capture_output=True, text=True)


def test_premiere_installation_autonome():
    r = _lancer(True)
    assert "OK" in r.stdout, r.stdout + r.stderr


def test_page_fermee_sur_serveur_public():
    r = _lancer(False)
    assert "OK" in r.stdout, r.stdout + r.stderr
