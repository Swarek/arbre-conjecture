# Checkpoints

Un commit stable doit satisfaire :

- `make quick` passe ;
- `make bench-quick` écrit un rapport JSON ou documente explicitement les
  timeouts/incomplétudes ;
- `docs/experiment_log.md` décrit l’hypothèse, la commande et la conclusion ;
- aucun contre-exemple connu n’est supprimé.

## Dernier commit green

- Initial setup : `e5f0ec3` (`checkpoint: baseline research setup with
  correctness and complexity gates`).
- Statut attendu : baseline exacte `n <= 8`, placeholder incomplet au-delà.
- Validation initiale : `make quick` vert et `make bench-quick` sans timeout,
  avec runs incomplets explicitement comptés pour `n > 8`.
- Checkpoint Goal 2026-05-22 : `7da77f5` (`checkpoint: add obstruction
  diagnostics and stress families`). Diagnostics d’obstructions,
  contre-exemples farthest, familles Piste F et benchmark ciblé ajoutés.
  Validation observée : `make quick`, `make hunt-counterexamples`,
  `make check`, `make bench-quick`, `make bench-piste-f`.
- Checkpoint Prop. 4.5 : `07120e4` (`checkpoint: add prop 4.5 fixed-order
  diagnostic`). Diagnostic d’ordre fixé quasi-circulaire ajouté. Validation
  observée : `make quick`, `make check`, probe exhaustif `n <= 5` sur ordres
  quasi-circulaires sans désaccord.

Dernier commit green avant T009 : `07120e4`.

- Checkpoint T009 : `f17ad89` (`checkpoint: add prop45 nogood frontier
  experiment`). Scan Prop. 4.5 comme nogood de frontier ajouté. Validation
  observée : `make unit`, `make quick`, `make check`, `make bench-quick`, probe
  random bornée sans désaccord sur ordres quasi-circulaires.
- Checkpoint T010 : `f7aa62f` (`checkpoint: add local domain csp scaffold`).
  Scaffold CSP à domaines locaux `P/C` ajouté. Validation observée :
  `make quick`, `make check`, `make bench-quick`, probe CSP directe sans
  désaccord sur 1600 instances.
- Checkpoint T011 : `53cc4cf` (`checkpoint: compile cr quartet nogoods`).
  Nogoods compilés de quartets cR ajoutés. Validation observée : `make quick`,
  `make check`, `make bench-quick`, probe compiled-nogood sans désaccord sur
  960 instances.
- Checkpoint T012 : `9346feb` (`checkpoint: add pruned nogood backtracking`).
  Backtracking pruné par nogoods compilés ajouté. Validation observée :
  `make quick`, `make check`, `make bench-quick`, probe pruned-nogood sans
  désaccord sur 640 instances.
- Checkpoint T013 : `1b0ad1c` (`checkpoint: add csp internal benchmark`).
  Benchmark interne Piste C ajouté. Validation observée : `make quick`,
  `make check`, `make bench-csp-quick`, `make bench-quick`.
- Checkpoint T014 : `0c60de8` (`checkpoint: add bad-side dp signature
  diagnostic`). Diagnostic bad-side fixed-order Piste B ajouté. Validation
  observée : `make unit`, probe bad-side `715875` comparaisons, `make quick`,
  `make check`, `make bench-quick`.
- Checkpoint T015 : `ed52c2e` (`checkpoint: measure bad-side block
  signatures`). Métriques de signature de bloc Piste B ajoutées. Validation
  observée : `make unit`, probe signature de blocs `27` lignes, `make quick`,
  `make check`, `make bench-quick`.
- Checkpoint T016 : `eff96c1` (`checkpoint: add universal bad-witness
  subcase`). Sous-cas universel `|B(a,b)| <= 1` intégré à la candidate.
  Validation observée : `make unit`, probe large-n `33` checks, `make quick`,
  `make check`, `make hunt-counterexamples`, `make bench-quick`.
- Checkpoint T017 : `376ecea` (`checkpoint: certify sampled positive
  witnesses`). Certification des témoins positifs échantillonnés. Validation
  observée :
  `make unit`, `make quick`, `make check`, `make hunt-counterexamples`,
  `make bench-quick`, `make bench` (`0` timeout, `42` incomplets visibles).
