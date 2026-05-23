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
- Checkpoint T034 courant : commit contenant la généralisation du certificat
  cycle haut impair vers
  `candidate_non_bipartite_high_graph_low_hub_obstruction`, le générateur
  `non_bipartite_high_graph_plus_low_hub`, et les régressions associées.
  Validation observée : tests candidats/générateurs/régressions ciblés,
  `make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
  `make bench-quick`, `make bench-piste-f`, `make bench`, benchmarks ciblés
  `odd_high_cycle_plus_low_hub/star` et
  `non_bipartite_high_graph_plus_low_hub/star`. Résultat observé :
  `mixed/star` garde `0` timeout et `0` incomplet jusqu'à `n=100` ; la famille
  non-cycle non-bipartie est rejetée en temps polynomial.
- Checkpoint T035 courant : commit contenant le générateur
  `even_high_cycle_plus_low_hub`, le certificat négatif
  `candidate_even_high_cycle_low_hub_obstruction`, et les régressions montrant
  que `C6` plus hub bas est négatif tandis que `C8` échappe au scan
  héréditaire `(4,5,6)`. Validation observée : tests
  candidats/générateurs/régressions ciblés, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`,
  et benchmark ciblé `even_high_cycle_plus_low_hub/star`. Résultat observé :
  `mixed/star` reste `0` timeout et `0` incomplet jusqu'à `n=100`; la famille
  cycle haut pair induit est rejetée en temps polynomial.
- Checkpoint T036 courant : commit contenant le diagnostic borné
  `low_hub_strong_ordering_report`, sans changement de `candidate.py`. Il teste
  expérimentalement la conjecture strong-ordering du cas binaire hub bas avec
  contrôles `C4`, `C6`, `C8`, `K3,3`, matching, chain/Ferrers, tree négatif,
  cas non applicables et limite factorielle. Validation observée :
  `tests/test_local_constraints.py`, probe exhaustive diagnostic `m=6`,
  `make unit`, `make quick`. Résultat observé : le diagnostic coïncide avec
  l'oracle exact jusqu'à `m<=5` et retrouve la frontière T035 à `m=6`.
- Checkpoint T037 courant : commit contenant
  `candidate_low_hub_strong_ordering_witness`, intégré seulement comme
  certificat positif vérifié. Les générateurs
  `chain_high_graph_plus_low_hub` et
  `complete_bipartite_high_graph_plus_low_hub` couvrent deux familles
  positives large-n ; les tests verrouillent le tree négatif, le PC-tree rigide
  non représentatif et `quasi_orders=[]`. Validation observée : tests ciblés
  candidats/générateurs/local-constraints/régressions, `make unit`,
  `make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
  `make bench`, plus benchmarks ciblés chain/complete low-hub star jusqu'à
  `n=80`. Résultat observé : `mixed/star` reste `0` timeout et `0` incomplet
  jusqu'à `n=100`; les familles positives ciblées sont acceptées sans timeout.
- Checkpoint T038 courant : commit contenant
  `passes_bad_side_precircular_cR` et
  `find_bad_side_precircular_cR_violation` dans `predicates.py`, utilisés par
  `candidate.py` et `low_hub_strong_ordering_report` pour valider les ordres en
  `O(n^3)` tout en gardant les tools d'oracle sur les quadruplets. Validation
  observée : tests ciblés prédicats/DP/candidate/local-constraints,
  probe local `6058` comparaisons, probe subagent `153291` comparaisons,
  `make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
  `make bench-quick`, `make bench`, et benchmarks ciblés chain/complete
  low-hub star jusqu'à `n=100`. Résultat observé : `mixed/star` reste `0`
  timeout et `0` incomplet jusqu'à `n=100`, médiane `0.0275s` à `n=100`.
- Checkpoint T039 courant : commit contenant
  `matching_high_graph_plus_low_hub`, la priorité composante-alignée de
  `low_hub_strong_ordering_report`, et la correction du diagnostic pour les
  niveaux bas `0` hors diagonale. Validation observée : tests ciblés
  local-constraints/générateurs/candidate, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`,
  et benchmark ciblé matching low-hub star jusqu'à `n=101`. Résultat observé :
  les matchings permutés sont trouvés au premier couple d'ordres, `mixed/star`
  reste `0` timeout et `0` incomplet jusqu'à `n=100`, médiane `0.0267s` à
  `n=100`.
- Checkpoint T040 courant : commit contenant
  `iter_low_hub_strong_ordering_witnesses`, la recherche candidate de témoin
  strong-ordering représenté par un PC-tree non-star, et la borne de frontiers
  root-aware pour ne pas sauter des énumérations exactes canoniques. Il ajoute
  les régressions matching non-star `n=18`, matching raffiné `n=10` à `720`
  frontiers réelles, et faux silence local `I_x(v)` sur `C6 + hub` raffiné.
  Validation observée : tests ciblés candidate/local-constraints, `make unit`,
  `make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
  `make bench`, et probe ciblée matching low-hub star jusqu'à `n=101`. Résultat
  observé : `mixed/star` reste `0` timeout et `0` incomplet jusqu'à `n=100`,
  médiane `0.0265s` à `n=100`.
