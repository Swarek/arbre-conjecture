# Experiment log

## 2026-05-21 initial setup

- Date/heure : 2026-05-21, Europe/Paris.
- Commit hash : pending until checkpoint commit is created.
- Hypothèse testée : une baseline brute force exacte sur petites tailles peut
  servir de harnais initial sans prétendre résoudre le problème général.
- Changement fait : création du dépôt, de l’oracle exact, des générateurs, de la
  candidate baseline, des gates de correction et du benchmark JSON.
- Commande exécutée : `make unit`.
- Résultat correction : `11 passed in 0.01s`.
- Commande exécutée : `make quick`.
- Résultat correction : `11 passed in 0.01s`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : rapport écrit dans
  `reports/complexity_report_quick.json`; 8 tailles, 0 timeout, 20 runs
  incomplets marqués sur les tailles `n > 8`; dernière médiane observée
  `n=20`: environ `0.00354s`.
- Conclusion : setup initial utilisable. La candidate reste une baseline exacte
  seulement pour `n <= 8` et incomplète au-delà.
- Next action : remplacer le placeholder grande taille par une première piste
  algorithmique mesurable, probablement Piste A ou E.

## 2026-05-21 agent guide

- Date/heure : 2026-05-21, Europe/Paris.
- Commit hash : pending until checkpoint commit is created.
- Hypothèse testée : un guide explicite réduit le risque qu’un agent futur
  confonde quick benchmark, benchmark fort et preuve.
- Changement fait : ajout de `docs/agent_loop_guide.md`; références ajoutées
  dans `README.md` et `AGENTS.md`.
- Commande exécutée : `make quick`.
- Résultat correction : `11 passed in 0.01s`, puis `JUSTE`.
- Résultat benchmark : non applicable, changement documentation seulement.
- Conclusion : guide ajouté sans modifier le comportement du solver ni des
  outils.
- Next action : utiliser le guide pour lancer une première piste algorithmique.

## 2026-05-22 Goal operating model

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : pending until checkpoint commit is created.
- Hypothèse testée : avant de démarrer le Goal algorithmique, le dépôt doit
  forcer une méthode contre-exemple-first et permettre l’exploration parallèle
  de plusieurs pistes.
- Changement fait : ajout d’un target `make hunt-counterexamples`; durcissement
  de `AGENTS.md`, `PLANS.md`, `README.md`, `docs/agent_loop_guide.md` et
  `docs/experiment_protocol.md` avec mode Goal, fanout jusqu’à 5 subagents et
  recherche active de contre-exemples.
- Commande exécutée : `make quick`.
- Résultat correction : `11 passed in 0.01s`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE` sur exhaustif `n=4`, `5000` random,
  `max-n=8`, seed `314159`, shrink actif.
- Résultat benchmark : non applicable, changement de protocole et Makefile.
- Conclusion : protocole Goal renforcé et target de chasse aux contre-exemples
  validé sur la baseline actuelle.
- Next action : lancer le Goal en assignant 4 à 5 pistes indépendantes, dont au
  moins une dédiée uniquement aux contre-exemples.

## 2026-05-22 farthest-crossing counterexamples

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : pending until checkpoint commit is created.
- Hypothèse testée : la condition de croisement farthest-neighbor brute pourrait
  servir de filtre local fort pour guider un solver.
- Changement fait : ajout de diagnostics `find_precircular_cR_violation` et
  `find_farthest_crossing_violation`; ajout de
  `classify_order_obstructions` et `measure_obstruction_support`; ajout de trois
  contre-exemples minimaux dans `tests/test_regression_counterexamples.py`;
  ajout de tests de projection d’obstructions sur PC-tree; mise à jour des
  obligations de preuve et du portefeuille.
- Commande exécutée : `make unit`.
- Résultat correction : `15 passed in 0.06s`.
- Commande exécutée : `make quick`.
- Résultat correction : `18 passed in 0.02s`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Résultat benchmark : non applicable, pas de changement de candidate.
- Conclusion : la condition farthest-crossing brute n’est ni nécessaire en cas
  non strict, ni suffisante même avec distances hors diagonale toutes
  distinctes. Elle reste utile comme diagnostic, pas comme décision. La
  prochaine piste doit utiliser les quadruplets cR exacts, soit comme
  obstructions CSP, soit comme état DP à falsifier.
- Next action : chercher quelles contraintes supplémentaires expliquent le
  contre-exemple strict, ou basculer vers une formulation CSP/DP.

## 2026-05-22 Piste F benchmark families

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : pending until checkpoint commit is created.
- Hypothèse testée : il faut séparer un sous-cas planted-cycle probablement
  facile d’une famille hard-looking à appariements farthest pour éviter de
  sur-optimiser `mixed`.
- Changement fait : ajout des générateurs explicites `permuted_cycle` et
  `paired_farthest`; ajout de diagnostics exacts `--diagnostics-up-to` dans le
  benchmark; ajout du target `make bench-piste-f`; tests unitaires dédiés.
- Commande exécutée : `make unit`.
- Résultat correction : `18 passed in 0.03s`.
- Commande exécutée : `make bench-piste-f`.
- Résultat benchmark : 3 rapports écrits, 0 timeout. `permuted_cycle/star` :
  `n=8` a `1/2520` ordre cR valide et `24/2520` ordres farthest-pass.
  `paired_farthest/star` : `n=8` a `12/2520` ordres cR valides et `24/2520`
  ordres farthest-pass. `paired_farthest/mixed` : aucun ordre cR valide dans
  les échantillons diagnostiqués `n=4,6,8`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit; 8 tailles,
  0 timeout, 20 runs incomplets explicitement marqués pour `n > 8`; médiane
  `n=20` environ `0.00354s`.
- Conclusion : Piste F dispose maintenant d’un sous-cas planted-cycle et d’une
  famille rare/hard-looking qui expose des faux positifs farthest. Ces familles
  sont explicites et ne polluent pas `mixed`.
- Next action : utiliser `paired_farthest` pour casser les futurs filtres
  locaux, et `permuted_cycle` pour tester la reconnaissance d’un témoin caché.