- Checkpoint T018 : `aad8e98` (`checkpoint: add minimum-distance cycle
  witness`). Commit contenant le témoin minimum-cycle star, le
  contre-exemple régressé `n=6` montrant que le graphe minimum cycle ne suffit
  pas pour cR, et la capture Proposition 4.4 conservée dans
  `docs/source_materials/images/`. Validation observée : `make unit`,
  `make quick`, `make check`, `make hunt-counterexamples`,
  `make bench-piste-f`, `make bench-quick`, `make bench` (`0` timeout, `42`
  incomplets visibles, fit polynomial empirique `p ~= 3.25`).
- Checkpoint T019 : `1588166` (`checkpoint: certify minimum-cycle witnesses in
  represented pc trees`). Commit contenant `represents_order` non énumératif
  pour les ordres fixés du scaffold PC-tree, l'extension du témoin
  minimum-cycle aux PC-trees non-star représentés, et le contre-exemple
  régressé où un min-cycle cR non représenté ne doit pas être accepté.
  Validation observée : `make unit`, probe membership `11837` checks,
  `make quick`, `make check`, `make hunt-counterexamples`,
  `make bench-piste-f`, `make bench-quick`, `make bench` (`0` timeout, `42`
  incomplets visibles, fit polynomial empirique `p ~= 3.25`).
- Checkpoint T020 courant : commit contenant le témoin structurel
  paired-farthest pour les matrices three-level à matching maximal, et le
  contre-exemple régressé où ce témoin cR n'est pas représenté par un PC-tree
  non-star. Validation observée : `make unit`, probe `paired_farthest`
  `380` checks, `make quick`, `make check`, `make hunt-counterexamples`,
  `make bench-piste-f`, `make bench-quick`, `make bench` (`0` timeout, `42`
  incomplets visibles, fit polynomial empirique `p ~= 3.24`).
- Checkpoint T021 courant : commit contenant les régressions
  `paired_farthest` non-star `n=6`, la documentation des résultats subagents
  Piste A/B/F, et la décision de ne pas intégrer la génération side-by-side
  non bornée dans `candidate.py`. Validation observée : test ciblé
  `tests/test_regression_counterexamples.py`, `make quick`, `make bench-piste-f`.
- Checkpoint T022 courant : commit contenant
  `project_farthest_sets_to_pc_nodes` comme diagnostic Piste A/D, tests
  égal-distance et nœud `C`, et documentation de non-décision. Validation
  observée : `tests/test_local_constraints.py`, `make unit`, `make quick`,
  `make bench-quick` (`0` timeout, `0` incomplet).
- Checkpoint T023 courant : commit contenant les prédicats stricts d'ordre fixé,
  `strict_order_report`, les régressions Fig. 2.2 / égal-distance / cycle /
  témoin strict non représenté, et la documentation de non-intégration
  candidate. Validation observée : `tests/test_strict_experiments.py`,
  `make unit`, `make quick`, `make bench-quick` (`0` timeout, `0` incomplet).
- Checkpoint T024 courant : commit contenant `strict_algorithm52_report`, un
  générateur expérimental inspiré de l'Algorithm 5.2 et filtré par les prédicats
  stricts directs, plus les régressions cycle/Fig. 2.2/random/PC-tree. Validation
  observée : `tests/test_strict_experiments.py`, probe stricte random bornée,
  `make unit`, `make quick`, `make bench-quick`.
- Checkpoint T025 courant : commit contenant `strict_ball_circular_ones_report`,
  diagnostic borné comparant boules non triviales comme arcs, quasi-circularité,
  strict quasi et strict circular, avec signatures exactes de modules par
  boules et contre-exemple random `ball_arc/quasi` non cR. Validation observée :
  `tests/test_strict_experiments.py`, probe ball/quasi random bornée,
  `make unit`, `make quick`, `make bench-quick`.
- Checkpoint T026 courant : commit contenant
  `bad_witness_arc_constraints_report`, diagnostic borné comparant la condition
  exacte one-side des mauvais témoins à deux contraintes d'arcs naïves. Il
  verrouille que `B(a,b)` arc est trop fort et que
  `B(a,b) union {a,b}` est ni nécessaire ni suffisant. Validation observée :
  `tests/test_dp_experiments.py`, `make unit`, `make quick`,
  `make bench-quick` (`0` timeout, `0` incomplet).