- Checkpoint T041 courant : commit contenant
  `permuted_chain_high_graph_plus_low_hub`,
  `low_hub_ferrers_strong_ordering_report`, et l'intégration candidate du
  certificat positif Ferrers/chain low-hub. Il ajoute les régressions chaîne
  permutée large, matching non-Ferrers, et PC-tree non-star où le témoin
  Ferrers canonique est non représenté mais un autre témoin existe. Validation
  observée : tests ciblés candidate/local-constraints/generators, `make unit`,
  `make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
  `make bench`, et benchmark ciblé chaîne Ferrers permutée jusqu'à `n=101`.
  Résultat observé : `mixed/star` reste `0` timeout et `0` incomplet jusqu'à
  `n=100`, médiane `0.0287s` à `n=100`; la chaîne Ferrers permutée star a `0`
  timeout et médiane `0.2606s` à `n=101`.
- Checkpoint T042 courant : commit contenant
  `permuted_disjoint_chain_high_graph_plus_low_hub`,
  `low_hub_component_ferrers_strong_ordering_report`, et l'intégration
  candidate du certificat positif pour unions de composantes Ferrers low-hub.
  Il ajoute les régressions trois composantes permutées, matching dégénéré,
  composantes désalignées, `low=0` avec hubs multiples, non-Ferrers, et PC-tree
  non-star où le témoin component-wise est non représenté. Validation observée :
  tests ciblés candidate/local-constraints/generators, probe exact petits cas,
  `make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
  `make bench-quick`, `make bench`, et benchmark ciblé disjoint-chain star
  jusqu'à `n=101`. Résultat observé : `mixed/star` reste `0` timeout et `0`
  incomplet jusqu'à `n=100`, médiane `0.0295s` à `n=100`; la disjoint-chain
  star a `0` timeout et médiane `0.2433s` à `n=101`.
- Checkpoint T043 courant : commit contenant
  `pc_tree_guided_low_hub_matching_witness_report` et l'intégration candidate du
  certificat positif matching low-hub guidé par PC-tree. Il ajoute les
  régressions non-star T040/T042 devenues positives complètes, le cas `low=0`,
  les contrôles négatifs `C6/C8/tree`, et deux limites documentées :
  split-hubs `n=6` manqué sans rejet, et frontier tardive `n=8` qui exige
  `frontier_limit=80`. Validation observée : tests ciblés
  candidate/local-constraints/generators, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`.
  Résultat observé : `mixed/star` reste `0` timeout et `0` incomplet jusqu'à
  `n=100`, médiane `0.0314s` à `n=100`; le certificat T043 résout les
  matchings non-star ciblés avec `frontiers_sampled=0`.
- Checkpoint T044 courant : commit contenant le test de projection frontier
  dans `pc_tree_guided_low_hub_matching_witness_report`. Le certificat accepte
  un frontier représenté dont les cordes du matching haut croisent toutes après
  suppression des hubs, puis le revalide cR et `represents_order`. Il ajoute les
  régressions split-hubs `n=6` devenu positif, split-hubs large `n=12` côté
  candidate, et non-crossing C `n=6` négatif. Validation observée : tests ciblés
  candidate/local-constraints/generators, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`.
  Résultat observé : `mixed/star` reste `0` timeout et `0` incomplet jusqu'à
  `n=100`, médiane `0.03139s` à `n=100`; la frontier tardive `n=8` reste une
  limite à `frontier_limit=64`.
