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

## 2026-05-23 non-enumerative PC-tree membership for witnesses

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : pour un ordre fixé, le scaffold PC-tree P/C/leaf permet un
  test de représentation exact sans énumérer toutes les frontiers, en parsant
  récursivement des blocs contigus d'enfants. Ce test peut certifier les
  témoins positifs minimum-cycle hors star.
- Changement fait : `represents_order` utilise maintenant un parseur exact
  non énumératif quand `limit is None`, tout en gardant l'ancien diagnostic
  borné si `limit` est fourni. `candidate.py` utilise ce test pour accepter
  `candidate_minimum_distance_cycle_witness` avec PC-tree non-star, et teste la
  représentation avant `is_precircular_order_cR` quand un PC-tree est fourni.
  `make bench-piste-f` ajoute un rapport `cycle/mixed`.
- Plan subagents : trois explorateurs lecture seule. Résultats : invariant
  membership confirmé par induction ; risque clé des rotations internes de `C`
  transformé en test ; contre-exemple `n=6` ajouté où le min-cycle est cR mais
  non représenté et l'oracle PC-tree répond `False`; mesure `permuted_cycle`
  balanced/mixed : hits très rares au-delà de `n=10`.
- Commande exécutée : `make unit`.
- Résultat correction : `70 passed in 0.55s`.
- Commande exécutée : probe membership avec `PYTHONPATH=src`, comparaison à
  `enumerate_frontiers` sur star/balanced `C/P/mixed` jusqu'à `n <= 8`, puis
  grands `cycle/mixed` et `paired_farthest`.
- Résultat correction : `OK checks 11837`; aucun désaccord membership, témoins
  `cycle/mixed` représentés et cR pour `n=10,14,20,40,80`.
- Résultat subagent benchmark : sur `permuted_cycle_metric`, seeds `0..999`,
  balanced/mixed représentent le cycle minimum pour `3/1000` seeds à `n=9`,
  `1/1000` à `n=10`, puis `0/1000` de `n=12` à `80`.
- Commande exécutée : `make quick`.
- Résultat correction : `70 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE` sur exhaustif `n=4`, `5000` random,
  `max-n=8`, seed `314159`, shrink actif.
- Commande exécutée : `make bench-piste-f`.
- Résultat benchmark : `reports/complexity_cycle_mixed.json` ajouté ;
  `cycle/mixed` et `permuted_cycle/star` ont `0` timeout et `0` incomplet, avec
  `candidate_minimum_distance_cycle_witness` pour tous les `n > 8`.
  `paired_farthest/star` reste incomplet sur `60` runs grande taille et
  `paired_farthest/mixed` sur `40` runs, sans timeout.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit ; 8 tailles,
  `0` timeout, `0` incomplet.
- Commande exécutée : `make bench`.
- Résultat benchmark : `reports/complexity_report.json` écrit ; tailles jusqu'à
  `n=100`, `0` timeout, `42` runs incomplets visibles ; médiane `n=100`
  environ `2.12s`, fit polynomial empirique `p ~= 3.25` (`r2 ~= 0.92`).
- Conclusion : extension sûre comme certificat positif d'ordre représenté dans
  le scaffold. Elle ne prouve aucun rejet et ne résout pas les cas où le cycle
  minimum n'est pas représenté ou n'existe pas.
- Next action : attaquer `paired_farthest` ou chercher une contrainte
  structurelle qui génère un ordre candidat représenté, pas seulement qui teste
  un ordre déjà connu.

## 2026-05-23 paired-farthest structural witness

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : une matrice three-level où les arêtes maximales forment un
  matching, les arêtes minimales forment deux cliques de même taille et un
  neutre éventuel, admet un témoin cR construit en plaçant une clique puis ses
  mates dans le même ordre.
- Changement fait : ajout de `_paired_farthest_order` et
  `candidate_paired_farthest_matching_witness` dans `candidate.py`. La branche
  est ignorée quand `quasi_orders` est fourni ; avec `pc_tree`, elle vérifie
  `represents_order` avant de retourner un positif. Tests ajoutés pour grandes
  tailles star, neutre impair, perturbation d'une clique low, non-contournement
  de `quasi_orders`, petites instances seeded, et contre-exemple PC-tree non
  représenté.
- Plan subagents : trois explorateurs lecture seule. Résultats : formule
  constructive confirmée par bad-side ; aucun faux positif cR trouvé pour le
  détecteur strict ; contre-exemple minimal `n=4` fourni si le garde
  `represents_order` est absent ; sur balanced/mixed, beaucoup de témoins cR ne
  sont pas représentés.
- Commande exécutée : `make unit`.
- Résultat correction : `75 passed in 0.55s`.
- Commande exécutée : probe `paired_farthest` avec `PYTHONPATH=src`, tailles
  `9,10,11,12,20,40,80,100`, seeds `0..9`, plus balanced/mixed et random.
- Résultat correction/complexité : `OK checks 380`; solver
  `candidate_paired_farthest_matching_witness` sur `paired_farthest/star`
  jusqu'à `n=100`; temps observé `n=100` environ `0.0056s`.
- Commande exécutée : `make quick`.
- Résultat correction : `75 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE` sur exhaustif `n=4`, `5000` random,
  `max-n=8`, seed `314159`, shrink actif.
- Commande exécutée : `make bench-piste-f`.
- Résultat benchmark : `paired_farthest/star` passe à `0` timeout et `0`
  incomplet ; `candidate_paired_farthest_matching_witness` est utilisé pour
  tous les `n > 8`. `paired_farthest/mixed` garde `40` incomplets grande taille
  car le témoin reconstruit n'est pas représenté par ces PC-trees.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit ; 8 tailles,
  `0` timeout, `0` incomplet.
- Commande exécutée : `make bench`.
- Résultat benchmark : `reports/complexity_report.json` écrit ; tailles jusqu'à
  `n=100`, `0` timeout, `42` runs incomplets visibles ; médiane `n=100`
  environ `2.14s`, fit polynomial empirique `p ~= 3.24` (`r2 ~= 0.92`). Le
  benchmark mixed/star ne contient pas `paired_farthest`, donc les incomplets
  sont inchangés.
- Conclusion : sous-cas positif large-n prouvé et utile pour la famille stress
  star. Il ne donne pas de rejet et ne résout pas paired-farthest non-star.
- Next action : attaquer la représentation non-star de paired-farthest ou
  basculer vers une piste A/C qui construit un ordre représenté sous contraintes
  plutôt que seulement un témoin canonique.

## 2026-05-23 paired-farthest non-star counterexamples

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : pour `paired_farthest` avec PC-tree non-star, le témoin
  canonique `A, mate(A)` peut être insuffisant ; une génération d'ordres dérivée
  des frontiers représentées ou des contraintes high-cross pourrait révéler les
  positifs manqués.
- Changement fait : ajout de deux régressions dans
  `tests/test_regression_counterexamples.py` : un cas `n=6 seed=1` où le témoin
  canonique paired-farthest est non représenté mais un autre ordre représenté
  est cR, et un cas `n=6 seed=21` où la condition brute de croisement farthest
  passe mais cR échoue. Mise à jour des pistes A/B/C/F, obligations de preuve,
  plans et checkpoints.
- Sources : les six PDF fournis et la capture Proposition 4.4 sont déjà
  conservés dans `docs/source_materials/` ; hashes vérifiés contre
  `docs/source_materials/README.md`.
- Plan subagents : cinq explorateurs lecture seule. Résultats : Piste A
  confirme que les projections `I_x(v)` sont utiles comme diagnostic mais non
  décisives ; Piste B réfute des signatures compactées agrégées ; Piste C
  teste un repair positive-only sans gain grande taille ; Piste E/F shrinke les
  cas paired-farthest non-star ; sources confirme les obligations autour
  Prop. 4.4/4.5, strict et circular-ones.
- Commande exécutée avant modification : `make quick`.
- Résultat correction : `75 passed in 0.52s`, puis `JUSTE`.
- Probe locale : génération naïve d'ordres side-by-side depuis rotations de
  frontiers représentées récupère tous les positifs oracle observés sur
  `paired_farthest` `n=6/8`, mais devient trop coûteuse sans borne. Version
  bornée : `n=10` hit `1/10`, puis `0` hit sur `n=12..40`, avec médiane temps
  jusqu'à `~0.25s` à `n=40` pour seulement `16` candidats.
- Résultat subagent E/F : sur seeds `0..999`, `balanced` et `mixed` donnent
  les mêmes counts dans le scaffold fanout 2. `n=6` : `202` canoniques
  représentés, `96` positifs oracle non canoniques, `702` oracle `False`.
  `n=8` : `36`, `20`, `944`. `n=10` : `6`, `12`, `982`. Le phénomène non
  canonique apparaît minimalement à `n=6`.
- Résultat subagent A : laminarité brute des `I_x` non nécessaire ; circular
  ones local sans faux rejet observé dans certains stress mais beaucoup de faux
  silences ; `paired_farthest` balanced/mixed souvent muet car projections
  singletons.
- Résultat subagent B : signatures DP agrégées compactent mais perdent la
  sémantique. Contre-exemple `paired_farthest n=8 seed=1008` où deux
  sous-frontiers ont même signature `forced_only` mais divergent cR dans le
  même contexte.
- Résultat subagent C : repair positive-only sûr si finalisé par
  `represents_order` + `is_precircular_order_cR`, mais aucun gain observé au-delà
  des cas déjà couverts par la candidate dans les probes `n >= 10`.
- Commande exécutée : `pytest -q tests/test_regression_counterexamples.py`.
- Résultat correction : `2 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `75 passed in 0.53s`, puis `JUSTE`.
- Commande exécutée : `make bench-piste-f`.
- Résultat benchmark : `cycle/mixed`, `permuted_cycle/star` et
  `paired_farthest/star` gardent `0` timeout et `0` incomplet ;
  `paired_farthest/mixed` garde `0` timeout et `40` incomplets visibles, tous
  via `candidate_large_n_placeholder`.
- Conclusion : ne pas intégrer de nouvelle branche candidate. Le résultat utile
  est négatif et durable : le témoin canonique ne caractérise pas l'existence
  non-star, et high-cross/farthest seul reste insuffisant. Les prochaines
  pistes doivent viser un sous-cas non-star prouvé ou un diagnostic local/CSP
  explicitement expérimental.
- Next action : soit formaliser un sous-cas strict/degree-bound où les ordres
  représentés se génèrent polynomialement, soit ajouter un rapport
  `project_farthest_sets_to_pc_nodes` pour guider les obstructions sans servir
  de solver.

## 2026-05-23 farthest set projection diagnostic

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les projections locales
  `I_x(v) = {i : B_i intersecte F_x}` ne décident pas l'existence, mais peuvent
  fournir un rapport reproductible d'obstructions locales : laminarité,
  intervalle dans l'ordre local déclaré et circular-ones exact à petit degré.
- Changement fait : ajout de `project_farthest_sets_to_pc_nodes` dans
  `src/pc_circular/solvers/local_constraints.py`; ajout de tests pour le cas
  égal-distance/star non laminaire mais intervalle/circular-ones compatible, et
  pour une violation d'intervalle déclarée sur un nœud `C`. Mise à jour
  `PLANS.md`, Piste A, index des pistes, obligations et checkpoints.
- Commande exécutée avant modification : `make quick`.
- Résultat correction : `75 passed in 0.53s`, puis `JUSTE`.
- Plan subagents : deux explorateurs lecture seule. L'un vérifie la forme
  minimale du diagnostic et les tests ; l'autre prépare le sous-cas strict pour
  décider si la suite doit basculer vers Piste F.
- Résultat subagent diagnostic : champs recommandés ajoutés ou conservés :
  `branch_sizes`, `child_label_sets`, `projection_size`, statut circular-ones
  et témoin d'ordre quand compatible. Le subagent recommande un futur test de
  faux silence avant toute promotion du diagnostic.
- Résultat subagent strict : le sous-cas strict est prometteur, mais une
  transcription naïve de l'Algorithm 5.2 rate `cycle_metric(6)` et produit des
  mismatches sur matrices `n=4`; il faut d'abord un module expérimental validé
  contre la définition directe et l'oracle, pas une intégration candidate.
- Probe exécutée : `project_farthest_sets_to_pc_nodes` sur familles
  `equal/cycle/random/paired_farthest`, arbres `star/mixed`, `n=8`.
- Résultat probe : `equal/star` produit `proper=8`, `laminar=28`,
  `interval=0`, `circular_ones_false=0`; `random/star` produit `proper=7`,
  `laminar=8`, `interval=6`, `circular_ones_false=1`; `random/mixed` et
  `paired_farthest/mixed` sont muets sur le scaffold binaire (`proper=0`).
- Commande exécutée : `pytest -q tests/test_local_constraints.py`.
- Résultat correction : `5 passed`.
- Commande exécutée : `make unit`.
- Résultat correction : `77 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `77 passed in 0.52s`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit ; `0`
  timeout, `0` incomplet ; dernier `n=20` via
  `candidate_universal_bad_witness_bound_all_orders` et
  `candidate_validated_sampled_witness`, fit polynomial empirique rapide
  `p ~= 2.70`.
- Conclusion : outil utile pour explorer Piste A/D et produire des signaux
  locaux, mais impropre à une décision directe. Il n'est pas appelé par
  `candidate.py`.
- Next action : soit tester le sous-cas strict à partir des sources, soit
  formaliser un rapport circular-ones/intersection qui relie ces projections à
  des contraintes prouvées plutôt qu'à de simples signaux.

## 2026-05-23 strict fixed-order predicates

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : avant toute intégration de l'Algorithm 5.2, on peut
  sécuriser le sous-cas strict avec des prédicats directs d'ordre fixé :
  strict Robinson linéaire, `sqcR`, `scR`, et définition stricte par arcs.
- Changement fait : ajout de `is_strict_robinson_linear`,
  `is_strict_quasi_circular_order`, `is_strict_precircular_order_cR`,
  `is_strict_circular_robinson_order` et fonctions de violation associées dans
  `predicates.py`; ajout de `src/pc_circular/solvers/strict_experiments.py`
  avec `strict_order_report`; ajout de `tests/test_strict_experiments.py`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction : `77 passed in 0.53s`, puis `JUSTE`.
- Plan subagents : deux explorateurs lecture seule. Résultats : les définitions
  directes strictes sont confirmées ; Fig. 2.2, equal-distance, cycle metric et
  témoin strict non représenté sont les régressions prioritaires.
- Commande exécutée : extraction `pdftotext` de Fig. 2.2.
- Résultat source : matrice Fig. 2.2 extraite :
  `[[0,1,2,3],[1,0,3,2],[2,3,0,1],[3,2,1,0]]`. L'ordre `(0,1,2,3)` est
  strict quasi mais viole `scR`; l'ordre `(0,1,3,2)` est strict circular.
- Probe exécutée : exhaustif `n=4`, valeurs `{1,2,3}`, tous ordres circulaires.
- Résultat probe : `2187` couples matrice-ordre ; aucun désaccord entre
  `is_strict_precircular_order_cR` et `is_strict_circular_robinson_order`.
  Counts par ordre : strict circular `261`, strict pre `261`, strict quasi
  `357`.
- Commande exécutée : `pytest -q tests/test_strict_experiments.py`.
- Résultat correction : `8 passed`.
- Commande exécutée : `make unit`.
- Résultat correction : `85 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `85 passed in 0.66s`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `0` timeout, `0` incomplet ; dernier `n=20` via
  `candidate_universal_bad_witness_bound_all_orders` et
  `candidate_validated_sampled_witness`, fit polynomial rapide `p ~= 2.70`.
- Conclusion : base strict fixed-order utile et verrouillée par régressions,
  mais toujours aucun solveur strict polynomial. `candidate.py` reste inchangé.
- Next action : implémenter un module expérimental de génération des candidats
  stricts, ou reproduire Algorithm 5.2 avec comparaison exhaustive contre
  `strict_order_report` avant toute promotion en candidate.

## 2026-05-23 Algorithm 5.2 strict candidates

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : l'Algorithm 5.2 peut être transcrit comme générateur
  expérimental de candidats stricts, à condition de filtrer les ordres produits
  par les prédicats fixed-order et de ne jamais conclure sans vérification de
  représentation PC-tree.
- Changement fait : ajout de `strict_algorithm52_report` dans
  `src/pc_circular/solvers/strict_experiments.py`; ajout de tests pour
  `cycle_metric(6)`, Fig. 2.2, un random strict positif `n=5 seed=33`, le
  témoin strict non représenté par PC-tree, et l'exhaustif `n=4`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction : `85 passed in 1.15s`, puis `JUSTE`.
- Plan subagents : cinq explorateurs lecture seule. Résultats reçus pendant
  l'itération : Piste C/D recommande un rapport strict PC-tree borné ; Piste
  sources/modules recommande un rapport balles/circular-ones ; Piste
  contre-exemples fournit `cycle_metric(5)`, Fig. 2.2, equal-distance, random
  `n=5 seed=33`, et le piège PC-tree non-star ; Piste B propose une signature
  strict-specific externe avec seuil `>=` à tester plus tard.
- Commande exécutée : `pytest -q tests/test_strict_experiments.py`.
- Résultat correction : `12 passed`.
- Probe exécutée : comparaison de `strict_algorithm52_report` aux ordres
  stricts exacts sur cycles `n=4..7`, equal-distance, random `n=5/6` seeds
  `0..199`.
- Résultat probe : aucun désaccord ; le rapport récupère exactement les ordres
  `strict_quasi` et `strict_circular` exacts dans ces familles.
- Probe exhaustive intégrée aux tests : `n=4`, valeurs `{1,2,3}`.
- Résultat probe : `729` matrices ; le rapport récupère exactement les ordres
  strict quasi et strict circular exacts.
- Conclusion : progrès utile Piste F. Le générateur filtré donne une base plus
  proche de l'Algorithm 5.2 et récupère des stricts positifs hors familles déjà
  intégrées, mais il reste expérimental et hors `candidate.py`.
- Next action : soit formaliser la complétude de la génération strict dans le
  dépôt, soit ajouter un rapport PC-tree/circular-ones borné pour relier ces
  candidats stricts à l'existence représentée par `T`.

## 2026-05-23 ball circular-ones strict diagnostic

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les boules métriques non triviales vues comme contraintes
  d'arcs/circular-ones coïncident avec la quasi-circularité d'un ordre fixé, et
  peuvent servir de diagnostic pour séparer génération quasi-circulaire et test
  cR/strict cR.
- Changement fait : ajout de `strict_ball_circular_ones_report` dans
  `src/pc_circular/solvers/strict_experiments.py`; ajout de tests cycle,
  Fig. 2.2, equal-distance, PC-tree non représenté, grande taille incomplète et
  exhaustif `n=4`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction : `89 passed in 0.87s`, puis `JUSTE`.
- Plan subagents : trois explorateurs lecture seule lancés sur invariants
  circular-ones/balles, contre-exemples petits et API PC-tree/CSP bornée.
  Résultats : confirmation que les boules doivent être non triviales
  `1 < |B| < n`; recommandation d'exposer signatures complètes de modules ;
  contre-exemples Fig. 2.2, equal-distance, random `n=6 seed=7` star et random
  `n=6 seed=17` balanced/mixed ; recommandation de champs `counts`, `exists`,
  `order_source`, `incomplete_reasons` et sanity check `represents_order`.
- Commande exécutée : `pytest -q tests/test_strict_experiments.py`.
- Résultat correction : `21 passed`.
- Probe exécutée : comparaison ball/quasi sur cycles `n=4..7`,
  equal-distance, random `n=5/6` seeds `0..199`, plus Fig. 2.2.
- Résultat probe : aucun désaccord ball/quasi ; Fig. 2.2 donne `ball_arc=2`
  et `strict_circular=1`.
- Probe exhaustive intégrée aux tests : `n=4`, valeurs `{1,2,3}`.
- Résultat probe : `729` matrices ; `ball_arc_orders` coïncide exactement avec
  les ordres `is_quasi_circular_order`, et les ordres strict quasi/strict
  circular du rapport coïncident avec les prédicats directs.
- Contre-exemple ajouté : random `n=6 seed=7`, ordre `(0,2,1,4,3,5)` est
  `ball_arc/quasi` mais pas cR ; le rapport star a `ball_arc=1` et `cR=0`.
- Gardes PC-tree ajoutés : labels invalides rejetés par `ValueError`, et arbre
  imbriqué `C(P(0,1), P(2,3), 4)` sans mismatch de représentation.
- Commande exécutée : `make unit`.
- Résultat correction : `98 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `98 passed in 1.14s`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `0` timeout, `0` incomplet ; dernier `n=20` via
  `candidate_universal_bad_witness_bound_all_orders` et
  `candidate_validated_sampled_witness`, fit polynomial rapide bruité
  `p ~= 2.69`.
