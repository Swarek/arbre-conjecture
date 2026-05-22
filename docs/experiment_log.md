# Experiment log

## 2026-05-21 initial setup

- Date/heure : 2026-05-21, Europe/Paris.
- Commit hash : e5f0ec3.
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
- Commit hash : b1a77fd.
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
- Commit hash : 6e497f5.
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
- Commit hash : 7da77f5.
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
- Commit hash : 7da77f5.
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

## 2026-05-22 per-track documentation

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : a51812f.
- Hypothèse testée : le journal chronologique ne suffit pas pour relire
  facilement 50 pistes/tentatives ; il faut un document vivant par piste.
- Changement fait : ajout de `docs/tracks/README.md` et d’un fichier dédié pour
  chaque piste A-F ; liens ajoutés depuis `README.md`,
  `docs/agent_loop_guide.md`, `docs/hypothesis_portfolio.md` et
  `docs/experiment_protocol.md`.
- Commande exécutée : `make quick`.
- Résultat correction : `18 passed in 0.03s`, puis `JUSTE`.
- Résultat benchmark : non applicable, documentation seulement.
- Conclusion : documentation par piste créée et reliée aux points d’entrée
  principaux.
- Next action : maintenir à jour à chaque tentative le fichier de piste
  correspondant et le compteur dans `docs/tracks/README.md`.

## 2026-05-22 source notes and Proposition 4.4

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : 3c12127.
- Hypothèse testée : les PDF fournis doivent être intégrés comme idées et
  références, sans remplacer les tests ni l’oracle.
- Changement fait : ajout de `docs/source_notes.md`; ajout du prédicat
  expérimental `passes_farthest_prop_4_4_condition`; clarification que la
  condition farthest brute précédemment réfutée n’est pas la Proposition 4.4
  complète car elle ignorait la clause dégénérée non stricte.
- Commande exécutée : `make unit`.
- Résultat correction : `21 passed in 0.03s`.
- Commande exécutée : `make quick`.
- Résultat correction : `21 passed in 0.02s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Résultat benchmark : non applicable.
- Conclusion : Proposition 4.4 devient une condition nécessaire documentée et
  testable pour ordre fixé, mais pas un solver d’existence dans PC-tree.
- Next action : tester expérimentalement le couple Proposition 4.4/4.5 comme
  accélérateur de test d’ordre fixé sous quasi-circularité.

## 2026-05-22 vendored source PDFs

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : 89782bf.
- Hypothèse testée : les documents de référence doivent être conservés dans le
  dépôt pour que les notes restent reproductibles même si `~/Downloads` change.
- Changement fait : copie des 6 PDF fournis dans `docs/source_materials/pdfs/`;
  ajout de `docs/source_materials/README.md` avec source originale et SHA-256 ;
  mise à jour de `docs/source_notes.md` pour pointer vers les copies versionnées.
- Commande exécutée : `make quick`.
- Résultat correction : `21 passed in 0.02s`, puis `JUSTE`.
- Résultat benchmark : non applicable, vendoring documentaire.
- Conclusion : les 6 PDF sont maintenant versionnés dans le dépôt avec
  manifeste de provenance et hashes. Le screenshot temporaire n’était plus
  récupérable comme fichier ; son contenu reste documenté dans
  `docs/source_notes.md`.
- Next action : si la capture d’écran Proposition 4.4 est fournie comme fichier
  stable, l’ajouter dans `docs/source_materials/images/`.

## 2026-05-22 Proposition 4.5 fixed-order diagnostic

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : 07120e4.
- Hypothèse testée : sous précondition quasi-circularité d’un ordre fixé,
  l’absence de certificat farthest Proposition 4.5 coïncide avec le prédicat
  exact `is_precircular_order_cR`.
- Changement fait : ajout de `find_farthest_prop_4_5_obstruction` et
  `passes_farthest_prop_4_5_order_test`; ajout de tests unitaires ciblés et
  d’un test exhaustif `n=4` sur les ordres quasi-circulaires.
- Commande exécutée : `make unit`.
- Résultat correction : `24 passed in 0.09s`.
- Commande exécutée : `make quick`.
- Résultat correction : `24 passed in 0.08s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : probe exhaustif local `n <= 5`, valeurs `{1,2,3}`,
  restreint aux ordres quasi-circulaires.