- Checkpoint T045 courant : commit contenant
  `exact_low_hub_matching_projection_search_report` et son intégration candidate
  bornée. Le rapport énumère paresseusement les ordres `seq + mate(seq)` avec
  hubs insérés, teste d'abord `represents_order`, puis cR, et retourne un
  négatif complet seulement si tous les candidats uniques sous la limite sont
  épuisés. Régressions ajoutées : frontier tardive `n=8` positive, rigide
  non-crossing `n=6` négatif, limite basse explicite, lazy hit `n=13`, et rejet
  candidate non-crossing `n=12`. Validation observée : tests ciblés
  candidate/local-constraints/generators, probe oracle `19` couples,
  `make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
  `make bench`. Résultat observé : `mixed/star` reste `0` timeout et `0`
  incomplet jusqu'à `n=100`, médiane `0.03311s` à `n=100`.
- Checkpoint T046 courant : commit contenant
  `exact_low_hub_matching_projected_pc_tree_search_report` et son intégration
  candidate bornée avant T045. Le rapport énumère seulement les projections
  matching `seq + mate(seq)`, relève les hubs via la structure `P/C` du PC-tree
  original, puis vérifie cR et représentation. Régressions ajoutées : frontier
  tardive projetée, rigide non-crossing, limite de projections, facteur hubs,
  oracle petits PC-trees, rejet candidate avec `5` paires et `8` hubs, faux
  silence local `I_x(v)` minimal `n=5`, et contre-exemple side-only/2-SAT naïf.
  Validation observée : tests ciblés candidate/local-constraints/régressions,
  probe oracle `14` couples, `make quick`, `make hunt-counterexamples`,
  `make check`, `make bench-quick`, `make bench`. Résultat observé :
  `mixed/star` reste `0` timeout et `0` incomplet jusqu'à `n=100`, médiane
  `0.03504s` à `n=100`.
- Checkpoint T047 courant : commit contenant la compilation bad-side
  support-local hors candidate. `compile_bad_side_nogoods_support_local`
  énumère le produit des domaines de `quartet_support_paths` par atom, puis
  déduplique par signature effective de pruning. Régressions ajoutées :
  reconstructeur de projection d'atom, wrapping, égal-distance, limite de
  support, collision de canonicalisation globale, solveur pruné support-local.
  Validation observée : `tests/test_sat_like_experiments.py`, probe
  support-local `577` couples sans mismatch, `make bench-csp-quick`
  (`0` mismatch, `0` support mismatch, `0` signature mismatch), `make quick`,
  `make check`, `make bench-quick`, `make bench`. Résultat observé : le
  benchmark interne passe de `31616` nogoods atom-labellisés à `2904`
  signatures support-local, avec ratio médian `support_vs_old_scan_ratio=0.25`,
  mais la compilation support-local reste plus lente sur les très petits arbres
  du quick benchmark ; `mixed/star` reste `0` timeout et `0` incomplet jusqu'à
  `n=100`, médiane `0.03458s` à `n=100`.
- Checkpoint T048 courant : commit contenant la compilation bad-side groupée
  par support hors candidate. `compile_bad_side_nogoods_grouped_support_local`
  énumère chaque produit de domaines de support une seule fois, teste les atoms
  du groupe et déduplique par signature effective. Validation observée :
  `tests/test_sat_like_experiments.py` (`31 passed`), probe indépendant
  `130` cas sans mismatch, `make bench-csp-quick` (`192` lignes,
  `0` mismatch, `0` support mismatch, `0` grouped mismatch,
  `0` signature mismatch), `make quick`, `make check`. Résultat observé :
  produit support T047 `72256` contre produit groupé `6224`, ratio médian
  `0.11111`, mêmes `2904` signatures que T047, mais
  `total_grouped_atom_checks=72256`; le prochain progrès doit donc réduire les
  tests atom-par-atom ou prouver une borne sur la taille des groupes.
- Checkpoint T049 courant : commit contenant la variante first-hit groupée hors
  candidate. `compile_bad_side_nogoods_grouped_first_hit_support_local`
  s'arrête au premier atom violé pour chaque affectation de support, en
  conservant les mêmes signatures effectives que T048/T047. Validation
  observée : `tests/test_sat_like_experiments.py` (`39 passed`), probe
  indépendant `130` cas sans mismatch, subagent contre-exemples `220` cas sans
  mismatch, `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `0` first-hit mismatch, `0` mismatch de signatures), `make quick`,
  `make check`. Résultat observé : `atom_checks` passe de `72256` à `41872` sur
  la gate CSP rapide, mais les diagnostics `atom`/`pair` deviennent des
  représentants de premier témoin et ne sont plus exhaustifs.
- Checkpoint T050 courant : commit contenant le profil first-hit hors
  candidate. Les métriques `first_hit_*` mesurent hits, no-hit, positions de
  premier hit et checks dépensés/sauvés, sans changer les signatures de pruning.
  Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`41 passed`), `make quick` (`223 passed`, puis `JUSTE`), `make check`,
  `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `0` first-hit mismatch, `0` mismatch de signatures), probe par familles
  `n=4..8`, et audit subagent de non-interférence. Résultat observé :
  `3320/6224` affectations de support sont no-hit sur la gate CSP rapide et
  consomment `30520` checks ; les métriques sont dépendantes de l'ordre de scan,
  pas des invariants mathématiques.
- Checkpoint T051 courant : commit contenant
  `bad_side_grouped_support_outcome_profile` hors candidate. Le profil mesure
  hit/no-hit par support groupé, tranches unaires pures et test
  pair-side/composantes de mauvais témoins. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`44 passed`), `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `0` first-hit mismatch, `profile_pair_side_split_mismatches=0`),
  `make quick` (`226 passed`, puis `JUSTE`), `make check`, et
  `make bench-quick` (`0` timeout, `0` incomplet). Résultat
  observé : le test pair-side est exact sur la gate mais plus coûteux que
  first-hit (`profile_pair_side_split_work_ratio=1.7732`) ; les tranches
  unaires couvrent `1888/3320` no-hit globalement mais `0%` sur les familles
  cycliques de la gate rapide.
