# Diagnostic IA pour cabinets d’avocats

Site statique de présentation d’une offre en phase de validation.

Le formulaire fonctionne uniquement dans le navigateur : aucune donnée n’est envoyée ni stockée.

## Contenu

- une page d’accueil commerciale ;
- un répertoire de quinze métiers du cabinet ;
- une page sourcée par rôle avec tâches, usages prudents de l’IA et garde-fous.

## Construire et tester

```bash
python3 scripts/build.py
python3 -m unittest tests/test_site.py -v
```

Les fichiers publics sont générés dans `docs/`.

## Publication

GitHub Pages publie la branche `main` depuis le dossier `/docs`.