- Résultat correction : 0 désaccord ; `n=5` a vérifié `73272` ordres
  quasi-circulaires.
- Résultat benchmark : non applicable, test d’ordre fixé.
- Conclusion : le diagnostic Prop. 4.5 est une bonne piste pour accélérer le
  test d’un ordre donné et générer des obstructions exactes, mais ne résout pas
  l’existence dans le PC-tree.
- Next action : utiliser ce certificat dans Piste C ou B pour contraindre les
  choix de branches plutôt que de tester les frontiers une par une.

## 2026-05-22 Prop. 4.5 nogood frontier scan

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : f17ad89.
- Hypothèse testée : Prop. 4.5 peut servir de nogood expérimental sur des
  frontiers énumérées, avec rapport explicite des faux positifs/faux négatifs,
  sans changer la candidate générale.
- Changement fait : ajout de `prop45_nogood_frontier_report` et
  `prop45_nogood_frontier_search` dans `sat_like_experiments.py`; ajout de tests
  unitaires Piste C ; mise à jour des docs de piste, obligations et checkpoints.
- Commande exécutée : `make quick` avant modification.
- Résultat correction : `24 passed in 0.09s`, puis `JUSTE`.
- Commande exécutée : `make unit`.
- Résultat correction : première exécution rouge à cause d’une attente de test
  erronée (`729` matrices attendues au lieu de `657` matrices ayant au moins un
  ordre quasi-circulaire) ; correction de l’assertion.
- Commande exécutée : `make unit`.
- Résultat correction : `27 passed in 0.29s`.
- Commande exécutée : probe random bornée `n=6..8`, familles
  `random/block/ultrametric/equal/non_strict/paired_farthest/permuted_cycle`,
  valeurs avec égalités, `40` répétitions par famille, tous les ordres pour
  `n<=7` et `200` ordres échantillonnés pour `n=8`.
- Résultat correction : aucun désaccord ; `173600` couples inspectés, `35068`
  ordres quasi-circulaires testés.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit; 8 tailles,
  0 timeout, 20 runs incomplets explicitement marqués pour `n > 8`; médiane
  `n=20` environ `0.0036s`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Conclusion : Piste C dispose maintenant d’un rapport de nogoods Prop. 4.5
  falsifiable sur frontiers énumérées. Cela reste une expérience, pas un CSP
  compact ni une preuve.
- Next action : implémenter le moteur CSP à domaines locaux sur petits nœuds
  `P/C`, d’abord avec nogoods cR directs, puis comparer à Prop. 4.5 sous
  précondition quasi-circulaire.

## 2026-05-22 local-domain CSP scaffold

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : f7aa62f.
- Hypothèse testée : avant de chercher une compression SAT/CSP, il faut valider
  que des variables locales `P/C` reconstruisent exactement les frontiers et que
  `source="cr"` coïncide avec le filtre cR exact par frontier.
- Changement fait : ajout de `build_local_domains`, `frontier_from_assignment`,
  `iter_local_assignments`, `assignment_frontier_report`,
  `solve_nogood_csp` et `accepted_frontiers_by_csp`; ajout de tests unitaires
  pour reconstruction de frontiers, filtre `source="cr"` et refus `unsupported`
  sur gros `P`.
