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
