# Changelog

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