- Conclusion : la piste D dispose maintenant d'un diagnostic reproductible. Il
  confirme le rôle des boules comme circular-ones pour quasi-circularité, mais
  documente aussi que cette contrainte ne décide pas circular Robinson.
- Next action : construire/intersecter un vrai PC-tree de boules avec le
  PC-tree fourni, ou chercher des contraintes d'arcs dérivées des quartets cR et
  les attaquer avec Fig. 2.2/equal-distance/paired-farthest.

## 2026-05-23 bad-witness arc constraints diagnostic

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les mauvais témoins
  `B(a,b) = {w : max(d(a,w), d(w,b)) > d(a,b)}` peuvent peut-être fournir des
  contraintes d'arcs/circular-ones plus proches de cR que les boules.
- Changement fait : ajout de `bad_witness_arc_order_report` et
  `bad_witness_arc_constraints_report` dans
  `src/pc_circular/solvers/dp_experiments.py`; ajout de régressions dans
  `tests/test_dp_experiments.py`; mise à jour Pistes D/E, obligations,
  `PLANS.md` et checkpoints.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `98 passed in 1.14s`, puis `JUSTE`.
- Plan subagents : trois explorateurs lecture seule. Résultats : confirmation
  que la condition one-side est exactement la condition cR pour ordre fixé ;
  `B(a,b)` arc est un filtre suffisant observé mais trop fort ; `B(a,b) union
  {a,b}` est ni nécessaire ni suffisant ; l'API doit rester bornée et marquer
  les absences inconnues si `frontier_limit` tronque l'énumération.
- Contre-exemples ajoutés : `n=5`, ordre `(0,2,4,1,3)`, cR vrai mais
  `B(0,3)={1,2}` non arc ; equal-distance `n=4` cR vrai mais
  `B(0,2) union {0,2}` non arc ; matrice
  `[[0,2,1,2],[2,0,2,1],[1,2,0,2],[2,1,2,0]]` où
  `B union endpoints` passe mais cR échoue.
- Commande exécutée : `pytest -q tests/test_dp_experiments.py`.
- Résultat correction : `15 passed`.
- Commande exécutée : `make unit`.
- Résultat correction : `102 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `102 passed in 1.75s`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark : `reports/complexity_report_quick.json` écrit ; `0`
  timeout, `0` incomplet ; tailles `[4,5,6,8,10,12,16,20]`, dernier `n=20`
  avec `candidate_validated_sampled_witness` sur 4 runs et
  `candidate_universal_bad_witness_bound_all_orders` sur 1 run.
- Conclusion : résultat négatif utile pour Piste D/E. La condition one-side est
  exacte pour ordre fixé, mais les contraintes d'arcs indépendantes ne sont pas
  une caractérisation exploitable directement comme circular-ones global.
  `candidate.py` reste inchangé.
- Next action : tenter un état DP/CSP qui mémorise, pour chaque paire
  concernée, quel côté contient déjà des mauvais témoins, ou prouver/refuter
  formellement la suffisance de `B(a,b)` arc comme filtre positif.

## 2026-05-23 bad-side pair nogood CSP compilation

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : compiler les obstructions bad-side par paire `{a,b}` peut
  représenter les mêmes rejets cR que les quartets ordonnés, avec moins
  d'atomes et de nogoods, tout en restant un diagnostic énumératif.
- Changement fait : ajout de `forbidden_bad_side_atoms`,
  `compile_bad_side_nogoods`, `solve_compiled_bad_side_nogood_csp` et
  `solve_pruned_bad_side_nogood_csp` dans
  `src/pc_circular/solvers/sat_like_experiments.py`; ajout de tests CSP ;
  mise à jour de `PLANS.md`, Pistes B/C/E, obligations et checkpoints.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `102 passed in 1.68s`, puis
  `JUSTE`.
- Plan subagents : trois explorateurs lecture seule. Résultats : garder
  l'itération comme compilation parallèle, tester égalités/wrapping/fanout 3 et
  paired-farthest, et documenter que la preuve reste fixed-order tant que la
  compilation énumère les affectations complètes.
- Commande exécutée : `pytest -q tests/test_sat_like_experiments.py`.
- Résultat correction : `19 passed`.
- Commande exécutée : `make unit`.
- Résultat correction : `108 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `108 passed in 1.81s`, puis `JUSTE`.
- Probe exécutée : comparaison bad-side/quartets sur `equal6_mixed`,
  `wrap4_c`, `cycle8_balC_f3`, `cycle8_mixed_f3`,
  `paired8_1008_balC_f3`, `paired8_1008_mixed_f3`.
- Résultat probe : tous les cas ont `validation_fp/fn = 0`. Les cas non
  triviaux ont exactement deux fois moins d'atomes et de nogoods bad-side que
  quartets : par exemple `cycle8_mixed_f3` `416/832` atomes et `1178/2356`
  nogoods ; `paired8_1008_mixed_f3` `168/336` atomes et `796/1592` nogoods.
  `equal6_mixed` produit `0` atome/nogood.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark CSP : `reports/csp_internal_benchmark_quick.json` écrit ;
  `192` lignes, `192` supportées, `0` mismatch, `31616` nogoods uniques,
  `1280` branches prunées, `2208/5760` feuilles vues.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; dernier `n=20` via
  `candidate_validated_sampled_witness` sur 4 runs et
  `candidate_universal_bad_witness_bound_all_orders` sur 1 run.
- Conclusion : représentation CSP plus nette et plus petite, mais pas un
  solveur compact. `candidate.py` reste inchangé.
- Next action : soit chercher une construction non énumérative de ces nogoods,
  soit revenir à un sous-cas prouvable où les supports bad-side se factorisent.

## 2026-05-23 bounded exact PC-tree candidate subcase

- Date/heure : 2026-05-23, Europe/Paris.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : quand le PC-tree fourni a un nombre de frontiers certifié
  sous une petite limite, on peut décider exactement l'existence cR même pour
  `n > 8`, sans prétendre résoudre les grands `P`.
- Changement fait : ajout de `EXACT_PC_TREE_FRONTIER_LIMIT`,
  `_pc_tree_frontier_upper_bound` et
  `candidate_exact_bounded_pc_tree_frontiers` dans `candidate.py`; ajout de
  tests `n=9` positif rigide sans shortcut, négatif rigide, et gros star qui
  doit rester incomplet malgré un témoin hors sample.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `108 passed in 1.82s`, puis
  `JUSTE`.
- Plan subagents : deux explorateurs lecture seule. Résultats : ne jamais
  utiliser une énumération tronquée comme preuve, garder `quasi_orders`
  prioritaire, placer la branche avant sampling, et tester un positif
  plateau-cycle sans shortcut, un négatif rigide, et un star trop grand qui
  reste `complete=False`.
- Commande exécutée : `pytest -q tests/test_candidate.py`.
- Résultat correction : `20 passed`.
- Probe exécutée : comparaison de la nouvelle branche à `exact_oracle_pc_tree`
  sur arbres rigides et one-P, `n=9..11`, familles cycle/equal/paired/random.
- Résultat probe : `42` décisions de
  `candidate_exact_bounded_pc_tree_frontiers`, aucun désaccord oracle.
- Commande exécutée : `make unit`.
- Résultat correction : `111 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `111 passed in 1.92s`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE` sur exhaustif `n=4`, `5000` random,
  `max-n=8`, seed `314159`, shrink actif.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; dernier `n=20` via
  `candidate_validated_sampled_witness` sur 4 runs et
  `candidate_universal_bad_witness_bound_all_orders` sur 1 run.
- Conclusion : sous-cas exact utile intégré. Les résultats négatifs complets
  sont permis uniquement quand l'upper bound indépendant prouve que toutes les
  frontiers du scaffold ont été énumérées.
- Next action : chercher une construction non énumérative pour les PC-trees
  au-delà de la limite, ou un sous-cas où la borne reste polynomialement petite.

## 2026-05-23 finite quasi-orders exact candidate subcase

- Date/heure : 2026-05-23 03:16:14 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : quand l'entrée fournit explicitement une famille finie
  `quasi_orders` sous une limite fixe, la candidate peut décider exactement
  l'existence cR relative à cette famille, même pour `n > 8`.
- Changement fait : ajout de `EXACT_QUASI_ORDER_LIMIT` et
  `candidate_exact_bounded_quasi_orders` dans `candidate.py`; ajout de tests
  pour famille vide non universelle, négatif fini exact, témoin hors budget
  sampling, famille trop grande, itérateur non dimensionné, et priorité de
  `quasi_orders` sur `pc_tree`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `111 passed in 1.91s`, puis
  `JUSTE`.
- Documents source : les six PDF fournis et la capture Proposition 4.4 étaient
  déjà versionnés sous `docs/source_materials/` avec hashes dans
  `docs/source_materials/README.md`; aucun recopiage nécessaire.
- Plan subagents : deux explorateurs lecture seule. Résultats : placer la
  branche après le sous-cas universel et avant les certificats `pc_tree`,
  garder la complétude relative à la famille explicite, ne pas consommer les
  itérateurs non dimensionnés, et noter que l'impact sur `make bench` actuel
  sera nul parce que le benchmark appelle `candidate(D, pc_tree=T)`.
- Commande exécutée : `pytest -q tests/test_candidate.py`.
- Résultat correction : `24 passed`.
- Commande exécutée : `make unit`.
- Résultat correction : `115 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `115 passed in 1.93s`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE` sur exhaustif `n=4`, `5000` random,
  `max-n=8`, seed `314159`, shrink actif.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; tailles `[4,5,6,8,10,12,16,20]`, dernier
  `n=20` via `candidate_validated_sampled_witness` sur 4 runs et
  `candidate_universal_bad_witness_bound_all_orders` sur 1 run ; fit rapide
  bruité `p ~= 2.70`.
- Incomplets restants connus : le rapport fort `mixed/star` précédent avait
  `42` incomplets via `candidate_large_n_placeholder`, et le rapport ciblé
  `paired_farthest/mixed` restait incomplet sur toutes les tailles testées.
  T029 ne les résout pas, car il concerne seulement les familles explicites
  `quasi_orders`.
- Conclusion : sous-cas API exact utile intégré. Un résultat `False` complet
  est maintenant permis seulement quand toute la famille explicite bornée a été
  inspectée. Ce n'est pas une avancée sur les grands PC-trees compacts.
- Next action : attaquer `paired_farthest/mixed` par synthèse représentée dans
  le PC-tree, ou instrumenter le benchmark `mixed/star` pour attribuer les
  placeholders aux sous-familles génératrices avant un nouveau certificat.

## 2026-05-23 mixed benchmark placeholder attribution

- Date/heure : 2026-05-23 03:29:53 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les incomplets du benchmark fort `mixed/star` se
  concentrent probablement sur une sous-famille précise ; il faut l'attribuer
  avant de choisir le prochain certificat.
- Changement fait : ajout de `MIXED_INSTANCE_KINDS` et
  `instance_by_kind_with_metadata` dans `generators.py`; extraction de
  `run_benchmark` dans `tools/pc_circular_complexity_benchmark.py`; ajout de
  `seed`, `mixed_instance_kinds`, `resolved_kind_counts`,
  `successful_runs_by_resolved_kind`, `timeouts_by_resolved_kind`,
  `incomplete_runs_by_resolved_kind`, `exists_true_by_resolved_kind`,
  `solver_counts_by_resolved_kind` et `diagnostics_sample_metadata` au rapport
  JSON ; ajout de tests ciblés générateur/benchmark.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `115 passed in 1.95s`, puis
  `JUSTE`.
- Plan subagents : deux explorateurs lecture seule. Résultats : préserver le
  tirage RNG `mixed`, ne pas ajouter `paired_farthest` au mixed par défaut,
  compter les timeouts par sous-famille même sans résultat candidate, ajouter
  `seed` au rapport, et garder `paired_farthest/mixed` comme piste T031
  séparée avec certificat positif vérifié par `represents_order` + cR.
- Commande exécutée : `pytest -q tests/test_generators.py
  tests/test_complexity_benchmark.py`.
- Résultat correction : `7 passed`.
- Commande exécutée : `make unit`.
- Résultat correction : `119 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `119 passed in 1.92s`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet, avec champs `resolved_kind_*`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `42` incomplets, tous dans `resolved_kind="random"` avec seed
  `20260521`.
- Commande exécutée : `make bench-piste-f`.
- Résultat benchmark ciblé : rapports Piste F écrits ; `0` timeout. Pour
  `paired_farthest/mixed`, `n=10` et `n=12` sont complets via
  `candidate_exact_bounded_pc_tree_frontiers`; les incomplets restants sont
  `n=16` et `n=20`, `10/10` chacun via `candidate_large_n_placeholder`.
- Conclusion : instrumentation utile. Les placeholders `mixed/star` ne viennent
  pas des sous-familles structurées `cycle/block/ultrametric/equal/non_strict`
  dans le benchmark fort courant ; ils viennent tous de `random`. Aucun
  algorithme nouveau n'est prouvé par cette étape.
- Next action : T031 peut soit attaquer les randoms avec génération de
  contre-exemples/oracle et classification positive/négative, soit continuer la
  famille ciblée `paired_farthest/mixed` avec un certificat positif miroir
  guidé par la structure du PC-tree.

## 2026-05-23 hereditary small obstruction certificate

- Date/heure : 2026-05-23 03:44:35 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les `random/star` incomplets du benchmark fort contiennent
  une obstruction induite de 4 points. Comme cR est héréditaire par restriction,
  une telle sous-matrice sans ordre cR prouve la non-existence globale.
- Changement fait : ajout de `SMALL_FORBIDDEN_SUBMATRIX_ORDER`,
  `SMALL_FORBIDDEN_SUBMATRIX_LIMIT`,
  `candidate_small_forbidden_submatrix_obstruction` et helper de sous-matrice
  induite dans `candidate.py`; ajout d'une validation cR directe avant
  acceptation du témoin paired-farthest ; ajout de tests pour random négatif,
  obstruction explicite et garde cycle positif.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `119 passed in 1.93s`, puis
  `JUSTE`.
- Plan subagents : deux explorateurs lecture seule. Résultats : preuve de
  soundness par restriction héréditaire confirmée ; le scan ne doit jamais
  conclure si la limite est atteinte sans témoin ; sur les `42` randoms du
  benchmark fort T030, `42/42` ont une obstruction 4-points avant la limite
  `4096`, avec rang max `154`; sur `400/400` randoms purs testés pour
  `n in {10,20,60,100}`, la limite `4096` trouve une obstruction.
- Commande exécutée : `pytest -q tests/test_candidate.py`.
- Résultat correction : `27 passed`.
- Commande exécutée : `make unit`.
- Résultat correction : `122 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `122 passed in 1.99s`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE` sur exhaustif `n=4`, `5000` random,
  `max-n=8`, seed `314159`, shrink actif.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`. Agrégat solver :
  `candidate_small_forbidden_submatrix_obstruction` sur `42` runs, les anciens
  placeholders random ; fit polynomial empirique `p ~= 3.22`.
- Commande exécutée : `make bench-piste-f`.
- Résultat benchmark ciblé : rapports Piste F écrits ; `0` timeout.
  `paired_farthest/star` reste complet ; `paired_farthest/mixed` garde `20`
  incomplets ciblés à `n=16,20`.
- Conclusion : progrès de candidate sound pour les négatifs random avec petite
  obstruction. Le benchmark principal demandé passe maintenant sans timeout ni
  incomplet, mais cela ne prouve pas le problème général : la recherche
  d'obstruction est bornée et son échec ne donne aucune décision négative.
- Next action : chercher une famille sans obstruction 4-points où le statut
  reste difficile, ou poursuivre le certificat positif représenté pour
  `paired_farthest/mixed` à `n=16,20`.

## 2026-05-23 five-point four-local obstruction stress

- Date/heure : 2026-05-23 04:04:26 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les obstructions 4-points ne caractérisent pas la
  non-existence cR globale. Un noyau 5-points globalement non-cR mais 4-local
  positif permettrait d'attaquer T031 et de justifier un certificat héréditaire
  taille 5.
- Changement fait : ajout de `four_local_non_cr_core` et
  `padded_four_local_non_cr`; ajout de tests générateurs/régressions montrant
  que le noyau 5-points est globalement non-cR mais que toutes ses restrictions
  4-points sont cR ; extension de
  `candidate_small_forbidden_submatrix_obstruction` à
  `SMALL_FORBIDDEN_SUBMATRIX_ORDERS = (4, 5)`.