- Commande exécutée : `make unit`.
- Résultat correction : `31 passed in 0.19s`.
- Commande exécutée : `make quick`.
- Résultat correction : `31 passed in 0.18s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : probe CSP `source="cr"` sur `n=4..7`, arbres
  balanced/mixed, familles `random/cycle/block/ultrametric/equal/non_strict/
  paired_farthest/permuted_cycle`, `25` répétitions par famille.
- Résultat correction : aucun désaccord ; `1600` instances comparées à
  `enumerate_frontiers(T)` filtré par `is_precircular_order_cR`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit; 8 tailles,
  0 timeout, 20 runs incomplets explicitement marqués pour `n > 8`; médiane
  `n=20` environ `0.00433s`.
- Conclusion : la couche de domaines locaux est cohérente sur petits arbres
  supportés. Elle reste une énumération d’affectations, pas encore un solver
  compact.
- Next action : compiler des nogoods de quartets cR sur supports de variables
  et mesurer si le pruning apparaît avant énumération complète.

## 2026-05-22 compiled cR quartet nogoods

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : 53cc4cf.
- Hypothèse testée : les quartets cR interdits peuvent être projetés sur les
  variables locales qui déterminent leur ordre cyclique, sans sur-rejet ni
  sous-rejet sur petits PC-trees supportés.
- Changement fait : ajout de `forbidden_cr_atoms`, `quartet_support_paths`,
  `compile_cr_nogoods` et `solve_compiled_nogood_csp`; ajout de tests pour
  support imbriqué, support affaibli, wrapping circulaire, unsupported gros `P`,
  et égalité avec le CSP cR direct.
- Commande exécutée : `make unit`.
- Résultat correction : `35 passed in 0.20s`.
- Commande exécutée : probe compiled-nogood vs `source="cr"` sur `n=4..7`,
  arbres balanced/mixed, familles `random/cycle/block/ultrametric/equal/
  non_strict/paired_farthest/permuted_cycle`, `15` répétitions par famille.
- Résultat correction : aucun désaccord ; `960` instances comparées,
  `153512` nogoods uniques produits sur la probe.
- Commande exécutée : `make quick`.
- Résultat correction : `35 passed in 0.19s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit; 8 tailles,
  0 timeout, 20 runs incomplets explicitement marqués pour `n > 8`; médiane
  `n=20` environ `0.00360s`.
- Conclusion : les nogoods compilés sont cohérents expérimentalement avec le
  filtre cR direct sur petits arbres supportés, mais la compilation reste
  énumérative et volumineuse.
- Next action : mesurer l’explosion des nogoods et implémenter un backtracking
  qui prune sur signatures partielles avant génération de toutes les frontiers.

## 2026-05-22 pruned nogood backtracking

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : 9346feb.
- Hypothèse testée : les nogoods compilés peuvent pruner des sous-arbres
  d’affectations avant reconstruction de frontier, tout en gardant exactement
  les mêmes frontiers acceptées que le filtre cR direct.
- Changement fait : ajout de `solve_pruned_nogood_csp`, indexation des nogoods
  par dernière variable de support, métriques de branches/feuilles prunées et
  validation optionnelle contre `accepted_frontiers_by_csp(source="cr")`; ajout
  de tests pour un cas avec pruning et un cas sans atoms cR.
- Commande exécutée : `make unit`.
- Résultat correction : `37 passed in 0.22s`.
- Commande exécutée : probe pruned vs cR direct sur `n=4..7`, arbres
  balanced/mixed, familles `random/cycle/block/ultrametric/equal/non_strict/
  paired_farthest/permuted_cycle`, `10` répétitions par famille.
- Résultat correction : aucun désaccord ; `640` instances comparées,
  `4284` branches prunées, `7396` feuilles visitées sur `19200` affectations
  complètes possibles.
- Commande exécutée : `make quick`.
- Résultat correction : `37 passed in 0.21s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit; 8 tailles,
  0 timeout, 20 runs incomplets explicitement marqués pour `n > 8`; médiane
  `n=20` environ `0.00498s`.
- Conclusion : le pruning post-compilation fonctionne expérimentalement et
  réduit les feuilles visitées dans la probe, mais ne résout pas encore le coût
  de compilation des nogoods.
- Next action : ajouter un benchmark interne de compilation/solve pour mesurer
  l’explosion des nogoods par famille et décider si Piste C reste prioritaire.

## 2026-05-22 CSP internal benchmark

- Date/heure : 2026-05-22, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : il faut mesurer séparément compilation, solve pruné et
  filtre direct pour savoir si Piste C reste prometteuse.
- Changement fait : ajout de `tools/pc_csp_internal_benchmark.py`, du target
  `make bench-csp-quick`, et d’un test unitaire minimal du rapport.
- Commande exécutée : `make unit`.
- Résultat correction : `38 passed in 0.22s`.
- Commande exécutée : `make quick`.
- Résultat correction : `38 passed in 0.21s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark : `reports/csp_internal_benchmark_quick.json` écrit ;
  `192` lignes, `0` mismatch, compilation médiane `~0.00104s`, solve pruné
  médian `~0.000285s`, filtre direct médian `~0.000307s`, `31616` nogoods
  uniques, `1280` branches prunées, `2208` feuilles visitées sur `5760`
  affectations possibles.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit; 8 tailles,
  0 timeout, 20 runs incomplets explicitement marqués pour `n > 8`; médiane
  `n=20` environ `0.00360s`.
