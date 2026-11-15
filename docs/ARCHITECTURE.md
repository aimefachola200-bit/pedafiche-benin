# Architecture — PédaFiche Bénin v2

```mermaid
flowchart TB
  subgraph Sources["Sources (SCOLARIS 2.5.1)"]
    C[pedafiche_corpus.json.gz<br/>4 382 fiches, 209 programmes]
    P[m_synoptique.py<br/>planification mensuelle + EDT officiels]
    K[m_calendrier_officiel.py<br/>arrêté 2026-2027]
    B[banque_*.py<br/>organigramme INFRE]
  end
  I[scripts/importer_scolaris.py] --> D[(pedafiche/data<br/>fiches/COURS.json.gz · planification · edt · calendrier)]
  Sources --> I
  subgraph Noyau["Noyau métier (Python pur, testé)"]
    corpus --> progression
    calendrier --> progression
    progression --> edt
    progression --> epreuves
    banque[banque/] --> epreuves
  end
  D --> corpus & calendrier
  subgraph Web["Couche web Flask"]
    auth[Comptes · rôles · CSRF] --> acl[Accès par classe]
    acl --> pages[Pages : semaine, fiches, mes fiches, journal, élèves, appel, notes, bulletins, annonces]
  end
  Noyau --> pages
  pages --> pdf[pdf.py : filigrane titulaire + pied concepteur + Page x/y]
  db[(SQLite : users, classes, affectations, edt_classe, suivi)] --> acl
```

## Flux pédagogique
Calendrier officiel (jours de classe) → planification mensuelle du cours (mois × matière : « U1 », « D1 SA1 », « SA3 Séq 1-4 »)
→ rattachement aux fiches (`progression.correspondances`) → tranche de la semaine → emploi du temps (créneaux × matière) → fiche du jour.
Les évaluations utilisent la même progression « jusqu'à la période » (mensuelle, trimestrielle, passage, CEP blanc).

## Modules web
`web/app.py` (comptes, accès par classe, fiches, progression, EDT, calendrier, évaluations) · `web/ens.py` (mes fiches, cahier journal, élèves, appel, carnet de notes, bulletins, annonces) · `web/securite.py` (blocage, mot de passe, audit, sauvegarde) · `notes.py` (moyennes, rangs, remédiation : Python pur testé) · `docx_export.py` (fiches Word).
Tables SQLite : users, classes, affectations, edt_classe, suivi, mes_fiches, eleves, presences, evals, notes, journal, annonces, annonces_lues, audit, tentatives.

## Sécurité
Mots de passe hachés (Werkzeug), jeton CSRF sur tout POST, cookie HttpOnly/SameSite, accès à une classe vérifié côté serveur
à chaque route (`classe_ou_403`) et fiche contrôlée contre le cours de la classe. Blocage après 5 essais faux, journal d'audit, HTTPS imposé par `PEDAFICHE_HTTPS=1` (cookie Secure + HSTS).