- Détail d'implémentation : les scans d'obstructions sont placés après les
  témoins positifs échantillonnés, car un ordre représenté et vérifié cR suffit
  déjà à prouver l'existence et évite de payer les scans sur ces cas faciles.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `122 passed in 1.96s`, puis
  `JUSTE`.
- Plan subagents : trois explorateurs lecture seule. Résultats : deux probes
  indépendantes ont trouvé le même noyau 5-points ; la direction héréditaire est
  un théorème mais la caractérisation 4-locale est fausse ; `paired_farthest`
  `mixed` reste incomplet à `n=16,20` faute de certificat négatif ou de preuve
  de complétude d'un diagnostic structurel.
- Contre-exemple minimal :
  `[[0,1,1,2,2],[1,0,2,1,2],[1,2,0,1,2],[2,1,1,0,2],[2,2,2,2,0]]`.
  Exhaustif `n=5`, valeurs `{1,2}` : trouvé après `236` matrices ; les `5`
  sous-matrices induites de taille `4` sont positives, mais le noyau complet est
  négatif.
- Commande exécutée : `pytest -q tests/test_candidate.py tests/test_generators.py tests/test_regression_counterexamples.py`.
- Résultat correction : `39 passed`.
- Commande exécutée : benchmark ciblé
  `tools/pc_circular_complexity_benchmark.py --sizes 5,6,8,9,10,12,20,40 --repeats 3 --instance-kind four_local_non_cr --pc-tree star`.
- Résultat benchmark ciblé : `reports/complexity_four_local_non_cr.json` écrit ;
  `0` timeout, `0` incomplet ; `candidate_small_forbidden_submatrix_obstruction`
  sur tous les runs `n > 8`.
- Commande exécutée : `make unit`.
- Résultat correction : `127 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `127 passed in 2.09s`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`. Agrégat solver inchangé :
  `candidate_small_forbidden_submatrix_obstruction` sur `42` runs ; fit
  polynomial empirique `p ~= 3.25`.
- Conclusion : T032 casse la conjecture 4-locale et ajoute un certificat
  héréditaire 5-points sound. Ce n'est toujours pas une caractérisation globale
  ni une preuve d'algorithme général.
- Next action : chercher une famille 5-locale positive mais globalement
  négative, ou formaliser un certificat négatif pour `paired_farthest/mixed`.

## 2026-05-23 six-point five-local obstruction and odd high cycle certificate

- Date/heure : 2026-05-23 04:10:18 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les obstructions induites de tailles `(4,5)` ne
  caractérisent pas la non-existence cR globale. Un noyau 6-points 5-localement
  positif, ou mieux une famille paramétrique, indiquerait une vraie hiérarchie
  d'obstructions.
- Changement fait : ajout de `five_local_non_cr_core`,
  `padded_five_local_non_cr`, `odd_high_cycle_plus_low_hub`,
  `SMALL_FORBIDDEN_SUBMATRIX_ORDERS = (4, 5, 6)`, et
  `candidate_odd_high_cycle_low_hub_obstruction`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `127 passed in 2.09s`, puis
  `JUSTE`.
- Plan subagents : trois explorateurs lecture seule. Résultats : noyau
  6-points trouvé indépendamment en exhaustif `{1,2}` ; coût d'un scan 6-points
  brut jugé acceptable seulement avec une famille concrète ; le noyau est une
  relabellisation d'un cycle haut impair `C5` plus hub bas universel.
- Contre-exemple minimal :
  `[[0,1,1,1,1,1],[1,0,1,1,2,2],[1,1,0,2,1,2],[1,1,2,0,2,1],[1,2,1,2,0,1],[1,2,2,1,1,0]]`.
  Exhaustif `n=6`, valeurs `{1,2}` : trouvé après `237` matrices ; les `6`
  sous-matrices induites de taille `5` sont positives, mais le noyau complet est
  négatif.
- Théorème de sous-cas ajouté : si le graphe des arêtes hautes d'une matrice
  binaire est un cycle impair connecté plus au moins un hub isolé, aucun ordre
  cR n'existe. La preuve utilise la caractérisation bad-side : chaque sommet du
  cycle devrait être source ou puits dans l'ordre linéaire autour du hub, ce qui
  force une alternance impossible sur un cycle impair.
- Commande exécutée : `pytest -q tests/test_candidate.py tests/test_generators.py tests/test_regression_counterexamples.py`.
- Résultat correction : `46 passed`.
- Commande exécutée : benchmark ciblé
  `tools/pc_circular_complexity_benchmark.py --sizes 6,7,8,9,10,12,20,40 --repeats 3 --instance-kind five_local_non_cr --pc-tree star`.
- Résultat benchmark ciblé : `reports/complexity_five_local_non_cr.json` écrit ;
  `0` timeout, `0` incomplet ; `candidate_small_forbidden_submatrix_obstruction`
  sur tous les runs `n > 8`.
- Commande exécutée : benchmark ciblé
  `tools/pc_circular_complexity_benchmark.py --sizes 6,8,10,12,20,40 --repeats 3 --instance-kind odd_high_cycle_plus_low_hub --pc-tree star`.
- Résultat benchmark ciblé : `reports/complexity_odd_high_cycle_plus_low_hub.json`
  écrit ; `0` timeout, `0` incomplet ; les tailles `n >= 10` passent par
  `candidate_odd_high_cycle_low_hub_obstruction`.
- Commande exécutée : `make unit`.
- Résultat correction : `134 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `134 passed in 2.93s`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet.
- Commande exécutée : `make bench-piste-f`.
- Résultat benchmark ciblé Piste F : rapports écrits ; `0` timeout.
  `paired_farthest/star` reste complet ; `paired_farthest/mixed` garde `20`
  incomplets à `n=16,20`, avec max observé `0.708s`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, fit polynomial empirique `p ~= 3.25`.
- Conclusion : T033 casse la conjecture 5-locale, ajoute un certificat
  héréditaire 6-points borné et surtout un sous-cas négatif polynomial pour
  cycle haut impair plus hub bas. Le problème général reste ouvert.
- Next action : chercher des modules/blow-ups de cycle impair avec hub bas, ou
  transformer le certificat odd-cycle en contrainte locale utilisable dans un
  PC-tree non-star.

## 2026-05-23 non-bipartite high graph low-hub certificate

- Date/heure : 2026-05-23 04:34:00 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : le certificat cycle haut impair avec hub bas se généralise
  à toute matrice binaire `low/high` possédant un hub bas universel et un
  graphe haut non biparti.
- Changement fait : remplacement de
  `candidate_odd_high_cycle_low_hub_obstruction` par
  `candidate_non_bipartite_high_graph_low_hub_obstruction`; ajout de
  `non_bipartite_high_graph_plus_low_hub`; tests de régression pour une
  famille non-cycle ; documentation de la preuve et des limites.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `134 passed in 2.62s`, puis
  `JUSTE`.
- Plan subagents : deux sidecars. Résultat preuve : sound sous les préconditions
  binaires `low < high`, au moins un hub bas, graphe haut non biparti. Résultat
  benchmark : impact attendu ciblé, pas de correction pour
  `paired_farthest/mixed`.
- Preuve : couper l'ordre supposé cR au hub bas `h`. Pour toute arête haute
  `{v,u}`, `u` est un mauvais témoin pour la paire basse `{h,v}`. Tous les
  voisins hauts de `v` doivent donc être du même côté de `v`. En orientant les
  arêtes hautes selon l'ordre linéaire, chaque sommet est source ou puits ; le
  graphe haut devrait être biparti. Contradiction si le graphe haut est non
  biparti.
- Probe exhaustive : tous les graphes hauts binaires avec un hub bas et `m=1..5`
  sommets non-hub. Résultat : `m=3` donne `1` non-biparti négatif, `m=4` donne
  `23`, `m=5` donne `648`, aucun désaccord avec l'oracle exact ; les graphes
  hauts bipartis restent positifs dans cette probe.
- Commande exécutée : `pytest -q tests/test_candidate.py tests/test_generators.py tests/test_regression_counterexamples.py`.
- Résultat correction : `49 passed`.
- Commande exécutée : benchmark ciblé
  `tools/pc_circular_complexity_benchmark.py --sizes 6,8,10,12,20,40 --repeats 3 --instance-kind non_bipartite_high_graph_plus_low_hub --pc-tree star`.
- Résultat benchmark ciblé : `reports/complexity_non_bipartite_high_graph_low_hub.json`
  écrit ; `0` timeout, `0` incomplet ; à `n=40`, médiane `0.00052s` et branche
  `candidate_non_bipartite_high_graph_low_hub_obstruction`.
- Commande exécutée : benchmark ciblé
  `tools/pc_circular_complexity_benchmark.py --sizes 6,8,10,12,20,40 --repeats 3 --instance-kind odd_high_cycle_plus_low_hub --pc-tree star`.
- Résultat benchmark ciblé : `reports/complexity_odd_high_cycle_plus_low_hub.json`
  écrit ; `0` timeout, `0` incomplet ; les tailles `n >= 10` passent maintenant
  par `candidate_non_bipartite_high_graph_low_hub_obstruction`.
- Commande exécutée : `make unit`.
- Résultat correction : `137 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `137 passed`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-piste-f`.
- Résultat benchmark ciblé Piste F : rapports écrits ; `0` timeout.
  `paired_farthest/mixed` garde `20` incomplets à `n=16,20`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `2.0747s` à `n=100`, fit
  polynomial empirique `p ~= 3.25`.
- Conclusion : T034 transforme le certificat odd-cycle en certificat non-biparti
  plus général et toujours polynomial. Cela reste un sous-cas négatif binaire,
  pas une résolution du problème général ni des cas `paired_farthest/mixed`.
- Next action : attaquer les graphes hauts bipartis avec hub bas, ou relier le
  certificat bad-side source/puits aux contraintes locales d'un nœud `P`.

## 2026-05-23 even high cycle low-hub certificate

- Date/heure : 2026-05-23 05:07:00 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : dans le cas binaire `low/high` avec hub bas universel, la
  bipartition du graphe haut n'est pas suffisante. Les cycles hauts induits
  pairs de longueur au moins `6` devraient être négatifs, contrairement à `C4`.
- Changement fait : ajout de `even_high_cycle_plus_low_hub`; ajout de
  `candidate_even_high_cycle_low_hub_obstruction`; régressions `C6`/`C8` et
  contrôle positif `C4`; documentation du lemme strong-ordering nécessaire.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `137 passed in 2.98s`, puis
  `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : un subagent trouve
  exhaustivement que les `60` négatifs bipartis à `6` sommets non-hub sont des
  labellisations de `C6`; un subagent recommande de nommer le sous-cas comme
  cycle pair induit plutôt que "biparti" ; un subagent identifie la
  caractérisation plus large plausible par strong ordering / bipartite
  permutation graph, à garder hors candidate pour l'instant.
- Probe exhaustive : pour `m` sommets non-hub avec hub bas, les graphes hauts
  bipartis sont tous positifs pour `m <= 5`. Pour `m=6`, `5117` positifs et
  `60` négatifs ; les négatifs ont tous degré haut `(2,2,2,2,2,2)`, donc sont
  les cycles `C6`.
- Contre-exemples/contrôles : `C4 + hub` positif ; `C6 + hub` négatif ;
  `C8 + hub` négatif et sans obstruction induite de taille `6` ; `K3,3 + hub`
  positif, donc "contient un cycle pair" n'est pas une obstruction suffisante.
- Preuve du sous-cas : un ordre cR coupé au hub bas impose une condition de
  strong ordering sur le graphe haut. Un cycle induit pair `C_{2r}`, `r >= 3`,
  viole cette condition en prenant le plus petit sommet d'une part et ses deux
  voisins cycliques ; la condition forcerait une corde absente du cycle induit.
- Commande exécutée : `pytest -q tests/test_candidate.py tests/test_generators.py tests/test_regression_counterexamples.py`.
- Résultat correction : `54 passed`.
- Commande exécutée : benchmark ciblé
  `tools/pc_circular_complexity_benchmark.py --sizes 7,9,11,13,21,41,61,81 --repeats 10 --instance-kind even_high_cycle_plus_low_hub --pc-tree star`.
- Résultat benchmark ciblé : `reports/complexity_even_high_cycle_low_hub.json`
  écrit ; `0` timeout, `0` incomplet ; à `n=81`, médiane `0.00248s` et branche
  `candidate_even_high_cycle_low_hub_obstruction`.
- Commande exécutée : `make unit`.
- Résultat correction : `142 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `142 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `2.0883s` à `n=100`, fit
  polynomial empirique `p ~= 3.24`.
- Conclusion : T035 ajoute un sous-cas négatif polynomial strictement plus loin
  que les obstructions `(4,5,6)` : `C8` plus hub bas est négatif sans
  obstruction induite de taille `6`. Le cas biparti général reste ouvert ; le
  candidat strong-ordering est une piste, pas une solution intégrée.
- Next action : tester la conjecture strong-ordering sur graphes hauts hub bas
  avec un détecteur expérimental borné, puis isoler un sous-cas positif prouvé
  comme chain/complete-bipartite/matching représenté par le PC-tree.

## 2026-05-23 low-hub strong-ordering diagnostic

- Date/heure : 2026-05-23 05:32:00 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : dans le cas binaire `low/high` avec hub bas universel,
  l'existence sous star/all-orders pourrait coïncider avec l'existence d'un
  strong ordering du graphe haut privé des hubs.
- Changement fait : ajout de `low_hub_strong_ordering_report` dans
  `local_constraints.py`, hors `candidate.py`. Le rapport détecte les cas non
  applicables, bipartit le graphe haut, énumère bornément les ordres des deux
  parts, teste la condition strong ordering, et vérifie directement le témoin
  `hubs + A + B` par `is_precircular_order_cR`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `142 passed in 2.97s`, puis
  `JUSTE`.
- Plan subagents : deux sidecars lecture seule. Résultats : l'intégration doit
  rester dans `local_constraints.py`, pas dans `candidate.py`; le rapport doit
  marquer `complete=False` si la limite factorielle est atteinte ; les contrôles
  prioritaires sont `C4`, `C6`, `C8`, `K3,3`, matching, chain/Ferrers, tree
  négatif et cas non applicables.
- Contrôles positifs : `C4 + hub`, `K3,3 + hub`, matching et chain/Ferrers
  trouvent un strong ordering dont le témoin construit est vérifié cR.
- Contrôles négatifs : `C6 + hub`, `C8 + hub`, et le tree haut
  `(1,2),(1,5),(2,3),(2,4),(3,6),(4,7)` plus hub n'ont pas de strong ordering ;
  le tree est aussi négatif par oracle exact.
- Probe exhaustive oracle : pour tous les graphes hauts avec hub bas et
  `m <= 5` sommets non-hub, le diagnostic coïncide avec `brute_force.solve`.
- Probe exhaustive diagnostic : pour `m=6`, résultats
  `{strong=True: 5117, strong=False: 27651}`, avec statuts
  `strong_ordering_found=5116`, `empty_high_graph=1`,
  `non_bipartite_high_graph=27591`, `no_strong_ordering=60`.
- Commande exécutée : `pytest -q tests/test_local_constraints.py`.
- Résultat correction : `12 passed`.
- Commande exécutée : `make unit`.
- Résultat correction : `149 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `149 passed`, puis `JUSTE`.
- Conclusion : T036 transforme la piste strong-ordering en artefact
  falsifiable et borné. Elle renforce la compréhension du cas hub bas binaire,
  mais ne change pas la candidate et ne prouve pas encore le problème PC-tree.
- Next action : soit prouver la suffisance du strong ordering et remplacer
  l'énumération factorielle par une reconnaissance polynomiale, soit isoler un
  sous-cas positif plus petit avec témoin représenté par le PC-tree.

## 2026-05-23 bounded low-hub strong-ordering witness

- Date/heure : 2026-05-23 05:14:10 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : le diagnostic T036 peut être intégré sans risque comme
  générateur de témoin positif si la candidate vérifie elle-même l'ordre cR et
  son appartenance au PC-tree avant de retourner `exists=True`.
- Changement fait : ajout de
  `candidate_low_hub_strong_ordering_witness`; ajout des générateurs
  `chain_high_graph_plus_low_hub` et
  `complete_bipartite_high_graph_plus_low_hub`; le diagnostic essaie quelques
  ordres prioritaires avant l'énumération factorielle pour trouver les témoins
  chain/complete en grande taille.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `149 passed`, puis `JUSTE`.
- Plan subagents : deux sidecars lecture seule. Résultats : l'intégration est
  sound si elle reste strictement positive, placée après les certificats
  négatifs hub-bas et les témoins positifs déjà prouvés ; elle doit tester les
  familles `K_{p,q}`/chain, les contrôles `C6`/`C8`/tree négatif, le garde de
  représentation PC-tree et l'absence de contournement de `quasi_orders`.
- Contrôles ajoutés : chain et complete-bipartite star acceptés ; tree négatif
  non accepté ; PC-tree `C` rigide ne représentant pas le témoin refusé ;
  `quasi_orders=[]` explicite reste décidé par la branche exacte
  `candidate_exact_bounded_quasi_orders`.
- Commande exécutée : `pytest -q tests/test_candidate.py tests/test_generators.py tests/test_local_constraints.py tests/test_regression_counterexamples.py`.
- Résultat correction : `72 passed`.
- Commande exécutée : benchmark ciblé
  `chain_high_graph_plus_low_hub/star`, tailles
  `5,6,8,10,12,16,20,40,80`, répétitions `10`.
- Résultat benchmark ciblé : `reports/complexity_chain_low_hub_star.json`
  écrit ; `0` timeout, `0` incomplet ; à `n=80`, médiane `1.7726s`, p95
  `1.8630s`, branche `candidate_low_hub_strong_ordering_witness`.
- Commande exécutée : benchmark ciblé
  `complete_bipartite_high_graph_plus_low_hub/star`, tailles
  `5,6,8,10,12,16,20,40,80`, répétitions `10`.
- Résultat benchmark ciblé :
  `reports/complexity_complete_bipartite_low_hub_star.json` écrit ; `0`
  timeout, `0` incomplet ; à `n=80`, médiane `1.8263s`, p95 `1.9229s`,
  branche `candidate_low_hub_strong_ordering_witness`.
- Commande exécutée : `make unit`.
- Résultat correction : `155 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `155 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.00379s`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `2.0845s` à `n=100`, p95
  `2.1490s`, fit polynomial empirique `p ~= 3.25`.
- Conclusion : T037 ajoute un certificat positif utile et vérifié pour des
  familles low-hub biparties, sans transformer la conjecture strong-ordering en
  théorème. Les limites factorielle et représentation PC-tree restent
  explicites.
