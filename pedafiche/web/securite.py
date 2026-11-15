"""Sécurité : blocage après essais faux, changement de mot de passe, journal d'audit, sauvegarde."""
from __future__ import annotations

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

from flask import abort, flash, g, redirect, render_template, request, send_file, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .. import config, db

MAX_ESSAIS = int(os.environ.get("PEDAFICHE_MAX_ESSAIS", "5"))
BLOCAGE_MIN = int(os.environ.get("PEDAFICHE_BLOCAGE_MIN", "10"))


def mot_de_passe_valide(mdp: str) -> None:
    if len(mdp) < 8 or mdp.isalpha() or mdp.isdigit():
        raise ValueError("Mot de passe : 8 caractères minimum, lettres et chiffres.")


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
        if request.method == "POST":
            try:
                if not check_password_hash(g.user["mdp_hash"], request.form.get("ancien", "")):
                    raise ValueError("Mot de passe actuel incorrect.")
                nouveau = request.form.get("nouveau", "")
                if nouveau != request.form.get("confirmation", ""):
                    raise ValueError("La confirmation ne correspond pas.")
                mot_de_passe_valide(nouveau)
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
