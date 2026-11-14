# Tests de silence.

Les deux suites Playwright vérifient les contrôles, les deux sons, l'animation, le retour à l'accueil et la gestion de la réduction des animations.

- `test_app_dom.py` : interactions sur le DOM avec le CSS et JavaScript réels.
- `test_app.py` : navigation HTTP, service worker et fonctionnement hors connexion.

Exécuter les tests depuis la racine du dépôt après installation de Python Playwright et Chromium :

```sh
python tests/test_app_dom.py
python tests/test_app.py
```

La publication SFTP est désactivée tant que la variable `OVH_DEPLOY_ENABLED` n'est pas définie sur `true`.
