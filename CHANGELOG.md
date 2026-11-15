# Changelog

Les versions officielles de **silence.** sont publiées sur [GitHub Releases](https://github.com/fanthomas/silence/releases).

## [3.13.0] - 2026-11-15

- Durées fixes : un seul repère sonore à la durée choisie, sans avertissement à 10 minutes.
- Mode Libre : repère répété toutes les 10 minutes sans arrêt automatique ; programmation renouvelée entre deux repères et recalculée après une pause.
- Option obsolète « Repère supplémentaire » retirée et anciennes préférences nettoyées.
- Réglages visuels clarifiés : « Cercle vivant » et « Écran noir après 20 s » compatibles, et distinction explicite avec « Garder l'écran allumé ».
- L'assombrissement fonctionne indépendamment de l'audio et suspend le calcul SVG tant que l'écran est masqué.
- Tests ciblés sur la programmation des sons, les pauses, le mode fixe et l'écran noir.

## [3.12.1] - 2026-11-15

- Sur les téléphones en paysage, l'interface occupe désormais deux colonnes : champ organique à gauche, durées et commandes à droite.
- SVG adapté à la hauteur disponible, contrôles redimensionnés et zones tactiles conservées, sans défilement horizontal.
- Position du champ stable pendant la séance, la pause et la reprise.
- Portrait et affichage ordinateur inchangés.
- Tests responsives ajoutés (480 × 320, 568 × 320, 667 × 375 et 844 × 390), rotation portrait/paysage et transitions des commandes.

## [3.12.0] - 2026-11-15

- Visuel « Orbites dorées vers le silence » validé, adapté en 1200 × 630 et intégré aux aperçus Open Graph et Twitter.
- Identité de partage recentrée sur « silence. », avec « un moment à soi » dans la description et sans séparateur artificiel.
- SVG de l'application enrichi de neuf orbites organiques et de deux voiles lumineux, dont les courbes se déforment réellement.
- Point central fixe (200, 200), avec une très légère pulsation de 7 %, sans mouvement orbital.
- Cohérence visuelle entre l'illustration de partage et le champ vivant, avec respect des animations réduites.
- Sons, minuteries, commandes et mode hors connexion conservés.

## [3.11.1] - 2026-11-15

- Point central, déplacement orbital et cercle statique supprimés : seules les courbes SVG organiques restent visibles.
- Lignes reconstruites en courbes de Bézier périodiques, avec raccord lisse et continu, sans angle à la fermeture.
- Reflets continus via un dégradé progressif animé, sans traits pointillés ni extrémités apparentes.
- Grand halo elliptique horizontal supprimé de l’arrière-plan, sans changer la structure des commandes.
- Durées, sons et animation lente conservés.

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
