# Changelog

## 2.5.2
- Français CE2 : 143 nouvelles fiches et leurs résumés (unités 1 à 12) pour les séances de la planification officielle qui n'avaient pas de fiche, avec le contenu du manuel « Je lis tout seul » ; 35 fiches renumérotées d'après la planification (unité, SA continue, séance = rang dans la semaine). Fiches à valider par le conseiller pédagogique.
- Fiches importées de GESCOL/SCOLARIS 2.9.5.

## 2.5.1
- Notes sur 20 comme dans GESCOL et SCOLARIS : barème par défaut 20, moyenne de passage 10/20, appréciations adaptées ; les évaluations déjà saisies sur un autre barème restent correctement converties.
- Excel : modèle officiel des élèves (le même que GESCOL/SCOLARIS) à télécharger et à importer ; feuille de notes Excel par évaluation, à télécharger et à importer.
- Fiches et résumés de GESCOL/SCOLARIS 2.9.3 (36 nouvelles fiches d'Éducation sociale et d'EPS) et modèles Excel officiels importés par le workflow « Importer les fiches de SCOLARIS ».

## 2.5.0
- Interface : menu latéral (tableau de menus) comme les autres applications ; sur téléphone et tablette, bouton « ☰ » ; menu de la classe ouverte avec toutes ses rubriques.
- Identifiant et mot de passe comme les applications enseignant de GESCOL et SCOLARIS : même règle de mot de passe (8 caractères, lettres et chiffres, pas trop simple, sans l'identifiant), nom et prénoms demandés, identifiant modifiable dans « Mon compte ».
- Nouvelles fiches et résumés de GESCOL/SCOLARIS (importés : CM2, CE1, CP).

## 2.4.1
- EPS CP : les fiches officielles des SA 10 à 13 (jeux de corde ; tâche sans contact corporel ; s'opposer à un adversaire sans objet ; jouer seul contre plusieurs adversaires), 19 séances, remplacent les versions conçues ; la SA 13 est ajoutée et la SA 4 est complétée (séances 4 et 5, conçues selon l'APC, à valider par le conseiller pédagogique).

## 2.4.0
- L'enseignant prend sa classe lui-même (menu « Ma classe ») : il crée sa classe ou prend une classe sans titulaire, sans attendre l'attribution du directeur. Il change de classe quand il le souhaite, mais reste dans son périmètre : une classe à la fois, jamais celle d'un collègue. Le directeur garde la main pour les affectations particulières.

## 2.3.0
- Installation SANS Internet : installateur Windows (PedaFiche-Installation.exe) et application Android autonome (PedaFiche.apk, téléphone et tablette), fabriqués par GitHub Actions (onglet Actions, étiquette `v2.3.0`) et publiés sur la page Releases.
- Premier lancement : création du compte directeur/enseignant sur l'appareil, données et sauvegardes locales.

## 2.2.0
Application réorganisée autour du travail quotidien de l'enseignant : préparer, enseigner, suivre, évaluer.
- **Préparer ma fiche** : éditeur de fiche (vierge ou « Adapter pour ma classe » à partir d'une fiche du corpus), « Mes fiches » (modifier, dupliquer, supprimer), partage avec les collègues du même cours et copie d'une fiche partagée. Export **PDF** (filigrane du titulaire) et **Word**, y compris pour les fiches du corpus.
- **Cahier journal** : leçons faites par jour (réalisée, partielle, non réalisée), alimenté automatiquement quand on marque une fiche comme réalisée, impression PDF.
- **Élèves de la classe** : ajout, import CSV (modèle fourni), liste de classe PDF, effectif mis à jour.
- **Appel et absences** : appel quotidien (présent, absent, retard, justifié, motif), refus des dates futures, bilan par période, alerte à 3 absences non justifiées, PDF.
- **Carnet de notes** : évaluations (barème, coefficient, trimestre), saisie avec contrôle, moyennes sur 10, rangs avec ex æquo, appréciation, taux de réussite, **remédiation** (élèves sous 5/10, PDF), résultats de la classe et **bulletins** individuels ou en lot (PDF).
- **Annonces du directeur** avec accusé de lecture et compteur de non lues.
- **Accueil** : fiches de la semaine déjà réalisées (jauge).
- **Sécurité** : blocage après 5 essais faux (10 minutes), changement de mot de passe, réinitialisation et désactivation de compte par le directeur, **journal d'audit**, **sauvegarde téléchargeable** de la base (administrateur), cookie « Secure » et HSTS avec `PEDAFICHE_HTTPS=1`.
- **Application installable** (ordinateur, téléphone, tablette) : manifeste et service worker ; seuls les fichiers de présentation sont gardés, jamais les données de l'école.
- 30 tests (17 existants + 13 nouveaux). Nouvelle dépendance : `python-docx`.

## 2.1.0
- Ajout des résumés (2 617, dont 39 de conjugaison « sans faute »), de la banque d'épreuves et des cahiers de révisions (volumes 1 à 3).
- Icône bleu nuit (le vert du drapeau ressort), thème de l'application harmonisé.
- Guide de déploiement GitHub + Render.

## 2.0.0
- Application Flask : accès par classe, filigrane du titulaire, concepteur en pied, progression annuelle, emplois du temps, calendrier scolaire, évaluations.