- Conclusion : Piste C a maintenant un benchmark interne. Le pruning est réel,
  mais la compilation énumérative produit déjà beaucoup de nogoods ; il faut
  décider entre compilation non énumérative, DP, ou sous-cas.
- Next action : produire une décision Piste C vs Piste B/F et tester une
  signature DP/collision avant de raffiner davantage le CSP énumératif.

## 2026-05-23 bad-side fixed-order DP diagnostic

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : pour un ordre circulaire fixé, la condition pre-circular cR
  est équivalente à l'absence d'une paire `{a,b}` ayant un témoin mauvais
  `w` sur chacun des deux arcs, avec
  `max(D[a][w], D[w][b]) > D[a][b]`.
- Changement fait : ajout de `is_bad_witness`,
  `bad_witnesses_by_pair`, `bad_side_signature`,
  `find_bad_side_cr_violation` et `passes_bad_side_cr_test` dans
  `src/pc_circular/solvers/dp_experiments.py`; ajout de
  `tests/test_dp_experiments.py`; mise à jour Piste B, obligations de preuve,
  plans et checkpoints.
- Plan subagents : trois explorateurs lecture seule. Résultats : preuve
  fixed-order confirmée ; aucun contre-exemple trouvé ; risque DP principal
  identifié comme explosion de signature en paires globales ; variante `>=`
  réfutée par les égal-distance.
- Commande exécutée avant modification : `make quick`.
- Résultat correction : `38 passed in 0.22s`, puis `JUSTE`.
- Commande exécutée : `make unit`.
- Résultat correction : `44 passed in 0.49s`.
- Commande exécutée : probe bad-side avec `PYTHONPATH=src`, exhaustif `n=4,5`,
  valeurs `{1,2,3}`, puis random `n=6,7`.
- Résultat correction : `OK checked=715875`, aucun désaccord avec
  `is_precircular_order_cR`.
- Résultat subagent contre-exemples : `926775` comparaisons sur familles
  variées jusqu'à `n=9`, `0` désaccord.
- Commande exécutée : `make quick`.
- Résultat correction : `44 passed in 0.48s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit ; 8 tailles,
  `0` timeout, `20` runs incomplets explicitement marqués pour `n > 8`,
  médiane `n=20` environ `0.00354s`.
- Conclusion : l'invariant bad-side est une réécriture exacte pour ordre fixé et
  un bon point de départ Piste B. Il ne décide pas l'existence dans un PC-tree :
  la signature de sous-arbre compacte reste à tester/falsifier.
- Next action : implémenter `find_signature_collision` ou un rapport
  `#signatures / #frontiers` pour mesurer si la piste DP compacte survit.

## 2026-05-23 block signature collision metrics

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : une signature de sous-frontier orientée fondée sur
  endpoints, masques `inside/external` et masques `inside/inside` peut compacter
  les frontiers sans perdre les interactions bad-side nécessaires à cR.
- Changement fait : ajout de `block_bad_side_signature`,
  `forced_bad_side_pairs_in_block`, `block_signature_bucket_report` et
  `find_signature_collision` dans `src/pc_circular/solvers/dp_experiments.py`;
  les masques `inside/inside` sont relatifs au bord du bloc (`between` /
  `through-boundary`) ; ajout de tests de masques, buckets, collision
  volontairement faible, collision endpoints-only et contexte égal-distance.
- Commande exécutée avant modification : `make quick`.
- Résultat correction : `44 passed in 0.49s`, puis `JUSTE`.
- Commande exécutée : `make unit`.
- Résultat correction : `49 passed in 0.66s`.
- Commande exécutée : probe signature de blocs avec `PYTHONPATH=src`, blocs de
  taille `4,5,6`, univers `n=6,7,8`, familles
  `equal/cycle/block/random/paired_farthest`.
- Résultat correction/complexité : `27` lignes, aucune collision réelle trouvée
  dans les contextes testés. Ratios `#signatures / #frontiers` : `equal`
  descend à `0.0417` pour `k=6`, `block` est partiellement compressé
  (`0.5667..0.8333`), mais `cycle`, `random` et `paired_farthest` sont
  quasi injectifs (`0.95..1.0`) ; beaucoup de frontiers sont déjà forcées
  rejetées.