- Next action : essayer de prouver la suffisance du strong ordering ou de
  réduire sa reconnaissance à un bipartite permutation graph polynomial ; en
  parallèle, ajouter une famille matching low-hub positive pour casser les
  simplifications trop spécifiques aux chain/complete.

## 2026-05-23 fast bad-side fixed-order predicate

- Date/heure : 2026-05-23 05:21:34 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : pour un ordre fixé, la condition pre-circular/cR est
  équivalente à l'absence d'une paire `{a,b}` dont les deux arcs ouverts
  contiennent chacun un mauvais témoin `w` avec
  `max(D[a][w], D[w][b]) > D[a][b]`. Cette forme doit accélérer la validation
  de témoins sans changer l'oracle.
- Changement fait : ajout de `find_bad_side_precircular_cR_violation` et
  `passes_bad_side_precircular_cR` dans `predicates.py`; remplacement des
  validations de témoins/échantillons dans `candidate.py`; remplacement de la
  vérification de témoin dans `low_hub_strong_ordering_report`. Les tools de
  correction continuent à utiliser `is_precircular_order_cR` par quadruplets.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `155 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : preuve
  d'équivalence confirmée ; aucun contre-exemple trouvé ; micro-benchmark à
  `n=100` estime un gain global `13.9x..17.5x` sur les familles low-hub
  chain/complete ; recommandation de garder l'oracle par quadruplets
  indépendant.
- Contre-exemples cherchés : exhaustif `n=4`, random `n=5..7`, familles exactes
  `n=4..8`, échantillons `n=9,10,12`, égal-distance, rotations/renversements
  et cas où deux mauvais témoins sont sur le même arc.
- Résultat contre-exemples : aucun désaccord sur le prédicat strict `>` ; la
  variante fautive `>=` est réfutée par égal-distance.
- Commande exécutée : `pytest -q tests/test_predicates.py tests/test_dp_experiments.py tests/test_candidate.py tests/test_local_constraints.py`.
- Résultat correction : `83 passed`.
- Commande exécutée : probe local d'équivalence random/familles avec
  `PYTHONPATH=src rtk .venv/bin/python -c ...`.
- Résultat probe local : `6058` comparaisons ordre fixé, `0` mismatch.
- Résultat probe subagent : `153291` comparaisons ordre fixé, `0` mismatch.
- Commande exécutée : benchmark ciblé
  `chain_high_graph_plus_low_hub/star`, tailles `20,40,80,100`, répétitions `5`.
- Résultat benchmark ciblé :
  `reports/complexity_chain_low_hub_bad_side_quick.json` écrit ; `0` timeout,
  `0` incomplet ; à `n=100`, médiane `0.2485s`, p95 `0.2504s`.
- Commande exécutée : benchmark ciblé
  `complete_bipartite_high_graph_plus_low_hub/star`, tailles `20,40,80,100`,
  répétitions `5`.
- Résultat benchmark ciblé :
  `reports/complexity_complete_low_hub_bad_side_quick.json` écrit ; `0`
  timeout, `0` incomplet ; à `n=100`, médiane `0.3284s`, p95 `0.3306s`.
- Commande exécutée : `make unit`.
- Résultat correction : `159 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `159 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.00099s`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `0.0275s` à `n=100`, p95
  `0.0362s`, fit polynomial empirique `p ~= 1.73`.
- Conclusion : T038 améliore le coût du test d'ordre fixé et des validations
  candidate, sans résoudre l'existence dans PC-tree. Le résultat est une
  conséquence directe de la condition cR, pas une conjecture.
- Next action : utiliser ce gain pour tester une reconnaissance low-hub
  strong-ordering plus ambitieuse, ajouter matching low-hub comme stress
  positif, ou reprendre la Piste B sur une signature de sous-arbre moins
  globale.

## 2026-05-23 permuted low-hub matching witness

- Date/heure : 2026-05-23 05:45:03 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : pour une matrice binaire `low/high` avec hubs bas et
  graphe haut matching, l'ordre `hubs, A_1..A_m, B_1..B_m` alignant les mates
  dans le même ordre donne un témoin cR. Pour le diagnostic strong-ordering
  plus général, essayer les composantes biparties dans le même ordre est une
  priorité de recherche sûre parce que tout témoin reste vérifié directement.
- Changement fait : ajout de `matching_high_graph_plus_low_hub`; ajout d'une
  priorité composante-alignée dans `low_hub_strong_ordering_report`; correction
  du diagnostic pour traiter `low=0` hors diagonale ; tests matching permutés
  multi-seed, hubs multiples, triangle `low=0`, positif retardé par limite de
  permutations et candidate star.
- Plan subagents : deux sidecars lecture seule. Résultats : l'audit confirme
  le certificat matching comme positif robuste ; la recherche de contre-exemples
  ne trouve pas de faux positif mais montre que `max_permutation_pairs=1` reste
  incomplet sur les positifs strong-ordering généraux (`1542/5117` trouvés à
  `m=6`).
- Commande exécutée : `pytest -q tests/test_local_constraints.py tests/test_generators.py tests/test_candidate.py`.
- Résultat correction : `68 passed`.
- Commande exécutée : benchmark ciblé
  `matching_high_graph_plus_low_hub/star`, tailles
  `5,7,9,11,21,41,81,101`, répétitions `10`, timeout `2.0`.
- Résultat benchmark ciblé :
  `reports/complexity_matching_low_hub_star.json` écrit ; `0` timeout, `0`
  incomplet ; à `n=101`, médiane `0.1810s`, p95 `0.1852s`, branche
  `candidate_low_hub_strong_ordering_witness` pour `n>=9`.
- Commande exécutée : `make unit`.
- Résultat correction : `163 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `163 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.000990s`, p95
  `0.001059s`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `0.0267s`, p95 `0.0366s`,
  fit polynomial empirique `p ~= 1.72`.
- Conclusion : T039 ajoute un stress positif matching et améliore nettement le
  premier témoin sur matchings permutés, sans transformer le diagnostic
  strong-ordering en décision complète. Les statuts limités restent
  explicitement incomplets.
- Next action : prouver la suffisance du strong ordering binaire hub bas ou
  identifier l'algorithme polynomial exact correspondant, tout en cherchant des
  contre-exemples sur PC-trees non-star et graphes bipartis positifs où le
  premier témoin n'est pas représenté.

## 2026-05-23 represented low-hub strong-ordering witness search

- Date/heure : 2026-05-23 06:03:35 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : la candidate peut certifier des positifs low-hub non-star
  en parcourant plusieurs témoins strong-ordering et en acceptant seulement un
  ordre représenté par le PC-tree et vérifié cR, sans convertir une limite de
  recherche en rejet.
- Changement fait : ajout de
  `iter_low_hub_strong_ordering_witnesses`; `candidate.py` utilise maintenant
  cet itérateur pour chercher un témoin représenté ; `_pc_tree_frontier_upper_bound`
  tient compte des permutations circulaires à la racine pour réduire les
  surestimations sûres mais trop pessimistes ; régressions ajoutées pour un
  matching non-star `n=18`, un PC-tree raffiné `n=10` dont la borne réelle est
  `720`, et un faux silence local `I_x(v)` sur `C6 + hub`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `163 passed`, puis `JUSTE`.
- Plan subagents : cinq sidecars lecture seule. Résultats : preuve bad-side de
  la suffisance du témoin `hubs,A,B` pour un strong ordering donné ; proposition
  CSP non-star comme diagnostic, pas solver ; faux silence local `I_x(v)` sur
  PC-tree raffiné ; recommandation T041 sur chain/Ferrers permuté ; contre-
  exemple `n=10` où la borne de frontiers empêchait une énumération exacte de
  `720` frontiers.
- Contre-exemple initial : `matching_high_graph_plus_low_hub(18)` avec racine
  `C` et deux gros blocs `P`; avant T040, la candidate restait placeholder
  après `64` samples ; après T040, elle trouve un témoin représenté après
  `761` couples de permutations.
- Contre-exemple subagent : `matching_high_graph_plus_low_hub(10)` avec
  `p_node([c_node([4,0,7,2]), 1,3,5,6,8,9])`; l'oracle PC-tree est positif, la
  borne ancienne saturait au-dessus de `4096`, mais le nombre réel de frontiers
  canoniques est `720`. La borne root-aware rend ce cas exact.
- Contre-exemple local A/D : `even_high_cycle_plus_low_hub(7)` avec
  `balanced_pc_tree(7, kind="mixed")` ; toutes les `16` frontiers sont non-cR,
  mais les projections locales `I_x(v)` restent compatibles sur tous les nœuds.
- Commande exécutée : `pytest -q tests/test_candidate.py tests/test_local_constraints.py`.
- Résultat correction : `59 passed`.
- Commande exécutée : benchmark ciblé
  `matching_high_graph_plus_low_hub/star`, tailles `21,41,81,101`, répétitions
  `3`, timeout `2.0`.
- Résultat benchmark ciblé :
  `reports/complexity_matching_low_hub_t040_probe.json` écrit ; `0` timeout,
  `0` incomplet ; à `n=101`, médiane `0.1812s`, p95 `0.1818s`.
- Commande exécutée : `make unit`.
- Résultat correction : `167 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `167 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.000983s`, p95
  `0.001069s`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `0.0265s`, p95 `0.0363s`,
  fit polynomial empirique `p ~= 1.72`.
- Conclusion : T040 améliore un vrai positif PC-tree non-star et corrige une
  borne trop pessimiste, tout en gardant les échecs de recherche incomplets. La
  suffisance d'un strong ordering donné est maintenant documentée comme preuve
  bad-side, mais la reconnaissance PC-tree-compatible reste non générale.
- Next action : implémenter le sous-cas chain/Ferrers low-hub permuté comme
  certificat positif vérifié, ou ajouter le rapport CSP non-star proposé par le
  sidecar pour mesurer précisément les cas où le témoin global n'est pas
  représenté.

## 2026-05-23 permuted Ferrers low-hub witness

- Date/heure : 2026-05-23 06:23:32 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : pour une matrice binaire `low/high` avec hub bas, si le
  graphe haut privé est biparti Ferrers/chain, alors l'ordre obtenu par
  voisinages emboîtés décroissants d'une part et ordre opposé de l'autre part
  est un strong ordering. Par le lemme bad-side T040, `hubs,A,B` est un témoin
  cR, à condition de le vérifier et de vérifier sa représentation par le
  PC-tree.
- Changement fait : ajout de
  `permuted_chain_high_graph_plus_low_hub`; ajout de
  `low_hub_ferrers_strong_ordering_report`; intégration dans `candidate.py`
  comme certificat positif vérifié avant l'itérateur factoriel ; régressions
  pour chaîne permutée grande, matching non-Ferrers, et PC-tree non-star où le
  témoin Ferrers canonique est non représenté mais un autre témoin existe.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `167 passed`, puis `JUSTE`.
- Plan subagents : quatre sidecars lecture seule. Résultats : preuve Ferrers
  validée sous inclusion réelle des voisinages ; aucune fausse acceptation
  trouvée sur `7552` probes Ferrers/permutées ni `600` probes jusqu'à `n=101` ;
  explosion factorielle confirmée avant T041 (`n=15` : premier témoin après
  `11,594,305` couples) ; contre-exemple non-star ajouté montrant que le témoin
  Ferrers canonique peut être cR mais non représenté ; contre-exemple au tri par
  degrés seulement sur matching low-hub `n=5`.
- Commande exécutée : `pytest -q tests/test_candidate.py tests/test_local_constraints.py tests/test_generators.py`.
- Résultat correction : `76 passed`.
- Commande exécutée : benchmark ciblé
  `permuted_chain_high_graph_plus_low_hub/star`, tailles
  `9,11,15,17,21,41,81,101`, répétitions `10`, timeout `2.0`.
- Résultat benchmark ciblé :
  `reports/complexity_permuted_chain_low_hub_star.json` écrit ; `0` timeout,
  `0` incomplet ; à `n=101`, médiane `0.2606s`, p95 `0.2677s`, fit polynomial
  empirique `p ~= 3.05`.
- Commande exécutée : `make unit`.
- Résultat correction : `171 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `171 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.00112s`, p95 `0.00122s`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `0.0287s`, p95 `0.0360s`,
  fit polynomial empirique `p ~= 1.76`.
- Conclusion : T041 supprime une explosion factorielle sur les graphes haut
  Ferrers relabellisés et fournit un certificat positif polynomial pour ce
  sous-cas. Ce n'est pas une caractérisation complète : matching low-hub reste
  positif non-Ferrers, les PC-trees non-star peuvent rejeter le témoin Ferrers
  canonique, et tout échec Ferrers reste non conclusif.
- Next action : explorer une reconnaissance polynomial-time plus large des
  graphes bipartis à strong-ordering compatibles PC-tree, ou produire un
  rapport CSP non-star hors candidate pour mesurer les conflits de
  représentation.

## 2026-05-23 component Ferrers low-hub witness

- Date/heure : 2026-05-23 06:38:19 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : pour une matrice binaire `low/high` avec hubs bas, si
  chaque composante du graphe haut privé est chain/Ferrers, alors concaténer les
  composantes dans le même ordre côté `A` et côté `B` produit un strong ordering
  global ; par le lemme bad-side T040, `hubs,A,B` est cR.
- Changement fait : ajout de `disjoint_chain_high_graph_plus_low_hub` et
  `permuted_disjoint_chain_high_graph_plus_low_hub`; ajout de
  `low_hub_component_ferrers_strong_ordering_report`; intégration dans
  `candidate.py` comme certificat positif vérifié ; régressions pour trois
  composantes permutées, matching dégénéré, graphe non-Ferrers, `low=0` avec
  hubs multiples, composantes désalignées, et PC-tree non-star où le témoin
  component-wise est cR mais non représenté.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `171 passed`, puis `JUSTE`.
- Plan subagents : cinq sidecars lecture seule. Résultats : preuve
  component-wise validée sous l'hypothèse du même ordre de composantes côté
  `A/B`; contre-exemple minimal deux arêtes désalignées ; mesure de l'explosion
  pré-T042 (`n=17` atteint la limite `100000` et devient placeholder) ;
  comparaison avec les graphes bipartis permutation montrant que T042 est un
  sous-cas strict ; checklist documentaire fournie.
- Commande exécutée : `pytest -q tests/test_candidate.py tests/test_local_constraints.py tests/test_generators.py`.
- Résultat correction : `86 passed`.
- Commande exécutée : probe exact petits cas
  `permuted_disjoint_chain_high_graph_plus_low_hub/star` pour `n=5..8`, seeds
  `0..9`.
- Résultat correction : aucun mismatch avec l'oracle exact ; tous les témoins
  positifs renvoyés sont cR.
- Commande exécutée : benchmark ciblé
  `permuted_disjoint_chain_high_graph_plus_low_hub/star`, tailles
  `13,17,21,31,41,81,101`, répétitions `10`, timeout `2.0`.
- Résultat benchmark ciblé :
  `reports/complexity_disjoint_chain_low_hub_star.json` écrit ; `0` timeout,
  `0` incomplet ; à `n=101`, médiane `0.2433s`, p95 `0.2454s`, fit polynomial
  empirique `p ~= 3.12`.
- Commande exécutée : `make unit`.
- Résultat correction : `181 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `181 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.00111s`, p95 `0.00123s`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `0.0295s`, p95 `0.0359s`,
  fit polynomial empirique `p ~= 1.76`.
- Conclusion : T042 élargit le certificat positif low-hub de Ferrers connexe à
  unions de composantes Ferrers et supprime une nouvelle explosion factorielle
  sur star. Ce n'est pas une reconnaissance générale des graphes bipartis à
  strong ordering, et les conflits de représentation PC-tree non-star restent
  incomplets.
- Next action : construire une intersection PC-tree avec les ordres
  component-Ferrers/strong-ordering ou ajouter hors candidate un rapport de
  reconnaissance bipartite permutation produisant un témoin vérifiable.

## 2026-05-23 PC-tree guided matching witness

- Date/heure : 2026-05-23 07:05:01 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : pour une matrice binaire `low/high` avec hubs bas et
  graphe haut matching, un frontier PC-tree contenant un segment avec exactement
  un endpoint de chaque paire peut guider la construction d'un témoin
  `hubs,A,B` représenté. Cette hypothèse ne donne qu'un certificat positif si
  l'ordre construit est ensuite vérifié cR et représenté.
- Changement fait : ajout de
  `pc_tree_guided_low_hub_matching_witness_report`; intégration dans
  `candidate.py` comme solver
  `candidate_low_hub_pc_tree_guided_matching_witness`; recherche sample-first
  avant énumération bornée ; régressions pour les cas non-star T040/T042,
  `low=0`, contrôles `C6/C8/tree`, split-hubs manqué et frontier tardive
  dépendante de `frontier_limit`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `181 passed`, puis `JUSTE`.
- Plan subagents : quatre sidecars lecture seule. Résultats : audit soundness
  validé sous garde matching/bad-side/representation ; mesure T040/T042
  confirmant un passage de recherche factorielle ou placeholder vers
  `templates_checked=1`; contre-exemples split-hubs `n=6` et frontier-limit
  `n=8`; checklist documentaire appliquée.
- Commande exécutée : `pytest -q tests/test_local_constraints.py tests/test_candidate.py tests/test_generators.py`.
- Résultat correction : `91 passed`.
- Commande exécutée : probes ciblées T040/T042 et matchings `star/mixed`
  `n=9,11,13,17`, seeds `0..4`.
- Résultat probes : T040 `n=18` et T042 `n=17` sont positifs complets par
  `candidate_low_hub_pc_tree_guided_matching_witness` avec
  `frontiers_sampled=0`; les probes mixed gardent `5/20` incomplets visibles,
  donc l'échec T043 n'est pas caché en rejet.
- Commande exécutée : `make unit`.
- Résultat correction : `186 passed`.
- Commande exécutée : `make quick`.
- Résultat correction : `186 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.00118s`, p95 `0.00132s`,
  fit polynomial empirique `p ~= 1.84`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `0.0314s`, p95 `0.0369s`,
  fit polynomial empirique `p ~= 1.80`.
- Conclusion : T043 améliore les matchings low-hub non-star ciblés et remplace
  une recherche factorielle par un certificat guidé PC-tree sample-first. Ce
  n'est pas une intersection complète : split-hubs et frontiers tardives restent
  des limites explicites, et tout échec du rapport reste incomplet.
- Next action : formaliser une vraie intersection PC-tree avec les ordres
  matching/component-Ferrers/strong-ordering, en commençant par les hubs
  séparés et par une stratégie non bornée pour éviter les témoins tardifs.

## 2026-05-23 projected frontier matching witness

