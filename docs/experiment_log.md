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