- Résultat subagents : convention `II` corrigée en `between` /
  `through-boundary`; métriques ajoutées `frontiers_per_signature`,
  `median_bucket_size` et `log2_signature_count`; une collision endpoints-only
  a été transformée en test. Une probe indépendante a trouvé des collisions de
  signature simples mais aucune collision sémantique sur `37924` checks de même
  contexte ; ratios équilibrés `random` `0.936121..1.0` et `paired_farthest`
  `0.949627..1.0`.
- Commande exécutée : `make quick`.
- Résultat correction : `49 passed in 0.47s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit ; 8 tailles,
  `0` timeout, `20` runs incomplets explicitement marqués pour `n > 8`,
  médiane `n=20` environ `0.00352s`.
- Conclusion : la signature candidate est cohérente et falsifiable, mais trop
  fine pour une DP compacte générale. Elle ressemble à une réénumération sur les
  familles stress.
- Next action : ne pas intégrer cette signature dans `candidate.py`. Basculer
  soit vers une signature moins globale/sous-cas borné, soit vers Piste F pour
  formaliser une obstruction de compacité.

## 2026-05-23 universal bad-witness subcase

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : si chaque paire `{a,b}` a au plus un témoin mauvais global
  `w` avec `max(D[a][w], D[w][b]) > D[a][b]`, alors tout ordre circulaire est
  circular Robinson ; l'existence dans un PC-tree non vide se réduit donc à
  produire une frontier représentée.
- Changement fait : ajout de `is_constant_off_diagonal` et
  `has_at_most_one_bad_witness_per_pair` dans `predicates.py`, ajout de
  `sample_frontier` dans `pc_tree.py`, et intégration du solver
  `candidate_universal_bad_witness_bound_all_orders` dans `candidate.py`.
- Plan subagents : deux explorateurs lecture seule. Résultats : preuve du cas
  constant confirmée ; sous-cas plus large `|B(a,b)| <= 1` proposé et intégré ;
  faux amis documentés, notamment une arête basse dans une matrice presque
  constante.
- Commande exécutée avant modification : `make quick`.
- Résultat correction : `49 passed in 0.49s`, puis `JUSTE`.
- Commande exécutée : `make unit`.
- Résultat correction : `58 passed in 0.49s`.
- Commande exécutée : probe large-n avec `PYTHONPATH=src`, arbres
  star/balanced/mixed, tailles `n=9,10,12,20,30`, matrices constantes et
  `constant + une arête haute`.
- Résultat correction : `OK checks=33`; témoins cR, représentés par énumération
  quand borné ou égaux à `sample_frontier` en grande taille ; le faux ami avec
  une arête basse reste hors sous-cas et retombe sur le placeholder incomplet.
- Commande exécutée : `make quick`.
- Résultat correction : `58 passed in 0.49s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE` sur exhaustif `n=4`, `5000` random,
  `max-n=8`, seed `314159`, shrink actif.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit ; 8 tailles,
  `0` timeout, `18` runs incomplets explicitement marqués pour `n > 8`;
  le sous-cas prouvé apparaît sur `n=16` et `n=20` dans le mixed benchmark ;
  médiane `n=20` environ `0.00369s`.
- Conclusion : premier sous-cas large-n prouvé intégré à la candidate. Il
  améliore la complétude sur une famille non stricte, sans prétendre résoudre
  le cas général.
- Next action : chercher un sous-cas plus structuré, par exemple planted-cycle
  représenté par le PC-tree, ou retourner à Piste F pour formaliser les
  obstructions de compacité.

## 2026-05-23 certified sampled positive witnesses

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : une recherche non exhaustive peut néanmoins produire une
  réponse positive complète si elle renvoie un ordre représenté et vérifié cR ;
  seules les réponses négatives après échantillonnage doivent rester
  incomplètes.
- Changement fait : `candidate.py` renvoie maintenant
  `candidate_validated_sampled_witness` avec `complete=True` lorsqu'un ordre
  échantillonné passe `is_precircular_order_cR`. Les résultats négatifs du
  placeholder restent `complete=False`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction : `58 passed in 0.50s`, puis `JUSTE`.
- Commande exécutée : `make unit`.
- Résultat correction : `59 passed in 0.51s`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit ; 8 tailles,
  `0` timeout, `0` run incomplet ; grandes tailles mixed/star via
  `candidate_validated_sampled_witness` ou sous-cas universel.
- Commande exécutée : `make quick`.
- Résultat correction : `59 passed in 0.50s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE` sur exhaustif `n=4`, `5000` random,
  `max-n=8`, seed `314159`, shrink actif.
- Commande exécutée : `make bench`.
- Résultat benchmark : `reports/complexity_report.json` écrit ; tailles jusqu'à
  `n=100`, `0` timeout, `42` runs incomplets visibles ; médiane `n=100`
  environ `2.10s`, fit polynomial empirique `p ~= 3.25`. Les runs incomplets
  sont des réponses négatives du placeholder, pas des faux `False` complets.
- Conclusion : les positifs échantillonnés sont maintenant correctement
  certifiés par témoin. Cela améliore les métriques sans transformer un échec
  d'échantillonnage en preuve de non-existence.
- Next action : lancer gates fortes, puis chercher un sous-cas plus structuré
  ou attaquer les cas négatifs incomplets.

## 2026-05-23 minimum-distance cycle witness

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : pour les instances planted-cycle, le graphe des distances
  minimales positives peut révéler un ordre circulaire témoin. Si cet ordre est
  directement vérifié cR et si la représentation est certaine (`pc_tree` absent
  ou star de feuilles), il fournit un certificat positif complet.
- Changement fait : ajout de `_minimum_distance_cycle_order` et
  `candidate_minimum_distance_cycle_witness` dans `candidate.py`; ajout de
  tests pour `permuted_cycle/star`, exclusion explicite des PC-trees non-star,
  et régression du faux positif `n=6` où le graphe minimum est un cycle simple
  mais l'ordre reconstruit n'est pas circular Robinson. La capture Proposition
  4.4 fournie par l'utilisateur est conservée dans
  `docs/source_materials/images/proposition_4_4_2026-05-22.png`.
- Plan subagents : deux explorateurs lecture seule. Le premier a confirmé que
  la branche ne devait être qu'un certificat positif star/None avec vérification
  cR. Le second a trouvé le contre-exemple `n=6`, transformé en régression.
- Commande exécutée : `shasum -a 256 docs/source_materials/pdfs/*.pdf
  docs/source_materials/images/proposition_4_4_2026-05-22.png`.
- Résultat source : les six PDF versionnés correspondent à l'index, et la
  capture a le hash
  `cef8d6fa5de1065658c45cb5b8072ac77957f9b21d117d4bb758e3bda9c66ad1`.
- Commande exécutée : `make unit`.
- Résultat correction : `62 passed in 0.50s`.
- Commande exécutée : `make quick`.
- Résultat correction : `62 passed in 0.49s`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE` sur exhaustif `n=4`, `5000` random,
  `max-n=8`, seed `314159`, shrink actif.
- Commande exécutée : `make bench-piste-f`.
- Résultat benchmark : `permuted_cycle/star` a `0` timeout et `0` incomplet,
  avec `candidate_minimum_distance_cycle_witness` pour tous les `n > 8`.
  `paired_farthest/star` reste incomplet sur `60` runs grande taille et
  `paired_farthest/mixed` sur `40` runs, sans timeout.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit ; 8 tailles,
  `0` timeout, `0` incomplet. La branche minimum-cycle apparaît dans le mixed
  benchmark à `n=16`, aux côtés du sous-cas universel et des témoins
  échantillonnés validés.
- Commande exécutée : `make bench`.
- Résultat benchmark : `reports/complexity_report.json` écrit ; tailles jusqu'à
  `n=100`, `0` timeout, `42` runs incomplets visibles ; médiane `n=100`
  environ `2.12s`, fit polynomial empirique `p ~= 3.25` (`r2 ~= 0.92`). Les
  incomplets restent des placeholders négatifs, pas des rejets justifiés.
- Conclusion : progrès utile comme certificat positif sur planted-cycle/star.
  Ce n'est pas une caractérisation : le contre-exemple `n=6` interdit d'utiliser
  le graphe minimum-cycle seul, et les PC-trees non-star restent hors périmètre.
- Next action : attaquer les cas négatifs incomplets, en priorité
  `paired_farthest` et les PC-trees non-star, ou chercher un test de
  représentation non énumératif pour promouvoir le témoin cycle au-delà du
  star.