- Date/heure : 2026-05-23 07:18:06 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : dans une matrice binaire `low/high` avec hubs bas et
  graphe haut matching, un ordre fixé est cR si et seulement si la projection
  sur les non-hubs fait croiser toutes les arêtes hautes deux à deux. On peut
  donc accepter un frontier PC-tree représenté tel quel si cette projection
  passe, après revérification cR et `represents_order`.
- Changement fait : ajout du test de projection `_matching_crossing_parts` dans
  `pc_tree_guided_low_hub_matching_witness_report`, avant la construction
  segmentaire T043 ; exposition du compteur `projected_frontiers_checked` dans
  `candidate.py`; régressions pour split-hubs `n=6`, split-hubs large `n=12`,
  non-crossing C `n=6`, et équivalence fixed-order sur `n=5..8`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `186 passed`, puis `JUSTE`.
- Plan subagents : cinq sidecars lecture seule. Résultats : preuve bad-side du
  lemme et de sa réciproque dans le sous-cas matching ; aucun faux positif sur
  probes exacts `n=5..10` et `400` couples `(D, PC-tree)` petits ; mesure
  montrant que T044 corrige les hubs séparés mais ne résout ni T040/T042 sans
  fallback segmentaire, ni les frontiers tardives ; rappel que l'API `PCNode`
  ne fournit pas encore d'intersection non bornée.
- Commande exécutée : `pytest -q tests/test_local_constraints.py tests/test_candidate.py tests/test_generators.py`.
- Résultat correction : `94 passed`.
- Commande exécutée : probe exact petits matchings `n=5..8` sur star,
  balanced/mixed, split-hubs, non-crossing C et frontier tardive.
- Résultat probe : tout témoin positif du rapport est cR et représenté ;
  split-hubs `n=6` est trouvé au premier frontier projeté ; non-crossing C
  `n=6` est exact négatif ; frontier tardive `n=8` reste manquée à
  `frontier_limit=64`.
- Commande exécutée : `make quick`.
- Résultat correction : `189 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.00120s`, p95 `0.00136s`,
  fit polynomial empirique `p ~= 1.85`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `0.03139s`, p95 `0.03742s`,
  fit polynomial empirique `p ~= 1.79`.
- Conclusion : T044 transforme la limite split-hubs de T043 en certificat
  positif sound dès qu'un frontier projeté croisé est inspecté, et verrouille la
  caractérisation fixed-order du sous-cas matching. L'existence dans un PC-tree
  compact reste non résolue : un échec de projection ou de limite de frontiers
  reste incomplet.
- Next action : construire un diagnostic exact petit `seq + mate(seq)` après
  pruning des hubs pour mesurer la vraie intersection PC-tree/matching, puis
  tenter un état DP/CSP si les contre-exemples locaux restent contrôlables.

## 2026-05-23 exact bounded matching projection search

- Date/heure : 2026-05-23 07:31:34 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : dans le sous-cas binaire low-hub matching, les ordres cR
  sont exactement les projections `seq + mate(seq)` avec hubs insérés
  arbitrairement. Si ces candidats uniques sont épuisés sous une limite, alors
  l'existence dans le PC-tree scaffold est décidée exactement pour ce sous-cas.
- Changement fait : ajout de
  `exact_low_hub_matching_projection_search_report`; intégration candidate
  bornée après T043/T044 et seulement si la borne PC-tree générale dépasse
  `EXACT_PC_TREE_FRONTIER_LIMIT`; énumération paresseuse jusqu'à
  `EXACT_LOW_HUB_MATCHING_PROJECTION_LIMIT = 100000`; métriques de borne brute,
  borne canonique, doublons, checks de représentation et checks cR ; régressions
  frontier tardive `n=8`, rigide non-crossing `n=6`, limite basse, lazy hit
  `n=13`, et rejet candidate non-crossing `n=12`.
- Commande exécutée avant modification : `make quick`.
- Résultat correction avant modification : `189 passed`, puis `JUSTE`.
- Plan subagents : cinq sidecars lecture seule. Résultats : preuve de
  complétude de `seq + mate(seq)` plus hubs sous les hypothèses matching ;
  aucun mismatch sur plusieurs centaines de couples petits `(D,T)` ; mesure
  montrant que T045 ne résout pas les placeholders mixed `n=17` et doit rester
  gardé ; recommandation appliquée de limite `100000` et de test
  `represents_order` avant cR.
- Commande exécutée : `pytest -q tests/test_local_constraints.py tests/test_candidate.py tests/test_generators.py`.
- Résultat correction : `99 passed`.
- Commande exécutée : probe oracle petits matchings contre
  `exact_oracle_pc_tree`.
- Résultat probe : `19` couples matching/PC-tree sans mismatch ; tout témoin
  trouvé est cR et représenté.
- Commande exécutée : `make quick`.
- Résultat correction : `194 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.00126s`, p95 `0.00143s`,
  fit polynomial empirique `p ~= 1.85`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `0.03311s`, p95 `0.03756s`,
  fit polynomial empirique `p ~= 1.81`.
- Conclusion : T045 donne une décision exacte bornée du sous-cas matching
  low-hub et produit des négatifs complets quand l'énumération finit. Il reste
  combinatoire, ne résout pas les placeholders mixed `n=17`, et tout dépassement
  de limite reste incomplet.
- Next action : chercher une formulation DP/CSP de l'intersection
  PC-tree avec les formes `seq + mate(seq)`, ou produire un contre-exemple
  minimal à une règle locale de synchronisation.

## 2026-05-23 hub-projected matching PC-tree lift

- Date/heure : 2026-05-23 07:50:07 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : dans le sous-cas binaire low-hub matching, on peut
  énumérer seulement les projections high-vertices `seq + mate(seq)` puis les
  relever exactement dans le PC-tree original. Cela enlève le facteur
  combinatoire des placements de hubs de T045, tout en gardant un rejet complet
  uniquement si toutes les projections uniques sous limite sont épuisées.
- Changement fait : ajout de
  `exact_low_hub_matching_projected_pc_tree_search_report`, d'un releveur
  récursif de projection dans les nœuds `P/C`, et intégration candidate avant
  l'énumération complète T045. Ajout de tests frontier tardive, rigide
  non-crossing, limite projection, facteur hubs, oracle petits PC-trees, rejet
  candidate avec beaucoup de hubs, contre-exemple local `I_x(v)` minimal `n=5`
  et contre-exemple side-only/2-SAT naïf.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `194 passed`, puis `JUSTE`.
- Plan subagents : cinq sidecars lecture seule. Résultats : Piste A trouve le
  contre-exemple minimal `n=5` aux règles locales `I_x(v)` ; Piste B confirme
  que T046 est une étape vers DP mais doit transporter l'ordre des paires
  ouvertes ; Piste C recommande des nogoods 4-aires/support-local et fournit le
  contre-exemple side-only ; Piste complexité classe T046 comme exact borné et
  non polynomial ; Piste E/F a été fermée après timeout sans livrable.
- Commande exécutée : `pytest -q tests/test_local_constraints.py
  tests/test_candidate.py tests/test_regression_counterexamples.py`.
- Résultat correction : `102 passed`.
- Commande exécutée : probe oracle matching low-hub sur petits PC-trees.
- Résultat probe : `14` couples matching/PC-tree sans mismatch entre
  `exact_oracle_pc_tree` et le rapport projeté complet.
- Commande exécutée : `make quick`.
- Résultat correction : `202 passed`, puis `JUSTE`.
- Commande exécutée : `make hunt-counterexamples`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.001331s`,
  p95 `0.001514s`, fit polynomial empirique `p ~= 1.91`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `0.03504s`,
  p95 `0.04181s`, fit polynomial empirique `p ~= 1.82`.
- Conclusion : T046 améliore strictement T045 sur les hubs en énumérant les
  projections plutôt que les ordres complets, avec témoins revérifiés et
  négatifs complets seulement sous limite. Cela reste factoriel en nombre de
  paires et ne résout pas l'intersection PC-tree générale.
- Next action : remplacer l'énumération `2^m * m!` par une DP/CSP
  support-local qui transporte l'ordre des paires ouvertes, ou documenter un
  contre-exemple montrant que cette compression explose.

## 2026-05-23 support-local bad-side nogood compilation

- Date/heure : 2026-05-23 08:07:33 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les variables de `quartet_support_paths(T, atom)`
  déterminent l'ordre relatif des quatre labels d'un atom bad-side. On peut
  donc compiler les signatures de pruning en énumérant seulement le produit des
  domaines de ce support, au lieu de parcourir toutes les affectations complètes
  du PC-tree pour chaque atom.
- Changement fait : ajout de
  `compile_bad_side_nogoods_support_local`,
  `compile_cr_nogoods_support_local`,
  `_project_atom_order_from_support_assignment` et
  `solve_support_local_bad_side_nogood_csp`; extension de
  `tools/pc_csp_internal_benchmark.py` avec métriques support-local,
  `same_effective_signatures`, `signature_mismatches` et
  `support_vs_old_scan_ratio`; tests de reconstructeur, wrapping,
  equal-distance, limite de compilation, collision de canonicalisation et solve
  pruné support-local.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `202 passed`, puis `JUSTE`.
- Plan subagents : quatre sidecars lecture seule. Résultats : audit Piste C
  valide l'approche au niveau signatures et recommande de ne pas comparer
  `(atom, signature)` ; Piste B trouve une collision de canonicalisation globale
  ajoutée en test ; contre-exemples exécute `1491` cas sans mismatch de
  signatures seules ni mismatch solveur ; complexité montre que le coût passe de
  `full_assignment_space * atoms` à `sum_support_products`, avec gains nets sur
  probes plus grandes mais pas toujours sur petits arbres.
- Commande exécutée : `pytest -q tests/test_sat_like_experiments.py`.
- Résultat correction : `26 passed`.
- Commande exécutée : probe support-local bad-side sur familles
  `random/cycle/block/ultrametric/equal/non_strict/paired_farthest/permuted_cycle`,
  arbres balanced/mixed et cas matching low-hub.
- Résultat probe : `577` couples famille/tree sans mismatch de signatures ni
  mismatch solveur contre le CSP cR direct.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch, `0` support mismatch,
  `0` signature mismatch ; médiane compilation complète `0.00104s`, médiane
  compilation support-local `0.00276s`, médiane solve support-local
  `0.000120s`, ratio médian `support_vs_old_scan_ratio=0.25`,
  `total_support_unique_nogoods=2904` contre
  `total_unique_nogoods=31616`.
- Commande exécutée : `make quick`.
- Résultat correction : `209 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark rapide : `reports/complexity_report_quick.json` écrit ;
  `0` timeout, `0` incomplet ; à `n=20`, médiane `0.001340s`,
  p95 `0.001529s`, fit polynomial empirique `p ~= 1.90`.
- Commande exécutée : `make bench`.
- Résultat benchmark fort : `reports/complexity_report.json` écrit ; `0`
  timeout, `0` incomplet jusqu'à `n=100`, médiane `0.03458s`,
  p95 `0.03771s`, fit polynomial empirique `p ~= 1.81`.
- Conclusion : T047 est un progrès de représentation CSP et de métrique :
  les signatures de pruning sont obtenues sans scan complet par atom et sont
  beaucoup moins nombreuses que les nogoods atom-labellisés. Sur les petites
  tailles du benchmark, la compilation support-local n'est pas encore plus
  rapide, donc ce n'est pas une solution algorithmique générale.
- Next action : regrouper les atoms par support/signature partielle ou chercher
  une borne structurelle sur `sum_support_products`; garder T047 hors
  `candidate.py` tant que cette borne n'existe pas.

## 2026-05-23 grouped support-local bad-side compilation

- Date/heure : 2026-05-23 08:24:11 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les atoms bad-side partagent massivement leur
  `quartet_support_paths`. En groupant les atoms par support, on peut énumérer
  chaque produit de domaines une seule fois et conserver les mêmes signatures de
  pruning que T047, tout en mesurant séparément le coût restant `atom_checks`.
- Changement fait : ajout de
  `compile_bad_side_nogoods_grouped_support_local` et
  `solve_grouped_support_local_bad_side_nogood_csp`; métriques
  `grouped_support_product_total`, `support_product_total_if_ungrouped`,
  `grouped_vs_ungrouped_support_ratio`, `atom_checks`,
  `support_group_count`, `max_atoms_per_support` et
  `effective_signature_count`; extension de
  `tools/pc_csp_internal_benchmark.py` avec métriques et mismatch groupés ;
  tests ciblés de signatures seules, solveur pruné, limite, unsupported et
  absence de faux pruning cR.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : worktree déjà dirty T048
  (`PLANS.md`, `sat_like_experiments.py`) ; `209 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : audit Piste C sans
  faux positif/faux négatif évident et recommandation de tests ajoutés ; Piste F
  mesure des collisions massives de support avec gains de produit `8x..43x`
  jusqu'à `n=10`, mais signale que `atom_checks` reste le coût critique ; Piste
  contre-exemples trouve `0` mismatch sur `84` cas généraux et `18` cas
  low-hub matching.
- Commande exécutée : `pytest -q tests/test_sat_like_experiments.py`.
- Résultat correction : `31 passed`.
- Commande exécutée : probe indépendant multi-familles `n=4..7` sur arbres
  balanced/mixed.
- Résultat probe : `130` cas, `0` mismatch de signatures, `0` mismatch solveur
  support-local/groupé, `0` mismatch contre le CSP cR direct ; produit support
  T047 `50048`, produit groupé `4128`, ratio `0.08248`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch, `0` support mismatch,
  `0` grouped mismatch, `0` signature mismatch,
  `0` grouped signature mismatch ; produit support T047 `72256`, produit
  groupé `6224`, ratio médian `0.11111`,
  `total_grouped_atom_checks=72256`, mêmes `2904` signatures que T047.
- Commande exécutée : `make quick`.
- Résultat correction : `214 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Résultat benchmark candidate : non relancé à ce stade ; `candidate.py` n'a
  pas été modifié par T048.
- Conclusion : T048 réduit clairement l'énumération des produits de supports
  distincts et confirme que les supports sont très partagés, mais le coût
  atom-par-atom reste inchangé dans l'implémentation naïve. Cela reste une
  brique Piste C hors candidate, pas une preuve de solveur compact.
- Next action : factoriser les atoms au sein d'un même support ou prouver une
  borne structurelle sur la taille des groupes de support ; sinon basculer vers
  une piste DP qui transporte directement les contraintes par support.

## 2026-05-23 first-hit grouped support compilation

- Date/heure : 2026-05-23 08:32:32 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : dans un groupe d'atoms partageant le même support, une
  affectation de support qui fait apparaître au moins un atom produit déjà la
  signature de pruning complète. Scanner les autres atoms de ce groupe pour la
  même affectation est redondant pour la décision, même si cela donne plus de
  diagnostics.
- Changement fait : ajout de
  `compile_bad_side_nogoods_grouped_first_hit_support_local` et
  `solve_grouped_first_hit_support_local_bad_side_nogood_csp`; métriques
  `stopped_after_first_hit`, `atom_checks_if_exhaustive` et
  `atom_checks_saved_by_first_hit`; extension du benchmark interne avec
  métriques et mismatches first-hit ; tests de signatures, solveur, limite,
  unsupported, absence de faux pruning, cas dense et perte diagnostique
  volontaire.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre sur `c142884`; `214 passed`, puis `JUSTE`.
- Plan subagents : quatre sidecars lecture seule. Résultats : audit soundness
  validant l'arrêt au premier hit pour les signatures effectives ; Piste B
  fournit un cas minimal où les signatures restent identiques mais les
  diagnostics atoms/pairs diminuent ; contre-exemples couvre `220` cas sans
  mismatch et mesure `356612 -> 82052` atom checks ; complexité couvre `160`
  cas jusqu'à `n=8`, `0` mismatch, et `48888/87328` checks évités (`56.0%`).
- Commande exécutée : `pytest -q tests/test_sat_like_experiments.py`.
- Résultat correction : `39 passed`.
- Commande exécutée : probe indépendant multi-familles `n=4..7` sur arbres
  balanced/mixed.
- Résultat probe : `130` cas, `0` mismatch de signatures,
  `0` mismatch contre le CSP cR direct ; `grouped_atom_checks=49760`,
  `first_hit_atom_checks=24168`, gain `25592`, ratio sauvegardé `0.5143`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch, `0` first-hit mismatch,
  `0` first-hit signature mismatch, mêmes `2904` signatures que T047/T048 ;
  `total_grouped_atom_checks=72256`,
  `total_first_hit_atom_checks=41872`,
  `total_first_hit_atom_checks_saved=30384`.
- Commande exécutée : `make quick`.
- Résultat correction : `222 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Résultat benchmark candidate : non relancé ; `candidate.py` n'a pas été
  modifié par T049.
- Conclusion : T049 est une optimisation sound des signatures de pruning et
  réduit réellement le coût atom-par-atom mesuré. Ce n'est pas une DP compacte :
  les diagnostics d'obstruction ne sont plus exhaustifs, et les groupes sans hit
  rapide restent linéaires en nombre d'atoms.
- Next action : mesurer et factoriser les groupes où le premier hit arrive
  tard, ou construire une table de support symbolique qui évite le scan
  séquentiel.

## 2026-05-23 first-hit position profiling

- Date/heure : 2026-05-23 08:39:35 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : pour savoir quoi optimiser après T049, il faut distinguer
  les hits précoces, les hits tardifs et les affectations de support sans aucun
  hit. Si les no-hit dominent, un simple réordonnancement des atoms ne suffira
  pas.
- Changement fait : ajout des métriques `first_hit_assignments`,
  `first_hit_no_hit_assignments`, `first_hit_position_histogram`,
  `first_hit_max_position`, `first_hit_average_position`,
  `first_hit_checks_spent_on_no_hit`, `first_hit_checks_saved_on_hits` et
  `atom_checks_if_exhaustive_seen`; extension du benchmark interne avec ces
  agrégats ; tests comptables pour les cas complets, limités, equal-distance et
  les agrégats JSON du benchmark.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre sur `337a2ea`; `222 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats déjà reçus : audit
  de non-interférence confirmant que les compteurs ne changent ni signatures ni
  frontiers et recommandant de documenter leur dépendance à l'ordre de scan ;
  probe complexité `960` échantillons, `0` unsupported/incomplet,
  `34264` affectations de support, `21256` hits, `13008` no-hit,
  `273880` atom checks et `273288` checks sauvés.
