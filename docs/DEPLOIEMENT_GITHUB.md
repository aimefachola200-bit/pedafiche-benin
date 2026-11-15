# Déployer PédaFiche Bénin : GitHub + hébergement

GitHub **héberge le code** et lance les tests ; il ne peut pas exécuter une application Flask (pas de GitHub Pages pour celle-ci).
Pour la mettre en ligne, on relie le dépôt GitHub à un hébergeur (Render, Railway, VPS).

## 1. Publier sur GitHub depuis Windows (invite de commandes `cmd`)
1. Installer Git : https://git-scm.com/download/win (options par défaut), puis rouvrir `cmd` et vérifier : `git --version`.
2. Se présenter (une fois) :
```
git config --global user.name "Aimé FACHOLA"
git config --global user.email "votre-adresse@exemple.com"
```
3. Créer sur github.com un dépôt **vide** nommé `pedafiche-benin` (privé conseillé : `pedafiche/data/` reprend des contenus officiels).
4. Décompresser le zip, puis dans `cmd` :
```
cd %USERPROFILE%\Documents\pedafiche-benin
git init -b main
git add -A
git commit -m "PedaFiche Benin v2.2.0"
git remote add origin https://github.com/aimefachola200-bit/pedafiche-benin.git
git push -u origin main
```
Une fenêtre du navigateur s'ouvre pour se connecter à GitHub : accepter.
5. Onglet **Actions** du dépôt : les 29 tests se lancent à chaque envoi (pastille verte = tout passe).
6. Étiquette de version :
```
git tag -a v2.2.0 -m "2.2.0"
git push origin v2.2.0
```

### Mises à jour suivantes
Décompresser la nouvelle version dans un dossier temporaire, puis :
```
cd %USERPROFILE%\Documents\pedafiche-benin
robocopy "C:\chemin\vers\nouvelle-version" . /E /XD .git
git add -A
git commit -m "Description du changement"
git push origin main
```

## 2. Mettre en ligne (Render, Docker)
1. render.com → *New → Blueprint* → choisir le dépôt : `render.yaml` crée le service, un disque `/data` (SQLite) et une clé `PEDAFICHE_SECRET`.
2. Ajouter la variable `PEDAFICHE_HTTPS=1` (cookie sécurisé et HSTS).
3. Ouvrir le *Shell* du service et créer le premier compte :
   `FLASK_APP=wsgi.py flask creer-utilisateur admin "<MotDePasse8+>" --nom DIRECTION --role admin`
4. Se connecter, puis *Administration* : classes, enseignants, affectations. Les enseignants ajoutent eux-mêmes leurs élèves (menu « Élèves »).
HTTPS est fourni par l'hébergeur. Chaque `git push` sur `main` redéploie.

## 3. Sauvegarde et mises à jour
- **Sauvegarde** : connecté en administrateur, « Administration » → « Journal d'audit et sauvegarde » → « Télécharger une sauvegarde de la base » (comptes, classes, élèves, notes, absences, journal, fiches personnelles). À faire chaque semaine, et avant chaque mise à jour.
- Restaurer : arrêter le service, remplacer `/data/pedafiche.db` par la sauvegarde, relancer.
- Données pédagogiques : `python scripts/importer_scolaris.py <dossier SCOLARIS>` puis commit et push.
- Changer le concepteur : variables `PEDAFICHE_CONCEPTEUR` et `PEDAFICHE_CONCEPTEUR_TEL`.
- Réglages de sécurité : `PEDAFICHE_MAX_ESSAIS` (5) et `PEDAFICHE_BLOCAGE_MIN` (10).
