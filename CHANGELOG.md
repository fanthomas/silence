# Changelog

Les versions officielles de **silence.** sont publiées sur [GitHub Releases](https://github.com/fanthomas/silence/releases).

## [3.11.0] - 2026-11-14

- Illustration fixe remplacée par quatre courbes SVG organiques réellement redessinées en temps réel.
- Anneaux superposés avec déformations sinusoïdales indépendantes et reflets qui parcourent lentement leurs contours.
- Animation cadencée à 30 images par seconde au maximum, arrêtée lorsque l'onglet est masqué, la séance en pause ou la réduction des animations active.
- Géométrie du cercle et emplacement des commandes conservés ; paramètres et trois sons inchangés.
- Suppression de la référence à l'ancien fichier illustratif et mise à jour du cache hors connexion.

## [3.10.0] - 2026-11-14

- Illustration des anneaux et filaments lumineux réellement intégrée au cercle, avec un mouvement très lent de 21 secondes.
- Nouvelle favicon circulaire à fond transparent et icônes PWA assorties, au lieu d'un carré uni.
- Aperçu de partage mis en cohérence avec la nouvelle identité.
- Nouveau son Goutte douce : signal original de 0,36 seconde, sans bruit de fond ni boucle.
- Bol feutré et Bois doux inchangés.

## [3.9.0] - 2026-11-14

- Cercle rendu purement visuel : aucun clic, aucune ouverture du chronomètre et aucune possibilité de le sélectionner au clavier.
- Barre de défilement masquée dès le tout premier rendu, sans saut de mise en page.
- Bol feutré retravaillé par une attaque douce, un filtrage des aigus et une décroissance rapide.
- Oscillation lente du cercle enrichie d'une onde intérieure et d'un petit point mobile qui s'éloigne puis revient au centre, sans changer le cycle de 14 secondes.
- Aperçu Open Graph et Twitter (1200 × 630), titres, descriptions, URL canonique et données structurées.
- Nouvelle favicon contrastée, nouveaux pictogrammes PWA et icône Apple.

## [3.8.0] - 2026-11-14

- Même emplacement et même taille du cercle et du logo avant, pendant et après la séance : espace de commandes stabilisé.
- « silence. » seul visible dès la première image, puis transition douce vers l'en-tête, le cercle apparaissant ensuite.
- Retour silencieux de 2 minutes et bouton « Revenir doucement » supprimés : les durées fixes se terminent directement.
- Pépiement aigu supprimé : Bol feutré et Bois doux conservés sans modification.
- Messages audio hors flux pour éviter les déplacements momentanés au démarrage.
- Tests de stabilité de la géométrie et de l'ouverture renforcés.

## [3.7.1] - 2026-11-14

- Sons de nature simplifiés : un seul pépiement naturel de 0,41 seconde, sans ambiance continue.
- Anciennes ambiances Forêt, Oiseau et Sous-bois retirées du sélecteur.
- Pépiement atténué à la lecture, Bol feutré et Bois doux inchangés.
- Anciennes préférences sonores naturelles automatiquement converties vers Pépiement.
- Cache PWA et tests mis à jour.

## [3.7.0] - 2026-11-14

- Accueil animé : silence. apparaît au centre puis gagne sa place dans l'en-tête.
- Deux petites ondulations du cercle, inspirées des gouttes d'eau, au démarrage.
- Amplitude du cercle augmentée durant la méditation, cycle conservé à 14 secondes.
- Texte visible « En pause » retiré : le bouton Lecture indique la reprise.
- Animation d'accueil ignorée lorsqu'une séance est reprise ou que les animations sont réduites.

## [3.6.0] - 2026-11-14

- Trois nouveaux repères extraits de véritables enregistrements naturels du domaine public : Forêt, Oiseau et Sous-bois.
- Sons courts et fondus, sans boucle musicale.
- Bol feutré et Bois doux conservés à l'identique.
- Cinq choix sonores disponibles aussi hors connexion.
- README simplifié, centré sur l'utilisation.

## [3.5.0] - 2026-11-14

Première version suivie par une release GitHub.

### Expérience
- Mode libre avec repères discrets à 10 minutes et, au choix, à 15 minutes.
- Sessions fixes de 10, 12, 15 et 20 minutes.
- Cercle animé lentement pendant la séance, avec prise en charge de la réduction des animations.
- Commandes Pause, Reprendre et Stop accessibles, avec retour direct à l'accueil.
- Retour silencieux de deux minutes.

### Sons
- Deux choix conservés : Bol feutré et Bois doux (Bambou).
- Réglage du volume et écoute d'aperçu.

### Application
- PWA installable, cache hors connexion et actualisation des fichiers.
- Préférences conservées localement.
- Contrôles automatiques dans Chromium et publication SFTP après validation.

Les versions antérieures à 3.5.0 n'avaient pas de releases GitHub.
