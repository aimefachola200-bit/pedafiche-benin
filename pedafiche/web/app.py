"""Application Flask : comptes, accès par classe, fiches, progression, EDT, calendrier, évaluations."""
from __future__ import annotations

import os
import re
import secrets
from datetime import date, datetime, timedelta
from functools import wraps

import click
from flask import (Flask, abort, flash, g, make_response, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from types import SimpleNamespace

from .. import calendrier, config, corpus, db, edt, epreuves, pdf, progression
from . import ens, securite

ROLES_GESTION = ("admin", "directeur")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(SECRET_KEY=config.SECRET_KEY, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
                      SESSION_COOKIE_SECURE=os.environ.get("PEDAFICHE_HTTPS") == "1")
    db.init()

    # ------------------------------------------------------------------ session / sécurité
    @app.before_request
    def _charger():
        g.user = None
        if session.get("uid"):
            g.user = db.q("SELECT * FROM users WHERE id=? AND actif=1", (session["uid"],), un=True)
        if request.method == "POST":
            if not secrets.compare_digest(request.form.get("_csrf", ""), session.get("_csrf", "-")):
                abort(400, "Jeton CSRF invalide.")

    @app.context_processor
    def _ctx():
        session.setdefault("_csrf", secrets.token_hex(16))
        non_lues = 0
        if g.get("user"):
            non_lues = db.q("SELECT COUNT(*) n FROM annonces a WHERE NOT EXISTS (SELECT 1 FROM annonces_lues l "
                            "WHERE l.annonce_id=a.id AND l.user_id=?)", (g.user["id"],), un=True)["n"]
        menu_classes = []
        if g.get("user"):
            try:
                menu_classes = mes_classes()
            except Exception:  # le menu ne doit jamais empêcher d'afficher une page
                menu_classes = []
        return dict(csrf=session["_csrf"], user=g.get("user"), config=config, corpus=corpus,
                    LIB_COURS=corpus.LIB_COURS, annee=config.ANNEE, non_lues=non_lues, menu_classes=menu_classes)

    @app.after_request
    def _entetes(r):
        r.headers.setdefault("X-Content-Type-Options", "nosniff")
        r.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        if os.environ.get("PEDAFICHE_HTTPS") == "1":
            r.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return r

    def connecte(f):
        @wraps(f)
        def w(*a, **k):
            if not g.user:
                return redirect(url_for("connexion", suite=request.path))
            return f(*a, **k)
        return w

    def gestionnaire(f):
        @wraps(f)
        @connecte
        def w(*a, **k):
            if g.user["role"] not in ROLES_GESTION:
                abort(403)
            return f(*a, **k)
        return w

    def mes_classes():
        if g.user["role"] in ROLES_GESTION:
            return db.q("SELECT * FROM classes WHERE annee=? ORDER BY cours, nom", (config.ANNEE,))
        return db.q("SELECT c.* FROM classes c JOIN affectations a ON a.classe_id=c.id "
                    "WHERE a.user_id=? AND c.annee=? ORDER BY c.cours, c.nom", (g.user["id"], config.ANNEE))

    def classe_ou_403(cid: int):
        """Un enseignant n'accède qu'aux classes qui lui sont affectées."""
        c = next((c for c in mes_classes() if c["id"] == cid), None)
        if not c:
            abort(403)
        return c

    def titulaire(c) -> str:
        r = db.q("SELECT u.* FROM users u JOIN affectations a ON a.user_id=u.id WHERE a.classe_id=? "
                 "ORDER BY u.id LIMIT 1", (c["id"],), un=True) or g.user
        return " ".join(x for x in (r["prenom"], r["nom"].upper()) if x)

    def ctx_pdf(c, d: date | None = None) -> dict:
        t = titulaire(c)
        return dict(filigrane=t, enseignant=t, ecole=c["ecole"], circonscription=c["circonscription"],
                    annee=c["annee"], classe=c["nom"], effectif=c["effectif"], date=d)

    def reponse_pdf(contenu: bytes, nom: str):
        r = make_response(contenu)
        r.headers["Content-Type"] = "application/pdf"
        r.headers["Content-Disposition"] = f'inline; filename="{nom}"'
        return r

    def audit(action: str, detail: str = "", ident: str = "") -> None:
        u = g.get("user")
        db.ex("INSERT INTO audit(quand, user_id, identifiant, action, detail) VALUES (?,?,?,?,?)",
              (datetime.now().isoformat(timespec="seconds"), u["id"] if u else None,
               u["identifiant"] if u else ident, action, detail[:300]))

    def jour_demande() -> date:
        try:
            return date.fromisoformat(request.args.get("jour", ""))
        except ValueError:
            return date.today()

    @app.route("/sw.js")
    def service_worker():
        """Service worker à la racine (portée « / ») : rend l'application installable."""
        r = app.send_static_file("sw.js")
        r.headers["Cache-Control"] = "no-cache"
        r.headers["Service-Worker-Allowed"] = "/"
        return r

    # ------------------------------------------------------------------ connexion
    @app.route("/connexion", methods=["GET", "POST"])
    def connexion():
        if _autonome() and _aucun_compte():
            return redirect(url_for("premiere_installation"))
        if request.method == "POST":
            ident = request.form.get("identifiant", "").strip().lower()
            reste = securite.minutes_restantes(ident)
            if reste:
                flash(f"Trop d'essais. Compte bloqué encore {reste} minute(s).", "erreur")
                return render_template("connexion.html"), 429
            u = db.q("SELECT * FROM users WHERE identifiant=? AND actif=1", (ident,), un=True)
            if u and check_password_hash(u["mdp_hash"], request.form.get("mdp", "")):
                securite.succes(ident)
                session.clear()
                session.permanent = True
                session["uid"] = u["id"]
                session["_csrf"] = secrets.token_hex(16)
                g.user = u
                audit("connexion")
                suite = request.args.get("suite", "")
                return redirect(suite if suite.startswith("/") and not suite.startswith("//") else url_for("accueil"))
            securite.echec(ident)
            audit("connexion_refusee", ident=ident)
            flash("Identifiant ou mot de passe incorrect.", "erreur")
        return render_template("connexion.html")

    # ------------------------------------------------------------------ première installation (applications autonomes)
    def _autonome():
        return os.environ.get("PEDAFICHE_AUTONOME") == "1"

    def _aucun_compte():
        return db.q("SELECT COUNT(*) n FROM users", un=True)["n"] == 0

    @app.route("/premiere-installation", methods=["GET", "POST"])
    def premiere_installation():
        """Application installée sur un PC, un téléphone ou une tablette : le premier utilisateur crée son compte directeur.
        Réservé aux applications autonomes (variable PEDAFICHE_AUTONOME) et refermé dès qu'un compte existe."""
        if not _autonome() or not _aucun_compte():
            return redirect(url_for("connexion"))
        if request.method == "POST":
            nom = request.form.get("nom", "").strip()
            prenom = request.form.get("prenom", "").strip()
            ident = request.form.get("identifiant", "").strip().lower()
            mdp = request.form.get("mdp", "")
            erreurs = []
            if not nom or not prenom:
                erreurs.append("Indiquez votre nom et vos prénoms.")
            if not re.fullmatch(r"[a-z0-9._-]{3,40}", ident) or ident == "admin":
                erreurs.append("Identifiant : 3 à 40 lettres, chiffres, points ou tirets (pas « admin »).")
            e_mdp = securite.erreur_mdp(mdp, ident)
            if e_mdp:
                erreurs.append(e_mdp)
            elif mdp != request.form.get("mdp2", ""):
                erreurs.append("La confirmation du mot de passe ne correspond pas.")
            if erreurs:
                for e in erreurs[:4]:
                    flash(e, "erreur")
            else:
                db.ex("INSERT INTO users(identifiant, nom, prenom, role, mdp_hash) VALUES (?,?,?,?,?)",
                      (ident, nom, prenom, "admin", generate_password_hash(mdp)))
                flash("Compte créé. Connectez-vous.", "ok")
                return redirect(url_for("connexion"))
        return render_template("premiere_installation.html")

    @app.route("/deconnexion", methods=["POST"])
    def deconnexion():
        session.clear()
        return redirect(url_for("connexion"))

    @app.route("/")
    @connecte
    def accueil():
        classes = mes_classes()
        taux = {c["id"]: H.taux_realisation(c) for c in classes}
        return render_template("accueil.html", classes=classes, taux=taux)

    # ------------------------------------------------------------------ ma classe
    @app.route("/classe/<int:cid>")
    @connecte
    def classe(cid):
        c = classe_ou_403(cid)
        jour = jour_demande()
        e = db.edt_de_la_classe(cid, c["cours"])
        lundi = jour - timedelta(days=jour.weekday())
        sugg = progression.fiches_de_la_semaine(c["cours"], jour)
        semaine = [(lundi + timedelta(days=k), edt.journee(e, c["cours"], lundi + timedelta(days=k), sugg))
                   for k in range(5)]
        faites = {r["fiche_id"] for r in db.q("SELECT fiche_id FROM suivi WHERE classe_id=?", (cid,))}
        return render_template("classe.html", c=c, jour=jour, semaine=semaine, sugg=sugg, faites=faites,
                               est_classe=calendrier.est_jour_classe(jour),
                               trimestre=calendrier.trimestre_de(jour),
                               evts=calendrier.evenements_du_jour(jour), titulaire=titulaire(c),
                               prec=lundi - timedelta(days=7), suiv=lundi + timedelta(days=7))

    @app.route("/classe/<int:cid>/fiches")
    @connecte
    def fiches(cid):
        c = classe_ou_403(cid)
        mat, mois, texte = request.args.get("matiere", ""), request.args.get("mois", ""), request.args.get("q", "")
        mats = corpus.matieres_du_cours(c["cours"])
        mat = mat if mat in mats else (mats[0] if mats else "")
        if mois:
            ligne = next((l for l in progression.progression_annuelle(c["cours"]) if l["mois"] == mois), None)
            liste = [corpus.fiche(i) for i in (ligne["matieres"].get(mat, {}).get("fiches", []) if ligne else [])]
            liste = [f for f in liste if f]
        else:
            liste = corpus.fiches(c["cours"], mat)
        if texte:
            ids = {f["id"] for f in corpus.fiches(c["cours"], mat, texte)}
            liste = [f for f in liste if f["id"] in ids]
        faites = {r["fiche_id"] for r in db.q("SELECT fiche_id FROM suivi WHERE classe_id=?", (cid,))}
        return render_template("fiches.html", c=c, mats=mats, mat=mat, mois=mois, q=texte,
                               liste=liste[:400], total=len(liste), faites=faites)

    def fiche_ou_404(c, fid):
        f = corpus.fiche(fid)
        if not f or f["cours"] != c["cours"]:
            abort(404)
        return f

    @app.route("/classe/<int:cid>/fiche/<fid>")
    @connecte
    def fiche(cid, fid):
        c = classe_ou_403(cid)
        f = fiche_ou_404(c, fid)
        s = db.q("SELECT * FROM suivi WHERE classe_id=? AND fiche_id=?", (cid, fid), un=True)
        return render_template("fiche.html", c=c, f=f, suivi=s, resumes=corpus.resumes_de_la_fiche(f))

    @app.route("/classe/<int:cid>/fiche/<fid>.pdf")
    @connecte
    def fiche_pdf(cid, fid):
        c = classe_ou_403(cid)
        f = fiche_ou_404(c, fid)
        return reponse_pdf(pdf.fiche_pdf(f, ctx_pdf(c)), f"fiche_{fid}.pdf")

    @app.route("/classe/<int:cid>/semaine.pdf")
    @connecte
    def classeur_semaine(cid):
        c = classe_ou_403(cid)
        jour = jour_demande()
        sugg = progression.fiches_de_la_semaine(c["cours"], jour)
        liste = [f for m in corpus.ORDRE_MAT for f in sugg.get(m, [])][:40]
        if not liste:
            abort(404, "Aucune fiche prévue cette semaine.")
        return reponse_pdf(pdf.lot_pdf(liste, ctx_pdf(c)), f"classeur_semaine_{jour.isoformat()}.pdf")

    @app.route("/classe/<int:cid>/suivi/<fid>", methods=["POST"])
    @connecte
    def suivi(cid, fid):
        c = classe_ou_403(cid)
        fiche_ou_404(c, fid)
        if request.form.get("fait") == "1":
            db.ex("INSERT INTO suivi(classe_id, fiche_id, date_realisee, observation) VALUES (?,?,?,?) "
                  "ON CONFLICT(classe_id, fiche_id) DO UPDATE SET date_realisee=excluded.date_realisee, "
                  "observation=excluded.observation",
                  (cid, fid, date.today().isoformat(), request.form.get("observation", "")[:500]))
            f = corpus.fiche(fid)
            if not db.q("SELECT 1 FROM journal WHERE classe_id=? AND fiche_id=?", (cid, fid), un=True):
                db.ex("INSERT INTO journal(classe_id, jour, matiere, titre, fiche_id, realise, observation) VALUES (?,?,?,?,?,?,?)",
                      (cid, date.today().isoformat(), f["matiere"], f["titre"], fid, "oui",
                       request.form.get("observation", "")[:500]))
        else:
            db.ex("DELETE FROM suivi WHERE classe_id=? AND fiche_id=?", (cid, fid))
        return redirect(request.referrer or url_for("fiche", cid=cid, fid=fid))

    # ------------------------------------------------------------------ résumés
    @app.route("/classe/<int:cid>/resumes")
    @connecte
    def resumes(cid):
        c = classe_ou_403(cid)
        mats = sorted({r["matiere"] for r in corpus.resumes_du_cours(c["cours"])}, key=corpus.ORDRE_MAT.index)
        mat, mois, texte = request.args.get("matiere", ""), request.args.get("mois", ""), request.args.get("q", "")
        mat = mat if mat in mats else (mats[0] if mats else "")
        liste = corpus.resumes(c["cours"], mat, mois or None, texte or None)
        return render_template("resumes.html", c=c, mats=mats, mat=mat, mois=mois, q=texte,
                               liste=liste[:300], total=len(liste), mois_liste=list(progression.MOIS_NOMS.values()))

    def resume_ou_404(c, rid):
        r = corpus.resume(rid)
        if not r or r["cours"] != c["cours"]:
            abort(404)
        return r

    @app.route("/classe/<int:cid>/resume/<rid>")
    @connecte
    def resume(cid, rid):
        c = classe_ou_403(cid)
        return render_template("resume.html", c=c, r=resume_ou_404(c, rid))

    @app.route("/classe/<int:cid>/resume/<rid>.pdf")
    @connecte
    def resume_pdf(cid, rid):
        c = classe_ou_403(cid)
        r = resume_ou_404(c, rid)
        corrige = request.args.get("corrige", "1") == "1"
        return reponse_pdf(pdf.resume_pdf(r, ctx_pdf(c), corrige), f"resume_{rid}.pdf")

    # ------------------------------------------------------------------ progression annuelle
    @app.route("/classe/<int:cid>/progression")
    @connecte
    def prog(cid):
        c = classe_ou_403(cid)
        return render_template("progression.html", c=c, plan=progression.progression_annuelle(c["cours"]),
                               mats=[m for m in progression.PLAN_COLS])

    @app.route("/classe/<int:cid>/progression.pdf")
    @connecte
    def prog_pdf(cid):
        c = classe_ou_403(cid)
        mats = list(progression.PLAN_COLS)
        lignes = [[f"{l['trimestre']} — {l['mois']}"] + [l["matieres"][m]["texte"] for m in mats] for l in
                  progression.progression_annuelle(c["cours"])]
        return reponse_pdf(pdf.tableau_pdf(
            f"PROGRESSION ANNUELLE {config.ANNEE} — {c['cours']}", f"{c['ecole']} · {c['nom']}",
            ["Mois"] + [corpus.LIB_MAT[m] for m in mats], lignes, [1.2] + [2] * len(mats), ctx_pdf(c), 7.5),
            f"progression_{c['cours']}.pdf")

    # ------------------------------------------------------------------ emploi du temps
    @app.route("/classe/<int:cid>/edt", methods=["GET", "POST"])
    @connecte
    def emploi_du_temps(cid):
        c = classe_ou_403(cid)
        e = db.edt_de_la_classe(cid, c["cours"])
        if request.method == "POST":
            if request.form.get("action") == "reinitialiser":
                db.ex("DELETE FROM edt_classe WHERE classe_id=?", (cid,))
                flash("Emploi du temps officiel rétabli.", "ok")
            else:
                lignes = []
                for i in range(int(request.form.get("n", 0))):
                    l = {"horaire": request.form.get(f"h{i}", "").strip()}
                    for j in edt.JOURS:
                        l[j] = request.form.get(f"c{i}_{j}", "").strip()
                    if l["horaire"] or any(l[j] for j in edt.JOURS):
                        lignes.append(l)
                db.enregistrer_edt(cid, {**e, "lignes": lignes})
                flash("Emploi du temps enregistré.", "ok")
            return redirect(url_for("emploi_du_temps", cid=cid))
        vide = {"horaire": "", **{j: "" for j in edt.JOURS}}
        return render_template("edt.html", c=c, e=e, lignes=e["lignes"] + [vide, vide],
                               jours=list(zip(edt.JOURS, edt.JOURS_LIB)), perso=bool(
                                   db.q("SELECT 1 FROM edt_classe WHERE classe_id=?", (cid,), un=True)))

    @app.route("/classe/<int:cid>/edt.pdf")
    @connecte
    def edt_pdf(cid):
        c = classe_ou_403(cid)
        e = db.edt_de_la_classe(cid, c["cours"])
        lignes = [[l.get("horaire", "")] + [l.get(j, "") for j in edt.JOURS] for l in e["lignes"]]
        return reponse_pdf(pdf.tableau_pdf(f"EMPLOI DU TEMPS — {c['nom']} ({c['cours']})",
                                           f"{c['ecole']} · Année {config.ANNEE}", ["Horaire"] + edt.JOURS_LIB,
                                           lignes, [1.1, 2, 2, 2, 2, 2], ctx_pdf(c), 8.5), f"edt_{cid}.pdf")

    # ------------------------------------------------------------------ calendrier scolaire
    @app.route("/calendrier")
    @connecte
    def calendrier_page():
        a = config.ANNEE
        deb = int(a[:4])
        mois = [(deb if m >= 9 else deb + 1, m) for m in (9, 10, 11, 12, 1, 2, 3, 4, 5, 6)]
        return render_template("calendrier.html", periodes=calendrier.periodes(a), ref=calendrier.reference(a),
                               resume=calendrier.resume(a), COUL=calendrier.COULEURS, TL=calendrier.TYPES_LIB,
                               grilles=[(an, m, calendrier.grille_mois(an, m, a)) for an, m in mois],
                               MOIS=calendrier.MOIS, aujourdhui=date.today())

    @app.route("/calendrier.pdf")
    @connecte
    def calendrier_pdf():
        a = config.ANNEE
        lignes = [[p["libelle"], calendrier.TYPES_LIB[p["type"]], p["debut_d"].strftime("%d/%m/%Y"),
                   p["fin_d"].strftime("%d/%m/%Y"), p["precision"] or "", p["duree"] or ""]
                  for p in calendrier.periodes(a)]
        return reponse_pdf(pdf.tableau_pdf(f"CALENDRIER SCOLAIRE {a}", calendrier.reference(a)["reference"],
                                           ["Période", "Type", "Du", "Au", "Précision", "Durée"], lignes,
                                           [3, 1.2, 1, 1, 3, 1.5], {"filigrane": ""}, 8.5), f"calendrier_{a}.pdf")

    # ------------------------------------------------------------------ évaluations
    @app.route("/classe/<int:cid>/evaluations")
    @connecte
    def evaluations(cid):
        c = classe_ou_403(cid)
        if c["cours"] not in epreuves.COURS_EVAL:
            return render_template("evaluations.html", c=c, periodes=[], jeu=None, per=None)
        pers = epreuves.periodes(c["cours"])
        per = request.args.get("per") or pers[0][0]
        if per not in {p[0] for p in pers}:
            abort(404)
        return render_template("evaluations.html", c=c, periodes=pers, per=per,
                               jeu=epreuves.epreuves_de_la_periode(c["cours"], per))

    @app.route("/classe/<int:cid>/evaluation/<per>/<code>/<mode>.pdf")
    @connecte
    def evaluation_pdf(cid, per, code, mode):
        c = classe_ou_403(cid)
        if mode not in ("sujet", "corrige", "grille") or c["cours"] not in epreuves.COURS_EVAL:
            abort(404)
        d = epreuves.epreuve(c["cours"], per, code)
        if not d:
            abort(404)
        return reponse_pdf(pdf.epreuve_pdf(d, ctx_pdf(c), mode), f"{d['cle']}_{mode}.pdf")

    # ------------------------------------------------------------------ administration
    @app.route("/admin", methods=["GET", "POST"])
    @gestionnaire
    def admin():
        if request.method == "POST":
            a = request.form.get("action")
            try:
                if a == "user":
                    mdp = request.form["mdp"]
                    if len(mdp) < 8 or mdp.isalpha() or mdp.isdigit():
                        raise ValueError("Mot de passe : 8 caractères minimum, lettres et chiffres.")
                    role = request.form.get("role", "enseignant")
                    if role == "admin" and g.user["role"] != "admin":
                        abort(403)
                    audit("compte_cree", request.form["identifiant"])
                    db.ex("INSERT INTO users(identifiant, nom, prenom, role, mdp_hash) VALUES (?,?,?,?,?)",
                          (request.form["identifiant"].strip().lower(), request.form["nom"].strip(),
                           request.form.get("prenom", "").strip(), role, generate_password_hash(mdp)))
                elif a == "classe":
                    if request.form["cours"] not in corpus.COURS:
                        raise ValueError("Cours inconnu.")
                    db.ex("INSERT INTO classes(nom, cours, ecole, circonscription, effectif, annee) VALUES (?,?,?,?,?,?)",
                          (request.form["nom"].strip(), request.form["cours"], request.form.get("ecole", ""),
                           request.form.get("circonscription", ""), int(request.form.get("effectif") or 0), config.ANNEE))
                elif a == "mdp":
                    cible = db.q("SELECT * FROM users WHERE id=?", (int(request.form["user_id"]),), un=True)
                    if not cible or (cible["role"] == "admin" and g.user["role"] != "admin"):
                        abort(403)
                    securite.mot_de_passe_valide(request.form["mdp"])
                    db.ex("UPDATE users SET mdp_hash=? WHERE id=?", (generate_password_hash(request.form["mdp"]), cible["id"]))
                    db.ex("DELETE FROM tentatives WHERE identifiant=?", (cible["identifiant"],))
                    audit("mdp_reinitialise", cible["identifiant"])
                elif a == "actif":
                    cible = db.q("SELECT * FROM users WHERE id=?", (int(request.form["user_id"]),), un=True)
                    if not cible or cible["id"] == g.user["id"] or (cible["role"] == "admin" and g.user["role"] != "admin"):
                        abort(403)
                    db.ex("UPDATE users SET actif=1-actif WHERE id=?", (cible["id"],))
                    audit("compte_active_ou_desactive", cible["identifiant"])
                elif a == "affecter":
                    db.ex("INSERT OR IGNORE INTO affectations(user_id, classe_id) VALUES (?,?)",
                          (int(request.form["user_id"]), int(request.form["classe_id"])))
                elif a == "retirer":
                    db.ex("DELETE FROM affectations WHERE user_id=? AND classe_id=?",
                          (int(request.form["user_id"]), int(request.form["classe_id"])))
                flash("Enregistré.", "ok")
            except Exception as exc:  # noqa: BLE001 - message affiché à l'utilisateur
                flash(f"Échec : {exc}", "erreur")
            return redirect(url_for("admin"))
        aff = db.q("SELECT a.user_id, a.classe_id, u.nom||' '||u.prenom AS ens, c.nom AS cl FROM affectations a "
                   "JOIN users u ON u.id=a.user_id JOIN classes c ON c.id=a.classe_id ORDER BY c.nom")
        return render_template("admin.html", users=db.q("SELECT * FROM users ORDER BY nom"),
                               classes=db.q("SELECT * FROM classes WHERE annee=? ORDER BY cours, nom", (config.ANNEE,)),
                               aff=aff)

    # ------------------------------------------------------------------ l'enseignant prend sa classe lui-même (sans attendre le directeur)
    @app.route("/ma-classe", methods=["GET", "POST"])
    @connecte
    def ma_classe():
        """Libre-service : l'enseignant crée sa classe ou prend une classe encore sans titulaire, puis peut en changer.
        Il reste dans son périmètre : une seule classe à la fois, jamais la classe d'un collègue. Le directeur garde la main."""
        if g.user["role"] in ROLES_GESTION:
            return redirect(url_for("admin"))
        mes = list(mes_classes())
        if request.method == "POST":
            a = request.form.get("action", "")
            try:
                if a in ("creer", "prendre") and mes:
                    raise ValueError("Vous avez déjà une classe : utilisez « Changer de classe » pour la quitter d'abord.")
                if a == "creer":
                    if request.form.get("cours") not in corpus.COURS:
                        raise ValueError("Choisissez un cours.")
                    nom = request.form.get("nom", "").strip()
                    if not nom:
                        raise ValueError("Indiquez le nom de la classe.")
                    prec = db.q("SELECT ecole, circonscription FROM classes WHERE annee=? ORDER BY id DESC LIMIT 1", (config.ANNEE,), un=True)
                    cid = db.ex("INSERT INTO classes(nom, cours, ecole, circonscription, effectif, annee) VALUES (?,?,?,?,?,?)",
                                (nom, request.form["cours"], request.form.get("ecole", "").strip() or (prec["ecole"] if prec else ""),
                                 request.form.get("circonscription", "").strip() or (prec["circonscription"] if prec else ""),
                                 int(request.form.get("effectif") or 0), config.ANNEE))
                    db.ex("INSERT OR IGNORE INTO affectations(user_id, classe_id) VALUES (?,?)", (g.user["id"], cid))
                    audit("classe_creee_par_enseignant", nom)
                elif a == "prendre":
                    cid = int(request.form["classe_id"])
                    libre = db.q("SELECT c.id FROM classes c WHERE c.id=? AND c.annee=? AND NOT EXISTS "
                                 "(SELECT 1 FROM affectations x WHERE x.classe_id=c.id)", (cid, config.ANNEE), un=True)
                    if not libre:
                        raise ValueError("Cette classe a déjà un titulaire.")
                    db.ex("INSERT OR IGNORE INTO affectations(user_id, classe_id) VALUES (?,?)", (g.user["id"], cid))
                    audit("classe_prise_par_enseignant", str(cid))
                elif a == "quitter":
                    cid = int(request.form["classe_id"])
                    if cid not in [c["id"] for c in mes]:
                        abort(403)
                    db.ex("DELETE FROM affectations WHERE user_id=? AND classe_id=?", (g.user["id"], cid))
                    audit("classe_quittee_par_enseignant", str(cid))
                flash("Enregistré.", "ok")
            except ValueError as exc:
                flash(str(exc), "erreur")
            return redirect(url_for("ma_classe"))
        libres = [] if mes else db.q("SELECT c.* FROM classes c WHERE c.annee=? AND NOT EXISTS "
                                     "(SELECT 1 FROM affectations x WHERE x.classe_id=c.id) ORDER BY c.cours, c.nom", (config.ANNEE,))
        return render_template("ma_classe.html", mes=mes, libres=libres)

    # ------------------------------------------------------------------ outils de l'enseignant et sécurité
    H = SimpleNamespace(connecte=connecte, gestionnaire=gestionnaire, classe_ou_403=classe_ou_403, ctx_pdf=ctx_pdf,
                        reponse_pdf=reponse_pdf, fiche_ou_404=fiche_ou_404, audit=audit)
    ens.register(app, H)
    securite.register(app, H)

    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(400)
    def _erreur(e):
        return render_template("erreur.html", e=e), e.code

    # ------------------------------------------------------------------ commandes
    @app.cli.command("init-db")
    def _init():
        db.init()
        click.echo("Base initialisée.")

    @app.cli.command("creer-utilisateur")
    @click.argument("identifiant")
    @click.argument("mot_de_passe")
    @click.option("--nom", required=True)
    @click.option("--prenom", default="")
    @click.option("--role", type=click.Choice(["admin", "directeur", "enseignant"]), default="admin")
    def _creer(identifiant, mot_de_passe, nom, prenom, role):
        db.init()
        db.ex("INSERT INTO users(identifiant, nom, prenom, role, mdp_hash) VALUES (?,?,?,?,?)",
              (identifiant.lower(), nom, prenom, role, generate_password_hash(mot_de_passe)))
        click.echo(f"Compte {role} « {identifiant} » créé.")

    return app