- Commande exécutée :
  `pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction : `41 passed`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch, `0` first-hit mismatch,
  `0` mismatch de signatures ; `total_first_hit_assignments=2904`,
  `total_first_hit_no_hit_assignments=3320`, ratio no-hit `0.5334`,
  `total_first_hit_atom_checks=41872`,
  `total_first_hit_atom_checks_if_exhaustive_seen=72256`,
  `total_first_hit_atom_checks_saved=30384`,
  `total_first_hit_checks_spent_on_no_hit=30520`,
  `total_first_hit_checks_saved_on_hits=30384`,
  `total_first_hit_position_sum=11352`, max position `36`.
- Commande exécutée : probe par familles `n=4..8`.
- Résultat probe : random no-hit `21.9%`, cycle `50.0%`,
  paired-farthest `44.4%`, matching low-hub `25.7%`, equal-distance `0` atom.
- Commande exécutée : `make quick`.
- Résultat correction : `223 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Résultat benchmark candidate : non relancé ; `candidate.py` n'a pas été
  modifié par T050.
- Conclusion : T050 montre que les hits sont souvent précoces, mais que le coût
  restant de la gate CSP rapide est principalement dans les affectations sans
  hit. Les métriques sont dépendantes de l'ordre de scan des atoms et ne doivent
  pas être lues comme invariants mathématiques.
- Next action : chercher une contrainte agrégée par support qui certifie
  directement hit/no-hit, ou une borne structurelle sur les familles où le
  no-hit est fréquent.

## 2026-05-23 support no-hit outcome profile

- Date/heure : 2026-05-23 09:18:00 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : le hit/no-hit d'un support groupé peut être reformulé par
  paires endpoint et composantes de graphes de mauvais témoins. Si cela coïncide
  avec le scan atomique et réduit le travail, ce serait une piste de
  compression support-level ; sinon, c'est un contre-signal pour cette
  compression naïve.
- Changement fait : ajout de `bad_side_grouped_support_outcome_profile`, avec
  compteurs hit/no-hit, tranches unaires pures, coût no-hit, top groupes, test
  pair-side/composantes, et intégration au benchmark CSP interne. Aucun
  changement dans `candidate.py`.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre sur `460871f`; `223 passed`, puis `JUSTE`.
- Plan subagents : quatre sidecars lecture seule. Résultats : Piste C propose
  l'invariant pair-side et prévient que les tranches unaires seules sont faibles
  sur cycle/random ; Piste F classe les familles no-hit adverses
  (`cycle`, `ultrametric`, `non_strict`, `block`, `paired_farthest`) et les
  hits tardifs (`permuted_cycle`) ; Piste B formule la version
  graphe/composantes et les contre-exemples aux masques trop faibles ; Piste
  tests recommande de verrouiller que no-hit local n'est pas un certificat
  positif.
- Commande exécutée :
  `pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction : `44 passed`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch, `0` support/grouped/first-hit mismatch,
  `0` mismatch de signatures, `profile_pair_side_split_mismatches=0`.
  Totaux principaux : no-hit `3320/6224`, checks no-hit `30520`,
  couverture unaire no-hit `1888/3320`, no-hit ambigus `1432/3320`,
  travail pair-side `74248` checks, ratio pair-side/first-hit `1.7732`.
- Résultat par familles : `cycle` et `permuted_cycle` ont `0%` de couverture
  unaire no-hit ; `ultrametric` et `non_strict` ont une couverture unaire forte
  mais restent dominés par le coût no-hit. Le pair-side/composantes est exact
  mais plus cher que first-hit sur toutes les agrégations rapides observées.
- Commande exécutée : `make quick`.
- Résultat correction : `226 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `0` timeout et `0` incomplet sur les tailles
  `4,5,6,8,10,12,16,20`. `candidate.py` n'a pas été modifié par T051.
- Conclusion : T051 donne un diagnostic exact et un résultat négatif utile. Les
  tranches unaires seules ne couvrent pas les familles cycliques, et le
  pair-side/composantes naïf ne réduit pas la complexité mesurée. La piste reste
  utile seulement si les côtés de témoins sont précompilés ou transportés par
  une vraie DP.
- Next action : précompiler/mettre en cache les côtés de témoins par paire et
  sous-arbre, ou basculer vers une signature DP de composantes ouvertes.

## 2026-05-23 cached witness-side profile

- Date/heure : 2026-05-23 09:44:00 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : le côté d'un témoin `w` relativement à une paire `{a,b}`
  dépend seulement de la signature locale du support minimal du triple
  `(a,b,w)`. Un cache par `(pair,witness,signature_triple)` devrait réduire le
  coût pair-side T051 ; si ce n'est pas suffisant, il faut viser les checks de
  composantes.
- Changement fait : ajout de `_witness_side_cache_key`, compteurs
  `pair_side_split_side_cache_hits/misses`,
  `pair_side_split_cached_checks`, et modèle de coût
  `pair_side_split_bitset_cached_checks`; extension du benchmark interne et des
  tests. Import aussi du corpus de références utilisateur dans
  `docs/references/`, avec manifeste. Aucun changement dans `candidate.py`.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre sur `a852ca9`; `226 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : audit soundness
  confirmant que la clé triple complète est correcte et donnant un
  contre-exemple si le choix imbriqué est omis ; probe complexité `96` cas où le
  cache de côtés réduit les projections à `27.9%` des brutes mais reste
  `0.94x` first-hit une fois les composantes incluses ; tests recommandés pour
  garder le cache comme diagnostic non décisionnel.
- Commande exécutée :
  `pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction : `45 passed`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch, `0` support/grouped/first-hit mismatch,
  `0` mismatch de signatures, `profile_pair_side_split_mismatches=0`.
  Travail pair-side brut `74248` checks (`1.7732x` first-hit), cache simple
  `49558` checks (`1.1836x`), modèle bitset-composantes `27846` checks
  (`0.6650x`), hits/misses de cache `24690/12778`.
- Résultat par familles : cache simple gagnant sur
  `cycle/block/ultrametric/non_strict`, perdant sur
  `random/permuted_cycle/paired_farthest`. Le modèle bitset gagne partout sauf
  `paired_farthest`, qui reste autour de `1.0x`.
- Commande exécutée : `make quick`.
- Résultat correction : `227 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `40/40` runs réussis, `0` timeout et `0` incomplet sur les tailles
  `4,5,6,8,10,12,16,20`. `candidate.py` n'a pas été modifié par T052.
- Conclusion : T052 montre que la signature triple est une brique correcte,
  mais que le cache simple ne suffit pas comme amélioration algorithmique. Le
  prochain progrès crédible est une vraie structure bitset/composantes ou une
  DP qui transporte ces masques.
- Next action : implémenter un profil bitset réel par composante et tester
  `paired_farthest` comme stress family, ou basculer vers une DP de masques de
  côtés.

## 2026-05-23 real component-bitset profile

- Date/heure : 2026-05-23 09:37:26 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : le modèle T052
  `side_cache_misses + component_checks` peut être rendu effectif en cachant
  des masques de côtés par composante de mauvais témoins. Pour une paire
  `{a,b}`, une composante est hit ssi son masque vaut `0b11`.
- Changement fait : ajout de `_component_side_cache_key` et
  `_pair_side_bitset_outcome`, compteurs réels
  `pair_side_split_bitset_*`, champs JSON du benchmark CSP interne, tests de
  parité bitset/scan, support imbriqué, composantes group-local, cas
  equal/limit/unsupported, et régression paired-farthest label-identity. Aucun
  changement dans `candidate.py`.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `227 passed`, puis `JUSTE`.
- Plan subagents : quatre sidecars lecture seule. Résultats : Piste C liste les
  invariants de parité et edge cases ; Piste B classe les masques comme atome
  DP local exact mais non signature globale et fournit un contre-exemple
  paired-farthest label-identity ; Piste F mesure les familles stress
  `paired_farthest/random/permuted_cycle` ; Piste tests fournit les assertions
  anti-faux-sens ajoutées.
- Commande exécutée :
  `pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction intermédiaire : `49 passed`.
- Commande exécutée : `pytest -q tests/test_sat_like_experiments.py
  tests/test_csp_internal_benchmark.py tests/test_regression_counterexamples.py`.
- Résultat correction ciblée : `60 passed`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch,
  `profile_pair_side_split_mismatches=0`,
  `profile_pair_side_split_bitset_mismatches=0`.
  Totaux principaux : first-hit `41872` atom-checks, bitset réel `44936`
  checks (`1.0732x`), projection bitset `27822` checks (`0.6645x`),
  visites de témoins `29868`, cache composantes `3000/12068`, cache côtés
  bitset `17114/12754`.
- Résultat par familles : `cycle` et `non_strict` restent des contrôles
  positifs ; `random`, `permuted_cycle` et `paired_farthest` restent les stress
  où les visites de témoins rendent le bitset réel plus cher. Sur l'agrégat
  rapide, `paired_farthest/mixed` est autour de `1.55x` first-hit en coût réel.
- Commande exécutée : `make quick`.
- Résultat correction : `232 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `40/40` runs réussis, `0` timeout et `0` incomplet sur les tailles
  `4,5,6,8,10,12,16,20`. `candidate.py` n'a pas été modifié par T053.
- Conclusion : T053 est exact comme classifieur local support-level, mais
  réfute l'idée qu'un cache direct de masques de composantes suffise comme
  amélioration algorithmique. Le modèle de projection reste prometteur, mais il
  faut éviter les visites de témoins ou mesurer/compresser les états de masques.
- Next action : mesurer la cardinalité des états de masques par support et
  famille, puis chercher une DP qui transporte ces masques sans rescanner les
  témoins, avec `paired_farthest` comme stress prioritaire.

## 2026-05-23 component-mask state cardinality

- Date/heure : 2026-05-23 09:49:29 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les états locaux
  `((pair, component, side_mask), ...)` pourraient être beaucoup moins nombreux
  que les affectations de support. Si c'est vrai, ils peuvent être une brique
  de DP ; sinon, ils servent à réfuter la compression bitset directe.
- Changement fait : ajout des compteurs `component_mask_state_*` au profil
  support-level et au benchmark CSP interne : nombre d'états, états hit/no-hit,
  états mixtes, mismatches, bucket max/moyen, ratio état/affectation, visites de
  témoins, hits/misses du cache de côtés, et ratios de coût. Aucun changement
  dans `candidate.py`.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `232 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : Piste C valide
  l'état support-group-local et recommande de trier les paires et de documenter
  les agrégats comme somme par support ; Piste B classe la métrique comme
  filtre de falsification DP, pas preuve ; Piste F confirme que
  `random/permuted_cycle/paired_farthest` restent les familles stress.
- Commande exécutée :
  `pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée : `49 passed`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch,
  `component_mask_state_mixed_count=0`,
  `component_mask_state_mismatches=0`. Totaux principaux : `2920` états pour
  `6224` affectations, ratio `0.4692`, bucket moyen `2.1315`, bucket max `4`,
  coût complet d'état `1.9412x` first-hit, coût de projection `0.9038x`.
- Commande exécutée : probe stress
  `tools/pc_csp_internal_benchmark.py --sizes 8 --repeats 3 --instance-kinds
  random,cycle,non_strict,paired_farthest,permuted_cycle --pc-trees
  balanced,mixed`.
- Résultat probe stress : `30` lignes, `0` mismatch, ratio états/affectations
  `0.4921`, bucket moyen `2.032`, bucket max `4`.
- Commande exécutée : `make quick`.
- Résultat correction : `232 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `40/40` runs réussis, `0` timeout et `0` incomplet sur les tailles
  `4,5,6,8,10,12,16,20`. `candidate.py` n'a pas été modifié par T054.
- Conclusion : T054 donne un classifieur local exact et un quotient réel, mais
  la compression reste faible et stable autour d'un facteur `2`. Cela ne suffit
  pas comme piste DP compacte.
- Next action : chercher un état plus abstrait mais encore sound, ou basculer
  vers un sous-cas prouvable / une obstruction de complexité. Toute suite DP
  doit prouver la composition parent-enfant des états, pas seulement leur
  cardinalité locale.

## 2026-05-23 quotient component-mask states

- Date/heure : 2026-05-23 10:00:10 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : des projections plus abstraites de l'état complet T054
  peuvent compresser davantage les affectations de support tout en restant
  sound pour le hit/no-hit local. Un quotient est réfuté s'il contient des
  états mixtes hit/no-hit.
- Changement fait : ajout de `_component_mask_state_quotients` et des champs
  `component_mask_quotients` au profil support-level et au benchmark CSP
  interne. Quotients mesurés : `full`, `mask_multiset`,
  `pair_mask_multiset`, `hit_components`, `hit_pairs`, `decision_only`, et
  contrôle négatif `side_blind_schema`. Aucun changement dans `candidate.py`.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `232 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : Piste C classe
  `mask_multiset` comme quotient non tautologique intéressant et
  `side_blind_schema` comme contrôle négatif ; Piste F confirme que les ratios
  locaux s'améliorent mais sans gain de coût sur familles stress ; le sidecar
  contre-exemples trouve un cas minimal `cycle_metric(4)` où
  `side_blind_schema` a un état mixte, tandis que les quotients gardant les
  masques restent non mixtes sur ses probes bornées.
- Commande exécutée :
  `pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée : `50 passed`.
- Régression ajoutée :
  `test_component_mask_quotient_negative_control_has_minimal_mixed_state`
  fixe le contrôle négatif sur `cycle_metric(4)` et
  `balanced_pc_tree(4, kind="C")`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch. Ratios principaux :
  `full=0.4692`, `mask_multiset=0.3959`, `hit_components=0.2121`,
  `hit_pairs=0.2121`, `decision_only=0.1825`, et `side_blind_schema=0.1250`
  avec `358` états mixtes.
- Commande exécutée : probe stress
  `tools/pc_csp_internal_benchmark.py --sizes 8 --repeats 3 --instance-kinds
  random,cycle,non_strict,paired_farthest,permuted_cycle --pc-trees
  balanced,mixed`.
- Résultat probe stress : `30` lignes, `0` mismatch ; ratios
  `full=0.4921`, `mask_multiset=0.4088`, `hit_components=0.2273`,
  `decision_only=0.1821`, `side_blind_schema=0.1250` avec `181` états mixtes.
- Commande exécutée : `make quick`.
- Résultat correction : `233 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40` runs réussis, `0` timeout et `0` incomplet. `candidate.py`
  n'a pas été modifié par T055.
- Conclusion : T055 trouve des quotients locaux plus compressés que T054, mais
  les plus forts sont proches de la décision locale et ne prouvent aucune
  composition DP. Le contrôle sans masques devient mixte, ce qui confirme que
  les masques portent une information nécessaire.
- Next action : tester la stabilité de `mask_multiset` ou `hit_components` sous
  extension par contexte parent, ou changer d'axe vers un sous-cas prouvable si
  cette composition échoue.

## 2026-05-23 quotient context collisions

- Date/heure : 2026-05-23 10:18:19 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : un quotient T055 peut être exact pour le hit/no-hit local
  d'un support groupé, mais ne pas être composable. Si deux affectations d'un
  support `S` ont le même quotient et un même contexte externe dans
  `(S union C) \\ S`, alors un support voisin `C` ne devrait pas pouvoir les
  distinguer si le quotient est un état DP autonome.
- Changement fait : ajout du diagnostic
  `component_mask_quotient_context_collision_profile`, câblage du benchmark CSP
  interne, tests de contexte, limites/unsupported, et régression durable
  `test_mask_multiset_quotient_same_context_global_cr_collision_counterexample`.
  Aucun changement dans `candidate.py`.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `233 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : Piste B formalise
  les collisions `boundary_hit/global_cr`; Piste F recommande de traiter
  `mask_multiset` comme prioritaire et de garder `side_blind_schema` comme
  contrôle négatif ; le sidecar contre-exemples trouve un témoin global `n=5`
  où `mask_multiset=(1,2)` avec même contexte externe donne un ordre cR et un
  ordre non-cR.
- Commande exécutée :
  `pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée intermédiaire : `52 passed`.
- Commande exécutée :
  `pytest -q tests/test_regression_counterexamples.py
  tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée : `64 passed`.
- Régression ajoutée : matrice `n=5` avec `balanced_pc_tree(5, kind="C")`,
  support local `((), (0,), (0,0))`, même `mask_multiset=(1,2)`, même contexte
  externe `(1,)=(0,1)`, frontiers canoniques `(0,1,4,3,2)` cR et
  `(0,1,3,4,2)` non-cR, distingués par l'atome bad-side `(2,4,3,0)`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch. Diagnostic contexte :
  `35728` affectations contextuelles, `1828` paires profilées,
  `74` lignes incomplètes visibles car `max_pairs=20`.
  Collisions : `assignment_signature=0`, `full=190`,
  `mask_multiset=856`, `hit_components=2438`, `decision_only=2194`,
  `side_blind_schema=1334`.
- Commande exécutée : probe stress
  `tools/pc_csp_internal_benchmark.py --sizes 8 --repeats 2 --instance-kinds
  random,cycle,non_strict,paired_farthest,permuted_cycle --pc-trees
  balanced,mixed`.
- Résultat probe stress : `20` lignes, `0` mismatch ;
  `context_collision_assignments_seen=9072`, `assignment_signature=0`,
  `full=8`, `mask_multiset=26`, `hit_components=414`,
  `decision_only=354`.
- Commande exécutée : `make quick`.
- Résultat correction : `236 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40` runs réussis, `0` timeout et `0` incomplet. `candidate.py`
  n'a pas été modifié par T056.
- Conclusion : `mask_multiset`, `hit_components`, `hit_pairs` et
  `decision_only` sont réfutés comme états DP autonomes. Les collisions de
  `full` indiquent aussi que l'état de masques fermé par support ne porte pas
  les obligations ouvertes entre supports voisins.
- Next action : soit définir une signature avec obligations ouvertes entre
  supports voisins, soit basculer vers un sous-cas prouvable / une piste de
  complexité plutôt que continuer à quotienter les états fermés.

## 2026-05-23 open boundary response states

- Date/heure : 2026-05-23 10:40:53 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les collisions T056 des états fermés peuvent être réparées
  en transportant, pour chaque affectation locale d'un support `S`, les
  réponses hit/no-hit des supports voisins `C` sous tous les choix de
  `(S union C) \\ S`. Si la signature ouverte est quasi-injective, elle est trop
  chère ; si elle compresse, elle devient une piste DP à tester récursivement.
- Changement fait : ajout de `component_mask_open_boundary_profile`, agrégats
  `open_boundary_*` dans le benchmark CSP interne, tests d'accounting, tests de
  troncature/unsupported, et métriques de buckets où la réponse de bord ou le
  hit local reste mélangé. Aucun changement dans `candidate.py`.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `236 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : Piste B formalise
  `Open(S, alpha)` et signale le risque one-hop ; Piste F propose les agrégats
  `boundary_mixed_count`, ratios d'états et coûts ; le troisième sidecar n'a
  pas répondu avant intégration, donc la clôture s'appuie sur les deux retours
  reçus et les probes locales.
