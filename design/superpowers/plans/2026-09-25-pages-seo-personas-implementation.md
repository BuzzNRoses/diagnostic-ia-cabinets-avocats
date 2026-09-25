# Plan d’implémentation — Pages SEO par persona

Date : 2026-09-25
Spécification : `design/superpowers/specs/2026-09-24-pages-seo-personas-design.md`

## Objectif

Construire, tester et publier un site statique comprenant un hub `/metiers/`, quinze pages persona documentées, les métadonnées SEO et les fichiers d’indexation, sans interrompre le site actuel avant validation complète de `/docs`.

## Principes d’exécution

- Développement piloté par les tests : chaque comportement commence par un test en échec.
- Python standard uniquement pour le générateur et les tests.
- Contenus métier sourcés ; aucune promesse ou pratique inventée.
- Sortie publique générée dans `/docs`.
- Bascule GitHub Pages seulement après contrôle local complet.

## Tâche 1 — Créer le contrat de contenu et les premiers tests

Fichiers :

- `tests/test_site.py`
- `content/site.json`
- `content/personas/` — initialement vide

Étapes :

1. Écrire les tests du schéma persona, du nombre attendu de quinze fichiers, de l’unicité des slugs/titres/descriptions/pilotes et des champs obligatoires.
2. Exécuter `python3 -m unittest tests/test_site.py -v` et vérifier l’échec dû aux fichiers absents.
3. Créer `content/site.json` et le premier fichier persona minimal.
4. Faire passer uniquement le premier test vertical, puis étendre les tests aux quinze fichiers.

## Tâche 2 — Construire le générateur statique

Fichiers :

- `scripts/build.py`
- `templates/base.html`
- `templates/home.html`
- `templates/hub-metiers.html`
- `templates/persona.html`
- `templates/404.html`

Étapes :

1. Écrire un test qui appelle le générateur et attend `docs/index.html`.
2. Vérifier l’échec en l’absence du générateur.
3. Implémenter le rendu minimal de l’accueil.
4. Ajouter successivement les tests et rendus du hub, d’une persona et de la page 404.
5. Faire échouer le build sur contenu invalide ou source absente.

## Tâche 3 — Mutualiser le design et migrer l’accueil

Fichiers :

- `assets-src/styles.css`
- `assets-src/site.js`
- `templates/home.html`
- `content/site.json`

Étapes :

1. Écrire les tests vérifiant les liens vers les ressources mutualisées et l’absence de CSS/JS inline substantiel.
2. Extraire le design actuel sans modifier son identité visuelle.
3. Conserver le formulaire local et son message de confidentialité.
4. Ajouter l’entrée de navigation « Métiers ».

## Tâche 4 — Rechercher et rédiger les quinze contenus persona

Fichiers : `content/personas/*.json`

Lots parallélisables :

- Lot A — direction et avocats : avocat individuel, associé dirigeant, collaborateur, contentieux, conseil/transactionnel.
- Lot B — production et support : élève-avocat/stagiaire, secrétaire/assistant juridique, office manager/assistant de direction, documentaliste/knowledge manager, DPO/conformité.
- Lot C — gestion et développement : RAF, facturation/recouvrement, RH/recrutement, communication/business development, référent informatique/DSI.

Pour chaque persona :

1. Identifier au moins une source métier crédible et les sources transversales utiles.
2. Distinguer responsabilités, frictions, assistance, automatisation sous conditions et exclusions.
3. Fournir un pilote limité et des questions de diagnostic uniques.
4. Ajouter deux à quatre personas connexes.
5. Exécuter les tests d’unicité et de complétude après chaque lot.
6. Relire le ton pour supprimer les formulations génériques et les promesses implicites.

## Tâche 5 — Créer le hub, le maillage et les données structurées

Fichiers :

- `templates/hub-metiers.html`
- `templates/persona.html`
- `scripts/build.py`

Étapes :

1. Tester la présence des quinze liens depuis le hub.
2. Tester deux à quatre liens connexes valides par persona.
3. Générer les fils d’Ariane visibles.
4. Générer `WebPage` et `BreadcrumbList` sans faux balisage `Person`, avis ou FAQ.

## Tâche 6 — Générer les fichiers SEO et vérifier les pages

Fichiers :

- `docs/sitemap.xml`
- `docs/robots.txt`
- `docs/404.html`

Étapes :

1. Tester la correspondance exacte entre le sitemap et les pages canoniques.
2. Tester l’unicité des titres, descriptions et URL canoniques.
3. Tester tous les liens internes et ressources locales.
4. Vérifier l’absence de `fetch`, `XMLHttpRequest`, `sendBeacon`, analytics ou ressources externes non autorisées.

## Tâche 7 — Vérifications visuelles et fonctionnelles

1. Lancer un serveur HTTP local sur `/docs`.
2. Vérifier sur ordinateur et mobile : accueil, hub, trois personas de familles différentes et 404.
3. Tester la navigation clavier, le focus visible, les débordements et le formulaire.
4. Parcourir programmatiquement toutes les URL du sitemap.
5. Corriger les défauts puis relancer l’intégralité des tests.

## Tâche 8 — Revue de code et contrôle éditorial

1. Exécuter `git diff --check`.
2. Vérifier qu’aucun CSV, fichier du vault, note de recherche temporaire ou secret n’est suivi.
3. Effectuer une revue sécurité, accessibilité, maintenabilité et anti-contenu répétitif.
4. Vérifier les quinze pages individuellement contre la spécification.

## Tâche 9 — Publication sans interruption

1. Committer la version complète.
2. Pousser la branche `main`.
3. Vérifier que le commit distant correspond au commit local.
4. Modifier GitHub Pages de `main:/` vers `main:/docs`.
5. Attendre le statut de build `built`.
6. Vérifier toutes les URL du sitemap en HTTP 200 et les métadonnées publiques.
7. En cas d’échec, remettre temporairement la source Pages sur `main:/`.

## Commandes de validation finales

```bash
python3 -m unittest tests/test_site.py -v
python3 scripts/build.py --check
python3 scripts/build.py
python3 -m unittest tests/test_site.py -v
git diff --check
git status --short
```

La publication n’est considérée terminée qu’après validation du site public et du formulaire dans un navigateur réel.
