"""Sécurité : blocage après essais faux, changement de mot de passe, journal d'audit, sauvegarde."""
from __future__ import annotations

import os
import re
import sqlite3
import unicodedata
import tempfile
from datetime import datetime, timedelta

from flask import abort, flash, g, redirect, render_template, request, send_file, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .. import config, db

MAX_ESSAIS = int(os.environ.get("PEDAFICHE_MAX_ESSAIS", "5"))
BLOCAGE_MIN = int(os.environ.get("PEDAFICHE_BLOCAGE_MIN", "10"))


FAIBLES = {
    "admin", "admin123", "admin1234", "administrateur", "password", "password1", "motdepasse", "azerty",
    "azerty123", "azertyuiop", "qwerty", "qwerty123", "123456", "1234567", "12345678", "123456789", "1234567890",
    "00000000", "11111111", "demo", "demo1234", "scolaris", "scolaris1", "gescol", "gescol1", "pedafiche",
    "pedafiche1", "ecole123", "ecole1234", "bonjour1", "benin123", "benin2026", "abc12345", "abcd1234",
    "directeur", "directeur1", "enseignant", "enseignant1",
}


def _norm(t) -> str:
    return unicodedata.normalize("NFD", str(t or "")).encode("ascii", "ignore").decode().lower()


def erreur_mdp(mdp: str, identifiant: str = ""):
    """Même règle que les applications enseignant de GESCOL et SCOLARIS : message d'erreur ou None."""
    m = str(mdp or "")
    if len(m) < 8:
        return "Le mot de passe doit faire au moins 8 caractères."
    if not re.search(r"[A-Za-zÀ-ÿ]", m) or not re.search(r"\d", m):
        return "Le mot de passe doit contenir au moins une lettre et un chiffre."
    n = _norm(m)
    if n in FAIBLES or len(set(n)) <= 2:
        return "Ce mot de passe est trop connu ou trop simple : choisissez-en un autre."
    ident = _norm(identifiant).strip()
    if ident and len(ident) >= 3 and ident in n:
        return "Le mot de passe ne doit pas contenir l'identifiant."
    return None


def mot_de_passe_valide(mdp: str, identifiant: str = "") -> None:
    e = erreur_mdp(mdp, identifiant)
    if e:
        raise ValueError(e)


def maintenant() -> datetime:
    return datetime.now()


def minutes_restantes(ident: str) -> int:
    r = db.q("SELECT bloque_jusqua FROM tentatives WHERE identifiant=?", (ident,), un=True)
    if not r or not r["bloque_jusqua"]:
        return 0
    reste = (datetime.fromisoformat(r["bloque_jusqua"]) - maintenant()).total_seconds()
    return int(reste // 60) + 1 if reste > 0 else 0


def echec(ident: str) -> None:
    db.ex("INSERT INTO tentatives(identifiant, n) VALUES (?,1) ON CONFLICT(identifiant) DO UPDATE SET n=n+1", (ident,))
    n = db.q("SELECT n FROM tentatives WHERE identifiant=?", (ident,), un=True)["n"]
    if n >= MAX_ESSAIS:
        db.ex("UPDATE tentatives SET n=0, bloque_jusqua=? WHERE identifiant=?",
              ((maintenant() + timedelta(minutes=BLOCAGE_MIN)).isoformat(timespec="seconds"), ident))


def succes(ident: str) -> None:
    db.ex("DELETE FROM tentatives WHERE identifiant=?", (ident,))


def register(app, H):
    connecte, gestionnaire = H.connecte, H.gestionnaire

    @app.route("/mon-compte", methods=["GET", "POST"])
    @connecte
    def mon_compte():
        if request.method == "POST" and request.form.get("action") == "identifiant":
            nv = (request.form.get("identifiant") or "").strip().lower()
            if not check_password_hash(g.user["mdp_hash"], request.form.get("mdp", "")):
                flash("Mot de passe incorrect : l'identifiant n'a pas été changé.", "erreur")
            elif not re.fullmatch(r"[a-z0-9._-]{3,40}", nv) or nv == "admin":
                flash("Identifiant : 3 à 40 lettres, chiffres, points ou tirets (pas « admin »).", "erreur")
            elif nv == g.user["identifiant"]:
                flash("C'est déjà votre identifiant.", "erreur")
            elif db.q("SELECT 1 FROM users WHERE identifiant=? AND id<>?", (nv, g.user["id"]), un=True):
                flash("Cet identifiant est déjà pris : choisissez-en un autre.", "erreur")
            else:
                ancien_id = g.user["identifiant"]
                db.ex("UPDATE users SET identifiant=? WHERE id=?", (nv, g.user["id"]))
                H.audit("identifiant_change", f"{ancien_id} -> {nv}")
                flash(f"Identifiant modifié : connectez-vous désormais avec « {nv} ».", "ok")
            return redirect(url_for("mon_compte"))
        if request.method == "POST":
            try:
                if not check_password_hash(g.user["mdp_hash"], request.form.get("ancien", "")):
                    raise ValueError("Mot de passe actuel incorrect.")
                nouveau = request.form.get("nouveau", "")
                if nouveau != request.form.get("confirmation", ""):
                    raise ValueError("La confirmation ne correspond pas.")
                mot_de_passe_valide(nouveau, g.user["identifiant"])
                db.ex("UPDATE users SET mdp_hash=? WHERE id=?", (generate_password_hash(nouveau), g.user["id"]))
                H.audit("mdp_change", "")
                flash("Mot de passe modifié.", "ok")
                return redirect(url_for("accueil"))
            except ValueError as e:
                flash(str(e), "erreur")
        return render_template("mon_compte.html")

    @app.route("/admin/journal")
    @gestionnaire
    def journal_audit():
        return render_template("audit.html", lignes=db.q("SELECT * FROM audit ORDER BY id DESC LIMIT 300"))

    @app.route("/admin/sauvegarde")
    @gestionnaire
    def sauvegarde():
        if g.user["role"] != "admin":
            abort(403)
        H.audit("sauvegarde", "")
        fd, chemin = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        src = sqlite3.connect(config.DB)
        dst = sqlite3.connect(chemin)
        with dst:
            src.backup(dst)
        src.close()
        dst.close()
        nom = f"pedafiche-sauvegarde-{maintenant().strftime('%Y%m%d-%H%M')}.db"
        r = send_file(chemin, as_attachment=True, download_name=nom, mimetype="application/octet-stream")
        r.call_on_close(lambda: os.path.exists(chemin) and os.remove(chemin))
        return r