- Commande exécutée :
  `pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée : `54 passed`.
- Cas minimal : `cycle_metric(5)` avec
  `balanced_pc_tree(5, kind="mixed")`. Résultats :
  `support_group_count=3`, `context_pair_count=6`,
  `local_assignments_seen=24`, `boundary_response_checks=96`,
  `assignment_signature=24`, `mask_multiset=9`,
  `boundary_response=12`, `mask_multiset_plus_boundary=12`,
  `full_plus_boundary=12`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch. Diagnostic ouvert borné :
  `6224` affectations locales, `35728` checks de réponses ouvertes,
  `1828` paires profilées, `74` lignes incomplètes visibles,
  `average_boundary_entries_per_assignment=5.7404`.
  Ratios : `boundary_response=0.2208`,
  `local_boundary_response=0.2625`,
  `mask_multiset_plus_boundary=0.4291`,
  `full_plus_boundary=0.4770`.
  Buckets à réponses de bord mélangées : `mask_multiset=203`, `full=49`,
  `mask_multiset_plus_boundary=0`, `full_plus_boundary=0`,
  `local_boundary_response=0`.
- Commande exécutée : probe stress
  `tools/pc_csp_internal_benchmark.py --sizes 8 --repeats 2 --instance-kinds
  random,cycle,non_strict,paired_farthest,permuted_cycle --pc-trees
  balanced,mixed`.
- Résultat probe stress : `20` lignes, `0` mismatch ;
  `open_boundary_local_assignments_seen=2088`,
  `open_boundary_response_checks=9072`, `20` lignes incomplètes.
  Ratios : `boundary_response=0.1518`,
  `local_boundary_response=0.2126`,
  `mask_multiset_plus_boundary=0.4119`,
  `full_plus_boundary=0.4895`.
- Commande exécutée : `make quick`.
- Résultat correction : `238 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40` runs réussis, `0` timeout et `0` incomplet. `candidate.py`
  n'a pas été modifié par T057.
- Documents sources : les PDFs et la capture Proposition 4.4 fournis par
  l'utilisateur sont conservés dans `docs/source_materials/` avec hashes et
  restent aussi accessibles via `docs/references/`.
- Conclusion : les réponses ouvertes one-hop réparent les collisions T056
  mesurées et gardent une compression non triviale, mais ne prouvent pas une DP
  globale. La signature est encore énumérative, bornée, et non testée sur une
  composition de deuxième ordre.
- Next action : chercher activement une collision de second ordre pour
  `local_boundary_response`, ou prouver que les réponses one-hop se composent
  sous une hypothèse de support précise.

## 2026-05-23 external global review after T057

- Date/heure : 2026-05-23 10:40:53 CEST, même checkpoint documentaire que T057.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : la revue externe GPT 5.5 Pro ne doit pas verrouiller la
  recherche sur T057. Elle doit être transformée en portefeuille de pistes
  falsifiables.
- Changement fait : ajout de
  `docs/external_reviews/gpt55_global_strategy_2026-05-23.md`, mise à jour du
  digest externe, des pistes B/C/D/E/F, de `PLANS.md`, de
  `docs/proof_obligations.md` et du registre des pistes.
- Commande exécutée : mêmes gates finales que T057 :
  `make quick`, `make check`, `make bench-quick`, `make bench-csp-quick`.
- Résultat correction : `make quick` passe avec `238 passed` puis `JUSTE` ;
  `make check` affiche `JUSTE`.
- Résultat benchmark : `make bench-quick` écrit
  `reports/complexity_report_quick.json` avec `8` tailles ; `make
  bench-csp-quick` écrit `reports/csp_internal_benchmark_quick.json` avec
  `192` lignes, `0` mismatch et `74` lignes incomplètes visibles sur le profil
  ouvert borné.
- Conclusion : la réponse externe est utile, mais le prompt l'a trop ancrée sur
  T056/T057. La suite est donc explicitement élargie à cinq axes : bad-side
  exact, CSP quartets/treewidth, sous-cas booléen 2-SAT, catalogue relations
  binaires/NP-hardness, et collision second ordre T057.
- Next action : commencer par le rapport `quartet_pc_scope_report(D, T)`, car il
  sert de base commune au 2-SAT, à la DP treewidth, au relation catalog et aux
  stress-tests de signatures ouvertes.

## 2026-05-23 quartet PC scope report

- Date/heure : 2026-05-23 12:59:06 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : une formulation CSP exacte par quartets est possible si le
  type ou au moins l'acceptation cR d'un quartet dépend d'un petit scope de
  variables PC-tree. Il faut mesurer la portée effective, pas supposer que le
  support structurel `quartet_support_paths` est minimal.
- Changement fait : ajout de `quartet_type`, `quartet_allowed_types` et
  `quartet_pc_scope_report`, plus câblage dans
  `tools/pc_csp_internal_benchmark.py`. Aucun changement dans `candidate.py`.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre au commit `ff62fb1`; `238 passed`, puis `JUSTE`.
- Plan subagents : quatre sidecars lecture seule. Résultats : Piste C précise
  l'API et recommande de ne pas promouvoir `<=2` en théorème ; Piste A/D ne
  trouve pas de contre-exemple petit mais souligne que `quartet_support_paths`
  est conservateur ; Piste F recommande les métriques 2-SAT/treewidth/relation
  catalog ; Piste E fournit les stress tests nested/dense, égalités et binaire
  `n=5`.
- Commande exécutée :
  `pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée : `61 passed`.
- Tests ajoutés : types de quartet contre cR direct à 4 points, equal-distance,
  support nested/dense, équivalence des types locaux avec cR complet sur
  frontiers représentées, et exhaustif binaire `n=5` pour les atoms bad-side.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes, `0` mismatch. Métriques T058 :
  `quartet_scope_quartets_profiled=2688`,
  `quartet_scope_support_assignments_seen=21504`,
  `quartet_scope_projection_mismatches=0`,
  `quartet_scope_support_scope_gt_2_count=2688`,
  `quartet_scope_effective_type_scope_gt_2_count=0`,
  `quartet_scope_effective_acceptance_scope_gt_2_count=0`,
  `quartet_scope_two_sat_candidate_quartet_count=2688`,
  histogrammes support `{3: 2688}`, type `{2: 2688}`, acceptation
  `{0: 1536, 2: 1152}`.
- Commande exécutée : probe stress
  `n=4..8`, fanout `2/3`, arbres `P/C/mixed`, familles
  `random/cycle/equal/non_strict/paired_farthest/permuted_cycle`.
- Résultat probe stress : `180` cas, `4536` quartets,
  `0` mismatch de projection, `0` portée effective type/acceptation `>2`,
  `630` quartets à portée effective d'acceptation non booléenne sur les arbres
  `P` fanout `3`.
- Commande exécutée : `make quick`.
- Résultat correction : `245 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40` runs réussis, `0` timeout et `0` incomplet. `candidate.py`
  n'a pas été modifié par T058.
- Conclusion : T058 donne un signal fort pour poursuivre la formulation CSP par
  quartets. La portée effective binaire observée rend le sous-cas 2-SAT
  plausible sur les arbres binaires, mais les domaines non booléens des nœuds
  `P` imposent une piste relation-catalog/treewidth avant toute revendication
  générale.
- Next action : construire les relations effectives par scope, le graphe primal
  et une première classification 2-SAT / treewidth / relation non booléenne.

## 2026-05-23 effective quartet relation CSP

- Date/heure : 2026-05-23 13:21:13 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : le diagnostic de portée T058 peut être transformé en CSP
  relationnel exact sur le scaffold supporté : une relation par quartet, puis
  fusion par scope effectif, avec validation contre le prédicat cR direct.
- Changement fait : ajout de `quartet_effective_relation_report` hors
  `candidate.py`, extraction de la génération des rows support-local de
  quartet, ajout du graphe primal et de bornes greedy de treewidth, câblage
  dans `tools/pc_csp_internal_benchmark.py`, et documentation T059 dans les
  pistes C/F, obligations de preuve, plans et revue externe addendum.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop` propre
  au commit `c7dac6e`; `245 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : Piste C confirme
  que T059 doit matérialiser les relations exactes et ne pas devenir une suite
  de T057 ; Piste F recommande les métriques primal/treewidth/2-SAT et le
  catalogue non booléen ; Piste E fournit les tests adversariaux bad-side,
  CSP/quartets, C-only/2-SAT et P-node non booléen.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée : `67 passed`.
- Tests ajoutés : relation-CSP vs cR sur cycle balanced/mixed ; tautologie
  equal-distance C-only ; relation constante rejetante ; UNSAT C-only via
  `four_local_non_cr_core`; nœud `P3` non booléen non 2-SAT ; trois blocs `P3`
  avec relations binaires non booléennes et treewidth observée.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes supportées, `0` mismatch, `0`
  `quartet_scope_projection_mismatches`, `0`
  `quartet_relation_validation_mismatches`. Résumé relationnel :
  `quartet_relation_row_class_histogram={'two_sat_candidate': 192}`,
  `quartet_relation_scope_count=650`,
  `quartet_relation_binary_boolean_count=433`,
  `quartet_relation_binary_non_boolean_count=0`,
  `quartet_primal_max_treewidth_upper_bound=4`.
- Commande exécutée : `make quick`.
- Résultat correction : `251 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
  `candidate.py` n'a pas été modifié.
- Conclusion : T059 fournit une base CSP exacte et falsifiable pour plusieurs
  pistes : 2-SAT booléen, DP treewidth, catalogue non booléen et recherche de
  contre-exemples. Cela ne prouve pas le problème général et ne résout pas les
  grands `P`; les domaines `P3` restent explicitement catalogués comme non
  2-SAT dans les tests ciblés.
- Next action : implémenter un sous-cas exact à partir de cette base, en
  priorité C-only/2-SAT ou DP par treewidth bornée, puis chercher des familles
  non booléennes qui cassent ou enrichissent le catalogue.

## 2026-05-23 2-SAT from effective quartet relations

- Date/heure : 2026-05-23 13:37:02 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : toute ligne complète
  `row_class="two_sat_candidate"` du CSP relationnel T059 se réécrit exactement
  en 2-SAT, en transformant chaque signature rejetée en clause et en vérifiant
  directement tout témoin SAT reconstruit.
- Changement fait : ajout de `solve_quartet_2sat` hors `candidate.py`,
  conversion des relations fusionnées en clauses, résolution par SCC du graphe
  d'implications, reconstruction/validation de témoin, métriques 2-SAT dans
  `tools/pc_csp_internal_benchmark.py`, tests adversariaux C-only, mixed
  booléen, tautologies, UNSAT constants et refus explicite des nœuds `P3`.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop` propre
  au commit `93b7feb`; `251 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : Piste C précise
  l'API et la traduction des tuples rejetés ; Piste E/F fournit les tests
  adversariaux C-only/mixed/P3/non strict ; preuve/limites rappelle que l'UNSAT
  2-SAT ne doit pas être intégré en rejet général avant preuve du modèle
  relationnel.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée : `73 passed`.
- Tests ajoutés : cycle C-only positif non tautologique ; equal-distance et
  non strict à gros farthest comme tautologies ; `quasi_circular_not_circular`
  et `four_local_non_cr_core` comme UNSAT par clause vide ; arbre mixte booléen
  SAT ; nœud `P3` refusé comme `not_two_sat_candidate`; chemin par défaut sans
  validation exhaustive complète.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes supportées, `0` mismatch, `0`
  `quartet_relation_validation_mismatches`, `192`
  `quartet_2sat_complete_rows`, `143` SAT, `49` UNSAT par clause vide, `0`
  incomplet, `0` échec de témoin, `1167` clauses dont `1118` binaires et `49`
  vides.
- Commande exécutée : `make quick`.
- Résultat correction : `257 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
  `candidate.py` n'a pas été modifié.
- Conclusion : T060 valide le sous-cas booléen du CSP relationnel comme
  solveur 2-SAT expérimental et falsifiable. Il ne résout pas le problème
  général, ne couvre pas les domaines non booléens des grands `P`, et ne doit
  pas servir de certificat négatif global avant preuve de suffisance du modèle
  relationnel.
- Next action : poursuivre soit une intégration positive-only vérifiée dans
  `candidate.py`, soit une DP treewidth pour les relations non booléennes, en
  continuant le catalogue de contre-exemples sur les nœuds `P3+`.

## 2026-05-23 treewidth DP for effective quartet relations

- Date/heure : 2026-05-23 13:51:53 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : le CSP relationnel T059 peut être résolu exactement par
  élimination sous treewidth bornée, y compris avec domaines non booléens `P3`,
  en gardant toute ligne au-dessus des caps comme incomplète.
- Changement fait : ajout de `store_full_relations` à
  `quartet_effective_relation_report`, ajout de
  `solve_quartet_treewidth_csp` hors `candidate.py`, calcul exact borné d'ordre
  d'élimination, élimination de facteurs, reconstruction/validation de témoin,
  métriques DP dans `tools/pc_csp_internal_benchmark.py`, et tests adversariaux
  P3 non booléens, UNSAT implication, tautologie, constant reject et cap de
  largeur.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop` propre
  au commit `ae1ea84`; `257 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : Piste F/C
  recommande la bucket-elimination bornée avec table complète ; contre-exemples
  fournit UNSAT implication, support imbriqué, P3 positif/négatif et clique
  primal `p3_block_tree(k)` ; intégration candidate recommande de garder T060
  en positive-only avec garde stricte si elle est tentée plus tard.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée : `78 passed`.
- Tests ajoutés : UNSAT 2-SAT sans clause vide ; trois blocs `P3` sur
  `cycle_metric(9)` SAT par DP treewidth ; trois blocs `P3` sur
  `paired_farthest_matching(9, seed=7)` UNSAT relationnel ; equal-distance
  tautologique ; `four_local_non_cr_core` constant reject ; cap
  `max_treewidth=2` retournant `treewidth_cap_exceeded`.
- Commande exécutée : `make bench-csp-quick`.
- Résultat benchmark interne : `reports/csp_internal_benchmark_quick.json`
  écrit ; `192` lignes supportées, `0` mismatch, `0`
  `quartet_relation_validation_mismatches`, `186`
  `quartet_treewidth_complete_rows`, `137` SAT, `49` UNSAT, `6` incomplètes par
  `treewidth_cap_exceeded`, `0` échec de témoin et treewidth exacte maximale
  `3` sur les lignes complètes.
- Commande exécutée : `make quick`.
- Résultat correction : `262 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
  `candidate.py` n'a pas été modifié.
- Conclusion : T061 dépasse le sous-cas 2-SAT booléen dans le scaffold en
  traitant les domaines non booléens sous largeur bornée. Ce n'est toujours pas
  une solution générale : la construction relationnelle reste énumérative, les
  lignes trop larges sont incomplètes, et les UNSAT restent confinés au modèle
  T059 tant que sa suffisance globale n'est pas prouvée.
- Next action : profiler `p3_block_tree(k)` comme famille de largeur croissante
  et décider si une intégration positive-only dans `candidate.py` apporte un
  gain mesurable sans ralentir `make bench`.

## 2026-05-23 P3 block width stress profile

- Date/heure : 2026-05-23 14:00:06 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les arbres `p3_block_tree(k)` forment une famille de
  stress où les relations de quartets restent exploitables mais où la treewidth
  du graphe primal croît avec `k`, rendant la DP T061 FPT plutôt que
  polynomiale générale.
- Changement fait : ajout de `p3_block_tree(block_count)`, de
  `tools/pc_csp_width_stress.py`, de la cible `make bench-width-stress`, de
  tests de génération/profil de largeur, et documentation T062 dans les pistes,
  obligations de preuve, protocole, plans et README.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop` propre
  au commit `ee779a2`; `262 passed`, puis `JUSTE`.
- Plan subagents : pas de nouveau sidecar ; T062 réutilise les livrables T061
  qui demandaient explicitement le stress `p3_block_tree(k)`.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_pc_tree_frontiers.py tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée : `89 passed`.
- Tests ajoutés : structure du générateur `p3_block_tree(3)` ; profil largeur
  avec `max_treewidth=3` où `k=3` cycle est SAT à treewidth exacte `3` et
  `k=4` cycle devient incomplet `treewidth_cap_exceeded`.
- Commande exécutée : `make bench-width-stress`.
- Résultat benchmark largeur : `reports/p3_width_stress.json` écrit ; `12`
  lignes, `0` relation incomplète, `0` mismatch de validation, `11` lignes DP
  complètes, `8` SAT, `3` UNSAT relationnels, `1` incomplète par
  `treewidth_cap_exceeded`, treewidth primal upper bound max `5`, treewidth
  exacte max calculée `4` sous cap `4`, domaine max `6`, `0` échec de témoin.