- Checkpoint T052 courant : commit contenant `_witness_side_cache_key` et le
  profil cached witness-side hors candidate, plus le corpus de références sous
  `docs/references/`. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`45 passed`), `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `profile_pair_side_split_mismatches=0`), `make quick` (`227 passed`, puis
  `JUSTE`), `make check`, `make bench-quick` (`40/40` runs, `0` timeout,
  `0` incomplet). Résultat observé : cache simple des
  côtés `49558` checks, ratio `1.1836x` first-hit ; modèle
  bitset-composantes `27846` checks, ratio `0.6650x`; la clé triple complète
  est protégée par un test de choix imbriqué.
- Checkpoint T053 courant : commit contenant le profil bitset/composantes réel
  hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`49 passed`), régressions ciblées (`60 passed`), `make bench-csp-quick`
  (`192` lignes, `0` mismatch,
  `profile_pair_side_split_bitset_mismatches=0`), `make quick`
  (`232 passed`, puis `JUSTE`), `make check`, `make bench-quick`
  (`40/40` runs, `0` timeout, `0` incomplet). Résultat observé : le
  classifieur local est exact sur la gate, mais le coût réel bitset est
  `44936` checks (`1.0732x` first-hit) contre une projection théorique
  `27822` checks (`0.6645x`). `candidate.py` n'a pas été modifié.
- Checkpoint T054 courant : commit contenant la mesure de cardinalité des états
  de masques hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`49 passed`), `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `component_mask_state_mismatches=0`), probe stress `n=8` (`30` lignes,
  `0` mismatch), `make quick` (`232 passed`, puis `JUSTE`), `make check`,
  `make bench-quick` (`40/40` runs, `0` timeout, `0` incomplet). Résultat
  observé : `2920` états pour `6224` affectations (`0.4692`), bucket moyen
  `2.1315`, bucket max `4`; quotient exact mais faible, pas DP compacte.
  `candidate.py` n'a pas été modifié.
- Checkpoint T055 courant : commit contenant les quotients d'états de masques
  hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`50 passed`), `make bench-csp-quick` (`192` lignes, `0` mismatch),
  probe stress `n=8` (`30` lignes, `0` mismatch), `make quick`
  (`233 passed`, puis `JUSTE`), `make check` (`JUSTE`), `make bench-quick`
  (`40/40` runs, `0` timeout, `0` incomplet). Résultat observé :
  `mask_multiset` compresse à `0.3959` sur la gate rapide sans état mixte,
  tandis que `side_blind_schema` descend à `0.1250` mais produit `358` états
  mixtes ; le cas minimal `cycle_metric(4)`/`balanced_pc_tree(4, kind="C")`
  est régressé. Aucun changement dans `candidate.py`.
- Checkpoint T056 courant : commit contenant le diagnostic de collisions de
  contexte des quotients hors candidate. Validation observée :
  `tests/test_regression_counterexamples.py tests/test_sat_like_experiments.py
  tests/test_csp_internal_benchmark.py` (`64 passed`),
  `make bench-csp-quick` (`192` lignes, `0` mismatch), probe stress `n=8`
  (`20` lignes, `0` mismatch), `make quick` (`236 passed`, puis `JUSTE`),
  `make check` (`JUSTE`), `make bench-quick` (`40/40` runs, `0` timeout,
  `0` incomplet). Résultat observé : `mask_multiset` a `856` collisions de
  contexte sur la gate CSP rapide et un contre-exemple global `n=5` avec même
  `mask_multiset=(1,2)` mais décisions cR différentes est régressé. Les
  collisions de `full` montrent que les états de masques fermés ne suffisent
  pas comme états DP autonomes. Aucun changement dans `candidate.py`.

## Rollback

Si une modification régresse et que la cause n’est pas claire :

1. noter la régression dans `docs/experiment_log.md` ;
2. inspecter `git diff` ;
3. corriger si la cause est claire ;
4. sinon revenir au dernier commit green indiqué ici.

Ne pas effacer les rapports ou contre-exemples importants pendant le rollback.