- Checkpoint T027 courant : commit contenant la compilation CSP bad-side par
  paire (`forbidden_bad_side_atoms`, `compile_bad_side_nogoods`,
  `solve_compiled_bad_side_nogood_csp`, `solve_pruned_bad_side_nogood_csp`).
  Les tests verrouillent l'exactitude fixed-order exhaustive `n=4`, les
  égalités, le wrapping non-cR et l'équivalence au filtre cR direct sur arbres
  supportés. Validation observée : `tests/test_sat_like_experiments.py`, probe
  fanout 3 bad-side/quartets, `make unit`, `make quick`, `make bench-csp-quick`,
  `make bench-quick`.
- Checkpoint T028 courant : commit contenant le sous-cas
  `candidate_exact_bounded_pc_tree_frontiers`. La candidate calcule une borne
  indépendante saturée sur le nombre de frontiers du PC-tree scaffold et énumère
  exactement seulement si la borne est sous `EXACT_PC_TREE_FRONTIER_LIMIT`.
  Validation observée : `tests/test_candidate.py`, probe oracle PC-tree `42`
  décisions, `make unit`, `make quick`, `make hunt-counterexamples`,
  `make check`, `make bench-quick`.
- Checkpoint T029 courant : commit contenant le sous-cas
  `candidate_exact_bounded_quasi_orders`. La candidate décide exactement une
  famille explicite `quasi_orders` seulement si elle expose une longueur fiable
  et si cette longueur est sous `EXACT_QUASI_ORDER_LIMIT`. Les familles trop
  grandes et les itérateurs non dimensionnés restent incomplets en négatif.
  Validation observée : `tests/test_candidate.py`, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`.
- Checkpoint T030 courant : commit contenant l'attribution `resolved_kind` des
  benchmarks `mixed`, sans changement de `candidate.py`. Le rapport de
  complexité conserve `seed`, `mixed_instance_kinds`, et les compteurs
  `resolved_kind_*`. Validation observée : tests générateurs/benchmark ciblés,
  `make unit`, `make quick`, `make check`, `make bench-quick`, `make bench`.
  Résultat observé : les `42` incomplets du benchmark fort `mixed/star` sont
  tous `random`, avec `0` timeout. `make bench-piste-f` passe aussi avec `0`
  timeout ; `paired_farthest/mixed` reste incomplet seulement pour `n=16,20`.
- Checkpoint T031 courant : commit contenant le certificat négatif héréditaire
  `candidate_small_forbidden_submatrix_obstruction` par sous-matrice 4 points,
  plus la validation cR directe du témoin paired-farthest. Validation observée :
  `tests/test_candidate.py`, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`,
  `make bench-piste-f`. Résultat observé : `make bench` a `0` timeout et `0`
  incomplet jusqu'à `n=100`; les `42` anciens placeholders random sont rejetés
  par obstruction 4-points.
- Checkpoint T032 courant : commit contenant le contre-exemple minimal
  `four_local_non_cr_core`, son padding large `padded_four_local_non_cr`, et
  l'extension du certificat héréditaire aux tailles `(4,5)`. Validation
  observée : tests candidats/générateurs/régressions ciblés, `make unit`,
  `make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
  `make bench`, benchmark ciblé `four_local_non_cr/star`. Résultat observé : le
  4-local seul est réfuté, mais les rejets 5-points restent sound quand le noyau
  induit est trouvé.
- Checkpoint T033 courant : commit contenant le contre-exemple minimal
  `five_local_non_cr_core`, son padding large `padded_five_local_non_cr`, le
  générateur `odd_high_cycle_plus_low_hub`, l'extension du certificat
  héréditaire aux tailles `(4,5,6)`, et le certificat structurel négatif
  `candidate_odd_high_cycle_low_hub_obstruction`. Validation observée : tests
  candidats/générateurs/régressions ciblés, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`,
  `make bench-piste-f`, benchmarks ciblés `five_local_non_cr/star` et
  `odd_high_cycle_plus_low_hub/star`. Résultat observé : le 5-local seul est
  réfuté ; la famille cycle haut impair plus hub bas est désormais rejetée par
  un certificat polynomial.

## Rollback

Si une modification régresse et que la cause n’est pas claire :

1. noter la régression dans `docs/experiment_log.md` ;
2. inspecter `git diff` ;
3. corriger si la cause est claire ;
4. sinon revenir au dernier commit green indiqué ici.

Ne pas effacer les rapports ou contre-exemples importants pendant le rollback.
