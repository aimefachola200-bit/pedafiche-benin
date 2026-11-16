<p align="center"><img src="pedafiche/web/static/icons/icon-512.png" width="140" alt="Icône PédaFiche Bénin"></p>

# PédaFiche Bénin v2

Application web (Flask + SQLite + ReportLab) de **préparation et de suivi de classe** pour les enseignants du Bénin :
4 382 fiches APC et 2 617 résumés (dont 39 de conjugaison « sans faute » ajoutés) par cours (Maternelle → CM2) issus de SCOLARIS, **progression annuelle** officielle,
**emplois du temps**, **calendrier scolaire 2026-2027** et **évaluations** (sujet, corrigé, grille).

## Ce que fait l'application (v2.2)
| Je prépare | J'enseigne et je suis | J'évalue |
|---|---|---|
| Fiches du corpus (PDF, Word), **Mes fiches** (éditeur, partage), résumés, progression annuelle, emploi du temps, calendrier | **Cahier journal**, **élèves**, **appel et absences**, annonces du directeur | **Carnet de notes**, résultats, rangs, **remédiation**, **bulletins**, sujets et corrigés |

## Ce que garantit l'application
- **Chaque enseignant n'accède qu'à sa classe** (affectation par le directeur ; 403 sinon, y compris pour les fiches d'un autre cours).
- **Son nom en filigrane** (oblique, éclaté) sur chaque page de fiche et d'épreuve ; **le concepteur en bas** : « Conception : … ».
- Fiche sur **une feuille recto-verso au plus** (police réduite automatiquement), « Page x / y ».
- Tout suit la **progression annuelle de SCOLARIS** : mois → SA / unités → fiches → semaine → emploi du temps.
- Les jours de classe suivent le **calendrier officiel** (arrêté du 28 juillet 2026) : 176 jours, 37 semaines.

## Démarrage
```bash
pip install -r requirements.txt
export FLASK_APP=wsgi.py PEDAFICHE_SECRET="une-longue-cle-secrete"
flask creer-utilisateur admin "MotDePasse2026" --nom "DIRECTION" --role admin
python wsgi.py          # http://127.0.0.1:5050  → Administration : créer classes, enseignants, affectations
```
Variables : `PEDAFICHE_DB`, `PEDAFICHE_ANNEE` (2026-2027), `PEDAFICHE_CONCEPTEUR`, `PEDAFICHE_CONCEPTEUR_TEL`.
En ligne : `Dockerfile` et `Procfile` fournis (Render, Railway, VPS). **Servir en HTTPS** (variable `PEDAFICHE_HTTPS=1`) et changer `PEDAFICHE_SECRET`.

## Mettre à jour les données depuis SCOLARIS
```bash
python scripts/importer_scolaris.py chemin/vers/SCOLARIS-2.5.1
```
Régénère `pedafiche/data/` (fiches par cours, progression, emplois du temps, calendrier) et recopie la banque d'épreuves.

## Tests
`pip install -r requirements-dev.txt && python -m pytest -q` (30 tests : accès par classe, CSRF, calendrier, PDF, filigrane, notes, bulletins, blocage de connexion…).

## Limites connues
- La maternelle a ses fiches mais pas de planification mensuelle officielle ni d'évaluations dans la banque.
- Quand la planification ne cite aucun numéro de SA, les fiches sont réparties linéairement sur les mois (indiqué à l'écran).
- Épreuves : « conçues selon l'APC — à valider par le conseiller pédagogique ».
- Pas encore : synchronisation avec SCOLARIS / GESCOL, secondaire, paiements, envoi de SMS aux parents, usage hors ligne (application installable sans serveur).
- Les moyennes sont calculées sur 10 (seuil de passage 5/10, réglable dans `pedafiche/notes.py`) ; les mentions suivent une échelle simple, à adapter à votre école.

## Déploiement
Voir `docs/DEPLOIEMENT_GITHUB.md` (GitHub + Render).

## Ajouter des résumés
`python scripts/generer_resumes_conjugaison.py` régénère la collection « Conjugaison sans faute » (`pedafiche/data/resumes_complements/`). Tout fichier `.json` placé dans ce dossier, au même format que les résumés SCOLARIS, est chargé automatiquement.

## Cahiers de révisions (PDF)
Trois volumes originaux sont générés par des scripts du dossier `scripts/` et fournis prêts à l'emploi dans `docs/ressources/` :

| Volume | Script | Contenu |
|---|---|---|
| 1 | `generer_cahiers_revision.py` | 13 dictées CE2, civisme CM1, récitations CI-CM2 |
| 2 | `generer_cahiers_revision_vol2.py` | maths CI/CP/CM2, français CI/CP/CE1/CM2, grammaire, conjugaison, chants et poèmes |
| 3 | `generer_cahiers_ci_lecture.py` | français CI : 42 leçons de lecture-écriture (règle de décodage vérifiée automatiquement) |

Régénérer : `python scripts/generer_cahiers_revision.py sortie.pdf` (idem pour les autres). Les tests (`pytest`) vérifient la structure des fiches et la règle de décodage du CI.