- Commande exécutée : `make quick`.
- Résultat correction : `264 passed`, puis `JUSTE`.
- Commande exécutée : `make check`.
- Résultat correction : `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
  `candidate.py` n'a pas été modifié.
- Conclusion : T062 fournit un artefact reproductible montrant que la largeur
  est un vrai paramètre limitant pour T061. La ligne `cycle,k=5` devient
  incomplète sous cap, donc la DP ne doit pas être présentée comme solution
  polynomiale générale.
- Next action : tester l'intérêt réel d'une intégration positive-only dans
  `candidate.py` sous garde stricte, ou poursuivre le catalogue de relations
  non booléennes/gadgets.

## 2026-05-23 external bad-side/quartet strategy reroute

- Date/heure : 2026-05-23 14:11:24 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : la nouvelle revue GPT 5.5 Pro fournie par l'utilisateur
  doit être conservée comme input de recherche, mais re-routée vers plusieurs
  pistes car le prompt était trop ancré sur T056/T057.
- Changement fait : ajout d'une synthèse durable
  `docs/external_reviews/gpt55_bad_side_quartet_strategy_2026-05-23.md`,
  correction de l'addendum externe périmé par T060-T062, et mise à jour du
  portefeuille pour dire explicitement que T057 reste une piste, pas le plan
  unique.
- Commande exécutée avant modification : arrêt d'un probe ad hoc trop large
  sans sortie exploitable ; aucun résultat scientifique n'en a été tiré.
- Commande exécutée : `make quick`.
- Résultat correction : `264 passed`, puis `JUSTE`.
- Résultat benchmark : non applicable, changement documentaire.
- Conclusion : la documentation sépare maintenant la revue externe en axes
  bad-side, quartet CSP, 2-SAT/treewidth, circular-ones/universalité, gadgets
  non booléens et collision T057. Elle ne prétend pas résoudre le problème.
- Next action : lancer un probe borné pour mesurer si T060/T061 apportent de
  vrais témoins positifs nouveaux avant toute intégration dans `candidate.py`,
  ou basculer vers le catalogue de relations non booléennes/gadgets.

## 2026-05-23 single P-node domain stress

- Date/heure : 2026-05-23 14:35:00 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : la treewidth du CSP de quartets n'est pas un paramètre
  suffisant si un gros nœud `P` garde un domaine local factoriel. Le cas star a
  une seule variable et treewidth `0`, mais domaine `(n-1)!/2`.
- Changement fait : ajout du gadget `single_bad_side_quartet_instance`, de
  `tools/pc_single_p_domain_stress.py`, de la cible
  `make bench-single-p-stress`, d'un test ciblé, et documentation R003/T064
  dans les pistes, obligations de preuve, protocole et plans.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop` propre
  au commit `915bdb6`; `264 passed`, puis `JUSTE`.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py::test_single_p_domain_stress_exposes_factorial_domain_even_at_treewidth_zero`.
- Résultat correction ciblée : `1 passed`.
- Commande exécutée : `make bench-single-p-stress`.
- Résultat benchmark single-P : `reports/single_p_domain_stress.json` écrit ;
  `30` lignes, `12` skipped, `treewidth_zero_rows=30`,
  `max_domain_size=181440`, `max_complete_domain_size=20160`,
  `incomplete_exact_count_rows=4`, `max_unordered_bad_side_constraints=650`,
  `zero_cr_rows=5`, `all_cr_rows=6`.
- Commande exécutée : `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py tests/test_pc_tree_frontiers.py`.
- Résultat correction ciblée élargie : `13 passed`.
- Commande exécutée : `make quick`.
- Résultat correction finale : `265 passed`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
- Conclusion : T064 rend durable le point red-team : treewidth faible ne suffit
  pas sans borne/compaction prouvée des domaines `P`. `candidate.py` n'a pas
  été modifié.
- Next action : poursuivre avec un catalogue de relations non booléennes entre
  petits nœuds `P`, en reportant toujours contraintes parasites, taille de
  domaine et validité du promise.

## 2026-05-23 non-boolean P-node relation catalog

- Date/heure : 2026-05-23 15:22:31 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les blocs `P3` exposent des relations binaires non
  booléennes de domaine `6 x 6`; leur diversité et leurs parasites donnent un
  signal utile pour la piste dureté/FPT sans constituer une preuve.
- Changement fait : ajout de `tools/pc_relation_catalog.py`, de la cible
  `make bench-relation-catalog`, d'un test ciblé et des métriques red-team :
  tailles de domaine, scopes, densités, ratios de tuples rejetés, parasites,
  statut `relation_unsat_only`, caveat de promise et claim de complexité
  autorisé.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop` propre
  au commit `cdbf1ec`; `265 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : le sidecar CSP
  recommande de réutiliser `quartet_effective_relation_report` et de
  canonicaliser les relations binaires ; le sidecar adversarial recommande les
  lignes `p3x2/p3x3` cycle, paired, equal et obstructions paddées ; le sidecar
  red-team recommande de rendre visibles `q`, treewidth, parasites, mismatchs
  et statut expérimental.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py::test_relation_catalog_reports_non_boolean_p3_relations_and_parasites`.
- Résultat correction ciblée : `1 passed`.
- Commande exécutée : `make bench-relation-catalog`.
- Résultat benchmark catalogue : `reports/relation_catalog.json` écrit ;
  `20` lignes, `20` complètes, `0` mismatch, `18`
  `non_boolean_relation_catalog`, `2` `two_sat_candidate`, `38` relations
  binaires non booléennes, `27` hashes distincts, `12` lignes avec
  `constant_reject`, `18` lignes avec parasite unaire non booléen, treewidth
  upper bound max `3`, produit de domaine max `36`, `13` lignes avec
  `0` affectation acceptée.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée élargie : `4 passed`.
- Commande exécutée : `make quick`.
- Résultat correction finale : `266 passed`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
- Conclusion : T065 produit un catalogue utile pour la piste gadget/dureté, mais
  les parasites fréquents empêchent toute conclusion NP-hard. `candidate.py`
  n'a pas été modifié.
- Next action : analyser les hashes de relations pour chercher une relation
  permutation-like / equality / disequality isolable sans parasite constant, ou
  basculer vers la preuve de suffisance du modèle relationnel si les parasites
  dominent.

## 2026-05-23 relation shape mining for non-boolean P-node profiles

- Date/heure : 2026-05-23 15:39:07 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les relations non booléennes cataloguées en T065 ont des
  formes reconnaissables qui peuvent guider la recherche de gadgets ou de
  compression, mais seulement si les parasites restent visibles.
- Changement fait : ajout de `tools/pc_relation_shape_search.py`, de la cible
  `make bench-relation-shapes`, d'un test ciblé et de la documentation T066.
  L'outil classe les profils par fonctionnalité, histogrammes de degrés,
  densité, taille de domaine et tags de composabilité.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `265 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : un sidecar propose
  la taxonomie forme/composabilité et des assertions de tests ; un sidecar
  propose les prochaines familles adversariales (`single P`, élimination de
  parasites, chaînes fonctionnelles, parasites comme obstruction, relèvement
  vers gros `P`) ; un sidecar propose le langage documentaire prudent T066.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py::test_relation_shape_search_classifies_non_boolean_relation_profiles`.
- Résultat correction ciblée : `1 passed`.
- Commande exécutée : `make bench-relation-shapes`.
- Résultat benchmark shapes : `reports/relation_shape_search.json` écrit ;
  `20` lignes catalogue, `20` complètes, `0` mismatch, `38` profils binaires
  non booléens, `27` hashes distincts, histogramme des formes :
  `active_two_regular=10`, `left_selector=5`, `partial_bijection=3`,
  `right_selector=4`, `small_domain_bridge=6`,
  `sparse_partial_matching=9`, `total_cover_dense=1`, et
  `candidate_gadget_instances=0`.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée élargie : `5 passed`.
- Commande exécutée : `make quick`.
- Résultat correction finale : `267 passed`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
- Conclusion : T066 rend le catalogue T065 exploitable par forme, mais aucun
  profil positif parasite-free n'est encore observé. Cela ne prouve ni
  NP-hardness ni polynomialité. `candidate.py` n'a pas été modifié.
- Next action : lancer une recherche d'élimination de parasites sur une forme
  stable (`partial_bijection` ou `sparse_partial_matching`) ou composer des
  chaînes fonctionnelles pour chercher une obstruction globale non locale.

## 2026-05-23 functional relation chain probe

- Date/heure : 2026-05-23 15:51:25 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les relations fonctionnelles non booléennes observées en
  T066 peuvent soit produire une corrélation globale utile, soit révéler que les
  rejets restent expliqués par parasites unaires/constantes.
- Changement fait : ajout de `tools/pc_relation_chain_probe.py`, de la cible
  `make bench-relation-chains`, d'un test ciblé et de la documentation T067.
  L'outil reconstruit le CSP relationnel complet, isole les relations
  fonctionnelles, mesure leurs composantes/cycles et compare les comptes
  fonctionnel seul, binaire non booléen seul, parasites seuls et toutes
  relations.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `267 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : un sidecar
  recommande les métriques de composition chaînes/cycles ; un sidecar trouve un
  sweep `paired_farthest` avec relations `permutation_like` sans parasite
  restrictif ; un sidecar propose le langage documentaire prudent T067.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py::test_relation_chain_probe_finds_permutation_like_near_misses`.
- Résultat correction ciblée : `1 passed`.
- Commande exécutée : `make bench-relation-chains`.
- Résultat benchmark chain probe : `reports/relation_chain_probe.json` écrit ;
  `40` lignes, `40` complètes, `0` mismatch, `31` lignes avec relations
  fonctionnelles, `2` lignes `permutation_like`, `2` lignes
  `permutation_like` sans parasite restrictif, `1` ligne
  `interaction_unsat`, `2` lignes avec composante fonctionnelle cyclique,
  `1` obstruction de cycle fonctionnel et `28` lignes avec `constant_reject`.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée élargie : `6 passed`.
- Commande exécutée : `make quick`.
- Résultat correction finale : `268 passed`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
- Conclusion : T067 trouve un signal positif de gadget (`permutation_like`
  sans parasite restrictif) et un signal de corrélation (`interaction_unsat`
  non expliqué par constantes seules). Cela reste expérimental dans le scaffold
  relationnel et ne prouve ni NP-hardness ni polynomialité. `candidate.py` n'a
  pas été modifié.
- Next action : minimiser la ligne `interaction_unsat` et lancer une recherche
  promise-aware autour des deux permutations-like `paired_farthest`.

## 2026-05-23 interaction UNSAT core minimization

- Date/heure : 2026-05-23 16:07:30 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : la ligne `interaction_unsat` T067 peut être minimisée en
  un noyau relationnel lisible. Le noyau est un diagnostic du CSP matérialisé,
  pas un certificat négatif global.
- Changement fait : ajout de `tools/pc_relation_unsat_core_probe.py`, de la
  cible `make bench-relation-unsat-cores`, d'un test de régression et de la
  documentation T068. L'outil reporte tuples bruts, projections, suppression de
  relations et suppression de quartets source.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop` avec
  seulement `PLANS.md` modifié par l'ExecPlan et le tool T068 en brouillon ;
  `268 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats reçus : un sidecar
  recommande un langage prudent "diagnostic CSP matérialisé" ; un second
  corrige l'hypothèse initiale et prédit un noyau de taille `2` composé de
  l'unaire sur `0` et de la binaire `0-1`, avec `unary(1)` comme bruit.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py::test_relation_unsat_core_probe_minimizes_interaction_unsat`.
- Résultat correction ciblée : `1 passed`.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée élargie : `7 passed`.
- Commande exécutée : `make bench-relation-unsat-cores`.
- Résultat benchmark T068 : `reports/relation_unsat_core_probe.json` écrit ;
  `40` lignes, `40` complètes, `0` mismatch, `1` ligne `interaction_unsat`,
  `1` ligne avec noyau minimal, `min_core_size=2`, `28` lignes avec
  `constant_reject`.
- Noyau minimal observé : relation `1` unaire non booléenne sur `0`, valeurs
  acceptées `[0,1,3,5]`, plus relation `2` binaire
  `sparse_partial_matching` entre `0` et `1`, tuples bruts acceptés
  `[(2,3),(4,1)]`. La projection gauche `[2,4]` est disjointe de l'unaire.
- Commande exécutée : `make quick`.
- Résultat correction finale : `269 passed`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
- Conclusion : T068 transforme le signal T067 en artefact minimal régressé et
  corrige l'interprétation : l'UNSAT est ici un conflit unaire+binaire local,
  pas un gadget global ni une preuve de dureté. `candidate.py` n'a pas été
  modifié.
- Next action : explorer les profils `permutation_like` `paired_farthest` sous
  contrôle promise-aware, ou shrinker plus finement les quartets source du
  noyau T068.

## 2026-05-23 promise-aware permutation-like probe

- Date/heure : 2026-05-23 16:20:25 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les profils `permutation_like` parasite-free observés en
  T067 sur `paired_farthest/P3x2` apparaissent précisément quand le scaffold
  `P3/P3` coïncide avec les ordres quasi-circulaires exacts de `D` en petite
  taille.
- Changement fait : ajout de `tools/pc_permutation_like_probe.py`, de la cible
  `make bench-permutation-like`, d'un test de régression et de la documentation
  T069. L'outil compare les frontiers du scaffold aux ordres quasi exacts
  énumérés pour `n=6`, reporte les profils de permutation, les parasites et les
  affectations acceptées qui restent quasi.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `269 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats : un sidecar donne
  les deux profils exacts T067 et les métriques minimales ; un second confirme
  que la bonne vérification sans Hsu/McConnell est `frontiers scaffold` versus
  ordres quasi exacts ; un troisième propose le langage prudent de non-preuve.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py::test_permutation_like_probe_checks_exact_small_quasi_scaffold`.
- Résultat correction ciblée : `1 passed`.
- Commande exécutée : `make bench-permutation-like`.
- Résultat benchmark T069 : `reports/permutation_like_probe.json` écrit ;
  `128` lignes, `128` complètes, `0` mismatch, `11` lignes
  `permutation_like`, `11` lignes parasite-free, `11` lignes
  `permutation_like_exact_quasi_scaffold`, `0` anomalie.
- Détail : les hashes observés sont `2b53bb78399e16b4`, `879a45396db9d606`,
  `8f00a6c3d8fbf547` et `95c822d2b89a3b08`. Les affectations acceptées par les
  profils ciblés sont toutes quasi-circulaires dans les lignes exactes.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée élargie : `8 passed`.
- Commande exécutée : `make quick`.
- Résultat correction finale : `270 passed`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
- Conclusion : T069 renforce le signal local `permutation_like` en petite
  taille, mais ne prouve ni NP-difficulté, ni composabilité, ni reconstruction
  Hsu/McConnell générale. `candidate.py` n'a pas été modifié.
- Next action : construire ou chercher une instance multi-blocs où ces
  bijections locales se composent sans parasites destructeurs, ou prouver que
  les égalités de quasi-scaffold restent limitées à `n=6`.

## 2026-05-23 multi-block permutation composition probe

- Date/heure : 2026-05-23 16:30:48 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : les relations locales `permutation_like` T069 peuvent
  peut-être se composer sur plusieurs blocs `P3` sans parasites restrictifs.
- Changement fait : ajout de `tools/pc_permutation_composition_probe.py`, de la
  cible `make bench-permutation-composition`, d'un test de régression et de la
  documentation T070. L'outil mesure composantes d'arêtes `permutation_like`,
  parasites, comptes SAT et blocages par taille de scaffold.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `270 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats reçus : un sidecar
  recommande de définir une composition propre comme au moins deux arêtes
  `permutation_like` dans une même composante sans parasites ; un autre signale
  que le langage doit rester strictement diagnostic, sans claim de dureté.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py::test_permutation_composition_probe_reports_no_clean_multiblock_candidate`.
- Résultat correction ciblée : `1 passed`.
- Commande exécutée : `make bench-permutation-composition`.
- Résultat benchmark T070 : `reports/permutation_composition_probe.json` écrit ;
  `192` lignes, `192` complètes, `0` mismatch, `6` lignes
  `permutation_like`, `0` ligne multi-permutation, `0` candidat de composition,
  `max_permutation_component_edges=1`.
- Détail par bloc : `k=2` donne `5` bijections isolées propres ; `k=3` ne donne
  aucune bijection et `56` lignes avec `constant_reject` ; `k=4` donne une
  bijection isolée bloquée par parasites et `64` lignes avec `constant_reject`.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée élargie : `9 passed`.
- Commande exécutée : `make quick`.
- Résultat correction finale : `271 passed`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
- Conclusion : T070 est un signal négatif expérimental contre la composition
  naïve des gadgets locaux T069 dans `paired_farthest/P3x{k}`. Cela ne prouve
  pas qu'une autre famille globale de `D` ne puisse pas composer des bijections.
  `candidate.py` n'a pas été modifié.
- Next action : soit construire un générateur explicitement multi-blocs pour
  aligner plusieurs bijections locales, soit basculer vers une autre forme
  relationnelle moins fragile que `permutation_like`.

## 2026-05-23 all non-boolean relation component probe

- Date/heure : 2026-05-23 16:47:00 CEST.
- Commit hash : checkpoint commit containing this entry; report with
  `git log -1`.
- Hypothèse testée : l'échec T070 est peut-être spécifique aux
  `permutation_like`; en incluant toutes les relations binaires non booléennes,
  on devrait voir des composantes multi-blocs, mais elles risquent d'être
  systématiquement contaminées par parasites dans `paired_farthest/P3x{k}`.
- Changement fait : ajout de `tools/pc_relation_component_probe.py`, de la cible
  `make bench-relation-components`, d'un test de régression et de la
  documentation T071. L'outil construit les composantes de toutes les relations
  `binary_non_boolean_catalog`, compte les affectations de composante sous borne
  et reporte les parasites de ligne.
- Commande exécutée avant modification : `git status --short --branch`, puis
  `make quick`.
- Résultat correction avant modification : branche `research/agent-loop`
  propre ; `271 passed`, puis `JUSTE`.
- Plan subagents : trois sidecars lecture seule. Résultats reçus : un sidecar
  recommande T071 comme généralisation de T070 et reporte sur `192` lignes
  `617` relations binaires non booléennes, `127` lignes multi-arêtes et `0`
  multi-arêtes parasite-free ; un sidecar recommande `sparse_partial_matching`
  comme prochaine forme à cibler après T071 ; un sidecar déconseille toute
  intégration `candidate.py` et recommande de rester expérimental.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py::test_relation_component_probe_reports_multi_edge_relations_blocked_by_parasites`.
- Résultat correction ciblée : `1 passed`.
- Commande exécutée : `make bench-relation-components`.
- Résultat benchmark T071 : `reports/relation_component_probe.json` écrit ;
  `192` lignes, `192` complètes, `0` mismatch, `617` relations binaires non
  booléennes, `127` lignes avec composante multi-arêtes, `0` ligne multi-arêtes
  parasite-free, `0` ligne multi-arêtes parasite-free SAT, `156` lignes avec
  `constant_reject`, `max_component_edges=6`, `max_component_nodes=5`.
- Détail par bloc : `k=2` a `0` ligne multi-arêtes et `5` lignes parasite-free
  isolées ; `k=3` a `64/64` lignes multi-arêtes, toutes parasitées ; `k=4` a
  `63/64` lignes multi-arêtes, toutes parasitées.
- Commande exécutée :
  `PYTHONPATH=src:. rtk .venv/bin/pytest -q tests/test_csp_internal_benchmark.py`.
- Résultat correction ciblée élargie : `10 passed`.
- Commande exécutée : `make quick`.
- Résultat correction finale : `272 passed`, puis `JUSTE`.
- Commande exécutée : `make bench-quick`.
- Résultat benchmark candidate : `reports/complexity_report_quick.json` écrit ;
  `8` tailles, `40/40` runs réussis, `0` timeout et `0` incomplet.
- Conclusion : T071 montre que les réseaux non booléens existent
  hors `permutation_like`, mais qu'ils sont tous bloqués par parasites dans ce
  sweep. Ce n'est pas une preuve d'impossibilité. `candidate.py` n'a pas été
  modifié.
- Next action : cibler `sparse_partial_matching` et les conflits
  unaire+binaire T068, ou construire une famille `D` explicitement conçue pour
  éliminer les parasites.
