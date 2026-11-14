# Tests de silence.

Les deux suites Playwright vérifient les contrôles, les cinq sons, l'animation, le retour à l'accueil et la gestion de la réduction des animations.

- `test_app_dom.py` : interactions sur le DOM avec le CSS et JavaScript réels.
- `test_app.py` : navigation HTTP, service worker et fonctionnement hors connexion.

Exécuter les tests depuis la racine du dépôt après installation de Python Playwright et Chromium :

```sh
python tests/test_app_dom.py
python tests/test_app.py
```

Chaque modification de `main` déclenche les tests, puis publie automatiquement dans le dossier OVH dédié si tous les contrôles réussissent.
