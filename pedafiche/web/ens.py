"""Outils de l'enseignant : mes fiches, cahier journal, élèves, appel, carnet de notes, bulletins, annonces."""
from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime, timedelta

from flask import abort, flash, g, redirect, render_template, request, url_for

from .. import calendrier, config, corpus, db, docx_export, notes as N, pdf, progression, xlsx_io as X

CHAMPS_FICHE = (("cd", "Compétence disciplinaire"), ("ct", "Compétences transversales"),
                ("contenus", "Contenus / connaissances"), ("strategies", "Stratégies"),
                ("materiel", "Matériel / supports"), ("objectifs", "Objectifs"),
                ("activite_preliminaire", "Activité préliminaire"))
FIN_FICHE = (("evaluation", "Évaluation"), ("projection", "Projection"), ("je_retiens", "Je retiens"))
PHASES = ("INTRODUCTION", "RÉALISATION", "RETOUR ET PROJECTION")
STATUTS = (("P", "Présent"), ("A", "Absent"), ("R", "Retard"))
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _nombre(txt):
    txt = (txt or "").strip().replace(",", ".")
    if txt == "":
        return None
    return float(txt)


def _maintenant() -> str:
    return datetime.now().isoformat(timespec="seconds")


def register(app, H):
    classe_ou_403, connecte, gestionnaire = H.classe_ou_403, H.connecte, H.gestionnaire

    # ---------------------------------------------------------------- utilitaires
    def eleves_de(cid):
        return [dict(r) for r in db.q("SELECT * FROM eleves WHERE classe_id=? AND actif=1 ORDER BY nom, prenom", (cid,))]

    def maj_effectif(cid):
        n = db.q("SELECT COUNT(*) n FROM eleves WHERE classe_id=? AND actif=1", (cid,), un=True)["n"]
        db.ex("UPDATE classes SET effectif=? WHERE id=?", (n, cid))

    def pdf_ou_docx(d, nom):
        r = app.response_class(d, mimetype=DOCX)
        r.headers["Content-Disposition"] = f'attachment; filename="{nom}"'
        return r

    # ================================================================ MES FICHES
    def fiche_perso_ou_403(mid):
        r = db.q("SELECT * FROM mes_fiches WHERE id=?", (mid,), un=True)
        if not r:
            abort(404)
        if r["user_id"] != g.user["id"] and g.user["role"] not in ("admin", "directeur"):
            abort(403)
        return r

    def fiche_depuis_ligne(r) -> dict:
        f = json.loads(r["contenu"])
        f.update(id=f"perso-{r['id']}", cours=r["cours"], matiere=r["matiere"], titre=r["titre"])
        return f

    def fiche_depuis_formulaire(c, base=None) -> dict:
        form = request.form
        titre = form.get("titre", "").strip()
        if not titre:
            raise ValueError("Le titre de la fiche est obligatoire.")
        mat = form.get("matiere", "")
        if mat not in corpus.LIB_MAT:
            raise ValueError("Matière inconnue.")
        f = {k: form.get(k, "").strip() for k, _ in CHAMPS_FICHE + FIN_FICHE}
        f.update(titre=titre, matiere=mat, cours=c["cours"], sous_matiere=form.get("sous_matiere", "").strip(),
                 unite=form.get("unite", "").strip(), intitule=form.get("intitule", "").strip(),
                 duree=form.get("duree", "").strip(), sa=form.get("sa", "").strip() or None,
                 seance=form.get("seance", "").strip() or None,
                 mention="Fiche personnelle de l'enseignant — à valider par le conseiller pédagogique.")
        f["deroulement"] = [[f"**{ph}**", form.get(f"cons{i}", "").strip(), form.get(f"res{i}", "").strip()]
                            for i, ph in enumerate(PHASES)]
        return f

    def formulaire_fiche(c, f, action, mid=None):
        return render_template("fiche_edit.html", c=c, f=f, champs=CHAMPS_FICHE, fin=FIN_FICHE, phases=PHASES,
                               mats=list(corpus.LIB_MAT), action=action, mid=mid)

    @app.route("/classe/<int:cid>/mes-fiches")
    @connecte
    def mes_fiches(cid):
        c = classe_ou_403(cid)
        miennes = db.q("SELECT * FROM mes_fiches WHERE user_id=? AND cours=? ORDER BY maj DESC", (g.user["id"], c["cours"]))
        partagees = db.q("SELECT m.*, u.nom||' '||u.prenom AS auteur FROM mes_fiches m JOIN users u ON u.id=m.user_id "
                         "WHERE m.partage=1 AND m.cours=? AND m.user_id<>? ORDER BY m.maj DESC LIMIT 100",
                         (c["cours"], g.user["id"]))
        return render_template("mes_fiches.html", c=c, miennes=miennes, partagees=partagees)

    @app.route("/classe/<int:cid>/mes-fiches/nouvelle", methods=["GET", "POST"])
    @connecte
    def fiche_nouvelle(cid):
        c = classe_ou_403(cid)
        if request.method == "POST":
            try:
                f = fiche_depuis_formulaire(c)
            except ValueError as e:
                flash(str(e), "erreur")
                return redirect(url_for("fiche_nouvelle", cid=cid))
            mid = db.ex("INSERT INTO mes_fiches(user_id, classe_id, cours, base_id, titre, matiere, contenu, cree, maj) "
                        "VALUES (?,?,?,?,?,?,?,?,?)", (g.user["id"], cid, c["cours"], request.form.get("base", ""),
                                                       f["titre"], f["matiere"], json.dumps(f, ensure_ascii=False),
                                                       _maintenant(), _maintenant()))
            flash("Fiche enregistrée dans « Mes fiches ».", "ok")
            return redirect(url_for("fiche_perso", cid=cid, mid=mid))
        base = corpus.fiche(request.args.get("base", ""))
        if base and base["cours"] != c["cours"]:
            abort(404)
        f = dict(base) if base else {"matiere": corpus.matieres_du_cours(c["cours"])[0] if corpus.matieres_du_cours(c["cours"]) else "francais",
                                     "deroulement": [[f"**{p}**", "", ""] for p in PHASES]}
        if base:
            f["titre"] = f["titre"] + " (adaptée)"
        return formulaire_fiche(c, f, url_for("fiche_nouvelle", cid=cid))

    @app.route("/classe/<int:cid>/mes-fiches/<int:mid>", methods=["GET", "POST"])
    @connecte
    def fiche_perso(cid, mid):
        c = classe_ou_403(cid)
        r = fiche_perso_ou_403(mid)
        if r["cours"] != c["cours"]:
            abort(404)
        if request.method == "POST":
            try:
                f = fiche_depuis_formulaire(c)
            except ValueError as e:
                flash(str(e), "erreur")
                return redirect(url_for("fiche_perso", cid=cid, mid=mid))
            db.ex("UPDATE mes_fiches SET titre=?, matiere=?, contenu=?, maj=? WHERE id=?",
                  (f["titre"], f["matiere"], json.dumps(f, ensure_ascii=False), _maintenant(), mid))
            flash("Fiche mise à jour.", "ok")
            return redirect(url_for("fiche_perso", cid=cid, mid=mid))
        return formulaire_fiche(c, fiche_depuis_ligne(r), url_for("fiche_perso", cid=cid, mid=mid), mid)

    @app.route("/classe/<int:cid>/mes-fiches/<int:mid>/<action>", methods=["POST"])
    @connecte
    def fiche_perso_action(cid, mid, action):
        c = classe_ou_403(cid)
        r = fiche_perso_ou_403(mid) if action != "copier" else db.q("SELECT * FROM mes_fiches WHERE id=?", (mid,), un=True)
        if not r:
            abort(404)
        if action == "supprimer":
            db.ex("DELETE FROM mes_fiches WHERE id=?", (mid,))
            flash("Fiche supprimée.", "ok")
        elif action == "partager":
            db.ex("UPDATE mes_fiches SET partage=1-partage WHERE id=?", (mid,))
            flash("Partage modifié : les collègues du même cours " + ("voient" if not r["partage"] else "ne voient plus") + " cette fiche.", "ok")
        elif action == "dupliquer":
            db.ex("INSERT INTO mes_fiches(user_id, classe_id, cours, base_id, titre, matiere, contenu, cree, maj) "
                  "VALUES (?,?,?,?,?,?,?,?,?)", (g.user["id"], cid, r["cours"], r["base_id"], r["titre"] + " (copie)",
                                                 r["matiere"], r["contenu"], _maintenant(), _maintenant()))
            flash("Fiche dupliquée.", "ok")
        elif action == "copier":
            if not r["partage"] or r["cours"] != c["cours"]:
                abort(403)
            db.ex("INSERT INTO mes_fiches(user_id, classe_id, cours, base_id, titre, matiere, contenu, cree, maj) "
                  "VALUES (?,?,?,?,?,?,?,?,?)", (g.user["id"], cid, r["cours"], r["base_id"], r["titre"],
                                                 r["matiere"], r["contenu"], _maintenant(), _maintenant()))
            flash("Fiche copiée dans « Mes fiches ».", "ok")
        else:
            abort(404)
        return redirect(url_for("mes_fiches", cid=cid))

    @app.route("/classe/<int:cid>/mes-fiches/<int:mid>.<fmt>")
    @connecte
    def fiche_perso_export(cid, mid, fmt):
        c = classe_ou_403(cid)
        r = db.q("SELECT * FROM mes_fiches WHERE id=?", (mid,), un=True)
        if not r or r["cours"] != c["cours"] or (r["user_id"] != g.user["id"] and not r["partage"]
                                                 and g.user["role"] not in ("admin", "directeur")):
            abort(404)
        f = fiche_depuis_ligne(r)
        if fmt == "pdf":
            return H.reponse_pdf(pdf.fiche_pdf(f, H.ctx_pdf(c)), f"fiche_perso_{mid}.pdf")
        if fmt == "docx":
            return pdf_ou_docx(docx_export.fiche_docx(f, H.ctx_pdf(c)), f"fiche_perso_{mid}.docx")
        abort(404)

    @app.route("/classe/<int:cid>/fiche/<fid>.docx")
    @connecte
    def fiche_docx(cid, fid):
        c = classe_ou_403(cid)
        f = H.fiche_ou_404(c, fid)
        return pdf_ou_docx(docx_export.fiche_docx(f, H.ctx_pdf(c)), f"fiche_{fid}.docx")

    # ================================================================ CAHIER JOURNAL
    def plage():
        try:
            du = date.fromisoformat(request.args.get("du", ""))
        except ValueError:
            j = date.today()
            du = j - timedelta(days=j.weekday())
        try:
            au = date.fromisoformat(request.args.get("au", ""))
        except ValueError:
            au = du + timedelta(days=4)
        return du, au

    def lignes_journal(cid, du, au):
        return db.q("SELECT * FROM journal WHERE classe_id=? AND jour BETWEEN ? AND ? ORDER BY jour, creneau, id",
                    (cid, du.isoformat(), au.isoformat()))

    @app.route("/classe/<int:cid>/journal", methods=["GET", "POST"])
    @connecte
    def journal(cid):
        c = classe_ou_403(cid)
        if request.method == "POST":
            a = request.form.get("action")
            if a == "ajouter":
                titre = request.form.get("titre", "").strip()
                try:
                    jour = date.fromisoformat(request.form.get("jour", "")).isoformat()
                except ValueError:
                    flash("Date invalide.", "erreur")
                    return redirect(url_for("journal", cid=cid))
                if not titre:
                    flash("Indiquez la leçon ou l'activité.", "erreur")
                    return redirect(url_for("journal", cid=cid))
                realise = request.form.get("realise", "oui")
                db.ex("INSERT INTO journal(classe_id, jour, creneau, matiere, titre, fiche_id, realise, observation) "
                      "VALUES (?,?,?,?,?,?,?,?)",
                      (cid, jour, request.form.get("creneau", "")[:30], request.form.get("matiere", "")[:20], titre[:200],
                       request.form.get("fiche_id", "")[:80], realise if realise in ("oui", "partiel", "non") else "oui",
                       request.form.get("observation", "")[:500]))
                flash("Ajouté au cahier journal.", "ok")
            elif a == "supprimer":
                db.ex("DELETE FROM journal WHERE id=? AND classe_id=?", (int(request.form.get("id", 0)), cid))
            return redirect(request.referrer or url_for("journal", cid=cid))
        du, au = plage()
        lignes = lignes_journal(cid, du, au)
        par_jour: dict = {}
        for l in lignes:
            par_jour.setdefault(l["jour"], []).append(l)
        return render_template("journal.html", c=c, du=du, au=au, par_jour=par_jour, n=len(lignes),
                               prec=du - timedelta(days=7), suiv=du + timedelta(days=7),
                               mats=corpus.LIB_MAT, aujourdhui=date.today())

    @app.route("/classe/<int:cid>/journal.pdf")
    @connecte
    def journal_pdf(cid):
        c = classe_ou_403(cid)
        du, au = plage()
        lignes = [[date.fromisoformat(l["jour"]).strftime("%d/%m/%Y"), l["creneau"], corpus.LIB_MAT.get(l["matiere"], l["matiere"]),
                   l["titre"], {"oui": "Réalisée", "partiel": "Partielle", "non": "Non réalisée"}[l["realise"]], l["observation"]]
                  for l in lignes_journal(cid, du, au)] or [["", "", "", "Aucune entrée sur la période.", "", ""]]
        return H.reponse_pdf(pdf.tableau_pdf(
            f"CAHIER JOURNAL — {c['nom']}", f"{c['ecole']} · du {du.strftime('%d/%m/%Y')} au {au.strftime('%d/%m/%Y')}",
            ["Date", "Horaire", "Matière", "Leçon / activité", "Réalisation", "Observation"], lignes,
            [1.2, 1.1, 1.6, 4, 1.3, 3], H.ctx_pdf(c), 8.5), f"journal_{cid}_{du.isoformat()}.pdf")

    # ================================================================ ÉLÈVES
    def lire_csv(texte: str) -> list[dict]:
        texte = texte.lstrip("﻿")
        if not texte.strip():
            return []
        delim = ";" if texte.split("\n")[0].count(";") >= texte.split("\n")[0].count(",") else ","
        lignes = [l for l in csv.reader(io.StringIO(texte), delimiter=delim) if any(x.strip() for x in l)]
        cles = ("nom", "prenom", "sexe", "naissance", "matricule", "tuteur", "telephone")
        if lignes and lignes[0] and lignes[0][0].strip().lower() in ("nom", "noms", "name"):
            lignes = lignes[1:]
        out = []
        for l in lignes:
            d = {k: (l[i].strip() if i < len(l) else "") for i, k in enumerate(cles)}
            d["sexe"] = d["sexe"].upper()[:1] if d["sexe"].upper()[:1] in ("M", "F") else ""
            if d["nom"]:
                out.append(d)
        return out

    @app.route("/classe/<int:cid>/eleves", methods=["GET", "POST"])
    @connecte
    def eleves(cid):
        c = classe_ou_403(cid)
        if request.method == "POST":
            a = request.form.get("action")
            if a == "ajouter":
                nom = request.form.get("nom", "").strip()
                if not nom:
                    flash("Le nom est obligatoire.", "erreur")
                else:
                    sexe = request.form.get("sexe", "")
                    db.ex("INSERT INTO eleves(classe_id, matricule, nom, prenom, sexe, naissance, tuteur, telephone) VALUES (?,?,?,?,?,?,?,?)",
                          (cid, request.form.get("matricule", "").strip(), nom.upper(), request.form.get("prenom", "").strip(),
                           sexe if sexe in ("M", "F") else "", request.form.get("naissance", "").strip(),
                           request.form.get("tuteur", "").strip(), request.form.get("telephone", "").strip()))
                    flash("Élève ajouté.", "ok")
            elif a == "importer":
                f = request.files.get("fichier")
                texte = request.form.get("texte", "")
                lignes = None
                if f and f.filename and f.filename.lower().endswith((".xlsx", ".xlsm")):
                    try:
                        lignes, err_x = X.lire_eleves(f.read(3_000_000), c["cours"])
                    except ImportError:
                        lignes, err_x = [], "Le composant Excel (openpyxl) n'est pas installé."
                    if err_x:
                        flash(err_x, "erreur")
                elif f and f.filename:
                    brut = f.read(1_000_000)
                    try:
                        texte = brut.decode("utf-8-sig")
                    except UnicodeDecodeError:
                        texte = brut.decode("latin-1")
                if lignes is None:
                    lignes = lire_csv(texte)
                if not lignes:
                    flash("Aucun élève trouvé. Utilisez le modèle Excel (Nom, Prénoms, Sexe, Date de naissance…) ou le format CSV : nom;prénom;sexe;naissance;matricule;tuteur;téléphone.", "erreur")
                else:
                    deja = {(e["nom"].upper(), e["prenom"].lower()) for e in eleves_de(cid)}
                    n = 0
                    for d in lignes:
                        if (d["nom"].upper(), d["prenom"].lower()) in deja:
                            continue
                        db.ex("INSERT INTO eleves(classe_id, matricule, nom, prenom, sexe, naissance, tuteur, telephone) VALUES (?,?,?,?,?,?,?,?)",
                              (cid, d["matricule"], d["nom"].upper(), d["prenom"], d["sexe"], d["naissance"], d["tuteur"], d["telephone"]))
                        deja.add((d["nom"].upper(), d["prenom"].lower()))
                        n += 1
                    flash(f"{n} élève(s) importé(s) ({len(lignes) - n} déjà présent(s)).", "ok")
            elif a == "retirer":
                db.ex("UPDATE eleves SET actif=0 WHERE id=? AND classe_id=?", (int(request.form.get("id", 0)), cid))
                H.audit("eleve_retire", f"classe {cid}")
                flash("Élève retiré de la classe (ses notes et ses absences sont conservées).", "ok")
            maj_effectif(cid)
            return redirect(url_for("eleves", cid=cid))
        return render_template("eleves.html", c=c, liste=eleves_de(cid))

    @app.route("/classe/<int:cid>/eleves.pdf")
    @connecte
    def eleves_pdf(cid):
        c = classe_ou_403(cid)
        ls = eleves_de(cid)
        lignes = [[str(i), e["matricule"], f"{e['nom']} {e['prenom']}", e["sexe"], e["naissance"], e["tuteur"], e["telephone"]]
                  for i, e in enumerate(ls, 1)]
        g_n = sum(1 for e in ls if e["sexe"] == "M")
        f_n = sum(1 for e in ls if e["sexe"] == "F")
        return H.reponse_pdf(pdf.tableau_pdf(
            f"LISTE DES ÉLÈVES — {c['nom']}", f"{c['ecole']} · {len(ls)} élèves (G : {g_n} · F : {f_n}) · Année {config.ANNEE}",
            ["N°", "Matricule", "Nom et prénoms", "Sexe", "Naissance", "Parent / tuteur", "Téléphone"], lignes,
            [0.6, 1.4, 4, 0.7, 1.4, 2.6, 1.6], H.ctx_pdf(c), 9), f"eleves_{cid}.pdf")

    MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def reponse_xlsx(octets, nom):
        r = app.response_class(octets, mimetype=MIME_XLSX)
        r.headers["Content-Disposition"] = f'attachment; filename="{nom}"'
        return r

    @app.route("/classe/<int:cid>/eleves-modele.xlsx")
    @connecte
    def eleves_modele_xlsx(cid):
        c = classe_ou_403(cid)
        try:
            return reponse_xlsx(X.modele_eleves(c["cours"], eleves_de(cid)), f"eleves_{c['cours']}_{cid}.xlsx")
        except ImportError:
            flash("Le composant Excel (openpyxl) n'est pas installé.", "erreur")
            return redirect(url_for("eleves", cid=cid))

    @app.route("/modele-eleves.csv")
    @connecte
    def modele_eleves():
        r = app.response_class("nom;prenom;sexe;naissance;matricule;tuteur;telephone\nADJOVI;Koffi;M;12/03/2017;;ADJOVI Paul;0196000000\n",
                               mimetype="text/csv; charset=utf-8")
        r.headers["Content-Disposition"] = 'attachment; filename="modele-eleves.csv"'
        return r

    # ================================================================ APPEL / ABSENCES
    @app.route("/classe/<int:cid>/appel", methods=["GET", "POST"])
    @connecte
    def appel(cid):
        c = classe_ou_403(cid)
        try:
            jour = date.fromisoformat(request.values.get("jour", ""))
        except ValueError:
            jour = date.today()
        els = eleves_de(cid)
        if request.method == "POST":
            if jour > date.today():
                flash("Impossible de faire l'appel d'un jour à venir.", "erreur")
                return redirect(url_for("appel", cid=cid, jour=jour.isoformat()))
            for e in els:
                s = request.form.get(f"s{e['id']}", "P")
                if s not in ("P", "A", "R"):
                    s = "P"
                db.ex("INSERT INTO presences(eleve_id, jour, statut, justifie, motif) VALUES (?,?,?,?,?) "
                      "ON CONFLICT(eleve_id, jour) DO UPDATE SET statut=excluded.statut, justifie=excluded.justifie, motif=excluded.motif",
                      (e["id"], jour.isoformat(), s, 1 if (s != "P" and request.form.get(f"j{e['id']}")) else 0,
                       request.form.get(f"m{e['id']}", "")[:120]))
            flash(f"Appel du {jour.strftime('%d/%m/%Y')} enregistré.", "ok")
            return redirect(url_for("appel", cid=cid, jour=jour.isoformat()))
        deja = {r["eleve_id"]: r for r in db.q("SELECT * FROM presences WHERE jour=? AND eleve_id IN (SELECT id FROM eleves WHERE classe_id=?)",
                                               (jour.isoformat(), cid))}
        return render_template("appel.html", c=c, jour=jour, liste=els, deja=deja, statuts=STATUTS,
                               est_classe=calendrier.est_jour_classe(jour), evts=calendrier.evenements_du_jour(jour),
                               prec=jour - timedelta(days=1), suiv=jour + timedelta(days=1), aujourdhui=date.today())

    def bilan(cid, du, au):
        els = eleves_de(cid)
        lignes = [dict(r) for r in db.q("SELECT p.* FROM presences p JOIN eleves e ON e.id=p.eleve_id WHERE e.classe_id=? "
                                        "AND p.jour BETWEEN ? AND ?", (cid, du, au))]
        b = {x["eleve_id"]: x for x in N.bilan_presences(lignes)}
        return els, b, N.decrocheurs(list(b.values()), 3)

    def periode_absences():
        a = int(config.ANNEE[:4])
        return request.args.get("du", f"{a}-09-01"), request.args.get("au", f"{a + 1}-07-31")

    @app.route("/classe/<int:cid>/absences")
    @connecte
    def absences(cid):
        c = classe_ou_403(cid)
        du, au = periode_absences()
        els, b, alertes = bilan(cid, du, au)
        return render_template("absences.html", c=c, liste=els, b=b, alertes=set(alertes), du=du, au=au)

    @app.route("/classe/<int:cid>/absences.pdf")
    @connecte
    def absences_pdf(cid):
        c = classe_ou_403(cid)
        du, au = periode_absences()
        els, b, alertes = bilan(cid, du, au)
        lignes = [[str(i), f"{e['nom']} {e['prenom']}", str(b.get(e["id"], {}).get("A", 0)),
                   str(b.get(e["id"], {}).get("A_nj", 0)), str(b.get(e["id"], {}).get("R", 0)),
                   "À contacter" if e["id"] in alertes else ""] for i, e in enumerate(els, 1)]
        return H.reponse_pdf(pdf.tableau_pdf(f"BILAN DES ABSENCES — {c['nom']}", f"Du {du} au {au}",
                                             ["N°", "Nom et prénoms", "Absences", "Non justifiées", "Retards", "Alerte"],
                                             lignes, [0.6, 4.5, 1.4, 1.8, 1.4, 2], H.ctx_pdf(c), 9), f"absences_{cid}.pdf")

    # ================================================================ CARNET DE NOTES
    def evaluation_ou_404(cid, eid):
        e = db.q("SELECT * FROM evals WHERE id=? AND classe_id=?", (eid, cid), un=True)
        if not e:
            abort(404)
        return e

    def toutes_notes(cid):
        return {(r["eval_id"], r["eleve_id"]): r["valeur"] for r in
                db.q("SELECT n.* FROM notes n JOIN evals e ON e.id=n.eval_id WHERE e.classe_id=?", (cid,))}

    @app.route("/classe/<int:cid>/notes", methods=["GET", "POST"])
    @connecte
    def notes(cid):
        c = classe_ou_403(cid)
        if request.method == "POST":
            try:
                titre = request.form["titre"].strip()
                mat = request.form["matiere"]
                bareme = _nombre(request.form.get("bareme", "20")) or 20
                coef = _nombre(request.form.get("coef", "1")) or 1
                jour = date.fromisoformat(request.form["jour"]).isoformat()
                per = request.form.get("periode", "T1")
                if not titre or mat not in corpus.LIB_MAT or per not in ("T1", "T2", "T3") or bareme <= 0 or coef <= 0:
                    raise ValueError
            except (ValueError, KeyError):
                flash("Évaluation incomplète ou invalide (titre, matière, date, barème > 0).", "erreur")
                return redirect(url_for("notes", cid=cid))
            eid = db.ex("INSERT INTO evals(classe_id, titre, matiere, jour, bareme, periode, coef) VALUES (?,?,?,?,?,?,?)",
                        (cid, titre[:120], mat, jour, bareme, per, coef))
            return redirect(url_for("saisie_notes", cid=cid, eid=eid))
        evs = db.q("SELECT e.*, (SELECT COUNT(*) FROM notes n WHERE n.eval_id=e.id AND n.valeur IS NOT NULL) AS saisies "
                   "FROM evals e WHERE classe_id=? ORDER BY jour DESC, id DESC", (cid,))
        return render_template("notes.html", c=c, evs=evs, mats=corpus.LIB_MAT, periodes=N.PERIODES,
                               n_eleves=len(eleves_de(cid)), aujourdhui=date.today(),
                               matieres_cours=corpus.matieres_du_cours(c["cours"]))

    @app.route("/classe/<int:cid>/notes/<int:eid>", methods=["GET", "POST"])
    @connecte
    def saisie_notes(cid, eid):
        c = classe_ou_403(cid)
        ev = evaluation_ou_404(cid, eid)
        els = eleves_de(cid)
        if request.method == "POST":
            if request.form.get("action") == "supprimer":
                db.ex("DELETE FROM evals WHERE id=?", (eid,))
                flash("Évaluation supprimée.", "ok")
                return redirect(url_for("notes", cid=cid))
            erreurs = []
            for e in els:
                brut = request.form.get(f"n{e['id']}", "")
                try:
                    v = _nombre(brut)
                except ValueError:
                    erreurs.append(f"{e['nom']} : « {brut} » n'est pas un nombre")
                    continue
                if v is not None and not 0 <= v <= ev["bareme"]:
                    erreurs.append(f"{e['nom']} : la note doit être comprise entre 0 et {ev['bareme']:g}")
                    continue
                db.ex("INSERT INTO notes(eval_id, eleve_id, valeur) VALUES (?,?,?) "
                      "ON CONFLICT(eval_id, eleve_id) DO UPDATE SET valeur=excluded.valeur", (eid, e["id"], v))
            if erreurs:
                flash("Notes non enregistrées pour : " + " ; ".join(erreurs[:5]), "erreur")
            else:
                flash("Notes enregistrées.", "ok")
            return redirect(url_for("saisie_notes", cid=cid, eid=eid))
        nn = toutes_notes(cid)
        return render_template("saisie_notes.html", c=c, ev=ev, liste=els, nn=nn,
                               remed=N.a_remedier(els, dict(ev), nn))

    @app.route("/classe/<int:cid>/notes/<int:eid>/modele.xlsx")
    @connecte
    def notes_modele_xlsx(cid, eid):
        classe_ou_403(cid)
        ev = evaluation_ou_404(cid, eid)
        nn = toutes_notes(cid)
        els = eleves_de(cid)
        try:
            return reponse_xlsx(X.modele_notes(els, dict(ev), {e["id"]: nn.get((eid, e["id"])) for e in els},
                                               corpus.LIB_MAT.get(ev["matiere"], ev["matiere"])), f"notes_{eid}.xlsx")
        except ImportError:
            flash("Le composant Excel (openpyxl) n'est pas installé.", "erreur")
            return redirect(url_for("saisie_notes", cid=cid, eid=eid))

    @app.route("/classe/<int:cid>/notes/<int:eid>/importer", methods=["POST"])
    @connecte
    def notes_importer_xlsx(cid, eid):
        classe_ou_403(cid)
        ev = evaluation_ou_404(cid, eid)
        f = request.files.get("fichier")
        if not f or not f.filename or not f.filename.lower().endswith((".xlsx", ".xlsm")):
            flash("Choisissez le fichier de notes Excel (.xlsx).", "erreur")
            return redirect(url_for("saisie_notes", cid=cid, eid=eid))
        try:
            res, msg = X.lire_notes(f.read(3_000_000), eleves_de(cid), dict(ev), ev["matiere"])
        except ImportError:
            res, msg = {}, ["Le composant Excel (openpyxl) n'est pas installé."]
        for el_id, v in res.items():
            db.ex("INSERT INTO notes(eval_id, eleve_id, valeur) VALUES (?,?,?) "
                  "ON CONFLICT(eval_id, eleve_id) DO UPDATE SET valeur=excluded.valeur", (eid, el_id, v))
        if res:
            H.audit("notes_import_xlsx", f"évaluation {eid} : {len(res)} note(s)")
        flash(f"{len(res)} note(s) importée(s)." + (" À vérifier : " + " ; ".join(msg[:5]) if msg else ""), "ok" if res and not msg else "erreur")
        return redirect(url_for("saisie_notes", cid=cid, eid=eid))

    @app.route("/classe/<int:cid>/notes/<int:eid>/remediation.pdf")
    @connecte
    def remediation_pdf(cid, eid):
        c = classe_ou_403(cid)
        ev = evaluation_ou_404(cid, eid)
        r = N.a_remedier(eleves_de(cid), dict(ev), toutes_notes(cid))
        lignes = [[str(i), f"{x['eleve']['nom']} {x['eleve']['prenom']}", f"{x['note20']:g} / 20", ""] for i, x in enumerate(r, 1)]
        return H.reponse_pdf(pdf.tableau_pdf(
            f"REMÉDIATION — {ev['titre']}", f"{c['nom']} · {corpus.LIB_MAT.get(ev['matiere'], ev['matiere'])} · élèves sous {N.SEUIL:g}/20",
            ["N°", "Nom et prénoms", "Note", "Difficultés repérées / activité de remédiation"], lignes or [["", "Aucun élève sous le seuil.", "", ""]],
            [0.6, 4, 1.4, 6], H.ctx_pdf(c), 9), f"remediation_{eid}.pdf")

    def resultats_classe(cid, periode):
        els = eleves_de(cid)
        evs = [dict(e) for e in db.q("SELECT * FROM evals WHERE classe_id=?", (cid,))]
        return N.resultats(els, evs, toutes_notes(cid), periode or None)

    def periode_demandee():
        p = request.args.get("periode", "")
        return p if p in ("T1", "T2", "T3") else ""

    @app.route("/classe/<int:cid>/resultats")
    @connecte
    def resultats(cid):
        c = classe_ou_403(cid)
        per = periode_demandee()
        return render_template("resultats.html", c=c, res=resultats_classe(cid, per), per=per, periodes=N.PERIODES,
                               LM=corpus.LIB_MAT, seuil=N.SEUIL)

    @app.route("/classe/<int:cid>/resultats.pdf")
    @connecte
    def resultats_pdf(cid):
        c = classe_ou_403(cid)
        per = periode_demandee()
        res = resultats_classe(cid, per)
        mats = res["matieres"]
        lignes = [[str(l["rang"] or ""), f"{l['eleve']['nom']} {l['eleve']['prenom']}"]
                  + ["" if l["par_matiere"][m] is None else f"{l['par_matiere'][m]:g}" for m in mats]
                  + ["" if l["moyenne"] is None else f"{l['moyenne']:g}", l["appreciation"]]
                  for l in sorted(res["lignes"], key=lambda x: (x["rang"] is None, x["rang"] or 0, x["eleve"]["nom"]))]
        s = res["stats"]
        lib = dict(N.PERIODES).get(per, "Année")
        sous = (f"{c['ecole']} · {lib} · moyenne de la classe : {s['moyenne'] if s['moyenne'] is not None else '—'}/20 · "
                f"taux de réussite : {s['taux_reussite'] if s['taux_reussite'] is not None else '—'} %")
        return H.reponse_pdf(pdf.tableau_pdf(
            f"RÉSULTATS — {c['nom']}", sous, ["Rang", "Nom et prénoms"] + [corpus.LIB_MAT.get(m, m) for m in mats] + ["Moyenne", "Appréciation"],
            lignes or [["", "Aucune note saisie", *([""] * (len(mats) + 2))]], [0.8, 3.6] + [1.3] * len(mats) + [1.3, 2], H.ctx_pdf(c), 8),
            f"resultats_{cid}.pdf")

    def bulletin_story(c, res, l, per):
        n_abs = db.q("SELECT COUNT(*) n FROM presences WHERE eleve_id=? AND statut='A'", (l["eleve"]["id"],), un=True)["n"]
        n_nj = db.q("SELECT COUNT(*) n FROM presences WHERE eleve_id=? AND statut='A' AND justifie=0", (l["eleve"]["id"],), un=True)["n"]
        lignes = [[corpus.LIB_MAT.get(m, m), "—" if l["par_matiere"][m] is None else f"{l['par_matiere'][m]:g} / 20",
                   N.appreciation(l["par_matiere"][m])] for m in res["matieres"]]
        lignes.append(["MOYENNE GÉNÉRALE", "—" if l["moyenne"] is None else f"{l['moyenne']:g} / 20", l["appreciation"]])
        lignes.append(["Rang", f"{l['rang']} / {res['stats']['classes']}" if l["rang"] else "—",
                       f"Moyenne de la classe : {res['stats']['moyenne'] if res['stats']['moyenne'] is not None else '—'} / 20"])
        lignes.append(["Absences", f"{n_abs} (dont {n_nj} non justifiées)", ""])
        return lignes

    @app.route("/classe/<int:cid>/bulletin/<int:eleve_id>.pdf")
    @connecte
    def bulletin_pdf(cid, eleve_id):
        c = classe_ou_403(cid)
        per = periode_demandee()
        res = resultats_classe(cid, per)
        l = next((x for x in res["lignes"] if x["eleve"]["id"] == eleve_id), None)
        if not l:
            abort(404)
        lib = dict(N.PERIODES).get(per, "Année scolaire")
        e = l["eleve"]
        return H.reponse_pdf(pdf.tableau_pdf(
            f"BULLETIN — {e['nom']} {e['prenom']}", f"{c['nom']} · {c['ecole']} · {lib} {config.ANNEE}",
            ["Matière", "Moyenne", "Appréciation"], bulletin_story(c, res, l, per), [4, 3, 5], H.ctx_pdf(c), 11),
            f"bulletin_{eleve_id}.pdf")

    @app.route("/classe/<int:cid>/bulletins.pdf")
    @connecte
    def bulletins_pdf(cid):
        from pypdf import PdfReader, PdfWriter
        c = classe_ou_403(cid)
        per = periode_demandee()
        res = resultats_classe(cid, per)
        if not res["lignes"]:
            abort(404, "Aucun élève dans la classe.")
        lib = dict(N.PERIODES).get(per, "Année scolaire")
        w = PdfWriter()
        for l in res["lignes"]:
            e = l["eleve"]
            d = pdf.tableau_pdf(f"BULLETIN — {e['nom']} {e['prenom']}", f"{c['nom']} · {c['ecole']} · {lib} {config.ANNEE}",
                                ["Matière", "Moyenne", "Appréciation"], bulletin_story(c, res, l, per), [4, 3, 5], H.ctx_pdf(c), 11)
            for p in PdfReader(io.BytesIO(d)).pages:
                w.add_page(p)
        buf = io.BytesIO()
        w.write(buf)
        return H.reponse_pdf(buf.getvalue(), f"bulletins_{cid}.pdf")

    # ================================================================ ANNONCES
    @app.route("/annonces", methods=["GET", "POST"])
    @connecte
    def annonces():
        if request.method == "POST":
            a = request.form.get("action")
            if a == "publier":
                if g.user["role"] not in ("admin", "directeur"):
                    abort(403)
                t, corps = request.form.get("titre", "").strip(), request.form.get("corps", "").strip()
                if not t or not corps:
                    flash("Titre et message obligatoires.", "erreur")
                else:
                    db.ex("INSERT INTO annonces(auteur_id, titre, corps, cree) VALUES (?,?,?,?)",
                          (g.user["id"], t[:150], corps[:4000], _maintenant()))
                    flash("Annonce publiée.", "ok")
            elif a == "lu":
                db.ex("INSERT OR IGNORE INTO annonces_lues(annonce_id, user_id, lu) VALUES (?,?,?)",
                      (int(request.form.get("id", 0)), g.user["id"], _maintenant()))
            elif a == "supprimer":
                if g.user["role"] not in ("admin", "directeur"):
                    abort(403)
                db.ex("DELETE FROM annonces WHERE id=?", (int(request.form.get("id", 0)),))
            return redirect(url_for("annonces"))
        liste = db.q("SELECT a.*, u.nom||' '||u.prenom AS auteur, "
                     "(SELECT COUNT(*) FROM annonces_lues l WHERE l.annonce_id=a.id) AS nb_lus, "
                     "EXISTS(SELECT 1 FROM annonces_lues l WHERE l.annonce_id=a.id AND l.user_id=?) AS lue "
                     "FROM annonces a JOIN users u ON u.id=a.auteur_id ORDER BY a.cree DESC LIMIT 100", (g.user["id"],))
        n_ens = db.q("SELECT COUNT(*) n FROM users WHERE actif=1 AND role='enseignant'", un=True)["n"]
        return render_template("annonces.html", liste=liste, n_ens=n_ens)

    # ================================================================ TAUX DE RÉALISATION (accueil)
    def taux_realisation(c):
        """Fiches de la semaine en cours (selon la progression) déjà marquées comme réalisées."""
        sugg = progression.fiches_de_la_semaine(c["cours"], date.today())
        ids = [f["id"] for liste in sugg.values() for f in liste]
        if not ids:
            return None
        faites = {r["fiche_id"] for r in db.q("SELECT fiche_id FROM suivi WHERE classe_id=?", (c["id"],))}
        n = sum(1 for i in ids if i in faites)
        return {"mois": "Cette semaine", "prevues": len(ids), "faites": n, "taux": round(100 * n / len(ids))}

    H.taux_realisation = taux_realisation
